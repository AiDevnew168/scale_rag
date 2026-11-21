#!/usr/bin/env python3
"""Faithful ORIGINAL DIAERESIS published DAP -> Translator -> Processor launcher.

Original author's Git commit 22dfe1900, no changes to original Scala code.
Maven Spark 3.1.1 Java 8 with local Spark master, original Hadoop fs-shell
commands mapped to local file:/// via actual Hadoop FsShell. This is an
author-source functional run in ONE GitHub Actions VM, NOT fair cross-host
runtime comparison with original publication.

Will fail closed and retain captured stage logs for incomplete pipeline.
"""
import hashlib,json,os,re,subprocess,sys,time,urllib.request,zipfile
from pathlib import Path
SRC="https://users.ics.forth.gr/~kondylak/SWJ/swdf.zip"
SHA="c1787940fbffab1b92e61bb338707bc11d2575931fefd15cabc78f88c00654de"
BASE=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"candidate3-DIAERESIS-author"
BASE.mkdir(exist_ok=True,parents=True)
OUT=Path("results_candidate3_diaeresis_faithful_runtime")
OUT.mkdir(exist_ok=True)
JAR=Path("diaeresis-pinned/target/DIAERESIS-1.0-SNAPSHOT.jar")
MASTER="local[2]"
N=4
HDFS=(BASE/"hdfsroot").resolve()
DATA=(BASE/"swdf"/"data"/"clean_swdf.nt").resolve()
SCHEMA=(BASE/"swdf"/"schema"/"schemaSWDF.txt").resolve()
QDIR=(BASE/"published_queries").resolve()

def stage(name,cmd,env=None,timeout=300):
    t=time.monotonic()
    details={"stage":name,"argv":cmd[:],"start_mono":t}
    try:
        p=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,
           stderr=subprocess.STDOUT,encoding="utf8",errors="replace",
           timeout=timeout,cwd=".",check=False)
        log=p.stdout;details["exit_code"]=p.returncode
        details["state"]="SUCCESS" if p.returncode==0 else "FAIL"
    except subprocess.TimeoutExpired as err:
        log=(err.stdout or b"")
        if isinstance(log,bytes):log=log.decode("utf8",errors="replace")
        details["state"]="TIMEOUT";details["exit_code"]=124
    except Exception as exc:
        log=type(exc).__name__+": "+str(exc)
        details["state"]="BLOCKED";details["exit_code"]=125
    details["elapsed_s"]=round(time.monotonic()-t,2)
    details["lines_logged"]=len(log.splitlines())
    details["head"]=log.splitlines()[:30]
    details["tail"]=log.splitlines()[-35:]
    (OUT/(name+".log")).write_text(log)
    print("AUTHOR_BASELINE_STAGE",name,details["state"],
          "elapsed_s",details["elapsed_s"],flush=True)
    return details

def main():
    d={"schema":"candidate3-original-author-DIAERESIS-real-full-pipeline-2026-11-21-v1",
      "upstream_SHA":"22dfe190078973f644f5d6279181e54ec116f6e3",
      "unmodified_upstream_scala_source":True,
      "published_original_artifact_url":SRC,
      "published_artifact_sha256":SHA,
      "max_worker_resources":"GitHub ubuntu hosted single VM Spark local[2]",
      "uses_true_distributed_HDFS_cluster":False,
      "uses_actual_Hadoop_FileSystem_Shell_on_file_URI":True,
      "publication_comparable_performance_claim":False,
      "full_original_three_stage_execution":False,
      "stages":[]}
    try:
        assert JAR.exists(),("Original author's Maven build missing",JAR)
        data=urllib.request.urlopen(urllib.request.Request(SRC,
          headers={"User-Agent":"ScaleRAG-DIAERESIS-published-source-verification/1.0"}),
          timeout=55).read(8_000_000)
        assert hashlib.sha256(data).hexdigest()==SHA
        zip_path=BASE/"original_author_swdf.zip";zip_path.write_bytes(data)
        with zipfile.ZipFile(zip_path) as z:
            assert all(".." not in name for name in z.namelist())
            z.extractall(BASE)
        assert DATA.exists() and SCHEMA.exists(),(DATA,SCHEMA)
        HDFS.mkdir(exist_ok=True,parents=True)
        QDIR.mkdir(exist_ok=True,parents=True)
        author_queries=Path("diaeresis-pinned/queries/swdf/swdf(u)")
        original_queries=sorted(author_queries.glob("query*.txt"))
        assert len(original_queries)>=5
        # The first 3 lexical queries have variable predicate branches.  The
        # author QueryTranslator's published subPartIndex map is commented
        # out, so those run into scala.NoSuchElementException on 00003.
        # Select first three ORIGINAL author queries whose BGP predicates
        # are constant URIs.  This is SOURCE STRUCTURE ONLY, not answer
        # or performance-based tuning.
        from rdflib.plugins.sparql.processor import prepareQuery
        from rdflib.plugins.sparql.parserutils import CompValue
        from rdflib.term import URIRef
        def static_bgp(file):
            try:
                alg=prepareQuery(file.read_text(encoding="utf8")).algebra
                names=[];triples=[]
                def walk(node):
                    if isinstance(node,CompValue):
                        names.append(node.name)
                        if node.name=="BGP":triples.extend(node["triples"])
                        for key,value in node.items():
                            if key not in ("triples","_vars"):walk(value)
                    elif isinstance(node,(tuple,list)):
                        for item in node:walk(item)
                walk(alg)
                return bool(triples) and all(isinstance(p,URIRef) for s,p,o in triples) and set(names).issubset(
                    {"SelectQuery","Project","BGP","Slice","Distinct","OrderBy","OrderCondition"})
            except Exception:
                return False
        compatible=[f for f in original_queries if static_bgp(f)]
        assert len(compatible)>=3,("insufficient_original_author_constant_predicate_queries",len(compatible))
        selected_queries=compatible[:3]
        for i,file in enumerate(selected_queries):
            (QDIR/("query_"+str(i)+".txt")).write_bytes(file.read_bytes())
        d["input"]={"original_schema_bytes":SCHEMA.stat().st_size,
             "original_instance_NTriples_bytes":DATA.stat().st_size,
             "selection":"Original author queries, lexical first 3 with all BGP predicates constant URI; no result inspection",
             "original_authored_query_count":len(original_queries),
             "original_authored_eligible_constant_predicate_queries":len(compatible),
             "n_original_unmodified_author_queries":len(selected_queries),
             "original_query_names":[x.name for x in selected_queries]}
        env=os.environ.copy()
        env.update({"SPARK_LOCAL_IP":"127.0.0.1","SPARK_LOCAL_HOSTNAME":"localhost",
              "HADOOP_USER_NAME":"runner","SPARK_DRIVER_MEMORY":"4g",
              "JAVA_TOOL_OPTIONS":"-Djava.net.preferIPv4Stack=true",
              "SPARK_SUBMIT_OPTS":"-Xmx4g"})
        assert "SPARK_HOME" in env and Path(env["SPARK_HOME"]).exists(), "Spark not installed"
        confdir=BASE/"hadoopconf";confdir.mkdir(exist_ok=True)
        (confdir/"core-site.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<configuration><property><name>fs.defaultFS</name><value>file:///</value></property></configuration>\n')
        env["HADOOP_CONF_DIR"]=str(confdir)
        bindir=BASE/"bin";bindir.mkdir(exist_ok=True)
        hdfs=bindir/"hdfs"
        hdfs.write_text("""#!/usr/bin/env bash
set -e
if [[ "${1:-}" == "dfs" ]]; then shift; fi
exec "$JAVA_HOME/bin/java" -cp "$HADOOP_CONF_DIR:$SPARK_HOME/jars/*" org.apache.hadoop.fs.FsShell "$@"
""")
        hdfs.chmod(0o755)
        env["PATH"]=str(bindir)+os.pathsep+env["SPARK_HOME"]+"/bin"+os.pathsep+env["PATH"]
        d["stages"].append(stage("hadoop-FsShell-version",
                 ["hdfs","dfs","-ls",str(HDFS)],env=env,timeout=35))
        if d["stages"][-1]["state"]!="SUCCESS":
            raise RuntimeError("Original Hadoop CLI emulation cannot access local filesystem")
        root_uri=HDFS.as_uri()
        spark=[
          "spark-submit",
          "--class","org.ics.isl.DAP",
          "--master",MASTER,
          "--driver-memory","4g",
          "--conf","spark.sql.shuffle.partitions=8",
          "--conf","spark.default.parallelism=8",
          "--conf","spark.driver.maxResultSize=2g",
          "--conf","spark.ui.enabled=false",
          "--conf","spark.local.dir="+str(BASE/"sparktmp"),
          str(JAR),"SWDF_Author",str(N),root_uri,str(DATA),str(SCHEMA)]
        (BASE/"sparktmp").mkdir(exist_ok=True)
        d["stages"].append(stage("original-DAP-partition",
                       spark,env=env,timeout=560))
        if d["stages"][-1]["state"]!="SUCCESS":
            raise RuntimeError("Unmodified author DAP failed; no query translation may be claimed")
        translate=spark[:]
        translate[2]="org.ics.isl.QueryTranslator"
        translate[-2:]=[]
        # Rebuild exact author invocation with 4 arguments after jar.
        translate=spark[:spark.index(str(JAR))+1]+[
                 "SWDF_Author",str(N),root_uri,str(QDIR)]
        translate[2]="org.ics.isl.QueryTranslator"
        d["stages"].append(stage("original-QueryTranslator",translate,env=env,timeout=240))
        if d["stages"][-1]["state"]!="SUCCESS":
            raise RuntimeError("Original author QueryTranslator failed")
        translated=QDIR/"translated_queries_4_bal"
        assert translated.is_dir()
        query_processor=spark[:spark.index(str(JAR))+1]+[
          "SWDF_Author",str(N),root_uri,str(translated)]
        query_processor[2]="org.ics.isl.QueryProcessor"
        d["stages"].append(stage("original-QueryProcessor",query_processor,env=env,timeout=330))
        if d["stages"][-1]["state"]!="SUCCESS":
            raise RuntimeError("Original author QueryProcessor failed")
        d["full_original_three_stage_execution"]=True
        d["gate"]="PASS_AUTHOR_PIPELINE_SINGLE_VM_ONLY"
    except Exception as e:
        d["gate"]="BLOCKED_OR_FAIL_ORIGINAL_FULL_PIPELINE"
        d["blocker"]=type(e).__name__+": "+str(e)[:420]
    (OUT/"report.json").write_text(json.dumps(d,indent=2))
    print("DIAERESIS_FULL_RUNTIME_GATE_START",flush=True)
    print(json.dumps({k:v for k,v in d.items() if k!="stages"}|
      {"stages":[{"stage":s["stage"],"state":s["state"],"exit_code":s["exit_code"],
          "elapsed_s":s["elapsed_s"],"head":s["head"][:22],
          "tail":s["tail"][-8:]} for s in d["stages"]]},
      indent=2),flush=True)
    print("DIAERESIS_FULL_RUNTIME_GATE_END",flush=True)
if __name__=="__main__":main()
