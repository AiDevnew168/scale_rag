"""P0 conditional identifiability checker for quantitatively read chart marks.

NOT an image parser, a scientific novelty result, or an unconditional verifier.
Only valid if external chart source identity, axis labels and pixel intervals are
independently validated. Solver uses floating-point LP, not formal proof.
"""
from dataclasses import dataclass
from typing import Sequence
import math
import re
import numpy as np
from scipy.optimize import linprog

class EvidenceError(ValueError):
    pass

@dataclass(frozen=True)
class Tick:
    pixel: float
    value_low: float
    value_high: float

@dataclass(frozen=True)
class Mark:
    name: str
    pixel_low: float
    pixel_high: float

@dataclass(frozen=True)
class Axis:
    source_sha256: str
    chart_id: str
    unit: str
    direction: str
    scale: str
    ticks: tuple[Tick, ...]
    independently_checked: bool


def _valid_float(x):
    return type(x) in (int,float) and math.isfinite(x)


class CorrelatedChart:
    """Linear chart worlds z=(a,b,y_0,...), y_i=a*p_i+b.

    Coefficients share the SAME axis calibration a,b across marks. This is the
    dependency the independent-interval control intentionally discards.
    """
    def __init__(self, axis:Axis, marks:Sequence[Mark]):
        if not axis.independently_checked:
            raise EvidenceError('untrusted_chart_geometry_or_tick_transcription')
        if not re.fullmatch(r'[a-f0-9]{64}',axis.source_sha256):
            raise EvidenceError('missing_verified_image_digest')
        if not axis.chart_id or not axis.unit:
            raise EvidenceError('chart_or_unit_absent')
        if axis.scale!='linear' or axis.direction not in ('increasing','decreasing'):
            raise EvidenceError('unsupported_axis_not_certifiable')
        if len(axis.ticks)<2 or len({t.pixel for t in axis.ticks})<2:
            raise EvidenceError('insufficient_distinct_calibration_ticks')
        if not marks or len(set(m.name for m in marks))!=len(marks):
            raise EvidenceError('mark_labels_missing_or_duplicate')
        self.axis=axis;self.marks=tuple(marks)
        self.names={m.name:i+2 for i,m in enumerate(marks)}
        n=2+len(marks)
        A=[];B=[]
        def put(coeff,limit):
            A.append(coeff);B.append(float(limit))
        for t in axis.ticks:
            if not all(_valid_float(v) for v in (t.pixel,t.value_low,t.value_high)) or t.value_low>t.value_high:
                raise EvidenceError('invalid_tick_value_interval')
            r=np.zeros(n);r[0]=t.pixel;r[1]=1
            put(r,t.value_high);put(-r,-t.value_low)
        min_tick=min(t.pixel for t in axis.ticks)
        max_tick=max(t.pixel for t in axis.ticks)
        for mark in marks:
            lo,hi=mark.pixel_low,mark.pixel_high
            if not mark.name or not all(_valid_float(x) for x in (lo,hi)) or lo>hi:
                raise EvidenceError('invalid_mark_evidence_interval')
            if lo<min_tick or hi>max_tick:
                raise EvidenceError('unproven_out_of_axis_range_extrapolation')
            lower_pixel=lo if axis.direction=='increasing' else hi
            upper_pixel=hi if axis.direction=='increasing' else lo
            lowr=np.zeros(n);lowr[0]=lower_pixel;lowr[1]=1;lowr[self.names[mark.name]]=-1
            hir=np.zeros(n);hir[0]=-upper_pixel;hir[1]=-1;hir[self.names[mark.name]]=1
            put(lowr,0);put(hir,0)
        self.A=np.array(A);self.B=np.array(B)
        slope_range=(1e-9,None) if axis.direction=='increasing' else (None,-1e-9)
        self.bounds=[slope_range]+[(None,None)]*(n-1)
        self._run(np.zeros(n))

    def _run(self,c):
        r=linprog(c,A_ub=self.A,b_ub=self.B,bounds=self.bounds,method='highs',
                  options={'primal_feasibility_tolerance':1e-8})
        if r.status!=0:
            raise EvidenceError('chart_world_infeasible_or_unbounded:'+str(r.status))
        return r

    def bound(self,weights:dict[str,float],offset:float=0.):
        if not _valid_float(offset) or any(not _valid_float(w) or name not in self.names for name,w in weights.items()):
            raise EvidenceError('unknown_mark_or_invalid_coefficient')
        c=np.zeros(len(self.bounds))
        for k,v in weights.items():c[self.names[k]]=v
        mini=self._run(c).fun+offset
        maxi=-self._run(-c).fun+offset
        if mini>maxi+1e-6:raise EvidenceError('invalid_numerical_projection')
        return (float(mini),float(maxi))

    def independent_baseline(self,weights:dict[str,float],offset:float=0.):
        """Baseline: interval arithmetic after dropping common calibration dependency."""
        lower=upper=offset
        for k,w in weights.items():
            lo,hi=self.bound({k:1})
            lower+=w*(lo if w>=0 else hi)
            upper+=w*(hi if w>=0 else lo)
        return (lower,upper)

    def answer(self,weights:dict[str,float],tolerance:float):
        if not _valid_float(tolerance) or tolerance<0:raise EvidenceError('invalid_answer_precision')
        lo,hi=self.bound(weights)
        return {'decision':'BOUNDED_WITHIN_TOLERANCE' if hi-lo<=2*tolerance else 'ABSTAIN_EXACT_VALUE',
                'feasible_value_interval':[lo,hi],
                'condition':'independent_source_and_tick_verification_required',
                'probabilistic_confidence_claim':False,
                'formal_floating_point_certificate':False}


def union_of_branch_bounds(branches:list[tuple[CorrelatedChart,dict[str,float]]]):
    """Union over ALL plausible visual bindings, never select a convenient one."""
    if not branches:raise EvidenceError('missing_plausible_binding_inventory')
    bounds=[chart.bound(expr) for chart,expr in branches]
    return {'convex_hull':[min(x[0] for x in bounds),max(x[1] for x in bounds)],
            'branch_intervals':bounds,'n_plausible_bindings':len(bounds),
            'claims_actual_correct_visual_binding':False}
