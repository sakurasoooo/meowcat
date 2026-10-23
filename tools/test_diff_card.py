"""GUI smoke: completion view difficulty progress card."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
import MewgenicsCatEditor as E

app = E.MewgenicsApp()
app.update()
app.on_nav_switch("🏅 职业通关")
app.update()
print('difficulty_progress:', app.save_mgr.difficulty_progress)
hbp = app.save_mgr.house_boss_progress
print('house_boss_progress beaten:', hbp.get('beaten_count'), '/', hbp.get('total'))
print('house bosses:', [(b['key'], b['beaten'], b.get('unlocked'), b['introduced']) for b in hbp.get('bosses', [])])
assert hbp.get('beaten_count') == sum(1 for b in hbp.get('bosses', []) if b['beaten'])
# 统计滚动区里关卡上方的难度卡 / 家园 Boss 卡是否生成
found = False
found_hb = False
found_mb = False
for w in app.completion_grid.winfo_children():
    def walk(wi):
        global found, found_hb, found_mb
        for c in wi.winfo_children():
            if isinstance(c, E.ctk.CTkLabel):
                t = c.cget('text') or ''
                if '难度推进' in t:
                    found = True
                if '家园 Boss' in t:
                    found_hb = True
                if '章节地图 Boss' in t:
                    found_mb = True
            walk(c)
    walk(w)
print('难度推进卡渲染:', found)
print('家园Boss卡渲染:', found_hb)
print('地图Boss卡渲染:', found_mb)
assert found_hb, 'missing house boss card'
assert found_mb, 'missing chapter map boss card'
assert hbp.get('total') == 9, 'expected 9 house bosses'
app.after(200, app.destroy)
app.mainloop()
print('ALL OK')
