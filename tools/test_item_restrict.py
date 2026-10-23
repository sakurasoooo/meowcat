"""GUI smoke: repair flow + backpack read-only gating."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
import MewgenicsCatEditor as E

app = E.MewgenicsApp()
app.update()
app.on_nav_switch("🎒 仓库道具")
app.update()

blob = app.save_mgr.inventories['storage']
worn_idx = next((i for i, it in enumerate(blob.items) if it.flag2 == 3), None)
print('worn item idx:', worn_idx, blob.items[worn_idx].name if worn_idx is not None else None)

if worn_idx is not None:
    it = blob.items[worn_idx]
    before = it.flag2
    app.on_select_item('storage', worn_idx)
    app.update()
    st = app.btn_item_repair.cget('state')
    print(f'repair btn state (worn): {st}')
    assert st == 'normal', 'repair should be enabled for worn item'
    app.on_item_repair()
    app.update()
    print(f'flag2 {before} -> {it.flag2}')
    assert it.flag2 == 1, 'repair should set flag2=1'
    # 还原（避免污染内存态）
    it.flag2 = 3
    app.on_select_item('storage', worn_idx)

# 任务道具：禁改禁删
quest_idx = next((i for i, it2 in enumerate(blob.items) if app._item_is_quest(it2)), None)
print('quest item idx:', quest_idx, blob.items[quest_idx].name if quest_idx is not None else None)
if quest_idx is not None:
    app.on_select_item('storage', quest_idx)
    app.update()
    print('  change btn:', app.btn_item_change.cget('state'), ' delete btn:', app.btn_item_delete.cget('state'))
    assert app.btn_item_change.cget('state') == 'disabled'
    assert app.btn_item_delete.cget('state') == 'disabled'

# 背包：只读
app.item_box_seg.set(app.ITEM_BOXES[1][0])
app.refresh_item_list()
app.update()
print('backpack add btn:', app.btn_item_add.cget('state'))
assert app.btn_item_add.cget('state') == 'disabled'
print('  change/delete/repair disabled:', app.btn_item_change.cget('state'), app.btn_item_delete.cget('state'), app.btn_item_repair.cget('state'))

app.after(200, app.destroy)
app.mainloop()
print('ALL OK')
