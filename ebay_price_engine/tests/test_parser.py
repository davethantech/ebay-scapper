from app.parser import parse_description, search_queries

def test_description_is_primary():
    s=parse_description("Dell1650-2xSL5XL","Dell PowerEdge 1650 Rackmount Server 2 x Intel Pentium III 1.4GHz CPU 2GB RAM Dell1650-2xSL5XL")
    assert s.model.lower().startswith("poweredge 1650")
    assert any(c.kind=="cpu" and c.qty==2 for c in s.components)
    assert any(c.kind=="ram" and c.capacity==2 for c in s.components)
    assert any("PowerEdge 1650" in q for q in search_queries(s))

def test_pn_not_required_in_queries():
    s=parse_description("ABC-123","Dell PowerEdge 1650 1U Server")
    assert search_queries(s)[0] != "ABC-123"
