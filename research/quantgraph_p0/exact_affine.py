"""Exact-rational 2D affine-axis feasible set for conditional chart bounds.

Provides exact arithmetic bounds *only under manually validated input evidence*.
No automatic chart reading, probabilistic coverage, or proof of source authenticity.
The mathematics is standard linear programming over rational inputs.
"""
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations

class EvidenceIncomplete(ValueError): pass


def Q(x):
    if type(x) not in (str,int,Fraction):
        raise EvidenceIncomplete('explicit rational inputs required, no floats')
    try:
        value=Fraction(x)
    except (ValueError,ZeroDivisionError):
        raise EvidenceIncomplete('invalid rational input')
    return value

@dataclass(frozen=True)
class Tick:
    pixel: str
    low: str
    high: str

@dataclass(frozen=True)
class Mark:
    name: str
    pixel_low: str
    pixel_high: str

class ExactSharedAxis:
    def __init__(self, ticks:list[Tick],marks:list[Mark],direction:str,provenance_verified:bool):
        if provenance_verified is not True:
            raise EvidenceIncomplete('visual provenance must be checked outside solver')
        if direction not in ('increasing','decreasing'):
            raise EvidenceIncomplete('unsupported axis orientation')
        if len(ticks)<2 or len(marks)<1:raise EvidenceIncomplete('need axis calibration and marks')
        self.direction=direction
        self.marks={}
        for m in marks:
            if m.name in self.marks or not m.name:
                raise EvidenceIncomplete('ambiguous mark identity')
            lo,hi=Q(m.pixel_low),Q(m.pixel_high)
            if lo>hi:raise EvidenceIncomplete('invalid pixel interval')
            self.marks[m.name]=(lo,hi)
        all_ticks=[]
        for t in ticks:
            p,lo,hi=Q(t.pixel),Q(t.low),Q(t.high)
            if lo>hi:raise EvidenceIncomplete('invalid tick values')
            all_ticks.append((p,lo,hi))
        all_ticks.sort(key=lambda r:r[0])
        for a,b in zip(all_ticks,all_ticks[1:]):
            if a[0]==b[0]:raise EvidenceIncomplete('duplicated calibration pixels')
            if direction=='decreasing' and not (a[1]>b[2]):
                raise EvidenceIncomplete('orientation not guaranteed by uncertain ticks')
            if direction=='increasing' and not (a[2]<b[1]):
                raise EvidenceIncomplete('orientation not guaranteed by uncertain ticks')
        for lo,hi in self.marks.values():
            if lo<all_ticks[0][0] or hi>all_ticks[-1][0]:
                raise EvidenceIncomplete('unjustified extrapolation')
        constraints=[]
        for p,lo,hi in all_ticks:
            constraints.extend([(p,Fraction(1),hi),(-p,Fraction(-1),-lo)])
        # Non-strict sign redundant under strict tick-interval monotonicity.
        constraints.append((Fraction(1),Fraction(0),Fraction(0)) if direction=='decreasing'
                           else (Fraction(-1),Fraction(0),Fraction(0)))
        vertices=set()
        for u,v in combinations(constraints,2):
            a1,b1,c1=u;a2,b2,c2=v
            det=a1*b2-a2*b1
            if not det:continue
            slope=(c1*b2-c2*b1)/det
            intercept=(a1*c2-a2*c1)/det
            if all(a*slope+b*intercept<=c for a,b,c in constraints):
                vertices.add((slope,intercept))
        if not vertices:raise EvidenceIncomplete('calibration infeasible')
        self.vertices=tuple(sorted(vertices))

    def bound(self,weights:dict[str,str],offset:str='0'):
        offset_q=Q(offset)
        q_weights={k:Q(v) for k,v in weights.items()}
        if not q_weights or any(k not in self.marks for k in q_weights):
            raise EvidenceIncomplete('missing or unknown mark')
        def opt(is_lower):
            p_sum=Fraction(0);w_sum=Fraction(0)
            for key,w in q_weights.items():
                lo,hi=self.marks[key]
                if self.direction=='decreasing':
                    pixel=(hi if w>=0 else lo) if is_lower else (lo if w>=0 else hi)
                else:
                    pixel=(lo if w>=0 else hi) if is_lower else (hi if w>=0 else lo)
                p_sum+=w*pixel;w_sum+=w
            evaluations=[p_sum*a+w_sum*b+offset_q for a,b in self.vertices]
            return min(evaluations) if is_lower else max(evaluations)
        return opt(True),opt(False)

    def evidence_flags(self):
        return {'conditional_on_external_visual_provenance':True,
                'rational_arithmetic_no_float_roundoff':True,
                'guarantee_for_trusted_affine_tick_and_pixel_intervals_only':True,
                'image_or_RAG_correctness_certified':False,
                'novel_mathematical_optimization_claim':False}
