"""GUI smoke: item category tab filters normal vs quest."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
import MewgenicsCatEditor as E

app = E.MewgenicsApp()
app.update()
app.on_nav_switch("🎒 仓库道具")
app.update()

blob = app.save_mgr.inventories['storage']
total = len(blob.items)
nq = sum(1 for i, it in enumerate(blob.items) if app._item_is_quest(it))

# 默认普通
app.item_cat_seg.set("🎒 普通道具")
app.refresh_item_list()
app.update()
print(f'普通 tab: 期望 {total-nq} 普通')
# 统计列表中渲染的按钮行数（约）
import customtkinter as ctk
def count_buttons(frame):
    n = 0
    for w in frame.winfo_children():
        n += sum(1 for c in w.winfo_children() if isinstance(c, ctk.CTkButton))
    return n
print('  渲染按钮数:', count_buttons(app.item_list))

app.item_cat_seg.set("📜 主线/支线道具")
app.refresh_item_list()
app.update()
print(f'任务 tab: 期望 {nq} 任务')
print('  渲染按钮数:', count_buttons(app.item_list))

app.after(200, app.destroy)
app.mainloop()
print('ALL OK')
