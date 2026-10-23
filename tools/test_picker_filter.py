"""GUI smoke: move picker filter count + completion grid icon load, then close."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
import customtkinter as ctk
from picker_dialog import UniversalGridPickerDialog
from mewgenics_core import BASIC_MOVE_ABILITIES, BASIC_ATTACK_ABILITIES

root = ctk.CTk()
root.withdraw()

picked = []
for label, keys in [('MOVE', BASIC_MOVE_ABILITIES), ('ATTACK', BASIC_ATTACK_ABILITIES)]:
    dlg = UniversalGridPickerDialog(root, title=f'{label} picker', catalog_type='ability',
                                    current_value='DefaultMove', allowed_keys=keys,
                                    on_select_callback=lambda v: picked.append(v))
    dlg.update()
    n = len(dlg.full_catalog)
    print(f'{label}: filtered_catalog={n} (期望 {len(keys)})')
    print(f'  展示前5: {[it["key"] for it in dlg.full_catalog[:5]]}')
    dlg.destroy()

# 验证图标加载辅助（不依赖完整 app，直接测资源存在性）
import os
for rel in ['icons/classes/Fighter.png', 'icons/areas/moon.png', 'icons/abilities/DefaultMove.png']:
    print(f'  asset {rel} 存在: {os.path.exists(os.path.join("assets", rel))}')

root.after(200, root.destroy)
root.mainloop()
print('GUI smoke OK')
