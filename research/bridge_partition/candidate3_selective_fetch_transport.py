#!/usr/bin/env python3
"""Safe training-only predicate triple-pattern pushdown for original SPARQL BGPs.

This is a deliberately simple, established baseline: constant-term triple
filtering, NOT a new semijoin algorithm. Every source N-Triples line returned
remains byte-identical to the immutable original source; bnode labels are
never regenerated. The worker may cache a parsed index for later requests.
"""
from collections import defaultdict
from rdflib import Literal as RDFLiteral, URIRef, Variable
from rdflib.plugins.sparql.processor import prepareQuery
from rdflib.plugins.sparql.parserutils import CompValue
from pyoxigraph import Literal as OxLiteral, NamedNode, BlankNode, RdfFormat, parse

XSD_STRING="http://www.w3.org/2001/XMLSchema#string"


def rdflib_const(node):
    if isinstance(node, URIRef):
        return ["iri", str(node)]
    if isinstance(node, RDFLiteral):
        return ["lit", str(node), (node.language or "").lower(),
                str(node.datatype) if node.datatype else
                ("http://www.w3.org/1999/02/22-rdf-syntax-ns#langString"
                 if node.language else XSD_STRING)]
    # Variables, blank-node syntax, or any other non-URI, nonliteral term
    # must never be treated as constants for conservative filtering.
    return None


def ox_term_key(term):
    if isinstance(term,NamedNode):
        return ["iri",term.value]
    if isinstance(term,BlankNode):
        return ["bnode",term.value]
    if isinstance(term,OxLiteral):
        return ["lit",term.value,(term.language or "").lower(),
                term.datatype.value if term.datatype else XSD_STRING]
    raise ValueError("Unsupported NTriples RDF term")


def bgp_triples(query):
    algebra=prepareQuery(query).algebra
    nodes=[];triples=[]
    def walk(x):
        if isinstance(x,CompValue):
            nodes.append(x.name)
            if x.name=="BGP":
                triples.extend(x["triples"])
            for k,v in x.items():
                if k not in ("triples","_vars"):
                    walk(v)
        elif isinstance(x,(tuple,list,set)):
            for child in x:walk(child)
    walk(algebra)
    eligible={"SelectQuery","Project","BGP","Slice","Distinct","OrderBy",
              "OrderCondition"}  # REDUCED is deliberately rejected
    if not nodes or not set(nodes).issubset(eligible):
        raise ValueError("Unsupported or unsafe original SELECT algebra")
    if algebra.get("datasetClause"):
        raise ValueError("Named graph clauses not supported")
    if len(triples)<2 or len(triples)>6:
        raise ValueError("Outside original 2-6 BGP domain")
    if any(not isinstance(p,URIRef) for _,p,_ in triples):
        raise ValueError("Dynamic predicate or property path")
    return triples


def compile_filters(query):
    """Predicate -> clauses or None (unrestricted due wildcard occurrence).

    Multiple same-predicate patterns are unioned, so one wildcard occurrence
    correctly forces a full fetch, never an unsafe intersecting filter.
    """
    bypred=defaultdict(list)
    for s,p,o in bgp_triples(query):
        subject=rdflib_const(s)
        obj=rdflib_const(o)
        bypred["<"+str(p)+">"].append({"subject":subject,"object":obj})
    result={}
    for p,clauses in bypred.items():
        if any(x["subject"] is None and x["object"] is None for x in clauses):
            result[p]=None
        else:
            result[p]=clauses
    return result


def index_original_lines(raw):
    """NTriples parsed per line, retaining each exact original source line."""
    if not isinstance(raw,bytes):
        raise TypeError("Source fragment must be original NTriples bytes")
    result=[]
    for line in raw.splitlines(keepends=True):
        if not line.strip():
            continue
        quads=list(parse(input=line,format=RdfFormat.N_TRIPLES,
                         rename_blank_nodes=False))
        if len(quads)!=1:
            raise RuntimeError("Original source line is not exactly one RDF triple")
        triple=quads[0]
        result.append((ox_term_key(triple.subject),ox_term_key(triple.object),line))
    return result


def select_original_lines(entries, clauses):
    if clauses is None:
        return b"".join(line for _,_,line in entries)
    if not isinstance(clauses,list) or not clauses:
        raise ValueError("At least one constant-bound clause required")
    out=[]
    for subject,obj,line in entries:
        if any((c["subject"] is None or c["subject"]==subject) and
               (c["object"] is None or c["object"]==obj) for c in clauses):
            out.append(line)
    return b"".join(out)


def filter_fragment(raw,clauses,cache=None,cache_key=None):
    """Keep original source lexical bnode IDs; never reconstruct RDF strings."""
    if clauses is None:
        return raw
    if cache is not None and cache_key in cache:
        parsed=cache[cache_key]
    else:
        parsed=index_original_lines(raw)
        if cache is not None:
            cache[cache_key]=parsed
    return select_original_lines(parsed,clauses)


def work_requests(groups,filters):
    """Original sharded router groups => correct original predicate coverage."""
    result={}
    for shard,predicates in groups.items():
        result[shard]={p:filters[p] for p in predicates}
    return result
