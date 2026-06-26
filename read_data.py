import csv

with open("data/baseline_prices.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row["country"], row["role"], row["list_efp"])