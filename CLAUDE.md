# CLAUDE.md — PriceAccess Navigator

This file is the project briefing for Claude Code. Read it before doing anything.
Do not modify it unless instructed by the user.

---

## What this project is

A personal portfolio project (not a commercial product) demonstrating AI-augmented
decision support for pharmaceutical International Reference Pricing (IRP) cascade
management. Built by Kubra Meydanli (pharmacist, commercial operations background).

Synthetic product: SyntaRelX — an IL-17A biologic inspired by secukinumab/Cosentyx.
Dispensed via hospital outpatient pharmacy channel.
Six modelled markets: DE, FR, NL, UK, ES, TR.

---

## File map

    priceaccess-navigator/
    ├── CLAUDE.md                  ← this file
    ├── app.py                     ← Streamlit UI (Step 6, in progress)
    ├── engine.py                  ← IRP cascade engine (complete, validated)
    ├── impact.py                  ← 3-year NS/GM impact calculation (complete)
    ├── load_data.py               ← merges baseline_prices + volume_assumptions
    ├── narrative.py               ← Claude API narrative generation (complete)
    ├── test_engine.py             ← pytest golden tests (4 passing)
    ├── .env                       ← API key (never commit this)
    ├── data/
    │   ├── baseline_prices.csv    ← list_efp per market + basket roles
    │   └── volume_assumptions.csv ← vol_y1, gtn_pct, gm_pct, vol_growth_pct, transmission_lag_years
    ├── config/
    │   └── baskets.yaml           ← IRP basket definitions per market
    └── prompts/
        └── narrative_uc1.txt      ← Pyramid Principle C-suite memo prompt

---

## Domain rules — never violate these

- DE and UK are FREE-PRICING markets. They have NO inbound IRP. They can trigger
  cascades but are never affected by them.
- Prices only move DOWN in a cascade. No market ever rises as a result of IRP.
- IRP operates on LIST (ex-factory) prices only, not net/tender prices.
- Transmission lags: ES=0 years, FR=1 year, NL=2 years.
  (NL references FR which references ES — sequential dependency.)
- Mandatory triggers only for UC1: AMNOG (DE), CEPS (FR), CIPM (ES).
  Voluntary price reductions are out of scope for UC1.

---

## Use cases

- UC1 (demo lead): Mandatory list price change cascade — post-launch.
  Risk prevention / compliance value bucket.
- UC2: Launch sequence optimisation — pre-launch, progressive basket fill.
  Revenue uplift / decision optimisation value bucket.
- UC3: HTA outcome stress test — post-launch, combined price erosion + volume restriction.
  Risk prevention / HTA negotiation readiness value bucket.

---

## Key data (current baseline prices, SyntaRelX)

| Market | List EFP (€) | Vol Y1 | GTN% | GM%  | Lag (yrs) |
|--------|-------------|--------|------|------|-----------|
| DE     | 1164        | 12000  | 15%  | 72%  | —         |
| FR     | 620         | 9000   | 22%  | 70%  | 1         |
| NL     | 582         | 4000   | 18%  | 71%  | 2         |
| UK     | 700         | 8000   | 12%  | 73%  | —         |
| ES     | 560         | 6000   | 18%  | 70%  | 0         |
| TR     | 195         | 3000   | 30%  | 68%  | —         |

---

## Validated output (golden test — do not break)

Spain CIPM cut to €400 → total ΔNS −€3.7M / −4.5%, ΔGM −€2.6M / −4.4%

---

## Streamlit UI architecture (app.py — in progress)

Three layers navigated via pill-style st.radio:

- Layer 1: Current prices strip (always visible) + collapsible commercial assumptions table
- Layer 2: Mode toggle (Demo / Edit manually / Upload Excel) → cascade inputs → Run Cascade
- Layer 3: 4 metric cards + unified As Is/After/Delta table + NS/GM bar chart (plotly) + AI narrative strip

Style: clean monochrome, one red accent (#C0392B) for affected markets, reMarkable-inspired.

---

## What Claude Code must NOT do

- Do not invent IRP rules not described in this file or baskets.yaml
- Do not add markets beyond the six listed
- Do not modify test_engine.py golden tests without explicit instruction
- Do not commit or touch .env
- Do not write a generic README — the domain-accurate version already exists
- Always write a simple print script first before refactoring into importable functions
- Always confirm with the user before making changes to existing validated files
