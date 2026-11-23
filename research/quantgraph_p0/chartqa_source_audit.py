"""Read-only original public ChartQA source *metadata* disagreement diagnostic.

This is NOT image verification, not proof labels are wrong, not a VLM run.
Queries are selected as known source-integrity hazards, not a benchmark score.
"""
import csv
import hashlib
import io
import json
import urllib.parse
import urllib.request
from pathlib import Path

SOURCE_COMMIT="044eabfc306abfe9340c5741f0093aefc5973d06"
BASE=f"https://raw.githubusercontent.com/vis-nlp/ChartQA/{SOURCE_COMMIT}/ChartQA Dataset/val/"
SAMPLES={
  "4576.png":{"query":"What is the max value of blue line?",
              "year":"2018","field":"Not too much/not at all","reported_label":"0.72"},
  "5734.png":{"query":"What's the percentage of respondents who say Job is a top priority for the president and Congress in 2016?",
              "year":"2016","field":"Jobs","reported_label":"68"},
}


def get(rel):
    url=urllib.parse.quote(BASE+rel,safe=":/")
    with urllib.request.urlopen(url,timeout=40) as response:
        data=response.read(2_000_000+1)
    if len(data)>2_000_000:raise ValueError("public source file exceeds cap")
    return data


def audit():
    human_b=get("val_human.json")
    human=json.loads(human_b)
    result=[]
    for name,spec in SAMPLES.items():
        q=[r for r in human if r.get("imgname")==name and r.get("query")==spec["query"]]
        if len(q)!=1:raise RuntimeError("original public benchmark question missing or duplicate")
        label=str(q[0]["label"])
        if label!=spec["reported_label"]:
            raise RuntimeError("public source label changed, must re-audit before using")
        table_b=get("tables/"+name.replace(".png",".csv"))
        table=list(csv.DictReader(io.StringIO(table_b.decode("utf-8-sig"))))
        source=[r for r in table if r.get("Year")==spec["year"]]
        if len(source)!=1 or spec["field"] not in source[0]:
            raise RuntimeError("public table entry missing or ambiguous")
        found=source[0][spec["field"]]
        result.append({"image_name":name,"source_query_sha256":
                     hashlib.sha256(spec["query"].encode()).hexdigest(),
                     "source_question_label":label,
                     "source_table_cell_as_string":found,
                     "year":spec["year"],"column":spec["field"],
                     "direct_string_values_disagree":found!=label,
                     "table_sha256":hashlib.sha256(table_b).hexdigest(),
                     "source_png_not_visually_checked":True})
    return {"schema":"quantgraph-p0-external-source-integrity-audit-v1",
            "original_repository":"vis-nlp/ChartQA",
            "original_commit":SOURCE_COMMIT,
            "read_only":True,
            "n_source_cases":len(result),
            "n_disagreements":sum(r["direct_string_values_disagree"] for r in result),
            "classification":"REQUIRES_MANUAL_IMAGE_ADJUDICATION",
            "no_claim_benchmark_gold_or_chart_image_wrong":True,
            "not_a_chartqa_test_set_performance_number":True,
            "cases":result}


if __name__=="__main__":
    d=audit()
    out=Path("results_quantgraph_p0")
    out.mkdir(exist_ok=True)
    (out/"source_audit.json").write_text(json.dumps(d,indent=2))
    print("ORIGINAL_CHARTQA_SOURCE_AUDIT",json.dumps(d),flush=True)
