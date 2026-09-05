import re
from .models import TargetSpec, Listing, MatchResult

BAD=re.compile(r"\b(for parts|not working|broken|repair|spares|parts only|parts\s*/\s*only|untested|as-is|empty box|dummy|manual|cable only|cover only|bezel only|tray only|caddy only)\b",re.I)

def txt(l): return " ".join([l.title or "", l.description or "", l.brand or "", l.mpn or "", " ".join(str(v) for v in (l.aspects or {}).values())]).lower()
def number_unit(s):
    m=re.search(r"(\d+(?:\.\d+)?)\s*(gb|tb|ghz|mhz)",s,re.I); return (float(m.group(1)),m.group(2).lower()) if m else None

def match(spec: TargetSpec, listing: Listing):
    t=txt(listing); reasons=[]; score=0
    if BAD.search(t): return MatchResult(listing,0,rejected=True,rejection_reason="damaged/parts/accessory language")
    if spec.brand:
        if spec.brand.lower() in t: score+=12; reasons.append("brand")
        else: score-=18; reasons.append("brand conflict")
    if spec.model:
        mt=[x for x in re.findall(r"[a-z0-9]+",spec.model.lower()) if len(x)>1]
        hit=sum(x in t for x in mt)
        score += min(38, 12*hit)
        if hit<len(mt): reasons.append("model incomplete")
        else: reasons.append("model")
    if spec.form_factor and spec.form_factor.lower() in t: score+=8; reasons.append("form factor")
    for c in spec.components:
        terms=[x for x in re.findall(r"[a-z0-9]+",c.name.lower()) if len(x)>1]
        hits=sum(x in t for x in terms)
        if hits>=max(1,min(2,len(terms))): score+=12; reasons.append(f"{c.kind} matched")
        if c.speed is not None:
            speeds=[number_unit(x) for x in re.findall(r"\d+(?:\.\d+)?\s*(?:ghz|mhz)",t)]
            if speeds and not any(abs(v-(c.speed if u==c.speed_unit.lower() else c.speed))<0.02 for v,u in speeds):
                score-=30; reasons.append("CPU speed conflict")
        if c.capacity is not None and c.kind=="ram":
            vals=[number_unit(x) for x in re.findall(r"\d+(?:\.\d+)?\s*(?:gb|tb)",t)]
            if vals and not any(abs(v-c.capacity)<0.01 and u==c.capacity_unit.lower() for v,u in vals):
                score-=22; reasons.append("RAM capacity conflict")
    if spec.part_number and spec.part_number.lower() in t: score+=10; reasons.append("part number corroborates")
    if listing.total is None: return MatchResult(listing,score,reasons,rejected=True,rejection_reason="shipping/total unavailable")
    if listing.currency is None: return MatchResult(listing,score,reasons,rejected=True,rejection_reason="currency unavailable")
    return MatchResult(listing,score,reasons)
