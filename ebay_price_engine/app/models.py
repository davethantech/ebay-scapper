from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class ComponentSpec:
    kind: str
    name: str
    qty: int = 1
    capacity: Optional[float] = None
    capacity_unit: Optional[str] = None
    speed: Optional[float] = None
    speed_unit: Optional[str] = None
    tokens: List[str] = field(default_factory=list)

@dataclass
class TargetSpec:
    part_number: str
    description: str
    brand: Optional[str] = None
    model: Optional[str] = None
    family: Optional[str] = None
    form_factor: Optional[str] = None
    components: List[ComponentSpec] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

@dataclass
class Listing:
    item_id: str
    title: str
    url: str
    item_price: Optional[float]
    shipping: Optional[float]
    total: Optional[float]
    currency: Optional[str]
    condition: Optional[str]
    buying_options: List[str] = field(default_factory=list)
    quantity_available: Optional[int] = None
    description: str = ""
    brand: Optional[str] = None
    mpn: Optional[str] = None
    aspects: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MatchResult:
    listing: Listing
    score: float
    reasons: List[str] = field(default_factory=list)
    rejected: bool = False
    rejection_reason: Optional[str] = None
    component_coverage: Dict[str, int] = field(default_factory=dict)

@dataclass
class MarketResult:
    price: Optional[float] = None
    shipping: Optional[float] = None
    total: Optional[float] = None
    method: Optional[str] = None
    link: Optional[str] = None
    matched_title: Optional[str] = None
    status: str = "NOT_FOUND"
    notes: str = ""
    audit: List[Dict[str, Any]] = field(default_factory=list)
