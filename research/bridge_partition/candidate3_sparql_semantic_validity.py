#!/usr/bin/env python3
"""Strict RDF-term-aware SPARQL SELECT validity checker, independent of result order.

FROZEN acceptance contract: CANDIDATE3_FROZEN_SPARQL_SEMANTIC_VALIDITY_CONTRACT_2026_11_21.md.
Exact multiset for unsliced unordered; valid sub-multiset of the unsliced
oracle for unordered top-level LIMIT/OFFSET. A globally consistent injective
blank-node renaming, across ALL rows, is mandatory. Ordered SELECTs are
validated sequence-exact, and non-unique ORDER BY keys require a separate
proven tie-aware comparator (not provided => fail closed).
The query is not modified for timed execution; only an independent oracle
reference version has safe top-level LIMIT/OFFSET removed.

DOES NOT claim cross-dataset research novelty; limits resource consumption.
"""
from __future__ import annotations
import collections
import re
from dataclasses import dataclass
from typing import Any

MAX_SOLUTIONS=20000
MAX_BLANK_ROWS=1500
MAX_SEARCH_STATES=400000
Term=tuple
Row=tuple
_ERR=object()

def normalize_term(value:Any):
    if value is None:return ("unbound",)
    if isinstance(value,tuple):
        if value and value[0] in ("iri","blank","literal","unbound"):
            return value
        raise ValueError("Invalid explicit RDF term")
    # pyoxigraph NamedNode, BlankNode, Literal.
    name=type(value).__name__
    if name=="NamedNode":
        return ("iri",value.value)
    if name=="BlankNode":
        return ("blank",value.value)
    if name=="Literal":
        dt=getattr(value,"datatype",None)
        lang=getattr(value,"language",None)
        return ("literal",value.value,lang,(dt.value if dt is not None else None))
    raise TypeError("Unsupported RDF value "+name)

def result_bag(store,query,cap=MAX_SOLUTIONS):
    result=store.query(query)
    names=tuple(sorted(v.value for v in result.variables))
    rows=[]
    for binding in result:
        if len(rows)>=cap:
            raise RuntimeError("RESOURCE_BLOCKED: full query row cap exceeded")
        rows.append(tuple(normalize_term(binding[name]) for name in names))
    return names,rows

def plain_rows(variables,rows):
    variables=tuple(variables)
    order=sorted(range(len(variables)),key=lambda i:variables[i])
    if len(set(variables))!=len(variables):
        raise ValueError("Duplicate SELECT output variable")
    return tuple(sorted(variables)),[tuple(normalize_term(row[i]) for i in order) for row in rows]

def _scan_modifiers(query):
    """Remove only end-of-string simple LIMIT OFFSET, preserving all other bytes.

    A simple SELECT whose algebra is already validated externally may have
    trailing LIMIT or OFFSET with optional final SPARQL comment. Reject any
    token after the numeric modifiers and reject nested slices/subqueries.
    """
    trimmed=re.sub(r"\s*#[^\n]*\s*$","",query).rstrip()
    limit=None;offset=None
    matches=[]
    while True:
        m=re.search(r"(?is)\s+(LIMIT|OFFSET)\s+(\d+)\s*$",trimmed)
        if not m:break
        key=m.group(1).upper();num=int(m.group(2))
        if num>10**9:raise ValueError("MODIFIER_VALUE_TOO_LARGE")
        if key=="LIMIT":
            if limit is not None:raise ValueError("DUPLICATE_LIMIT")
            limit=num
        else:
            if offset is not None:raise ValueError("DUPLICATE_OFFSET")
            offset=num
        matches.append(key)
        trimmed=trimmed[:m.start()].rstrip()
    if len(matches)>2:raise ValueError("UNSUPPORTED_MODIFIER_CHAIN")
    if re.search(r"(?i)\b(LIMIT|OFFSET)\s+\d+\b",trimmed):
        # Fail closed on nested slices. A "LIMIT" occurring within a literal
        # could false-block, but never false-accept unsafe rewriting.
        raise ValueError("NESTED_OR_UNRECOGNIZED_LIMIT_OFFSET")
    if not re.search(r"(?is)\bSELECT\b",trimmed):
        raise ValueError("NOT_SELECT")
    ordered=bool(re.search(r"(?i)\bORDER\s+BY\b",trimmed))
    return trimmed,limit,offset,ordered

def plan(query):
    unsliced,limit,offset,ordered=_scan_modifiers(query)
    if ordered and (limit is not None or offset is not None):
        return {"status":"ORDERED_SLICE_STRICT_ONLY","reference_query":query,
            "limit":limit,"offset":offset,"ordered":True}
    return {"status":"READY","reference_query":unsliced,
            "limit":limit,"offset":offset,"ordered":ordered}

def _shape_term(t):
    return ("blank",) if t[0]=="blank" else t

def _shape_row(row):
    return tuple(_shape_term(x) for x in row)

def _match_row(candidate,reference,forward,reverse):
    f=dict(forward);g=dict(reverse)
    for t,s in zip(candidate,reference):
        if t[0]=="blank" and s[0]=="blank":
            if t[1] in f and f[t[1]]!=s[1]:return None
            if s[1] in g and g[s[1]]!=t[1]:return None
            f[t[1]]=s[1];g[s[1]]=t[1]
        elif t!=s:return None
    return f,g

def _blank_alpha_subbag(reference,candidate,ordered=False):
    if len(candidate)>MAX_BLANK_ROWS:
        return False,"RESOURCE_BLOCKED_BLANK_ALPHA_ROWS"
    if len(reference)>MAX_SOLUTIONS:
        return False,"RESOURCE_BLOCKED_REFERENCE_ROWS"
    if len(candidate)>len(reference):
        return False,"COUNT_EXCEEDS_REFERENCE"
    for r in reference+candidate:
        if len(r)!=(len(reference[0]) if reference else (len(candidate[0]) if candidate else 0)):
            return False,"ROW_ARITY_MISMATCH"
    # Nonblank fast check, also guards tuple bag multiplicities.
    rshape=collections.Counter(map(_shape_row,reference))
    cshape=collections.Counter(map(_shape_row,candidate))
    if any(cshape[k]>rshape[k] for k in cshape):
        return False,"STRUCTURAL_SUBBAG_MISMATCH"
    if ordered:
        if len(reference)!=len(candidate):
            return False,"ORDERED_COUNT_MISMATCH"
        state_f={};state_g={}
        for a,b in zip(candidate,reference):
            pair=_match_row(a,b,state_f,state_g)
            if pair is None:return False,"ORDERED_ALPHA_MISMATCH"
            state_f,state_g=pair
        return True,"ORDERED_EXACT_GLOBAL_ALPHA"
    # Search injective row assignment + global bnode mapping.
    # Query row order is arbitrary; most constrained structural class first.
    refs_by_shape=collections.defaultdict(list)
    for idx,row in enumerate(reference):
        refs_by_shape[_shape_row(row)].append((idx,row))
    candidates=sorted(candidate,key=lambda row:(
        len(refs_by_shape[_shape_row(row)]),
        -sum(t[0]!="blank" for t in row),
        repr(row)))
    state_count=0
    def dfs(i,used,forward,reverse):
        nonlocal state_count
        state_count+=1
        if state_count>MAX_SEARCH_STATES:raise OverflowError("global blank mapping state cap")
        if i==len(candidates):return True
        x=candidates[i]
        for idx,y in refs_by_shape[_shape_row(x)]:
            if idx in used:continue
            mapping=_match_row(x,y,forward,reverse)
            if mapping is None:continue
            if dfs(i+1,used|{idx},*mapping):return True
        return False
    try:
        ok=dfs(0,set(),{}, {})
    except (OverflowError,RecursionError):
        return False,"RESOURCE_BLOCKED_ALPHA_SEARCH"
    return (ok,"VALID_GLOBAL_ALPHA_SUBBAG" if ok else "GLOBAL_BNODE_MAPPING_MISMATCH")

def validate(reference_variables,unsliced_reference,answer_variables,answer_rows,
             *,limit=None,offset=None,ordered=False,unambiguous_order=False):
    """Return a decision; a failure/blocked decision is never a PASS.

    'reference' must be the FULL unsliced output unless ordered=True.
    For ordered query output, supply the original ordered sliced oracle and
    unambiguous_order=True only when ordering is uniquely determined.
    """
    refvars,refs=plain_rows(reference_variables,unsliced_reference)
    ansvars,answers=plain_rows(answer_variables,answer_rows)
    if refvars!=ansvars:return {"pass":False,"reason":"BINDING_VARIABLE_SET_MISMATCH"}
    if ordered and not unambiguous_order:
        return {"pass":False,"reason":"ORDER_BY_TIES_UNCERTIFIED"}
    if ordered:
        if len(refs)!=len(answers):
            return {"pass":False,"reason":"ORDERED_COUNT_MISMATCH"}
    else:
        k=max(0,len(refs)-(offset or 0))
        if limit is not None:k=min(k,limit)
        if len(answers)!=k:
            return {"pass":False,"reason":"UNORDERED_SLICE_COUNT_MISMATCH",
                "expected":k,"actual":len(answers)}
    if len(refs)>MAX_SOLUTIONS or len(answers)>MAX_SOLUTIONS:
        return {"pass":False,"reason":"RESOURCE_BLOCKED_RESULT"}
    blanks=any(t[0]=="blank" for row in refs+answers for t in row)
    if blanks:
        correct,reason=_blank_alpha_subbag(refs,answers,ordered=ordered)
        return {"pass":correct,"reason":reason,"blank_alpha":True}
    if ordered:
        ok=refs==answers
        return {"pass":ok,"reason":"ORDERED_EXACT" if ok else "ORDERED_BINDINGS_DIFFER"}
    a=collections.Counter(answers);b=collections.Counter(refs)
    ok=all(a[r]<=b[r] for r in a)
    return {"pass":ok,"reason":"VALID_UNORDERED_SOLUTION_SUBBAG" if ok
             else "UNORDERED_SOLUTION_NOT_IN_FULL_REFERENCE",
             "full_solutions":len(refs),"answer_count":len(answers)}
