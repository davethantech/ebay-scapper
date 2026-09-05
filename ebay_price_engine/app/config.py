import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    client_id: str
    client_secret: str
    search_pages: int = 3
    search_page_size: int = 50
    max_candidates_per_query: int = 150
    max_detail_calls_per_market: int = 80
    min_match_score: float = 72
    max_component_depth: int = 3
    timeout: int = 30
    retries: int = 4
    au_country: str = "AU"
    au_postal: str = ""
    us_country: str = "US"
    us_postal: str = ""

    @classmethod
    def from_env(cls):
        cid, secret = os.getenv("EBAY_CLIENT_ID"), os.getenv("EBAY_CLIENT_SECRET")
        if not cid or not secret:
            raise RuntimeError("Set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET in .env or the environment.")
        return cls(
            cid, secret,
            int(os.getenv("SEARCH_PAGES", 3)),
            int(os.getenv("SEARCH_PAGE_SIZE", 50)),
            int(os.getenv("MAX_CANDIDATES_PER_QUERY", 150)),
            int(os.getenv("MAX_DETAIL_CALLS_PER_MARKET", 80)),
            float(os.getenv("MIN_MATCH_SCORE", 72)),
            int(os.getenv("MAX_COMPONENT_DEPTH", 3)),
            int(os.getenv("REQUEST_TIMEOUT", 30)),
            int(os.getenv("RETRY_COUNT", 4)),
            os.getenv("AU_SHIP_TO_COUNTRY", "AU"), os.getenv("AU_SHIP_TO_POSTAL_CODE", ""),
            os.getenv("US_SHIP_TO_COUNTRY", "US"), os.getenv("US_SHIP_TO_POSTAL_CODE", ""),
        )
