import tkinter as tk
import customtkinter as ctk
from PIL import Image

from attribute_renderer import (
    create_stat_badges_bar,
    extract_stats_from_item,
    extract_core_stat_keys,
    format_rich_description,
    get_stat_icon,
)

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
        x, y = event.x_root, event.y_root
        try:
            self.after_id = widget.after(120, lambda: self.show(x, y))
        except Exception:
            self.after_id = None

    def on_motion(self, event):
        if self.tip_window and self._window_alive():
            self.position_window(event.x_root, event.y_root)

    def cancel_schedule(self):
        if self.after_id and self.current_widget:
            try:
                self.current_widget.after_cancel(self.after_id)
            except Exception:
                pass
        self.after_id = None

    def _window_alive(self):
        try:
            return bool(self.tip_window and self.tip_window.winfo_exists())
        except Exception:
            return False

    def hide(self):
        self.cancel_schedule()
        if not self._window_alive():
            self.tip_window = None
            return
        try:
            self.tip_window.withdraw()
            for child in self.tip_window.winfo_children():
                child.destroy()
        except Exception:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None

    def _ensure_window(self, host):
        """Reuse one Toplevel parented to the current grab/host window.

        An orphan tk.Toplevel() plus a modal grab_set() deadlocks after a few
        open/close cycles on Windows.
        """
        if self._window_alive() and self.tip_window.master is host:
            return self.tip_window
        if self._window_alive():
            try:
                self.tip_window.destroy()
            except Exception:
                pass
        self.tip_window = tk.Toplevel(host)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.withdraw()
        try:
            self.tip_window.attributes("-topmost", True)
        except Exception:
            pass
        return self.tip_window

    def show(self, x, y):
        if not self.item_data:
            return
        try:
            if self.current_widget and not self.current_widget.winfo_exists():
                return
            host = self.current_widget.winfo_toplevel() if self.current_widget else None
            if host is None or not host.winfo_exists():
                return
        except Exception:
            return

        win = self._ensure_window(host)
        for child in win.winfo_children():
            child.destroy()
        
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
        en_name = (self.item_data.get('name_en') or '').strip()
        code = self.item_data.get('key', '')
        if en_name and code and en_name != code:
            en_line = f"{en_name}  ·  {code}"
        else:
            en_line = en_name or code

        ctk.CTkLabel(f_titles, text=cn_name, font=("Arial", 14, "bold"), text_color="#fbbf24", anchor="w").pack(anchor="w")
        if en_line and en_line != cn_name:
            ctk.CTkLabel(f_titles, text=en_line, font=("Arial", 10), text_color="#94a3b8", anchor="w").pack(anchor="w")

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

        core_stats = extract_core_stat_keys(self.item_data)
        if core_stats:
            f_core = ctk.CTkFrame(f_titles, fg_color="transparent")
            f_core.pack(anchor="w", pady=(2, 0))
            for sk in core_stats:
                simg = get_stat_icon(sk, size=(16, 16))
                if simg:
                    ctk.CTkLabel(f_core, text="", image=simg, width=16, height=16).pack(side="left", padx=(0, 2))

        # Item Rarity & Kind badge
        rarity = self.item_data.get('rarity', '')
        kind = self.item_data.get('kind', '')
        if rarity or kind:
            rarity_colors = {
                'common': '#94a3b8',
                'uncommon': '#22c55e',
                'rare': '#38bdf8',
                'very_rare': '#c084fc',
                'epic': '#c084fc',
                'quest': '#f59e0b',
                'sidequest': '#f59e0b',
            }
            rc = rarity_colors.get(str(rarity).lower(), '#94a3b8')
            tag_kind = f" · {kind.upper()}" if kind else ""
            tag_text = f"✦ {str(rarity).upper()}{tag_kind}"
            ctk.CTkLabel(f_titles, text=tag_text, font=("Arial", 10, "bold"), text_color=rc, anchor="w").pack(anchor="w", pady=(2, 0))

        # Furniture Set badge
        f_set = self.item_data.get('set', '')
        if f_set and f_set != 'none':
            ctk.CTkLabel(f_titles, text=f"🏠 套装: {str(f_set).title()}", font=("Arial", 10, "bold"), text_color="#38bdf8", anchor="w").pack(anchor="w", pady=(2, 0))

        # 2. Stats strip (Mana, Damage, Range, Shield, Brace, Furniture Stats, etc.)
        mana = self.item_data.get('mana', 0)
        damage = self.item_data.get('damage', '')
        rng = self.item_data.get('range', 0)

        extra_items = []
        if mana > 0:
            extra_items.append(('mana', f"消耗 {mana}"))
        if damage:
            extra_items.append(('damage', str(damage)))
        if rng > 0:
            extra_items.append(('range', str(rng)))

        stats_list = extract_stats_from_item(self.item_data)

        f_badges = create_stat_badges_bar(outer, stats_list, extra_items=extra_items, max_per_row=3)
        if f_badges:
            f_badges.pack(fill="x", padx=10, pady=(2, 4))

        # 3. Description Body
        raw_desc = (self.item_data.get('desc') or '').strip()
        raw_en = (self.item_data.get('desc_en') or '').strip()
        desc = format_rich_description(raw_desc)
        desc_en = format_rich_description(raw_en)
        if desc_en and desc_en == desc:
            desc_en = ""
        if desc or desc_en:
            f_desc = ctk.CTkFrame(outer, fg_color="transparent")
            f_desc.pack(fill="x", padx=12, pady=(4, 8))
            if desc:
                ctk.CTkLabel(
                    f_desc,
                    text=desc,
                    font=("Arial", 11),
                    text_color="#e2e8f0",
                    wraplength=320,
                    justify="left",
                    anchor="w"
                ).pack(anchor="w")
            if desc_en:
                ctk.CTkLabel(
                    f_desc,
                    text=desc_en,
                    font=("Arial", 10),
                    text_color="#94a3b8",
                    wraplength=320,
                    justify="left",
                    anchor="w"
                ).pack(anchor="w", pady=(6, 0))

        # 4. Variant / Tier 2 info
        var_of = self.item_data.get('variant_of', '')
        if var_of:
            f_var = ctk.CTkFrame(outer, fg_color="#2e1065", corner_radius=4)
            f_var.pack(fill="x", padx=12, pady=(2, 8))
            ctk.CTkLabel(f_var, text=f"✨ 进阶形态 (原形: {var_of})", font=("Arial", 10, "bold"), text_color="#c084fc").pack(padx=8, pady=3)

        self.tip_window.update_idletasks()
        self.position_window(x, y)
        try:
            self.tip_window.deiconify()
            self.tip_window.lift()
        except Exception:
            pass

    def position_window(self, x, y):
        if not self._window_alive():
            self.tip_window = None
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
