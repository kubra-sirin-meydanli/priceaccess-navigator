import os

from dotenv import load_dotenv
load_dotenv()

import anthropic
from load_data import load_prices, load_assumptions
from impact import compute_impact

def generate_narrative(trigger_market, new_price, rows):
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    total_ns_asis = sum(r["ns_asis"] for r in rows)
    total_ns_after = sum(r["ns_after"] for r in rows)
    total_delta_ns = sum(r["delta_ns"] for r in rows)
    total_delta_gm = sum(r["delta_gm"] for r in rows)
    total_delta_ns_pct = round(total_delta_ns / total_ns_asis * 100, 1)
    affected = [r["market"] for r in rows if r["delta_ns"] != 0]

    def _fmt_m(val):
        sign = "-" if val < 0 else "+"
        return f"{sign}€{abs(val) / 1_000_000:.1f}M"

    market_lines = "\n".join([
        f"- {r['market']}: ΔNS {_fmt_m(r['delta_ns'])} ({r['delta_ns_pct']}%), ΔGM {_fmt_m(r['delta_gm'])} ({r['delta_gm_pct']}%)"
        for r in rows if r["delta_ns"] != 0
    ])

    prompt = f"""You are a pharmaceutical pricing analyst writing a briefing memo for a Chief Commercial Officer.

A mandatory list price change has been triggered in {trigger_market} (new price: EUR {new_price}),
initiating an IRP cascade across reference pricing baskets.

Portfolio impact over 3 years:
- Markets affected: {', '.join(affected)}
- Total ΔNet Sales: {total_delta_ns:,} EUR ({total_delta_ns_pct}%)
- Total ΔGross Margin: {total_delta_gm:,} EUR

Market-by-market breakdown:
{market_lines}

Write a structured executive briefing following the Pyramid Principle.
Use EXACTLY this format and no other:

**[One sentence: total financial impact + number of markets affected — lead with the "so what"]**

- [Affected market 1]: [ΔNS in EUR M] ([ΔNS%]) — [IRP mechanism in plain English], [lag note if applicable]
- [Affected market 2]: [ΔNS in EUR M] ([ΔNS%]) — [IRP mechanism in plain English], [lag note if applicable]
- Recommended action: [one concrete commercial recommendation, max 15 words]

Rules:
- Only list markets where delta ≠ 0 in the bullets — do not mention unaffected markets
- The headline must use **bold markdown** (double asterisks)
- Each bullet must be concise — max 15 words
- Start each bullet line with a hyphen and a space - — do not use dots, dashes of other lengths, or any other character. The markdown must render as a proper bullet list.
- Format ΔNS as -€2.5M (-28.6%) — not as ΔNS -2.46M EUR (-28.6%)
- Use only the exact transmission lag values provided in the market breakdown data above — do not estimate, approximate, or invent lag timings
- Do not add any preamble, sign-off, label, or explanation outside this exact structure
- Do not number the bullets
- Output only the headline and bullets — nothing else"""

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text

if __name__ == "__main__":
    rows = compute_impact("ES", 400)
    narrative = generate_narrative("ES", 400, rows)
    print("\n--- AI NARRATIVE ---\n")
    print(narrative)