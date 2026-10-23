"""GUI smoke test for the class completion badges page."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from MewgenicsCatEditor import MewgenicsApp
from mewgenics_core import MAJOR_CHECKMARK_ZONES

app = MewgenicsApp()
app.on_nav_switch("🏅 职业通关")
app.update()

# matrix sanity: count cleared cells vs core records
recs = app.save_mgr.class_zone_records
print(f'class_zone_records: {len(recs)}')
expect = {}
for (cls, zone), (a, b, v) in recs.items():
    if zone in MAJOR_CHECKMARK_ZONES and a == -1 and cls != 'any':  # 'any' 为聚合行，不显示
        expect[cls] = expect.get(cls, 0) + 1
print('expected per class:', expect)

pct = []
for row in app.completion_grid.winfo_children():
    for w in getattr(row, 'winfo_children', lambda: [])():
        try:
            t = w.cget('text')
        except ValueError:
            continue
        if isinstance(t, str) and t.endswith('/9'):
            pct.append(t)
print('per-class progress:', pct)
total = sum(int(p.split('/')[0]) for p in pct)
print(f'total badges lit: {total}')
assert total == sum(expect.values()), 'matrix mismatch between UI and core data'

# Druid should have 4 (caves, moon, core, meatworld) per earlier RE
dru = next(p for p in pct if p == '4/9')
print('Druid 4/9 present:', dru)

# route switching still fine
for r in ["🐱 猫咪编辑", "🎒 仓库道具", "🪑 家具管理", "🏅 职业通关"]:
    app.on_nav_switch(r)
    app.update()
app.destroy()
print('\nCOMPLETION PAGE: ALL OK')
