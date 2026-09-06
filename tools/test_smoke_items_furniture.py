"""Smoke test: item/furniture add-remove-edit round-trip on a COPY of the live save.
Never touches the real save.
"""
import os, sys, io, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mewgenics_core import MewgenicsSaveManager

src = MewgenicsSaveManager.find_default_save()
tmp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'verify_temp_save.sav')
shutil.copy2(src, tmp)
print(f'testing on copy: {tmp}')

mgr = MewgenicsSaveManager(tmp)
n_items = len(mgr.inventories['storage'].items)
n_furn = len(mgr.furniture)
print(f'before: storage={n_items} items, furniture={n_furn}')

# add item + furniture, edit, delete
it = mgr.inventories['storage'].add_item('Stopwatch')
mgr.inventories['storage'].items[0].name = 'Ankh'  # 改类型
rec = mgr.add_furniture('object_cattree1', 'Attic')
rec.x, rec.y = 3, -4
mgr.save()

# reload and verify
mgr2 = MewgenicsSaveManager(tmp)
items2 = mgr2.inventories['storage'].items
furn2 = mgr2.furniture
checks = [
    ('item added', len(items2) == n_items + 1),
    ('added item is Stopwatch', items2[-1].name == 'Stopwatch'),
    ('added item serial is max+1', items2[-1].serial == max(x.serial for x in items2)),
    ('item type changed', items2[0].name == 'Ankh'),
    ('furniture added', len(furn2) == n_furn + 1),
    ('added furniture fields', rec.key in furn2 and furn2[rec.key].name == 'object_cattree1'
     and furn2[rec.key].room == 'Attic' and furn2[rec.key].x == 3 and furn2[rec.key].y == -4),
    ('cats intact', len(mgr2.cats) == len(mgr.cats)),
]
ok = True
for name, passed in checks:
    print(f'  {"PASS" if passed else "FAIL"}: {name}')
    ok &= passed

# delete test
mgr2.inventories['storage'].remove_item(len(items2) - 1)
mgr2.remove_furniture(rec.key)
mgr2.save()
mgr3 = MewgenicsSaveManager(tmp)
d1 = len(mgr3.inventories['storage'].items) == n_items
d2 = rec.key not in mgr3.furniture
print(f'  {"PASS" if d1 else "FAIL"}: item deleted')
print(f'  {"PASS" if d2 else "FAIL"}: furniture deleted')
ok &= d1 and d2

os.remove(tmp)
print('\nRESULT:', 'ALL OK' if ok else 'FAILURES')
sys.exit(0 if ok else 1)
