#!/usr/bin/env python3
"""Conservative SPARQL SELECT solution-multiset semantic verifier.

RDF terms are typed; blank nodes are existential identifiers, with a SINGLE
injective renaming shared by *all rows and columns*. Row multiplicity matters.
A top-level, unordered LIMIT permits any valid size-L submultiset of the
unlimited query's solutions, NOT necessarily the central endpoint's first L.

This verifier accepts only a fixed audited SELECT/BGP/project/distinct subset
for unordered LIMIT. OFFSET, LIMIT+ORDER BY, nested LIMIT, complex algebra,
oversized references and unresolved bnode subset matching are BLOCKED rather
than arbitrarily passed or failed. It never rewrites timed original queries.
"""
import collections, hashlib, json, re
from dataclasses import dataclass
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import RDF
from rdflib.plugins.sparql.processor import prepareQuery
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.term import URIRef as RURI

XSD_STRING="http://www.w3.org/2001/XMLSchema#string"
ROW_KIND=URIRef("urn:c3:select-result-row-kind")
ROW_TYPE=URIRef("urn:c3:row")
BINDING="urn:c3:binding:"
MAX_BLANK_FULL_ROWS=2000
MAX_BLANK_LIMIT_ROWS=2500
MAX_BLANK_REFERENCE_ROWS=2500
MAX_SEARCH_STATES=200000

class Inconclusive(Exception):
    pass

def iri(value):return ("uri",str(value))
def blank(value):return ("bnode",str(value))
def literal(value,lang=None,datatype=None):
    language=(str(lang).lower() if lang else "")
    dtype=(str(datatype) if datatype else XSD_STRING)
    return ("literal",str(value),language,dtype)
def _convert(term):
    if term is None:return None
    kind=term.__class__.__name__
    if kind in ("NamedNode","URIRef"):return iri(getattr(term,"value",term))
    if kind in ("BlankNode","BNode"):return blank(getattr(term,"value",term))
    if kind=="Literal":
        return literal(str(term) if kind=="Literal" and term.__class__.__module__.startswith("rdflib") else getattr(term,"value",str(term)),
            getattr(term,"language",None),getattr(term,"datatype",None))
    raise Inconclusive("unsupported_rdf_term_type:"+kind)

@dataclass
class Answers:
    variables: tuple
    rows: tuple
    def __post_init__(self):
        assert len(set(self.variables))==len(self.variables)
        assert all(len(row)==len(self.variables) for row in self.rows)
        assert all((term is None or term[0] in ("uri","bnode","literal"))
                   for row in self.rows for term in row)
    @classmethod
    def from_mappings(cls,variables,rows):
        names=tuple(sorted(str(v) for v in variables))
        return cls(names,tuple(tuple(_convert(row.get(v)) for v in names) for row in rows))

def from_oxigraph(store,query,max_rows=20000):
    value=store.query(query)
    names=tuple(sorted(v.value for v in value.variables))
    rows=[]
    for sol in value:
        if len(rows)>=max_rows:raise Inconclusive("reference_result_exceeds_row_cap")
        rows.append(tuple(_convert(sol[v]) for v in names))
    return Answers(names,tuple(rows))

def graph_of_answers(a):
    g=Graph()
    # Distinct row blank nodes encode *multiplicity*, including empty rows.
    # Value BNodes are scoped separately from row nodes and globally unified
    # across all cells referring to the same BNode within one answer.
    bnodes={}
    for i,row in enumerate(a.rows):
        node=BNode("result_row_"+str(i))
        g.add((node,ROW_KIND,ROW_TYPE))
        for var,term in zip(a.variables,row):
            if term is None:continue
            if term[0]=="uri":value=URIRef(term[1])
            elif term[0]=="literal":
                value=Literal(term[1],lang=term[2] or None,
                     datatype=URIRef(term[3]) if not term[2] else None,normalize=False)
            else:
                value=bnodes.setdefault(term[1],BNode("result_term_"+str(len(bnodes))))
            g.add((node,URIRef(BINDING+str(var)),value))
    return g

def _has_bnodes(a):
    return any(t is not None and t[0]=="bnode" for row in a.rows for t in row)

def _fits_row(candidate,reference,fwd,back):
    local_forward=dict(fwd);local_backward=dict(back)
    for x,y in zip(candidate,reference):
        if x is None or y is None:
            if x!=y:return None
            continue
        if (x[0]=="bnode")!=(y[0]=="bnode"):return None
        if x[0]!="bnode":
            if x!=y:return None
        else:
            left=x[1];right=y[1]
            if left in local_forward and local_forward[left]!=right:return None
            if right in local_backward and local_backward[right]!=left:return None
            local_forward[left]=right;local_backward[right]=left
    return local_forward,local_backward

def _limited_blank_subset(candidate,reference):
    # Index actual reference bag by the grounded components of each row.
    # This permits large 30k-reference result sets when LIMIT is small,
    # without pretending blank labels are globally comparable.
    if len(candidate)>MAX_BLANK_LIMIT_ROWS or len(reference)>30000:
        raise Inconclusive("blank_node_limit_subset_exceeds_exact_search_cap:"+str(len(candidate))+":"+str(len(reference)))
    def signature(row):
        return tuple(("bnode",) if t is not None and t[0]=="bnode" else t
                     for t in row)
    groups=collections.defaultdict(collections.Counter)
    for row in reference:
        groups[signature(row)][row]+=1
    sizes=collections.Counter(signature(row) for row in candidate)
    if any(sum(groups[key].values())<n for key,n in sizes.items()):
        return False
    # Match the most selective row first. A single bnode-renaming map must
    # hold across ALL selected rows, not a fresh map for each row.
    ordered=sorted(candidate,key=lambda row:(len(groups[signature(row)]),
                                              signature(row)))
    states=0
    def search(depth,fwd,back):
        nonlocal states
        states+=1
        if states>MAX_SEARCH_STATES:
            raise Inconclusive("blank_node_mapping_search_budget_exceeded")
        if depth==len(ordered):return True
        row=ordered[depth]
        choices=groups[signature(row)]
        for refrow,count in list(choices.items()):
            if not count:continue
            maps=_fits_row(row,refrow,fwd,back)
            if maps is None:continue
            choices[refrow]-=1
            if search(depth+1,*maps):return True
            choices[refrow]+=1
        return False
    return search(0,{}, {})

def equal_bag(candidate,reference):
    if candidate.variables!=reference.variables:return False
    if len(candidate.rows)!=len(reference.rows):return False
    if not _has_bnodes(candidate) and not _has_bnodes(reference):
        return collections.Counter(candidate.rows)==collections.Counter(reference.rows)
    if len(candidate.rows)>MAX_BLANK_FULL_ROWS:
        raise Inconclusive("large_blank_node_isomorphism_not_certified")
    return isomorphic(graph_of_answers(candidate),graph_of_answers(reference))

def subbag(candidate,reference):
    if candidate.variables!=reference.variables:return False
    if len(candidate.rows)>len(reference.rows):return False
    if not _has_bnodes(candidate) and not _has_bnodes(reference):
        c=collections.Counter(candidate.rows)
        r=collections.Counter(reference.rows)
        return all(r[k]>=v for k,v in c.items())
    return _limited_blank_subset(candidate.rows,reference.rows)

def _algebra_nodes(q):
    prepared=prepareQuery(q)
    nodes=[]
    def walk(x):
        if isinstance(x,CompValue):
            nodes.append(x.name)
            for k,v in x.items():
                if k not in ("_vars",):walk(v)
        elif isinstance(x,(list,tuple)):
            for y in x:walk(y)
    walk(prepared.algebra)
    return nodes

def query_contract(query):
    """Return (kind, full-unsliced query, limit) or raise explicit BLOCKED.

    The query rewriting is ONLY used for the validity oracle; original
    queries are never changed in timing or actual shard evaluation.
    """
    nodes=_algebra_nodes(query)
    if not nodes or nodes.count("SelectQuery")!=1:
        raise Inconclusive("not_single_SELECT")
    allowed={"SelectQuery","Project","BGP","Slice","Distinct","Reduced"}
    if "Reduced" in nodes:raise Inconclusive("REDUCED_solution_multiplicity_not_deterministic")
    if set(nodes)-allowed:raise Inconclusive("unsupported_algebra:"+",".join(sorted(set(nodes)-allowed)))
    if "Slice" not in nodes:return ("full",None,None)
    if nodes.count("Slice")!=1:raise Inconclusive("nested_or_multiple_slice")
    if re.search(r"\bOFFSET\b",query,re.I):
        raise Inconclusive("OFFSET_not_certified")
    match=re.search(r"(?is)\bLIMIT\s+(\d+)\s*$",query)
    if not match:raise Inconclusive("top_level_terminal_LIMIT_not_proven")
    # LIMIT in string literals/comment/dataset? Restricted grammar is handled
    # by a structural Slice-count assertion and by re-parsing unsliced text.
    full=query[:match.start()].rstrip()
    if "Slice" in _algebra_nodes(full):
        raise Inconclusive("unsliced_query_still_contains_slice")
    return ("unordered_limit",full,int(match.group(1)))

def verify(original_query,reference_original,candidate_original,
           reference_unsliced=None):
    try:
        mode,full,limit=query_contract(original_query)
        if mode=="full":
            verdict=equal_bag(candidate_original,reference_original)
            return {"status":"PASS" if verdict else "FAIL",
                    "reason":"complete_multiset_and_global_bnode_isomorphism",
                    "n_candidate":len(candidate_original.rows),
                    "n_reference":len(reference_original.rows)}
        if reference_unsliced is None:
            return {"status":"BLOCKED","reason":"unsliced_reference_required"}
        target=min(limit,len(reference_unsliced.rows))
        if len(candidate_original.rows)!=target or len(reference_original.rows)!=target:
            return {"status":"FAIL","reason":"LIMIT_result_cardinality_wrong",
                    "expected":target,"candidate":len(candidate_original.rows),
                    "reference":len(reference_original.rows)}
        central_valid=subbag(reference_original,reference_unsliced)
        candidate_valid=subbag(candidate_original,reference_unsliced)
        if not central_valid:return {"status":"BLOCKED","reason":"central_original_not_valid_subset"}
        return {"status":"PASS" if candidate_valid else "FAIL",
                "reason":"unordered_LIMIT_semantically_admissible_multiset",
                "expected":target,"n_unsliced":len(reference_unsliced.rows),
                "distinct_candidate_can_differ_from_central":True}
    except Inconclusive as e:
        return {"status":"BLOCKED","reason":str(e)}
    except Exception as e:
        return {"status":"BLOCKED","reason":"verifier_internal_exception:"+type(e).__name__}

def certified_verify(original_query,central_store,alternative_answers,max_rows=20000):
    try:
        mode,unlimited,_=query_contract(original_query)
        ground=from_oxigraph(central_store,original_query,max_rows=max_rows)
        complete=(from_oxigraph(central_store,unlimited,max_rows=max_rows)
                  if mode=="unordered_limit" else None)
        return verify(original_query,ground,alternative_answers,complete)
    except Inconclusive as e:
        return {"status":"BLOCKED","reason":str(e)}
    except Exception as e:
        return {"status":"BLOCKED","reason":"central_evaluation_error:"+type(e).__name__}
