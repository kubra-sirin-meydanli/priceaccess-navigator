import csv

with open("data/volume_assumptions.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row["market"], row["vol_y1"], row["gtn_pct"], row["gm_pct"], row["vol_growth_pct"])