from app.models import ComponentSpec, Listing
from app.pricing import extract_quantity, bundle_cover

def L(total,title): return Listing(title,title,title,total,0,total,'AUD','Used',['FIXED_PRICE'])

def test_bundle_quantity_semantic():
    c=ComponentSpec('ram','16GB DDR4',qty=2)
    assert extract_quantity('16GB DDR4 2 Pack Memory',c)==2

def test_bundle_optimizer_uses_actual_bundle_cost():
    c=ComponentSpec('ram','16GB DDR4',qty=3)
    a=L(25,'16GB DDR4 single'); b=L(60,'16GB DDR4 3 pack')
    cost,plan=bundle_cover([(a,1),(b,3)],3)
    assert cost==60
