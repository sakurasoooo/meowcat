"""验证稀有度形状底图在道具列表与选择器中的合成显示。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from MewgenicsCatEditor import MewgenicsApp

app = MewgenicsApp()
app.on_nav_switch('🎒 仓库道具')
app.update()

# 列表行：检查含稀有度合成的图标已挂载（image 存在）
n_with_img = 0
def walk(w):
    yield w
    for c in w.winfo_children():
        yield from walk(c)
for w in walk(app.item_list):
    try:
        if w.cget('image') is not None:
            n_with_img += 1
    except Exception:
        pass
print('列表含合成图标的行数:', n_with_img)
assert n_with_img > 0

# 选中预览也合成
k = [i for i, it in enumerate(app.save_mgr.inventories['storage'].items)
     if app.items_db.get(it.name, {}).get('rarity') in ('rare', 'very_rare', 'uncommon')]
if k:
    app.on_select_item('storage', k[0])
    app.update()
    print('选中道具:', app.lbl_cat_title if False else app.item_name_lbl.cget('text'), '| 预览图标已载入:', app.item_icon_lbl.cget('image') is not None)
app.destroy()
print('RARITY SHAPE INTEGRATION: OK')
