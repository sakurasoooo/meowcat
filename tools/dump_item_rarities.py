"""Dump all storage items with wiki rarity to find the misclassified quest item."""
import io, sys, os, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from mewgenics_core import MewgenicsSaveManager

mgr = MewgenicsSaveManager(); mgr.load()
db = {}
with open('wiki_data/csv/items.csv', encoding='utf-8-sig') as f:
    db = {r['item_code']: r for r in csv.DictReader(f)}
items = mgr.inventories['storage'].items
print(f'{len(items)} items:')
for it in items:
    r = db.get(it.name, {})
    print(f'  {it.name:26s} rarity={r.get("rarity", "?"):12s} extra={it.extra!r}')
