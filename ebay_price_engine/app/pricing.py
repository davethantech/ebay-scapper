import re
from typing import List, Tuple
from .models import Listing, ComponentSpec

def extract_quantity(text, component: ComponentSpec):
    t=text.lower()
    for p in [r"\b(\d+)\s*(?:pack|pcs?|pieces?|units?)\b",r"\b(\d+)\s*[x×]\s*(?:modules?|sticks?|drives?|cpus?|processors?|pieces?)\b"]:
        m=re.search(p,t)
        if m:return max(1,int(m.group(1)))
    if component.kind=="cpu":
        m=re.search(r"\b(\d+)\s*[x×]\s*(?:intel|amd|xeon|pentium|processor|cpu)",t)
        if m:return max(1,int(m.group(1)))
    return 1

def bundle_cover(candidates: List[Tuple[Listing,int]], required:int):
    inf=10**18; dp=[(inf,[]) for _ in range(required+max([q for _,q in candidates],default=1))]; dp[0]=(0,[])
    for i in range(1,len(dp)):
        for idx,(l,q) in enumerate(candidates):
            if l.total is None:continue
            prev=max(0,i-q); cost,plan=dp[prev]
            if cost+l.total<dp[i][0]:dp[i]=(cost+l.total,plan+[idx])
    best=None
    for i in range(required,len(dp)):
        if dp[i][0]<inf and (best is None or dp[i][0]<best[0]):best=(dp[i][0],dp[i][1])
    return best
