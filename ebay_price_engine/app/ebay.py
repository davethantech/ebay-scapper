import base64, time, requests

class EbayClient:
    def __init__(self, client_id, client_secret, timeout=30, retries=4):
        self.cid=client_id; self.secret=client_secret; self.timeout=timeout; self.retries=retries; self.token=None; self.expires_at=0
        self.session=requests.Session()

    def token_value(self):
        if self.token and time.time() < self.expires_at-120: return self.token
        basic=base64.b64encode(f"{self.cid}:{self.secret}".encode()).decode()
        r=self.session.post("https://api.ebay.com/identity/v1/oauth2/token", headers={"Authorization":f"Basic {basic}","Content-Type":"application/x-www-form-urlencoded"}, data={"grant_type":"client_credentials","scope":"https://api.ebay.com/oauth/api_scope"}, timeout=self.timeout)
        r.raise_for_status(); j=r.json(); self.token=j["access_token"]; self.expires_at=time.time()+int(j.get("expires_in",7200)); return self.token

    def _get(self, url, params=None, headers=None):
        for attempt in range(self.retries):
            h={"Authorization":f"Bearer {self.token_value()}","Accept":"application/json","Accept-Language":"en-AU"}; h.update(headers or {})
            r=self.session.get(url, params=params, headers=h, timeout=self.timeout)
            if r.status_code==401:
                self.token=None; continue
            if r.status_code==429 or 500 <= r.status_code < 600:
                time.sleep(min(30,2**attempt)); continue
            r.raise_for_status(); return r.json()
        raise RuntimeError(f"eBay request failed after {self.retries} attempts: {url}")

    def search(self, marketplace_id, query, pages=3, page_size=50):
        url="https://api.ebay.com/buy/browse/v1/item_summary/search"
        all_items=[]
        for page in range(pages):
            data=self._get(url, {"q":query,"limit":page_size,"offset":page*page_size,"filter":"buyingOptions:{FIXED_PRICE}"}, {"X-EBAY-C-MARKETPLACE-ID":marketplace_id})
            items=data.get("itemSummaries",[]) or []
            all_items.extend(items)
            if len(items)<page_size or not data.get("next"): break
        return all_items

    def detail(self, marketplace_id, item_id, country=None, postal=None):
        headers={"X-EBAY-C-MARKETPLACE-ID":marketplace_id}
        if country:
            ctx=f"contextualLocation=country={country}"
            if postal: ctx += f";zip={postal}"
            headers["X-EBAY-C-ENDUSERCTX"]=ctx
        return self._get(f"https://api.ebay.com/buy/browse/v1/item/{item_id}", headers=headers)
