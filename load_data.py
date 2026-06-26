import csv

def load_prices(path="data/baseline_prices.csv"):
    prices = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["role"] == "modelled":
                prices[row["country"]] = float(row["list_efp"])
    return prices

def load_assumptions(path="data/volume_assumptions.csv"):
    assumptions = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            assumptions[row["market"]] = {
                "vol_y1": int(row["vol_y1"]),
                "gtn_pct": float(row["gtn_pct"]),
                "gm_pct": float(row["gm_pct"]),
                "vol_growth_pct": float(row["vol_growth_pct"]),
                "transmission_lag_years": int(row["transmission_lag_years"]),
            }
    return assumptions

if __name__ == "__main__":
    prices = load_prices()
    assumptions = load_assumptions()
    for market in prices:
        p = prices[market]
        a = assumptions[market]
        print(market, "| list:", p, "| vol_y1:", a["vol_y1"], "| gtn:", a["gtn_pct"], "| gm:", a["gm_pct"], "| growth:", a["vol_growth_pct"], "| lag:", a["transmission_lag_years"])
        