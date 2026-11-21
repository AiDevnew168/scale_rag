#!/usr/bin/env python3
"""Conservative original-SPARQL SELECT semantic acceptance (no false PASS).

SPARQL 1.1: LIMIT without ORDER BY selects an arbitrary bounded SUB-BAG of
the original unsliced solutions. Compare each original unchanged response
against a separately computed, unsliced centralized solution bag. Blank node
labels are RESULT-SCOPE LOCAL; require one consistent bijective mapping
across the whole multiset of solution bindings. For ordered LIMIT boundary
ties, REDUCED, unsupported nested LIMIT, or excessive search: INCONCLUSIVE,
not automatic PASS. Never rewrite the timed original query: unslicing only
applies to the separate truth verifier, not benchmark query execution.

References:
W3C SPARQL 1.1 Query Language §§15.4-15.6
W3C SPARQL 1.1 JSON Query Results §3.2.2 (bnode label scope)
"""
from __future__ import annotations
import collections
import re
from dataclasses import dataclass
from typing import Any
from rdflib.plugins.sparql.processor import prepareQuery
from rdflib.plugins.sparql.parserutils import CompValue
from pyoxigraph import BlankNode, Literal, NamedNode

MAX_TRUTH_ROWS=30_000
MAX_MATCH_NODES=400_000

def term_key(term):
    if term is None:return ("unbound",)
    if isinstance(term,NamedNode):return ("iri",term.value)
    if isinstance(term,BlankNode):return ("bnode",term.value)
    if isinstance(term,Literal):
        return ("lit",term.value,term.language.lower() if term.language else "",
                term.datatype.value if term.datatype else "")
    raise ValueError("Unsupported RDF result term: "+type(term).__name__)

def solution_rows(store,query,maximum=MAX_TRUTH_ROWS):
    result=store.query(query)
    if not hasattr(result,"variables"):
        raise ValueError("Only SELECT solution results supported")
    variables=tuple(sorted(v.value for v in result.variables))
    rows=[]
    for row in result:
        if len(rows)>=maximum:raise RuntimeError("result_row_limit_guard")
        rows.append(tuple(term_key(row[var]) for var in variables))
    return variables,rows

def skeleton(row):
    return tuple(("bnode",) if k[0]=="bnode" else k for k in row)

def is_subset_with_global_bnode_bijection(required,reference,max_match_nodes=MAX_MATCH_NODES):
    """Prove bag-inclusion up to *one global* injective bnode renaming.

    This implementation never returns True on a shortcut, and refuses
    combinatorially hard cases rather than silently assuming correctness.
    """
    if len(required)>len(reference):return False
    reqgroup=collections.Counter(map(skeleton,required))
    refgroup=collections.Counter(map(skeleton,reference))
    if any(reqgroup[k]>refgroup[k] for k in reqgroup):return False
    if not any(k[0]=="bnode" for row in required+reference for k in row):
        c=collections.Counter(reference)
        return all(c[r]>=n for r,n in collections.Counter(required).items())
    reference_groups=collections.defaultdict(collections.Counter)
    for row in reference:reference_groups[skeleton(row)][row]+=1
    needed=sorted(required,key=lambda row:(len(reference_groups[skeleton(row)]),
                -sum(k[0]=="bnode" for k in row),row))
    used_forward={};used_reverse={}
    nodes=[0]
    def walk(index):
        if index==len(needed):return True
        nodes[0]+=1
        if nodes[0]>max_match_nodes:raise RuntimeError("bnode_isomorphism_budget_exhausted")
        row=needed[index]
        possible=reference_groups[skeleton(row)]
        for candidate in list(possible):
            if not possible[candidate]:continue
            add=[]
            valid=True
            for left,right in zip(row,candidate):
                if left[0]!="bnode":continue
                x,y=left[1],right[1]
                if (x in used_forward and used_forward[x]!=y) or (
                    y in used_reverse and used_reverse[y]!=x):
                    valid=False;break
                if x not in used_forward:
                    used_forward[x]=y;used_reverse[y]=x;add.append((x,y))
            if valid:
                possible[candidate]-=1
                if walk(index+1):return True
                possible[candidate]+=1
            for x,y in add:
                del used_forward[x];del used_reverse[y]
        return False
    return walk(0)

@dataclass(frozen=True)
class QuerySlice:
    kind:str
    unsliced_query:str|None=None
    limit:int|None=None
    offset:int=0
    rationale:str=""

def characterize(query):
    try:algebra=prepareQuery(query).algebra
    except Exception as exc:
        return QuerySlice("inconclusive",rationale="query_parse_"+type(exc).__name__)
    nodes=[]
    def walk(x):
        if isinstance(x,CompValue):
            nodes.append(x.name)
            for key,value in x.items():
                if key!="_vars":walk(value)
        elif isinstance(x,(list,tuple)):
            for v in x:walk(v)
    walk(algebra)
    if "Reduced" in nodes or nodes.count("Slice")>1:
        return QuerySlice("inconclusive",rationale="REDUCED_or_nested_SLICE")
    if "Slice" not in nodes:return QuerySlice("full_bag")
    if "OrderBy" in nodes:
        return QuerySlice("ordered_slice",rationale="ORDER_BY_with_slice_may_have_boundary_ties")
    # Only trailing LIMIT/OFFSET at top level. Algebra already confirms
    # there is exactly one slice node and no ORDER BY.
    pos=len(query)
    parts={}
    while True:
        m=re.search(r"(?is)\s+\b(LIMIT|OFFSET)\s+(\d+)\s*$",query[:pos])
        if not m:break
        typ=m.group(1).upper()
        if typ in parts:return QuerySlice("inconclusive",rationale="duplicate_slice_modifier")
        parts[typ]=int(m.group(2));pos=m.start()
    if not parts:return QuerySlice("inconclusive",rationale="could_not_remove_trailing_slice")
    raw=query[:pos].rstrip()
    if not raw:return QuerySlice("inconclusive",rationale="empty_unsliced_query")
    try:
        stripped=prepareQuery(raw).algebra
        chk=[]
        def scan(x):
            if isinstance(x,CompValue):
                chk.append(x.name)
                for k,v in x.items():
                    if k!="_vars":scan(v)
            elif isinstance(x,(tuple,list)):
                for v in x:scan(v)
        scan(stripped)
        if "Slice" in chk:return QuerySlice("inconclusive",rationale="not_simple_top_level_slice")
    except Exception:
        return QuerySlice("inconclusive",rationale="unsliced_query_parse_failed")
    return QuerySlice("unordered_slice",unsliced_query=raw,
                       limit=parts.get("LIMIT"),offset=parts.get("OFFSET",0))

def certify(central,distribution,query,truth_full_cache=None):
    """Report method independent semantic outcomes and proof category.

    Returns PASS, FAIL, or INCONCLUSIVE. For unordered slices, both
    central+sharded original responses must satisfy full centralized
    unsliced bag membership and cardinality. It is possible for valid
    original responses to have distinct row contents.
    """
    meta=characterize(query)
    response={"schema":"candidate3-conservative-SPARQL-SELECT-semantics-v1",
      "kind":meta.kind,"rationale":meta.rationale}
    try:
        cv,cr=solution_rows(central,query)
        dv,dr=solution_rows(distribution,query)
        response.update({"central_rows":len(cr),"sharded_rows":len(dr)})
        if cv!=dv:
            response.update({"status":"FAIL","reason":"SELECT_variable_schema_mismatch"})
            return response
        if meta.kind=="inconclusive":
            return response|{"status":"INCONCLUSIVE","reason":meta.rationale}
        if meta.kind=="full_bag":
            valid=is_subset_with_global_bnode_bijection(cr,dr) and (
                   is_subset_with_global_bnode_bijection(dr,cr))
            return response|{"status":"PASS" if valid else "FAIL",
               "reason":"full_solution_multiset_isomorphic" if valid else "full_multiset_mismatch"}
        if meta.kind=="ordered_slice":
            valid=(len(cr)==len(dr) and is_subset_with_global_bnode_bijection(cr,dr)
                   and is_subset_with_global_bnode_bijection(dr,cr))
            return response|{"status":"PASS" if valid else "INCONCLUSIVE",
                "reason":"ordered_slice_exact_match" if valid else
                  "ordered_slice_boundary_ties_not_certified"}
        if meta.kind=="unordered_slice":
            truth_cache_key=meta.unsliced_query
            if truth_full_cache is not None and truth_cache_key in truth_full_cache:
                vars_,full=truth_full_cache[truth_cache_key]
            else:
                vars_,full=solution_rows(central,meta.unsliced_query)
                if truth_full_cache is not None:
                    truth_full_cache[truth_cache_key]=(vars_,full)
            if vars_!=cv:
                return response|{"status":"INCONCLUSIVE","reason":"unsliced_variable_schema_changed"}
            remaining=max(len(full)-meta.offset,0)
            expected=min(remaining,meta.limit) if meta.limit is not None else remaining
            # Both independently sampled result bags may differ while
            # fulfilling the original unordered SPARQL SELECT semantics.
            cvalid=(len(cr)==expected and
                 is_subset_with_global_bnode_bijection(cr,full))
            dvalid=(len(dr)==expected and
                 is_subset_with_global_bnode_bijection(dr,full))
            return response|{"status":"PASS" if cvalid and dvalid else "FAIL",
               "reason":"unordered_slice_legal_subbag" if cvalid and dvalid else
                        "unordered_slice_cardinality_or_subset_violation",
               "unsliced_truth_rows":len(full),"expected_slice_rows":expected,
               "central_legally_valid":cvalid,"sharded_legally_valid":dvalid}
        raise RuntimeError("unreachable_query_kind")
    except RuntimeError as exc:
        return response|{"status":"INCONCLUSIVE","reason":str(exc)[:150]}
    except Exception as exc:
        return response|{"status":"INCONCLUSIVE",
             "reason":type(exc).__name__+": "+str(exc)[:130]}
