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

    market_lines = "\n".join([
        f"- {r['market']}: ΔNS {r['delta_ns']:,} EUR ({r['delta_ns_pct']}%), ΔGM {r['delta_gm']:,} EUR ({r['delta_gm_pct']}%)"
        for r in rows
    ])

    prompt = f"""You are a pharmaceutical pricing analyst writing a briefing memo for a Chief Commercial Officer.

A mandatory list price change has been triggered in {trigger_market} (new price: {new_price} EUR), initiating an IRP cascade across reference pricing baskets.

Portfolio impact over 3 years:
- Markets affected: {', '.join(affected)}
- Total ΔNet Sales: {total_delta_ns:,} EUR ({total_delta_ns_pct}%)
- Total ΔGross Margin: {total_delta_gm:,} EUR

Market-by-market breakdown:
{market_lines}

Write an executive briefing following the Pyramid Principle in this exact format:

HEADLINE
One sentence only. Lead with total revenue at risk, number of markets affected, and the trigger market. No hedging.

WHAT HAPPENED
· One bullet. State the regulatory trigger, the mechanism (IRP cascade), and the new price. Be specific.

MARKET IMPACT
· One bullet per market that is affected — state the market, ΔNS in EUR, ΔNS%, and if there is a transmission lag, note it in plain English (e.g. "effective from Year 2")
· One bullet for unaffected markets grouped together — state why they are insulated

GROSS MARGIN
· One bullet. Total ΔGM in EUR. State which markets account for the majority of the margin impact as a %.

COMMERCIAL IMPLICATION
· One bullet. Forward-looking. What does this mean for the portfolio and what should leadership be aware of next. No jargon.

Rules:
- Use exact numbers from the data — do not invent relative rankings or qualitative claims not supported by the numbers
- No prose paragraphs — bullets only except the headline
- No hedging language
- Write for a CCO who has 30 seconds to read this"""

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