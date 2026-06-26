import csv
import yaml

# 1. Load prices into a dictionary: {country: price}
prices = {}
with open("data/baseline_prices.csv") as f:
    for row in csv.DictReader(f):
        prices[row["country"]] = float(row["list_efp"])

# 2. Load baskets
with open("config/baskets.yaml") as f:
    baskets = yaml.safe_load(f)

# 3. Compute one market's binding ceiling
def compute_binding_ceiling(market, prices, baskets):
    rule = baskets[market]["rule"]
    basket = baskets[market]["basket"]

    if rule == "free":
        return None

    member_prices = []
    for country in basket:
        member_prices.append(prices[country])

    if rule == "min":
        return min(member_prices)
    if rule == "average":
        return sum(member_prices) / len(member_prices)

# 4. Turn a ceiling change into a new price
def marginal_transmission(current_price, old_ceiling, new_ceiling):
    drop = max(0, old_ceiling - new_ceiling)   # how far the ceiling fell (never negative)
    new_price = current_price - drop
    return max(0, new_price)                    # never below zero

# 5. Run the full cascade from one shock
def run_cascade(trigger, new_price, prices, baskets):
    current = dict(prices)                         # work on a copy, leave originals alone

    # each market's ceiling BEFORE the shock (our reference point)
    pre_ceilings = {}
    for market in baskets:
        pre_ceilings[market] = compute_binding_ceiling(market, prices, baskets)

    current[trigger] = new_price                   # apply the mandated cut

    changed = True
    while changed:                                 # keep looping until nothing moves
        changed = False
        for market in baskets:
            if market == trigger:
                continue                           # the cut market is fixed
            if baskets[market]["rule"] == "free":
                continue                           # free markets never move
            new_ceiling = compute_binding_ceiling(market, current, baskets)
            updated = marginal_transmission(prices[market], pre_ceilings[market], new_ceiling)
            if updated != current[market]:
                current[market] = updated
                changed = True                     # something moved, so loop again

    return current


if __name__ == "__main__":
    result = run_cascade("ES", 400, prices, baskets)
    print("Spain cut to 400:")
    for market in baskets:
        delta = result[market] - prices[market]
        print(" ", market, ":", prices[market], "->", result[market], " delta:", delta)