# eBay Description-First Price Engine

Real-data Python CLI for independently pricing inventory on eBay Australia and eBay US.

## Core rule
Product Description is the source of truth. Part Number is supporting evidence, never a mandatory title match.

The engine:
- parses description into model/form-factor/component requirements;
- generates progressive description/model searches and optionally searches the P/N;
- searches AU and US independently through eBay Browse API;
- retrieves listing details before pricing;
- rejects damaged/parts/accessory listings and conflicting configurations;
- requires known shipping before using a listing total;
- evaluates every valid candidate it retrieves, then chooses the lowest valid total rather than the highest-ranked result;
- prefers a complete configured listing;
- if no complete listing is found and components were identified, searches components independently;
- solves bundle quantity as an acquisition-cost problem (whole bundle price + shipping), not unit-price division;
- never treats chassis expressions such as `16x SFF` as a purchase quantity;
- keeps AUD and USD completely separate;
- checkpoints rows using a stable hash of part number + description.

## Install
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows
```

Set production eBay `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET`. Browse API search and item retrieval use an Application access token.

## Run
```bash
python -m app.cli "Server_price analysis.csv" --output results.xlsx
```

It writes `results.xlsx` and `results.csv` and maintains `checkpoint.json`.

## Shipping
For calculated shipping, configure the destination postal code in `.env`. If eBay does not provide a shipping cost, the listing is not priced as free shipping; it is rejected for pricing until shipping is known.

## Important limitation
Semantic extraction is deterministic and intentionally conservative. It does not invent specifications that are absent from the description. Complex descriptions may need additional parser rules for new hardware families. No fake/mock eBay data is included.
