from load_data import load_prices, load_assumptions
from engine import run_cascade, prices, baskets

def compute_impact(trigger_market, new_price, assumptions=None):
    if assumptions is None:
        assumptions = load_assumptions()
    cascade_result = run_cascade(trigger_market, new_price, prices, baskets)

    markets = list(assumptions.keys())
    rows = []

    for market in markets:
        a = assumptions[market]
        lag = a["transmission_lag_years"]
        list_asis = prices[market]
        list_after = cascade_result[market]
        growth = a["vol_growth_pct"]
        vol_y1 = a["vol_y1"]
        vol_y2 = vol_y1 * (1 + growth)
        vol_y3 = vol_y2 * (1 + growth)
        vols = [vol_y1, vol_y2, vol_y3]

        ns_asis = 0
        ns_after = 0
        gm_asis = 0
        gm_after = 0

        for i, vol in enumerate(vols):
            year = i + 1
            net_asis = list_asis * (1 - a["gtn_pct"])
            net_after = list_after * (1 - a["gtn_pct"]) if year > lag else list_asis * (1 - a["gtn_pct"])

            ns_asis += vol * net_asis
            ns_after += vol * net_after
            gm_asis += vol * net_asis * a["gm_pct"]
            gm_after += vol * net_after * a["gm_pct"]

        rows.append({
            "market": market,
            "list_asis": list_asis,
            "list_after": list_after,
            "ns_asis": round(ns_asis),
            "gm_asis": round(gm_asis),
            "ns_after": round(ns_after),
            "gm_after": round(gm_after),
            "delta_ns": round(ns_after - ns_asis),
            "delta_gm": round(gm_after - gm_asis),
            "delta_ns_pct": round((ns_after - ns_asis) / ns_asis * 100, 1),
            "delta_gm_pct": round((gm_after - gm_asis) / gm_asis * 100, 1),
        })

    return rows

if __name__ == "__main__":
    rows = compute_impact("ES", 400)
    print(f"{'Mkt':<5} {'NS AsIs':>12} {'GM AsIs':>12} {'NS After':>12} {'GM After':>12} {'ΔNS':>12} {'ΔNS%':>7} {'ΔGM':>12} {'ΔGM%':>7}")
    print("-" * 95)
    for r in rows:
        print(f"{r['market']:<5} {r['ns_asis']:>12,} {r['gm_asis']:>12,} {r['ns_after']:>12,} {r['gm_after']:>12,} {r['delta_ns']:>12,} {r['delta_ns_pct']:>6}% {r['delta_gm']:>12,} {r['delta_gm_pct']:>6}%")
    print("-" * 95)
    total_ns_asis = sum(r["ns_asis"] for r in rows)
    total_gm_asis = sum(r["gm_asis"] for r in rows)
    total_ns_after = sum(r["ns_after"] for r in rows)
    total_gm_after = sum(r["gm_after"] for r in rows)
    total_delta_ns = total_ns_after - total_ns_asis
    total_delta_gm = total_gm_after - total_gm_asis
    total_delta_ns_pct = round(total_delta_ns / total_ns_asis * 100, 1)
    total_delta_gm_pct = round(total_delta_gm / total_gm_asis * 100, 1)
    print(f"{'Total':<5} {total_ns_asis:>12,} {total_gm_asis:>12,} {total_ns_after:>12,} {total_gm_after:>12,} {total_delta_ns:>12,} {total_delta_ns_pct:>6}% {total_delta_gm:>12,} {total_delta_gm_pct:>6}%")