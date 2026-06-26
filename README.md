<<<<<<< HEAD
# priceaccess-navigator
AI-augmented decision support for pharmaceutical pricing &amp; market access — IRP cascade simulation across 6 markets. [Live one-pager](https://kubra-sirin-meydanli.github.io/priceaccess-navigator/)
=======
# priceaccess-engine

**UC1 Price-Change Cascade Engine** — part of [PriceAccess Navigator](https://github.com/kubrameydanli/priceaccess-navigator), a personal portfolio project demonstrating pharmaceutical pricing and market-access analytics.

> All data is synthetic. SyntaRelX is a fictitious IL-17A inhibitor; no real product prices are represented.

---

## What This Module Does

Models the mandatory ex-factory list-price (EFP) cascade that follows a regulated price reduction in one reference market. When a post-launch price renegotiation is concluded — triggered by AMNOG benefit assessment in Germany, CEPS arbitration in France, or a CIPM revision in Spain — other markets that hold IRP baskets referencing that country must reassess their own approved prices.

The engine applies **marginal transmission logic**: a market's approved price declines only by the extent to which the shocked EFP lowers its binding IRP ceiling. If the new reference price remains above a market's current approved price, no cascade occurs for that market in that iteration.

### Use-case scope

| Use case | Description | Status |
|---|---|---|
| **UC1** | Mandatory list-price cascade across IRP baskets (post-launch, full-basket trigger) | This module |
| UC2 | Launch-sequence optimisation — ordering markets to minimise IRP exposure | Planned |
| UC3 | HTA outcome stress test — simulating reimbursement delisting or step-therapy constraints | Planned |

---

## IRP Basket Coverage

Six markets modelled. All prices are normalised to EUR (Turkey converted at the fixed MoH reference rate). Basket composition and the ceiling rule for each market are configurable in `config/baskets.yaml`.

| Market | Regulatory anchor | Ceiling rule | IRP basket (markets referenced) | Price referenced |
|---|---|---|---|---|
| Germany | AMNOG benefit assessment → GKV-SV negotiated Erstattungsbetrag | Free pricing (no inbound IRP) | — (a reference *for* others; references none) | List (EFP) |
| France | HAS (ASMR) → CEPS-negotiated price | Lowest of basket | Germany, UK, Spain, Netherlands, Italy, Belgium, Sweden, Austria, Finland, Portugal | List (EFP) |
| Netherlands | WGP maximum price (IRP-based) / ZIN | Average of basket | France, UK, Belgium, Norway | List (EFP) |
| UK | NICE appraisal / VPAG | Free pricing (no inbound IRP) | — (references none) | List (EFP) |
| Spain | CIPM resolution | Lowest of basket | Germany, France, UK, Italy, Portugal | List (EFP) |
| Turkey | TİTCK / MoH reference basket | Lowest of basket | France, Spain, Greece, Italy, Portugal | List (EFP), at the fixed MoH reference rate |

Basket weights and active/inactive status are defined in `config/baskets.yaml`.

---

## Core Logic

```
Shock input: (market, old_EFP, new_EFP, effective_date)
                    │
                    ▼
        compute_binding_ceiling(market, baskets)
          → min EFP across active basket members
                    │
                    ▼
        marginal_transmission(current_approved_price,
                              old_ceiling, new_ceiling)
          → max(0, current_price - (old_ceiling - new_ceiling))
                    │
                    ▼
        propagate to next-degree markets
          (markets that reference the shocked market)
                    │
                    ▼
        repeat until no further reduction propagates
```

**List vs net price distinction:** The model tracks both the approved list EFP and an estimated net price (list minus managed-entry agreement discount). IRP cross-references use list prices throughout, consistent with the predominant regulatory practice in the six markets covered. Net prices are reported separately and are not propagated.

---

## Synthetic Asset

**SyntaRelX** — IL-17A inhibitor archetype (specialty biologic, subcutaneous, 150 mg/mL auto-injector). Indication: moderate-to-severe plaque psoriasis. Launched sequentially across the six markets with synthetic list EFPs, net discount assumptions, and IRP trigger dates. All figures are illustrative and designed to produce non-trivial cascade behaviour for demonstration purposes.

Reference prices and launch dates are defined in `data/syntarelx_baseline.csv`.

---

## Validation

The cascade model is validated against a hand-built Excel workbook (`validation/UC1_golden_model.xlsx`) that implements the same marginal transmission formula independently. The test suite compares engine output against the workbook's golden cases for each market and each cascade iteration.

```bash
pytest tests/test_uc1_golden.py -v
```

A mismatch between engine output and the golden workbook causes the test to fail with a per-market diff table.

---

## Optional Narrative Output

After the cascade completes, the engine can call the Claude API to produce a plain-English market-access memo summarising which markets were affected, by how much, and the policy rationale. This is a single, optional call; it has no effect on the numerical output.

Set `NARRATIVE=true` in `.env` to enable it. Requires `ANTHROPIC_API_KEY`.

---

## Stack

- **Python 3.12** — all cascade logic
- **pandas / numpy** — basket calculations and currency conversion
- **pytest** — golden-case validation
- **PyYAML** — basket and config files
- **Anthropic Python SDK** — optional narrative generation (Claude API)

---

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in ANTHROPIC_API_KEY if using narrative
```

### Run a cascade

```bash
python -m engine.uc1 \
  --market DE \
  --old-efp 850.00 \
  --new-efp 712.00 \
  --effective-date 2025-01-01
```

### Run tests

```bash
pytest
```

---

## Repository Layout

```
priceaccess-engine/
├── config/
│   └── baskets.yaml          # basket composition per market
├── data/
│   └── syntarelx_baseline.csv
├── engine/
│   ├── uc1.py                # cascade entry point
│   ├── basket.py             # binding-ceiling calculation
│   ├── transmission.py       # marginal transmission formula
│   └── narrative.py          # optional Claude API call
├── tests/
│   └── test_uc1_golden.py
├── validation/
│   └── UC1_golden_model.xlsx
├── .env.example
└── requirements.txt
```

---

## Part of PriceAccess Navigator

PriceAccess Navigator is a portfolio project demonstrating analytical skills in pharmaceutical pricing strategy and market access. It is not a commercial product.
>>>>>>> 3c6cee7 (initial commit: engine, impact, narrative, UI scaffold, CLAUDE.md, prompts)
