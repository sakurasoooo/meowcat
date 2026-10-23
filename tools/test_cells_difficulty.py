"""Check class grid cells now show difficulty."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
import MewgenicsCatEditor as E

app = E.MewgenicsApp()
app.update()
app.on_nav_switch("🏅 职业通关")
app.update()
# 收集所有格子文本
txts = {}
def walk(w):
    for c in w.winfo_children():
        if isinstance(c, E.ctk.CTkLabel):
            t = c.cget('text') or ''
            if t.startswith('普') or t.startswith('✔') or t.startswith('🚶'):
                txts.setdefault(t, 0)
                txts[t] += 1
        walk(c)
walk(app.completion_grid)
print('格子文本统计:', txts)
app.after(200, app.destroy)
app.mainloop()
print('OK')
