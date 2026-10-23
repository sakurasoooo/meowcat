"""GUI smoke test: open MutationPicker for legs, screenshot it, then auto-close."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
import customtkinter as ctk
from mutation_picker import MutationPicker
from mewgenics_core import CatRecord, get_game_data_cache

root = ctk.CTk()
root.withdraw()

gd = get_game_data_cache()
entries = gd['mutations_detailed']['legs']
picked = []

dlg = MutationPicker(root, '选择突变 - 腿部突变 (右侧)', entries,
                     CatRecord.get_birth_defect_ids(), 418, 100, lambda mid: picked.append(mid))
dlg.update()

# 截图留证
try:
    from PIL import ImageGrab
    dlg.update()
    x, y = dlg.winfo_rootx(), dlg.winfo_rooty()
    w, h = dlg.winfo_width(), dlg.winfo_height()
    ImageGrab.grab((x, y, x + w, y + h)).save('tools/_picker_shot.png')
    print('screenshot saved', w, h)
except Exception as e:
    print('screenshot failed:', e)

# 模拟：切到"负面"分类 + 搜索
dlg._on_category('✖ 负面')
dlg.update()
dlg.search_var.set('bone')
dlg._on_filter()
dlg.update()
print('filtered items (负面+bone):', len(dlg._filtered()))
print('total legs entries:', len(entries), '| first page items:', len(dlg._filtered()))

root.after(300, root.destroy)
root.mainloop()
print('GUI smoke OK')
