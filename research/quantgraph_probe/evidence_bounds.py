"""Conditional evidence-bound reasoning for LINEAR chart axes.
Not image recognition, not a calibrated probabilistic method, not a novelty claim.
Assumes *externally verified* axis and mark pixel intervals that truly contain
source values. Exact Fraction arithmetic preserves affine shared dependencies.
"""
from dataclasses import dataclass
from fractions import Fraction
from typing import Mapping

class InsufficientEvidence(ValueError):
    pass

def rational(value):
    if isinstance(value, float):
        raise TypeError("inexact binary floats not allowed in exact bound")
    return Fraction(value)

@dataclass(frozen=True)
class Interval:
    low: Fraction
    high: Fraction
    def __post_init__(self):
        if self.low > self.high:
            raise ValueError("inverted evidence interval")
    @classmethod
    def of(cls, low, high):
        return cls(rational(low), rational(high))
    def contains(self, v):
        return self.low <= rational(v) <= self.high
    def add(self, other):
        return Interval(self.low + other.low, self.high + other.high)
    def neg(self):
        return Interval(-self.high, -self.low)
    def mul(self, other):
        corners=[self.low*other.low,self.low*other.high,self.high*other.low,self.high*other.high]
        return Interval(min(corners),max(corners))
    def div(self, other):
        if other.low <= 0 <= other.high:
            raise InsufficientEvidence("possible zero denominator")
        inv=Interval(min(1/other.low,1/other.high),max(1/other.low,1/other.high))
        return self.mul(inv)

@dataclass(frozen=True)
class AxisLinear:
    p0: Fraction
    p1: Fraction
    v0: Fraction
    v1: Fraction
    chart_id: str
    calibration_verified: bool
    @classmethod
    def of(cls, chart_id, p0, v0, p1, v1, *, calibration_verified):
        if not chart_id or rational(p0)==rational(p1) or rational(v0)==rational(v1):
            raise InsufficientEvidence("missing/degenerate linear-axis calibration")
        return cls(rational(p0),rational(p1),rational(v0),rational(v1),
                   chart_id,calibration_verified)
    def read(self, pixel_interval, *, mark_verified, observation_id):
        if not self.calibration_verified or not mark_verified or not observation_id:
            raise InsufficientEvidence("unverified axis/mark provenance")
        slope=(self.v1-self.v0)/(self.p1-self.p0)
        a=self.v0+(pixel_interval.low-self.p0)*slope
        b=self.v0+(pixel_interval.high-self.p0)*slope
        return Observation(self.chart_id,observation_id,Interval(min(a,b),max(a,b)))

@dataclass(frozen=True)
class Observation:
    chart_id: str
    observation_id: str
    values: Interval
    @property
    def key(self):
        return self.chart_id+"/"+self.observation_id

@dataclass(frozen=True)
class LinearExpression:
    coefficients: Mapping[str,Fraction]
    intercept: Fraction=Fraction(0)
    @classmethod
    def variable(cls,key):
        if not key: raise InsufficientEvidence("missing variable identity")
        return cls({key:Fraction(1)})
    def plus(self,other):
        c=dict(self.coefficients)
        for key,val in other.coefficients.items():
            c[key]=c.get(key,Fraction(0))+val
        return LinearExpression({k:v for k,v in c.items() if v},
                                self.intercept+other.intercept)
    def scale(self,factor):
        f=rational(factor)
        return LinearExpression({k:v*f for k,v in self.coefficients.items()},
                                self.intercept*f)
    def minus(self,other):
        return self.plus(other.scale(-1))
    def evaluate(self,evidence:Mapping[str,Observation]):
        lo=self.intercept;hi=self.intercept
        for key,factor in self.coefficients.items():
            if key not in evidence or evidence[key].key!=key:
                raise InsufficientEvidence("missing chart-grounded source: "+key)
            v=evidence[key].values
            lo+=factor*(v.low if factor>=0 else v.high)
            hi+=factor*(v.high if factor>=0 else v.low)
        return Interval(lo,hi)

@dataclass(frozen=True)
class Decision:
    status: str
    margin: Interval

def compare_gt(left,right,evidence):
    delta=left.minus(right).evaluate(evidence)
    if delta.low>0:return Decision("PROVEN_TRUE",delta)
    if delta.high<=0:return Decision("PROVEN_FALSE",delta)
    return Decision("ABSTAIN",delta)

def naive_independent_subtraction(left,right):
    return left.add(right.neg())
