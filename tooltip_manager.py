import tkinter as tk
import customtkinter as ctk
from PIL import Image

class GameTooltip:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GameTooltip()
        return cls._instance

    def __init__(self):
        self.tip_window = None
        self.after_id = None
        self.current_widget = None
        self.item_data = None
        self.get_icon_func = None

    def bind_widget(self, widget, item_data, get_icon_func=None):
        widget.bind("<Enter>", lambda e: self.schedule_show(widget, item_data, e, get_icon_func))
        widget.bind("<Leave>", lambda e: self.hide())
        widget.bind("<Motion>", lambda e: self.on_motion(e))

    def schedule_show(self, widget, item_data, event, get_icon_func=None):
        self.cancel_schedule()
        self.current_widget = widget
        self.item_data = item_data
        self.get_icon_func = get_icon_func
        # 120ms debounce delay for smooth UX
        self.after_id = widget.after(120, lambda: self.show(event.x_root, event.y_root))

    def on_motion(self, event):
        if self.tip_window:
            self.position_window(event.x_root, event.y_root)

    def cancel_schedule(self):
        if self.after_id and self.current_widget:
            try:
                self.current_widget.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def hide(self):
        self.cancel_schedule()
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None

    def show(self, x, y):
        if not self.item_data or self.tip_window:
            return

        self.tip_window = tk.Toplevel()
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.attributes("-topmost", True)
        
        # Outer container frame (Gold/Cyberpunk border)
        border_color = "#38bdf8" if self.item_data.get('class') != 'None' else "#64748b"
        outer = ctk.CTkFrame(self.tip_window, fg_color="#0f172a", border_color=border_color, border_width=2, corner_radius=8)
        outer.pack(fill="both", expand=True, padx=1, pady=1)

        # 1. Header (Icon + Titles)
        f_header = ctk.CTkFrame(outer, fg_color="transparent")
        f_header.pack(fill="x", padx=12, pady=(10, 6))

        # Icon
        icon_img = None
        if self.get_icon_func:
            icon_img = self.get_icon_func(self.item_data.get('key'))
        
        if icon_img:
            lbl_icon = ctk.CTkLabel(f_header, text="", image=icon_img, width=48, height=48)
            lbl_icon.pack(side="left", padx=(0, 10))

        # Title block
        f_titles = ctk.CTkFrame(f_header, fg_color="transparent")
        f_titles.pack(side="left", fill="x", expand=True)

        cn_name = self.item_data.get('name') or self.item_data.get('key', '未知技能')
        en_name = self.item_data.get('key', '')
        
        ctk.CTkLabel(f_titles, text=cn_name, font=("Arial", 14, "bold"), text_color="#fbbf24", anchor="w").pack(anchor="w")
        if en_name and en_name != cn_name:
            ctk.CTkLabel(f_titles, text=en_name, font=("Arial", 10), text_color="#94a3b8", anchor="w").pack(anchor="w")

        # Class badge
        cls_name = self.item_data.get('class', '')
        if cls_name and cls_name != 'None':
            cls_colors = {
                'Fighter': '#ef4444',
                'Mage': '#a855f7',
                'Necromancer': '#7c3aed',
                'Hunter': '#10b981',
                'Medic': '#0ea5e9',
                'Tank': '#3b82f6',
                'Thief': '#eab308',
                'Butcher': '#dc2626',
                'Druid': '#14b8a6',
                'Monk': '#f97316',
                'Psychic': '#ec4899',
                'Tinkerer': '#f59e0b',
                'Jester': '#8b5cf6',
                'Colorless': '#64748b'
            }
            c_color = cls_colors.get(cls_name, '#64748b')
            badge = ctk.CTkLabel(f_titles, text=f"✦ {cls_name}", font=("Arial", 10, "bold"), text_color=c_color, anchor="w")
            badge.pack(anchor="w", pady=(2, 0))

        # 2. Stats strip (Mana, Damage, Range)
        mana = self.item_data.get('mana', 0)
        damage = self.item_data.get('damage', '')
        rng = self.item_data.get('range', 0)
        
        stats_present = (mana > 0 or damage or rng > 0)
        if stats_present:
            f_stats = ctk.CTkFrame(outer, fg_color="#1e293b", corner_radius=4)
            f_stats.pack(fill="x", padx=12, pady=4)
            
            if mana > 0:
                ctk.CTkLabel(f_stats, text=f"💧 消耗 {mana} 魔能", font=("Arial", 11, "bold"), text_color="#60a5fa").pack(side="left", padx=8, pady=3)
            if damage:
                dmg_text = f"⚔️ 伤害 {damage}"
                ctk.CTkLabel(f_stats, text=dmg_text, font=("Arial", 11, "bold"), text_color="#f87171").pack(side="left", padx=8, pady=3)
            if rng > 0:
                ctk.CTkLabel(f_stats, text=f"🎯 射程 {rng}", font=("Arial", 11, "bold"), text_color="#fbbf24").pack(side="left", padx=8, pady=3)

        # 3. Description Body
        desc = self.item_data.get('desc', '').strip()
        if desc:
            f_desc = ctk.CTkFrame(outer, fg_color="transparent")
            f_desc.pack(fill="x", padx=12, pady=(6, 8))
            ctk.CTkLabel(
                f_desc,
                text=desc,
                font=("Arial", 11),
                text_color="#e2e8f0",
                wraplength=310,
                justify="left",
                anchor="w"
            ).pack(anchor="w")

        # 4. Variant / Tier 2 info
        var_of = self.item_data.get('variant_of', '')
        if var_of:
            f_var = ctk.CTkFrame(outer, fg_color="#2e1065", corner_radius=4)
            f_var.pack(fill="x", padx=12, pady=(2, 8))
            ctk.CTkLabel(f_var, text=f"✨ 进阶形态 (原形: {var_of})", font=("Arial", 10, "bold"), text_color="#c084fc").pack(padx=8, pady=3)

        self.tip_window.update_idletasks()
        self.position_window(x, y)

    def position_window(self, x, y):
        if not self.tip_window:
            return
        w = self.tip_window.winfo_width()
        h = self.tip_window.winfo_height()
        
        # Screen bounds
        sw = self.tip_window.winfo_screenwidth()
        sh = self.tip_window.winfo_screenheight()

        pos_x = x + 16
        pos_y = y + 16

        # Avoid right overflow
        if pos_x + w > sw - 10:
            pos_x = x - w - 16
        # Avoid bottom overflow
        if pos_y + h > sh - 10:
            pos_y = y - h - 16

        pos_x = max(10, pos_x)
        pos_y = max(10, pos_y)

        self.tip_window.geometry(f"+{pos_x}+{pos_y}")
