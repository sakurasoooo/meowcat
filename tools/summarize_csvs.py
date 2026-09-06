import csv
import os
import json

csv_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\_archived_csv"

summary = {}
for fname in os.listdir(csv_dir):
    if fname.endswith('.csv'):
        fpath = os.path.join(csv_dir, fname)
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            rows = list(reader)
            headers = rows[0] if rows else []
            keys = [r[0] for r in rows[1:] if r and not r[0].startswith('//')]
            summary[fname] = {
                'total_rows': len(rows),
                'keys_count': len(keys),
                'sample_keys': keys[:15]
            }

print(json.dumps(summary, indent=2, ensure_ascii=False))
