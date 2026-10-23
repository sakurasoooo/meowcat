"""Screenshot the completion view (grid aligned)."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
import MewgenicsCatEditor as E

app = E.MewgenicsApp()
app.geometry("1200x760")
app.update()
app.on_nav_switch("🏅 职业通关")
app.update()
try:
    from PIL import ImageGrab
    app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    ImageGrab.grab((x, y, x + w, y + h)).save('tools/_completion_shot.png')
    print('screenshot saved', w, h)
except Exception as ex:
    print('shot failed:', ex)
app.after(300, app.destroy)
app.mainloop()
print('OK')
