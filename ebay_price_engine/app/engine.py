import hashlib, json, logging, os
from .config import Config
from .ebay import EbayClient
from .models import Listing, MarketResult, TargetSpec
from .parser import parse_description, search_queries
from .matcher import match
from .pricing import extract_quantity, bundle_cover

LOG=logging.getLogger("ebay-engine")
MARKETS={"AU":{"id":"EBAY_AU","currency":"AUD","country_key":"au_country","postal_key":"au_postal"},"US":{"id":"EBAY_US","currency":"USD","country_key":"us_country","postal_key":"us_postal"}}

def money(x):
    try:return float(x)
    except:return None

def listing_from_json(j, currency):
    ship=None; opts=j.get("shippingOptions") or []; vals=[]
    for o in opts:
        c=(o.get("shippingCost") or {}).get("value")
        if c is not None: vals.append(money(c))
    if vals: ship=min(vals)
    p=money((j.get("price") or {}).get("value")); cur=(j.get("price") or {}).get("currency") or currency
    total=p+ship if p is not None and ship is not None else None
    aspects={str(a.get("name")):a.get("value") for a in (j.get("localizedAspects") or [])}
    return Listing(j.get("itemId","") or j.get("legacyItemId",""),j.get("title","") or "",j.get("itemWebUrl","") or "",p,ship,total,cur,(j.get("condition") or j.get("conditionId")),j.get("buyingOptions") or [],(j.get("estimatedAvailabilities") or [{}])[0].get("estimatedAvailableQuantity"),j.get("shortDescription","") or "",None,None,aspects,j)

def listing_search_text(j):
    parts=[j.get("title","")]
    for a in j.get("localizedAspects") or []: parts += [str(a.get("name","")),str(a.get("value",""))]
    return " ".join(parts)

def candidate_ids(client, market_id, queries, cfg):
    ids={}
    for q in queries:
        try: items=client.search(market_id,q,cfg.search_pages,cfg.search_page_size)
        except Exception as e: LOG.warning("Search failed [%s]: %s",q,e); continue
        for x in items:
            iid=x.get("itemId") or x.get("legacyItemId")
            if iid and iid not in ids: ids[iid]=x
            if len(ids)>=cfg.max_candidates_per_query: break
    return ids

def analyse_market(spec, market, client, cfg):
    m=MARKETS[market]; queries=search_queries(spec); ids=candidate_ids(client,m["id"],queries,cfg); details=[]; audit=[]; calls=0
    for iid,summary in ids.items():
        if calls>=cfg.max_detail_calls_per_market: break
        try:
            j=client.detail(m["id"],iid,getattr(cfg,m["country_key"]),getattr(cfg,m["postal_key"])); calls+=1; l=listing_from_json(j,m["currency"]); r=match(spec,l)
            audit.append({"item_id":iid,"title":l.title,"price":l.item_price,"shipping":l.shipping,"total":l.total,"score":r.score,"rejected":r.rejected,"reason":r.rejection_reason or "","reasons":"; ".join(r.reasons)})
            if not r.rejected and l.currency==m["currency"] and r.score>=cfg.min_match_score: details.append(r)
        except Exception as e: audit.append({"item_id":iid,"title":summary.get("title","")[:200],"rejected":True,"reason":f"detail error: {e}"})
    details.sort(key=lambda x:x.listing.total if x.listing.total is not None else 10**18)
    if details:
        b=details[0].listing; return MarketResult(b.item_price,b.shipping,b.total,"complete_listing",b.url,b.title,"FOUND","; ".join(details[0].reasons),audit)
    component_results=[]
    for c in spec.components[:cfg.max_component_depth]:
        cqueries=[f"{spec.brand or ''} {spec.model or ''} {c.name}".strip(),c.name]; ids2=candidate_ids(client,m["id"],cqueries,cfg); cs=[]
        for iid in ids2:
            if calls>=cfg.max_detail_calls_per_market*2: break
            try:
                j=client.detail(m["id"],iid,getattr(cfg,m["country_key"]),getattr(cfg,m["postal_key"])); calls+=1; l=listing_from_json(j,m["currency"]); r=match(TargetSpec(spec.part_number,c.name,spec.brand,spec.model,spec.family,spec.form_factor,[c],c.tokens),l)
                if not r.rejected and r.score>=cfg.min_match_score and l.currency==m["currency"]: cs.append((l,extract_quantity(l.title+" "+l.description,c)))
            except Exception: pass
        if not cs: return MarketResult(status="COMPONENT_UNAVAILABLE",notes=f"No independently priced valid {c.kind} listing",audit=audit)
        cov=bundle_cover(cs,c.qty)
        if not cov: return MarketResult(status="COMPONENT_UNAVAILABLE",notes=f"Cannot acquire required quantity of {c.name}",audit=audit)
        cost,plan=cov; component_results.append((c,cost,[cs[i][0] for i in plan]))
    total=sum(x[1] for x in component_results); links=" | ".join(dict.fromkeys(l.url for _,_,ls in component_results for l in ls)); titles=" | ".join(dict.fromkeys(l.title for _,_,ls in component_results for l in ls))
    return MarketResult(None,None,total,"components",links,titles,"FOUND","; ".join(f"{c.name} x{c.qty}" for c,_,_ in component_results),audit)

def row_key(row): return hashlib.sha256((str(row.get("Part number",""))+"|"+str(row.get("Product Description",""))).encode()).hexdigest()
def load_checkpoint(path):
    if not os.path.exists(path): return {}
    try:return json.load(open(path,encoding="utf8"))
    except:return {}
def save_checkpoint(path,data):
    tmp=path+".tmp"; json.dump(data,open(tmp,"w",encoding="utf8"),indent=2,ensure_ascii=False); os.replace(tmp,path)

def analyse_dataframe(df,cfg,checkpoint="checkpoint.json"):
    df=df.rename(columns={c:c.strip() for c in df.columns}); pn=next((c for c in df.columns if c.lower()=="part number"),None); desc=next((c for c in df.columns if c.lower()=="product description"),None)
    if not pn or not desc: raise ValueError("Input must contain Part number and Product Description columns.")
    client=EbayClient(cfg.client_id,cfg.client_secret,cfg.timeout,cfg.retries); cp=load_checkpoint(checkpoint); out=[]
    for i,(_,row) in enumerate(df.iterrows(),1):
        base=row.to_dict(); spec=parse_description(str(row[pn]),str(row[desc]),str(row.get("Brand", "")) or None); key=row_key({"Part number":row[pn],"Product Description":row[desc]}); LOG.info("[%d/%d] %s",i,len(df),spec.part_number)
        rec=cp.get(key)
        if rec and rec.get("finalized"): out.append(rec["row"]); continue
        au=analyse_market(spec,"AU",client,cfg); us=analyse_market(spec,"US",client,cfg); result=dict(base)
        result.update({"Ebay AU cheapest price":au.item_price,"Ebay AU link":au.link,"Ebay AU shipping":au.shipping,"Ebay AU total":au.total,"Ebay AU method":au.method,"Ebay AU status":au.status,"Ebay US cheapest price":us.item_price,"Ebay US link":us.link,"Ebay US shipping":us.shipping,"Ebay US total":us.total,"Ebay US method":us.method,"Ebay US status":us.status})
        cp[key]={"finalized":True,"row":result}; save_checkpoint(checkpoint,cp); out.append(result)
    import pandas as pd
    return pd.DataFrame(out)
