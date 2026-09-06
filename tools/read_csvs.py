import csv
import os

csv_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\_archived_csv"
for fname in ['mutations.csv', 'abilities.csv', 'passives.csv', 'items.csv', 'units.csv']:
    fpath = os.path.join(csv_dir, fname)
    if os.path.exists(fpath):
        print(f"\n=================== {fname} ===================")
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i < 6:
                    print(f"Row {i}:", row[:8])
                else:
                    break
