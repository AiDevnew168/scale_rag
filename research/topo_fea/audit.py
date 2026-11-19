#!/usr/bin/env python3
"""Real TopoGraphRAG layout-text feasibility gate. No gold fields enter retrieval."""
import csv, hashlib, io, json, random, re, tarfile, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import zstandard
from sklearn.feature_extraction.text import TfidfVectorizer

SEED=261119
BASE="https://huggingface.co/datasets/diandianone123/topographrag-bench/resolve/main/"
OUT=Path("results"); OUT.mkdir(exist_ok=True)

def download(remote,local):
    path=Path(local)
    if not path.exists(): urllib.request.urlretrieve(BASE+remote,path)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    print("SOURCE",remote,path.stat().st_size,digest,flush=True)
    return path

def gold(q):
    if q["question_type"]=="synthesis":
        facts=q.get("answer",{}).get("evidence_points",[]) or []
        required=set((q.get("evidence_validation") or {}).get("required") or [])
        if required: facts=[p for p in facts if p.get("fact_id") in required]
        return {(int(x["source_page"]),int(x["source_layout"])) for x in facts if x.get("source_page") is not None and x.get("source_layout") is not None}
    return {(int(x["page_id"]),int(x["layout_id"])) for x in q.get("evidence_sources",[]) if x.get("page_id") is not None and x.get("layout_id") is not None}

def sample(questions):
    rng=random.Random(SEED); output=[]
    for kind,target in [("bridge_chain",180),("synthesis",120)]:
        groups=defaultdict(list)
        for q in questions:
            if q["question_type"]==kind and len(gold(q))>1:groups[q["doc_id"]].append(q)
        docs=sorted(groups); rng.shuffle(docs)
        for g in groups.values():rng.shuffle(g)
        picked=[]
        while len(picked)<target and any(groups.values()):
            for doc in docs:
                if groups[doc] and len(picked)<target:picked.append(groups[doc].pop())
        output+=picked
    rng.shuffle(output)
    return output

def text_layouts(archive, manifest):
    name2id={d["files"]["layout_content"].replace("\\","/").lstrip("./"):int(d["doc_id"]) for d in manifest["documents"]}
    docs=defaultdict(list); stats=Counter(); printed=False
    with open(archive,"rb") as f:
        with zstandard.ZstdDecompressor().stream_reader(f) as stream:
            with tarfile.open(fileobj=stream,mode="r|") as tar:
                for member in tar:
                    if not member.isfile() or not member.name.endswith(".jsonl"):continue
                    name=member.name.lstrip("./")
                    doc=name2id.get(name)
                    if doc is None:
                        # Archive may include harmless root prefix.
                        matches=[i for n,i in name2id.items() if name.endswith("/"+n) or name==n]
                        doc=matches[0] if len(matches)==1 else None
                    if doc is None:stats["unmapped_files"]+=1;continue
                    content=tar.extractfile(member).read().decode("utf-8",errors="replace")
                    for line in content.splitlines():
                        if not line.strip():continue
                        try:x=json.loads(line)
                        except json.JSONDecodeError:stats["invalid_line"]+=1;continue
                        page=x.get("page_idx",x.get("page_id"))
                        layout=x.get("layout",x.get("layout_id"))
                        if not isinstance(page,int) or not isinstance(layout,int):
                            stats["missing_location"]+=1;continue
                        typ=str(x.get("type","text")).lower()
                        parts=[x.get(k) for k in ("text","ocr_text","vlm_text")]
                        txt=" ".join(v.strip() for v in parts if isinstance(v,str) and v.strip())[:6000]
                        stats["layouts_total"]+=1
                        stats["modality_"+typ]+=1
                        if not txt:stats["no_text_"+typ]+=1;continue
                        docs[doc].append(dict(page=page,layout=layout,type=typ,text=txt))
                        if not printed:
                            print("FIRST_LAYOUT",json.dumps(docs[doc][-1],ensure_ascii=False)[:400],flush=True)
                            printed=True
    print("LAYOUT_STATS",json.dumps(dict(stats)),flush=True)
    print("MAPPED_DOCS",len(docs),flush=True)
    return docs,stats

def choose_pool(scores,n=50):
    return np.argsort(-scores,kind="stable")[:min(n,len(scores))].tolist()

def select_mmr(pool,raw,M,k):
    res=[]
    while len(res)<min(k,len(pool)):
        def utility(i):
            sim=max((float(M[i].multiply(M[j]).sum()) for j in res),default=0.)
            return raw[i]-.3*sim
        res.append(max((i for i in pool if i not in res),key=utility))
    return res

def select_graph(pool,raw,M,items,k):
    # Frozen, query-blind pairwise coherence proxy; not a published SOTA solver.
    cand=pool[:20]
    if len(cand)<2:return cand
    def edge(i,j):
        sim=float(M[i].multiply(M[j]).sum())
        page_gap=abs(items[i]["page"]-items[j]["page"])
        return .15*min(sim,.35)-.1*max(0.,sim-.65)+.02/(1+page_gap)
    best=max(((raw[i]+raw[j]+edge(i,j),i,j) for idx,i in enumerate(cand) for j in cand[idx+1:]),key=lambda x:x[0])
    result=[best[1],best[2]]
    while len(result)<min(k,len(pool)):
        def utility(i):
            redundant=max((float(M[i].multiply(M[j]).sum()) for j in result),default=0.)
            return raw[i]+max(edge(i,j) for j in result)-.3*redundant
        result.append(max((i for i in pool if i not in result),key=utility))
    return result

def role_match(question,items,M,vec,pool,raw,k=6):
    """Blind bipartite two-role assignment; roles parsed from question alone."""
    q=question.strip()
    m=re.match(r"(?is)^(?:for|among|in|of)\b(.{12,350}?),\s*(.+)$",q)
    if m:
        r1,r2=m.group(1),m.group(2)
    else:
        split=re.search(r",\s*(?:what|which|how|where|who|why)\b",q,re.I)
        if split:r1,r2=q[:split.start()],q[split.start()+1:]
        else:
            parts=q.split()
            mid=max(1,len(parts)//2)
            r1,r2=" ".join(parts[:mid])," ".join(parts[mid:])
    if len(r1.split())<3 or len(r2.split())<3:return pool[:k]
    v1=vec.transform([r1]);v2=vec.transform([r2])
    a=np.asarray((M@v1.T).toarray()).ravel()
    b=np.asarray((M@v2.T).toarray()).ravel()
    cand=pool[:min(40,len(pool))]
    similarity=(M[cand]@M[cand].T).toarray()
    best=(-1e30,None,None)
    for x,i in enumerate(cand):
        for y,j in enumerate(cand):
            if i==j:continue
            sim=float(similarity[x,y])
            cohesion=.10*min(sim,.5)-.15*max(0.,sim-.7)
            score=.55*(a[i]+b[j])+.45*(raw[i]+raw[j])+cohesion
            if score>best[0]:best=(score,i,j)
    if best[1] is None:return pool[:k]
    selected=[best[1],best[2]]
    selected.extend(i for i in pool if i not in selected)
    return selected[:k]

def predictions(question,items,M,vectorizer):
    scores=np.asarray((M@vectorizer.transform([question]).T).toarray()).reshape(-1)
    pool=choose_pool(scores,50)
    return {"top":pool,"mmr":select_mmr(pool,scores,M,6),"graph_proxy":select_graph(pool,scores,M,items,6),"role_match":role_match(question,items,M,vectorizer,pool,scores,6)}

def score(q,items,pred):
    # Evaluation-only access to gold. None of the above functions gets q.
    target=gold(q);allkeys={(x["page"],x["layout"]) for x in items}
    out=dict(qid=q.get("mh_id") or q.get("sq_id"),doc_id=q["doc_id"],kind=q["question_type"],
             n_gold=len(target),n_layouts=len(items),all_gold_text_available=int(target<=allkeys),
             cross_modal=int(bool(q.get("cross_modal"))))
    for method,p in pred.items():
        for k in (2,6,50):
            seen={(items[i]["page"],items[i]["layout"]) for i in p[:k]}
            out[f"{method}_full_{k}"]=int(target<=seen)
            out[f"{method}_recall_{k}"]=len(target&seen)/len(target)
    return out

def main():
    p=download("annotations/benchmark.json","benchmark.json")
    m=download("manifest.json","manifest.json")
    a=download("archives/layout_content.tar.zst","layouts.tar.zst")
    questions=json.loads(p.read_text());manifest=json.loads(m.read_text())
    assert len(questions)==2024
    chosen=sample(questions); assert len(chosen)==300,len(chosen)
    print("SAMPLE_COUNTS",dict(Counter(q["question_type"] for q in chosen)),
          "SAMPLED_DOCS",len({q["doc_id"] for q in chosen}),flush=True)
    (OUT/"sample_ids.json").write_text(json.dumps([q.get("mh_id") or q.get("sq_id") for q in chosen],indent=2))
    docs,source_stats=text_layouts(a,manifest)
    by_doc=defaultdict(list)
    for q in chosen:by_doc[q["doc_id"]].append(q)
    rows=[];missing=Counter()
    for doc,queries in by_doc.items():
        items=docs.get(doc,[])
        if len(items)<2:missing["unavailable_doc"]+=len(queries);continue
        try:
            vec=TfidfVectorizer(stop_words="english",ngram_range=(1,2),sublinear_tf=True,max_features=45000)
            M=vec.fit_transform([x["text"] for x in items])
        except ValueError:
            missing["empty_vocabulary"]+=len(queries);continue
        for q in queries:
            pred=predictions(q["question"],items,M,vec)
            rows.append(score(q,items,pred))
    with (OUT/"per_question.csv").open("w",newline="",encoding="utf8") as f:
        if rows:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    def avg(k,part):
        return round(100*sum(r[k] for r in part)/len(part),2) if part else None
    metric_keys=["all_gold_text_available"]+ [f"{method}_{what}_{k}" for method in ("top","mmr","graph_proxy","role_match") for what in ("full","recall") for k in (2,6)] + ["top_full_50"]
    by_kind={}
    for kind in ("bridge_chain","synthesis"):
        part=[x for x in rows if x["kind"]==kind]
        by_kind[kind]={"n":len(part),"metrics_percent":{key:avg(key,part) for key in metric_keys}}
    # Fixed paired comparisons; bootstrap resamples whole source documents.
    rng=random.Random(SEED)
    bydoc=defaultdict(list)
    for rr in rows:bydoc[rr["doc_id"]].append(rr)
    document_ids=sorted(bydoc)
    paired={}
    for method in ("mmr","graph_proxy","role_match"):
        for budget in (2,6):
            new=f"{method}_full_{budget}"; old=f"top_full_{budget}"
            wins=sum(x[new] and not x[old] for x in rows)
            losses=sum(x[old] and not x[new] for x in rows)
            delta=round(100*(wins-losses)/len(rows),3)
            boots=[]
            for _ in range(2000):
                picks=[rng.choice(document_ids) for _ in document_ids]
                rr=[row for d in picks for row in bydoc[d]]
                boots.append(100*sum(x[new]-x[old] for x in rr)/len(rr))
            ci=np.percentile(boots,[2.5,97.5])
            paired[f"{method}_versus_top_at{budget}"]={"wins":wins,"losses":losses,
                "delta_pp":delta,"cluster_bootstrap_ci95_pp":[round(float(ci[0]),3),round(float(ci[1]),3)]}
    report={"schema":"topo-failure-headroom-v1","source_dataset":"diandianone123/topographrag-bench",
       "seed":SEED,"total_questions":2024,"requested":300,"scored":len(rows),
       "missing":dict(missing),"source_layout_stats":dict(source_stats),
       "metrics_percent":{key:avg(key,rows) for key in metric_keys},"by_topology":by_kind,"paired":paired,
       "status":"valid_initial_text_proxy" if len(rows)>=200 else "insufficient_scored_questions",
       "limitations":["Real layout text/OCR/VLM descriptions only, no direct image reading",
        "TF-IDF is a weak lexical baseline, not Cross-Encoder or FlowReader",
        "Pairwise graph proxy is a fixed diagnostic heuristic, NOT a proposed novel optimizer",
        "Two-role assignment is a fixed lexical pilot, NOT a trained semantic constrained optimizer",
        "Gold labels exclusively used in metric computation",
        "No VLM end-to-end answer-accuracy test was run"]}
    (OUT/"report.json").write_text(json.dumps(report,indent=2))
    print("RESULT_JSON_START",flush=True);print(json.dumps(report,indent=2),flush=True);print("RESULT_JSON_END",flush=True)
    if len(rows)<200:raise SystemExit("INCOMPLETE: fewer than 200 real questions scored")
if __name__=="__main__":main()
