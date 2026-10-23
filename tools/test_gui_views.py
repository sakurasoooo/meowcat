"""GUI instantiation smoke test: build app, switch all three routes, simulate item/furniture ops."""
import os, sys, io, faulthandler
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
faulthandler.dump_traceback_later(25, exit=True)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import customtkinter as ctk
from MewgenicsCatEditor import MewgenicsApp

app = MewgenicsApp()
app.update()  # process pending geometry/pack

# switch routes
for route in ["🎒 仓库道具", "🪑 家具管理", "🐱 猫咪编辑"]:
    app.on_nav_switch(route)
    app.update()
    print(f'route OK: {route}')

# items: select first item, change type, add, delete
app.on_nav_switch("🎒 仓库道具")
app.on_select_item('storage', 0)
app.update()
print('select item OK:', app.save_mgr.inventories['storage'].items[0].name)
app.item_add_combo.set(app.item_labels_sorted[0])
import tkinter.messagebox as mb
_orig_warn = mb.showwarning
mb.showwarning = lambda *a, **k: None  # 屏蔽"仓库已满"等模态弹窗
app.on_item_add()
mb.showwarning = _orig_warn
app.update()
n = len(app.save_mgr.inventories['storage'].items)
print(f'add item OK: storage now {n} items')
app.on_select_item('storage', n - 1)
app.on_item_delete()
print('delete item OK')

# furniture: select first, apply, add, delete
app.on_nav_switch("🪑 家具管理")
first_key = sorted(app.save_mgr.furniture.keys())[0]
app.on_select_furniture(first_key)
app.update()
app.furn_x_entry.delete(0, 'end'); app.furn_x_entry.insert(0, '2')
app.on_furniture_apply()
print('furniture apply OK:', app.save_mgr.furniture[first_key].x == 2)
app.furn_add_combo.set(app.furn_labels_sorted[0])
app.on_furniture_add()
new_key = max(app.save_mgr.furniture.keys())
app.on_furniture_delete()
print('furniture add/delete OK:', new_key not in app.save_mgr.furniture)

app.on_nav_switch("🐱 猫咪编辑")
app.update()
app.destroy()
print('\nGUI SMOKE: ALL OK')
