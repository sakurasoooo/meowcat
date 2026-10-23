"""验证道具选择器与列表的稀有度背景着色（单 Tk 实例）。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from MewgenicsCatEditor import MewgenicsApp
from picker_dialog import UniversalGridPickerDialog, RARITY_BG

app = MewgenicsApp()
app.on_nav_switch('🎒 仓库道具')
app.update()

# 1. 列表行稀有度着色（递归遍历分组容器）
def walk(w):
    yield w
    for c in w.winfo_children():
        yield from walk(c)
n_tinted = 0
tint_values = set(v for k, v in RARITY_BG.items()) | {'#334155'}
for w in walk(app.item_list):
    try:
        fg = w.cget('fg_color')
        if fg in tint_values and fg != '#1e293b':
            n_tinted += 1
    except Exception:
        pass
print('列表稀有度着色行数:', n_tinted)
assert n_tinted > 0, 'no tinted rows'

# 2. 选择器稀有度背景（挂在 app 下，单一 Tk 实例）
dlg = UniversalGridPickerDialog(app, catalog_type='item')
dlg.update()
seen = {}
for s in dlg.card_slots:
    if s['item']:
        r = s['item'].get('rarity', '')
        seen.setdefault(r, s['card'].cget('fg_color'))
ok = True
for r, bg in seen.items():
    expect = RARITY_BG.get(r, '#131d2e')
    status = 'OK' if bg == expect else 'MISMATCH'
    if bg != expect:
        ok = False
    name = r if r else '(none)'
    print(f'{name:10s} bg={bg} {status}')
dlg.destroy()
assert ok

app.destroy()
print('\nRARITY BG: ALL OK')
