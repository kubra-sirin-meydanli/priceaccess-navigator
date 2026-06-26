import yaml

with open("config/baskets.yaml") as f:
    baskets = yaml.safe_load(f)

for market, info in baskets.items():
    print(market, "-", info["rule"], "- basket:", info["basket"])