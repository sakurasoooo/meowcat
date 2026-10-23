"""GUI smoke: button visibility (pack vs pack_forget) for items & furniture."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
import MewgenicsCatEditor as E

app = E.MewgenicsApp()
app.update()
app.on_nav_switch("🎒 仓库道具")
app.update()

def shown(w):
    return w.winfo_manager() != ''

blob = app.save_mgr.inventories['storage']
# 普通可编辑道具
nidx = next((i for i, it in enumerate(blob.items) if not app._item_is_quest(it) and it.flag2 != 3), None)
app.on_select_item('storage', nidx)
app.update()
print(f'普通道具 [{blob.items[nidx].name}]: change={shown(app.btn_item_change)} delete={shown(app.btn_item_delete)} repair={shown(app.btn_item_repair)}')
assert shown(app.btn_item_change) and shown(app.btn_item_delete) and not shown(app.btn_item_repair)

# 磨损道具 -> 修理按钮显示
widx = next((i for i, it in enumerate(blob.items) if it.flag2 == 3), None)
app.on_select_item('storage', widx)
app.update()
print(f'磨损道具 [{blob.items[widx].name}]: repair={shown(app.btn_item_repair)}')
assert shown(app.btn_item_repair)

# 任务道具 -> 三按钮全隐藏
qidx = next((i for i, it in enumerate(blob.items) if app._item_is_quest(it)), None)
app.on_select_item('storage', qidx)
app.update()
print(f'任务道具 [{blob.items[qidx].name}]: change={shown(app.btn_item_change)} delete={shown(app.btn_item_delete)} repair={shown(app.btn_item_repair)}')
assert not shown(app.btn_item_change) and not shown(app.btn_item_delete) and not shown(app.btn_item_repair)

# 背包 -> 编辑按钮隐藏、添加 frame 隐藏
app.item_box_seg.set(app.ITEM_BOXES[1][0])
app.refresh_item_list()
app.update()
print(f'背包: add_frame={shown(app.f_item_add)} change={shown(app.btn_item_change)}')
assert not shown(app.f_item_add) and not shown(app.btn_item_change)

# 回到仓库 -> 添加 frame 显示
app.item_box_seg.set(app.ITEM_BOXES[0][0])
app.refresh_item_list()
app.update()
print(f'仓库: add_frame={shown(app.f_item_add)}')
assert shown(app.f_item_add)

# 家具：仓库空间显示添加+选中显示更换/删除
app.on_nav_switch("🪑 家具管理")
app.update()
furn = app.save_mgr.furniture
wh = next((k for k, r in furn.items() if app._is_warehouse_furniture(r)), None)
print(f'家具仓库空间: add_frame={shown(app.furn_add_frame)}')
assert shown(app.furn_add_frame)
if wh:
    app.on_select_furniture(wh)
    app.update()
    print(f'选仓库家具: change={shown(app.furn_change_btn)} del={shown(app.furn_del_btn)}')
    assert shown(app.furn_change_btn) and shown(app.furn_del_btn)
app.furn_space_seg.set("🛋️ 一层大厅")
app.on_furn_space_changed("🛋️ 一层大厅")
app.update()
print(f'一层大厅空间: add_frame={shown(app.furn_add_frame)} change={shown(app.furn_change_btn)} del={shown(app.furn_del_btn)}')
assert not shown(app.furn_add_frame) and not shown(app.furn_change_btn) and not shown(app.furn_del_btn)

app.after(200, app.destroy)
app.mainloop()
print('ALL OK')
