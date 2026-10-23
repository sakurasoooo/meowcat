"""GUI smoke: build app, switch to shop route, screenshot, close."""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
import customtkinter as ctk
import MewgenicsCatEditor as E

app = E.MewgenicsApp()
app.update()
app.on_nav_switch("🏪 商店与家园")
app.update()
# 截图
try:
    from PIL import ImageGrab
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    ImageGrab.grab((x, y, x + w, y + h)).save('tools/_shop_shot.png')
    print('screenshot saved', w, h)
except Exception as ex:
    print('screenshot failed:', ex)
app.after(300, app.destroy)
app.mainloop()
print('GUI smoke OK')
