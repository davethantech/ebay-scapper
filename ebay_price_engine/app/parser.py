import re
from .models import TargetSpec, ComponentSpec

STOP={"the","and","for","with","from","other","alt","ea","each","used","new","server","system","kit","assy","assembly","only","unit"}
BRANDS=("Dell","HP","HPE","IBM","Lenovo","Cisco","Supermicro","Intel","AMD","NetApp","EMC","Fujitsu","Oracle")

def clean(s): return re.sub(r"\s+"," ",str(s or "")).strip()
def norm(s): return re.sub(r"[^a-z0-9]+","",str(s or "").lower())

def parse_description(part_number,description,brand_hint=None):
    d=clean(description)
    brand=brand_hint.strip().title() if brand_hint and brand_hint.strip() else next((b for b in BRANDS if re.search(rf"\b{re.escape(b)}\b",d,re.I)),None)
    model=None
    for p in [r"\b(PowerEdge\s+[A-Za-z0-9-]+)",r"\b(ProLiant\s+[A-Za-z0-9-]+)",r"\b(ThinkServer\s+[A-Za-z0-9-]+)",r"\b(ThinkSystem\s+[A-Za-z0-9-]+)",r"\b(Precision\s+[A-Za-z0-9-]+)",r"\b(OptiPlex\s+[A-Za-z0-9-]+)",r"\b([A-Z]{1,5}\d{3,6}(?:-[A-Z0-9]+)?)\b"]:
        m=re.search(p,d,re.I)
        if m: model=clean(m.group(1)); break
    form=next((x for x in ["12U","8U","6U","4U","2U","1U","tower","rackmount","rack mount","SFF","LFF","blade"] if re.search(rf"\b{re.escape(x)}\b",d,re.I)),None)
    family=re.sub(r"[^A-Za-z]+"," ",model).strip() if model else None
    comps=[]
    cpu_re=re.compile(r"(?:(\d+)\s*[x×]\s*)?(?:intel\s+|amd\s+)?((?:xeon|pentium|core\s+i[3579]|celeron|epyc|opteron|atom)[^,;]*?)(?=\s+(?:cpu|processor|processors|ram|memory|\d+\s*(?:gb|tb))\b|[,;]|$)",re.I)
    for m in cpu_re.finditer(d):
        raw=clean(m.group(2)); qty=int(m.group(1) or 1); sm=re.search(r"(\d+(?:\.\d+)?)\s*(ghz|mhz)",raw,re.I)
        comps.append(ComponentSpec("cpu",raw,qty,speed=float(sm.group(1)) if sm else None,speed_unit=sm.group(2).upper() if sm else None,tokens=re.findall(r"[a-z0-9]+",raw.lower())))
    for m in re.finditer(r"(?:(\d+)\s*[x×]\s*)?(\d+(?:\.\d+)?)\s*(GB|TB)\s*(DDR\d(?:[-/][A-Z0-9]+)?|ECC|RAM|MEMORY)?",d,re.I):
        qty=int(m.group(1) or 1); cap=float(m.group(2)); unit=m.group(3).upper(); typ=(m.group(4) or "RAM").upper(); prev=d[max(0,m.start()-25):m.start()].lower()
        if any(x in prev for x in ["hdd","ssd","sas","sata","nvme","hard drive","disk","storage"]): continue
        comps.append(ComponentSpec("ram",f"{cap:g}{unit} {typ}",qty,capacity=cap,capacity_unit=unit,tokens=[typ.lower(),unit.lower(),str(cap)]))
    for m in re.finditer(r"(?:(\d+)\s*[x×]\s*)?(\d+(?:\.\d+)?)\s*(TB|GB)\s*(SAS|SATA|SSD|HDD|NVME)",d,re.I):
        qty=int(m.group(1) or 1); cap=float(m.group(2)); unit=m.group(3).upper(); typ=m.group(4).upper()
        comps.append(ComponentSpec("storage",f"{cap:g}{unit} {typ}",qty,capacity=cap,capacity_unit=unit,tokens=[typ.lower(),unit.lower(),str(cap)]))
    keywords=[x for x in re.findall(r"[A-Za-z0-9][A-Za-z0-9+._/-]*",d) if len(x)>=2 and x.lower() not in STOP]
    return TargetSpec(clean(part_number),d,brand,model,family,form,comps,keywords)

def search_queries(spec):
    q=[]
    def add(x):
        x=clean(x)
        if len(x)>=3 and x not in q:q.append(x)
    if spec.brand and spec.model:add(f"{spec.brand} {spec.model}")
    if spec.model:add(spec.model)
    if spec.model and spec.form_factor:add(f"{spec.model} {spec.form_factor}")
    for c in spec.components:
        if spec.model:add(f"{spec.brand or ''} {spec.model} {c.name}".strip())
        if c.kind=="cpu":
            add(f"{spec.model or spec.brand or ''} {c.name}".strip())
            if c.speed:add(f"{spec.model or ''} {c.speed:g}{c.speed_unit or 'GHz'}")
        elif c.capacity:add(f"{spec.model or ''} {c.capacity:g}{c.capacity_unit or ''} {c.kind}")
    if spec.part_number:add(spec.part_number)
    core=[x for x in spec.keywords if not re.fullmatch(r"[A-Z0-9_-]{8,}",x)]
    add(" ".join(core[:8]))
    return q[:12]
