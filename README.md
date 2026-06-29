# PriceAccess Navigator

AI-augmented decision support for pharmaceutical pricing & market access — IRP cascade simulation across 6 markets.

[Live one-pager](https://kubra-sirin-meydanli.github.io/priceaccess-navigator/) · Built by Kubra Meydanli

---

## What this project is

A personal portfolio project demonstrating IRP (International Reference Pricing) cascade management logic across six European markets using a synthetic IL-17A biologic called SyntaRelX (modelled on secukinumab/Cosentyx), dispensed via hospital outpatient pharmacy channel. Not a commercial product.

---

## Use cases

| | Use case | Scope |
|---|---|---|
| UC1 | Mandatory list price cascade | Post-launch, full basket, regulatory trigger only |
| UC2 | Launch sequence optimisation | Pre-launch, progressive basket fill |
| UC3 | HTA outcome stress test | Post-launch, price erosion + volume restriction |

---

## Markets covered

| Market | Regulatory anchor | IRP role |
|---|---|---|
| DE | AMNOG / Erstattungsbetrag | Free pricing — trigger only |
| FR | HAS / CEPS | Inbound IRP, lag 1 year |
| NL | WGP / ZIN | Inbound IRP, lag 2 years |
| UK | NICE / VPAS | Free pricing — trigger only |
| ES | CIPM | Inbound IRP, lag 0 |
| TR | TİTCK / SGK | Inbound IRP |

---

## Synthetic asset

**SyntaRelX** is a fictitious IL-17A inhibitor modelled on secukinumab (Cosentyx), used as the demonstration asset throughout this project. It is launched sequentially across the six markets with synthetic list EFPs, net discount assumptions, and IRP trigger dates. All figures are illustrative and designed to produce non-trivial cascade behaviour for demonstration purposes. No real product prices are represented.

---

## Validation

The cascade engine is validated against four pytest golden tests covering key scenarios: Spain CIPM trigger, German free-pricing (no cascade), no market rising, and pre-shock ceiling checks.

```bash
pytest test_engine.py -v
```

A mismatch between engine output and the expected golden values causes the test to fail with a per-market diff.

---

## Stack

- Python — cascade engine, impact model, narrative layer
- Streamlit — interactive UI (in progress)
- Claude API (Haiku) — C-suite narrative generation
- pytest — golden test validation
- Synthetic data only — no real pricing conclusions can be drawn

---

## Key domain notes

- IRP operates on list (ex-factory) prices only — net/tender prices are tracked separately and never propagated
- DE and UK are free-pricing markets — they trigger cascades but are never affected by inbound IRP
- Cascade logic uses marginal transmission — a market's price falls only by the extent its binding IRP ceiling is lowered

---

## Repository layout

```
priceaccess-engine/
├── CLAUDE.md               ← project briefing for Claude Code
├── app.py                  ← Streamlit UI (in progress)
├── engine.py               ← IRP cascade engine
├── impact.py               ← 3-year NS/GM impact calculation
├── load_data.py            ← unifies baseline prices + volume assumptions
├── narrative.py            ← Claude API narrative generation
├── test_engine.py          ← pytest golden tests
├── data/
│   ├── baseline_prices.csv
│   └── volume_assumptions.csv
├── config/
│   └── baskets.yaml
└── prompts/
    └── narrative_uc1.txt
```

---

> All data is synthetic. SyntaRelX is a fictitious IL-17A inhibitor. No real product prices are represented.
