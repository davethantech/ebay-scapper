import re
from .models import TargetSpec, Listing, MatchResult

BAD=re.compile(r"\b(for parts|not working|broken|repair|spares|parts only|parts\s*/\s*only|untested|as-is|empty box|dummy|manual|cable only|cover only|bezel only|tray only|caddy only|heatsink only|fan only|power supply only)\b",re.I)

def txt(l):
    return " ".join([l.title or "",l.description or "",l.brand or "",l.mpn or ""]+[str(v) for v in (l.aspects or {}).values()]).lower()
def tokens(s): return re.findall(r"[a-z0-9]+",str(s or "").lower())
def numbers(s,units): return [(float(v),u.lower()) for v,u in re.findall(r"(\d+(?:\.\d+)?)\s*("+"|".join(units)+r")\b",s,re.I)]

def _model_ok(spec,t):
    if not spec.model:return True,0
    mt=tokens(spec.model); hit=sum(x in t for x in mt if len(x)>1)
    if hit==len(mt):return True,40
    # Model family words alone are not sufficient when the numeric model is absent.
    if len(mt)>1 and hit>=len(mt)-1:return True,18
    return False,-45

def _cpu_ok(c,t):
    ct=tokens(c.name)
    # Require the meaningful CPU family/model tokens, not merely the word CPU.
    meaningful=[x for x in ct if x not in {"cpu","processor","intel","amd"} and len(x)>1]
    if meaningful and not all(x in t for x in meaningful): return False,-35
    if c.speed is not None:
        vals=numbers(t,["ghz","mhz"])
        if vals:
            target=c.speed if (c.speed_unit or "GHZ").lower()=="ghz" else c.speed
            unit=(c.speed_unit or "GHZ").lower()
            if not any(abs(v-target)<0.021 and u==unit for v,u in vals): return False,-40
    return True,22

def _ram_ok(c,t):
    if c.capacity is None:return True,8
    vals=numbers(t,["gb","tb"])
    unit=(c.capacity_unit or "GB").lower()
    if vals and not any(abs(v-c.capacity)<0.01 and u==unit for v,u in vals):return False,-30
    return True,12

def _storage_ok(c,t):
    if c.capacity is None:return True,8
    vals=numbers(t,["gb","tb"]); unit=(c.capacity_unit or "GB").lower()
    typ=next((x for x in ("sas","sata","ssd","hdd","nvme") if x in t),None)
    required_type=next((x for x in ("sas","sata","ssd","hdd","nvme") if x in c.name.lower()),None)
    if required_type and typ and required_type!=typ:return False,-25
    if vals and not any(abs(v-c.capacity)<0.01 and u==unit for v,u in vals):return False,-25
    return True,10

def match(spec:TargetSpec,listing:Listing):
    t=txt(listing); reasons=[]; score=0
    if BAD.search(t):return MatchResult(listing,0,rejected=True,rejection_reason="damaged/parts/accessory language")
    if spec.brand:
        if spec.brand.lower() in t:score+=15; reasons.append("brand")
        else:return MatchResult(listing,-30,rejected=True,rejection_reason="brand conflict")
    ok,pts=_model_ok(spec,t)
    if not ok:return MatchResult(listing,score+pts,reasons,rejected=True,rejection_reason="model/generation mismatch")
    score+=pts; reasons.append("model")
    if spec.form_factor:
        ff=spec.form_factor.lower().replace(" ","")
        if ff in t.replace(" ","") or spec.form_factor.lower() in t:score+=8; reasons.append("form factor")
    for c in spec.components:
        if c.kind=="cpu":ok,pts=_cpu_ok(c,t)
        elif c.kind=="ram":ok,pts=_ram_ok(c,t)
        elif c.kind=="storage":ok,pts=_storage_ok(c,t)
        else:ok,pts=True,5
        if not ok:return MatchResult(listing,score+pts,reasons,rejected=True,rejection_reason=f"{c.kind} configuration conflict")
        score+=pts; reasons.append(f"{c.kind} configuration")
    if spec.part_number and spec.part_number.lower() in t:score+=10;reasons.append("part number corroborates")
    if listing.total is None:return MatchResult(listing,score,reasons,rejected=True,rejection_reason="shipping/total unavailable")
    if listing.currency is None:return MatchResult(listing,score,reasons,rejected=True,rejection_reason="currency unavailable")
    return MatchResult(listing,score,reasons)
