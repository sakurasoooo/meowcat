"""GUI smoke test for the new shop-progress / durability / warehouse-furniture features."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from MewgenicsCatEditor import MewgenicsApp
from mewgenics_core import storage_capacity

app = MewgenicsApp()
app.update()

# 1. shop progress card populated
app.on_nav_switch("🎒 仓库道具")
app.update()
txt = app.shop_info_lbl.cget('text')
assert 'Butch' in txt and 'Jack' in txt and 'Tracy' in txt, txt
print('shop card OK:')
print(txt)

# 2. durability shown in list rows
found_dur = None
for w in app.item_list.winfo_children():
    t = w.cget('text')
    if '耐久' in t:
        found_dur = t
        break
print('durability row sample:', found_dur)
assert found_dur, 'no durability text found in any row'

# 3. storage capacity enforcement: fill to cap and confirm block
lv = app.save_mgr.properties.get('house_storage_upgrades', 0)
cap = storage_capacity(lv)
cur = len(app.save_mgr.inventories['storage'].items)
print(f'storage: {cur}/{cap} (Lv.{lv})')
# add until cap without touching save (memory only), then next add must be blocked
while len(app.save_mgr.inventories['storage'].items) < cap:
    app.save_mgr.inventories['storage'].add_item('Stopwatch')
app.item_add_combo.set(app.item_labels_sorted[0])
import tkinter.messagebox as mb
orig = mb.showwarning
mb.showwarning = lambda *a, **k: None
app.on_item_add()  # should be blocked
mb.showwarning = orig
blocked = len(app.save_mgr.inventories['storage'].items) == max(cur, cap)  # 数量未增加
print('capacity block OK:', blocked)
assert blocked

# 4. furniture: warehouse editable, placed read-only
app.on_nav_switch("🪑 家具管理")
app.update()
wh = sorted(k for k, r in app.save_mgr.furniture.items() if app._is_warehouse_furniture(r))
placed = sorted(k for k, r in app.save_mgr.furniture.items() if not app._is_warehouse_furniture(r))
print(f'warehouse={len(wh)}, placed={len(placed)}')
app.on_select_furniture(wh[0])
app.update()
assert str(app.furn_apply_btn.cget('state')) == 'normal', 'warehouse should be editable'
print('warehouse editable OK:', app.furn_lock_note.cget('text'))
app.on_select_furniture(placed[0])
app.update()
assert str(app.furn_apply_btn.cget('state')) == 'disabled', 'placed should be read-only'
print('placed read-only OK:', app.furn_lock_note.cget('text'))
info = app.furn_info_lbl.cget('text')
print('placed info card:', info.replace(chr(10), ' | ')[:160])

# 5. mapped stats formatting
mapped = app._format_furniture_stats('{"comfort": 5, "stimulation": -2, "food_storage": 40}')
print('stats mapped:', mapped)
assert '舒适度 +5' in mapped and '刺激度 -2' in mapped and '食物储存 +40' in mapped

# 6. add furniture goes to warehouse
app.furn_add_combo.set(app.furn_labels_sorted[0])
app.on_furniture_add()
new_key = max(app.save_mgr.furniture.keys())
rec = app.save_mgr.furniture[new_key]
assert app._is_warehouse_furniture(rec), 'new furniture must land in warehouse'
print('add-to-warehouse OK:', rec.name, rec.room, rec.x, rec.y)

app.destroy()
print('\nGUI SMOKE: ALL OK')
