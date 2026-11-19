#!/usr/bin/env python3
"""Human-annotated real edge-link audit. Auxiliary domain, NOT RAG QA."""
import io,os,re,json,math,random,hashlib,urllib.request,zipfile
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np,networkx as nx
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
SEED=261119
URL="https://guillaumejaume.github.io/FUNSD/dataset.zip"
OUT=Path("results_relation");OUT.mkdir(exist_ok=True)
TAUS=[-3,-2,-1,0,1,2,3,4,5,6]
MODES=["indep1","greedy1","flow1","indep2","greedy2","flow2"]
def load():
    b=urllib.request.urlopen(urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0"}),timeout=120).read()
    print("ARCHIVE_SHA256",hashlib.sha256(b).hexdigest(),"BYTES",len(b),flush=True)
    z=zipfile.ZipFile(io.BytesIO(b))
    arr={"train":[],"test":[]}
    for n in sorted(z.namelist()):
        if "__MACOSX" in n or "/annotations/" not in n or not n.endswith(".json"):continue
        split="train" if "/training_data/" in n else "test" if "/testing_data/" in n else None
        if split:
            obj=json.loads(z.read(n))
            arr[split].append({"name":n,"form":obj["form"]})
    print("RAW_SPLIT",{k:len(v) for k,v in arr.items()},flush=True)
    assert len(arr["train"])==149 and len(arr["test"])==50
    return arr,hashlib.sha256(b).hexdigest()
def tokens(s):return set(re.findall(r"[a-z0-9]{2,}",s.lower()))
def overlap(b,c,axis):
    a,d=(0,2) if axis=="h" else (1,3)
    return max(0,min(b[d],c[d])-max(b[a],c[a]))/max(1,min(b[d]-b[a],c[d]-c[a]))
def feats(q,a,W,H):
    qbox,abox=q["box"],a["box"]
    dx=((abox[0]+abox[2])-(qbox[0]+qbox[2]))/(2*W)
    dy=((abox[1]+abox[3])-(qbox[1]+qbox[3]))/(2*H)
    qt,at=q.get("text",""),a.get("text","")
    qtok,atok=tokens(qt),tokens(at)
    return [dx,dy,abs(dx),abs(dy),math.hypot(dx,dy),int(dx>=0),int(dy>=0),
            overlap(qbox,abox,"h"),overlap(qbox,abox,"v"),
            max(0,abox[0]-qbox[2])/W,max(0,abox[1]-qbox[3])/H,
            min(100,len(qt))/100,min(100,len(at))/100,
            int(qt.strip().endswith(":")),int(bool(re.search(r"\d",at))),
            len(qtok&atok)/max(1,len(qtok|atok)),
            int(bool(qt.strip()) and qt.lower() in at.lower()),
            int(bool(at.strip()) and at.lower() in qt.lower())]
def prep(doc):
    es=doc["form"];byid={e["id"]:e for e in es}
    qs=[e for e in es if e.get("label")=="question" and len(e.get("box",[]))==4]
    ans=[e for e in es if e.get("label")=="answer" and len(e.get("box",[]))==4]
    links=set()
    for e in es:
        for edge in e.get("linking",[]):
            if len(edge)==2:links.add(tuple(sorted(edge)))
    gold=set();other=Counter()
    for p,q in links:
        if p not in byid or q not in byid:
            other["unknown_id"]+=1;continue
        x,y=byid[p],byid[q]
        if x.get("label")=="question" and y.get("label")=="answer":gold.add((p,q))
        elif x.get("label")=="answer" and y.get("label")=="question":gold.add((q,p))
        else:other["other_label_link"]+=1
    W=max([e["box"][2] for e in es if len(e.get("box",[]))==4] or [1])
    H=max([e["box"][3] for e in es if len(e.get("box",[]))==4] or [1])
    pairs=[(q["id"],a["id"]) for q in qs for a in ans]
    X=np.asarray([feats(q,a,max(W,1),max(H,1)) for q in qs for a in ans],dtype=float).reshape((-1,18))
    y=np.asarray([int(p in gold) for p in pairs],dtype=int)
    return {"name":doc["name"],"qs":qs,"ans":ans,"pairs":pairs,"X":X,"y":y,"gold":gold,"other":other}
def choose(d,scores,tau,method,cap):
    pairs=d["pairs"]
    if not pairs:return set()
    order=sorted(range(len(pairs)),key=lambda i:(-scores[i],pairs[i]))
    if method in ("indep","greedy"):
        cntq=Counter();cnta=Counter();chosen=set()
        for i in order:
            q,a=pairs[i]
            if scores[i]<=tau:break
            if cntq[q]>=cap or (method=="greedy" and cnta[a]>=cap):continue
            chosen.add((q,a));cntq[q]+=1;cnta[a]+=1
        return chosen
    assert method=="flow"
    qids=[x["id"] for x in d["qs"]];aids=[x["id"] for x in d["ans"]]
    supply=len(qids)*cap
    g=nx.DiGraph()
    g.add_node("S",demand=-supply);g.add_node("T",demand=supply)
    for q in qids:
        g.add_edge("S",("Q",q),capacity=cap,weight=0)
        g.add_edge(("Q",q),"T",capacity=cap,weight=0)
    for a in aids:g.add_edge(("A",a),"T",capacity=cap,weight=0)
    for i,(q,a) in enumerate(pairs):
        utility=scores[i]-tau
        if utility>0:
            g.add_edge(("Q",q),("A",a),capacity=1,weight=-int(round(10000*utility)))
    assignment=nx.min_cost_flow(g)
    return {(q,a) for q,a in pairs if assignment.get(("Q",q),{}).get(("A",a),0)}
def triple(gold,pred):
    return (len(gold&pred),len(pred-gold),len(gold-pred))
def metric(cnt):
    if not cnt:return {"f1":0,"tp":0,"fp":0,"fn":0}
    tp,fp,fn=map(int,np.sum(np.asarray(cnt,dtype=int),axis=0))
    return {"f1":round(2*tp/max(1,2*tp+fp+fn),5),
            "precision":round(tp/max(1,tp+fp),5),
            "recall":round(tp/max(1,tp+fn),5),
            "tp":tp,"fp":fp,"fn":fn}
def main():
    forms,sha=load()
    tr=[prep(x) for x in forms["train"]];test=[prep(x) for x in forms["test"]]
    rng=random.Random(SEED);rng.shuffle(tr);dev=tr[:30];train=tr[30:]
    X=np.concatenate([x["X"] for x in train if len(x["X"])])
    y=np.concatenate([x["y"] for x in train if len(x["y"])])
    print("LEARNED_PAIR_TRAIN",len(train),len(y),"POSITIVE",int(y.sum()),flush=True)
    model=make_pipeline(StandardScaler(),LogisticRegression(class_weight="balanced",max_iter=500,random_state=SEED))
    model.fit(X,y)
    for d in dev+test:
        d["score"]=model.decision_function(d["X"]) if len(d["X"]) else np.array([])
    taus={};val={}
    for mode in MODES:
        method,cap=mode[:-1],int(mode[-1])
        best=(-1.,None)
        for tau in TAUS:
            result=metric([triple(d["gold"],choose(d,d["score"],tau,method,cap)) for d in dev])
            if result["f1"]>best[0]:best=(result["f1"],tau)
        taus[mode]=best[1];val[mode]={"f1":best[0],"threshold":best[1]}
    print("TUNING_ON_DEV_ONLY",json.dumps(val),flush=True)
    per=[];degreeq=Counter();degreea=Counter();ex=Counter()
    for d in test:
        row={"name":d["name"],"n_questions":len(d["qs"]),"n_answers":len(d["ans"]),"n_gold":len(d["gold"])}
        for q,a in d["gold"]:
            degreeq[(d["name"],q)]+=1
            degreea[(d["name"],a)]+=1
        ex.update(d["other"])
        for mode in MODES:
            pred=choose(d,d["score"],taus[mode],mode[:-1],int(mode[-1]))
            row[mode]=list(triple(d["gold"],pred))
        per.append(row)
    summary={mode:metric([r[mode] for r in per]) for mode in MODES}
    paired={}
    for newer,older in [("flow1","greedy1"),("flow2","greedy2"),
                        ("flow1","indep1"),("flow2","indep2")]:
        rng2=random.Random(SEED)
        delta=[]
        for i in range(2000):
            sample=[rng2.choice(per) for _ in per]
            v1=metric([r[newer] for r in sample])["f1"]
            v2=metric([r[older] for r in sample])["f1"]
            delta.append(100*(v1-v2))
        ci=np.percentile(delta,[2.5,97.5])
        paired[newer+"_vs_"+older]={"delta_f1_pp":round(100*(summary[newer]["f1"]-summary[older]["f1"]),3),
             "ci95_pp":[round(float(ci[0]),3),round(float(ci[1]),3)],
             "equal_predictions_document_count":sum(r[newer]==r[older] for r in per)}
    report={"schema":"funsd-oracle-node-edge-link-gate-v1","status":"real_data_complete",
      "source":URL,"source_sha256":sha,"seed":SEED,
      "splits":{"train":len(train),"dev":len(dev),"test":len(test)},
      "train_pair_count":len(y),"train_positive_count":int(y.sum()),
      "test_gold_qa_links":sum(len(x["gold"]) for x in test),
      "test_candidate_pairs":sum(len(x["pairs"]) for x in test),
      "degree_gt1_question_nodes":sum(v>1 for v in degreeq.values()),
      "degree_gt1_answer_nodes":sum(v>1 for v in degreea.values()),
      "test_non_qa_annotations":dict(ex),"dev_tuned":val,
      "test_metrics":summary,"paired_document_bootstrap":paired,
      "limitations":["Not a RAG experiment: scanned forms key-value link extraction",
       "Gold question/answer node TYPES are provided equally to all methods (oracle node roles)",
       "No test links are provided to the logistic pair scorer or either decoder",
       "No direct image pixels, only entity text and location; missing edges assumed negative",
       "Heuristic feature set and capacity-one/two assumptions, not a semantic multimodal solver",
       "Exploratory diagnostic, not a guarantee of transfer to scientific RAG"]}
    (OUT/"report.json").write_text(json.dumps(report,indent=2))
    (OUT/"per_doc.jsonl").write_text("".join(json.dumps(r)+"\n" for r in per))
    print("STRUCTURAL_RESULT_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("STRUCTURAL_RESULT_END",flush=True)
    assert len(test)==50 and report["test_gold_qa_links"]>=50
if __name__=="__main__":main()
