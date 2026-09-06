import os
import sys
import json
import tkinter as tk
import customtkinter as ctk
from PIL import Image

from tooltip_manager import GameTooltip
from picker_dialog import UniversalGridPickerDialog

class SkillCardWidget(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        catalog_type="ability",
        width=300,
        height=48,
        command=None,
        get_current_class_func=None,
        **kwargs
    ):
        super().__init__(parent, fg_color="#182234", border_color="#334155", border_width=1, corner_radius=6, width=width, height=height, **kwargs)
        self.pack_propagate(False)
        
        self.catalog_type = catalog_type
        self.command = command
        self.get_current_class_func = get_current_class_func
        self.current_value = "None"
        self.state = "normal"

        # Assets & Catalog
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        if getattr(sys, 'frozen', False):
            self.base_dir = sys._MEIPASS
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.icons_dir = os.path.join(self.assets_dir, "icons", "abilities" if catalog_type == "ability" else "passives")
        self.fallback_path = os.path.join(self.assets_dir, "icons", "fallback.png")

        # Load catalog dict for quick lookup
        if catalog_type == "disorder":
            cat_fn = "disorders_catalog.json"
        elif catalog_type == "ability":
            cat_fn = "abilities_catalog.json"
        else:
            cat_fn = "passives_catalog.json"
        cat_path = os.path.join(self.assets_dir, cat_fn)
        self.catalog_map = {}
        if os.path.exists(cat_path):
            try:
                with open(cat_path, 'r', encoding='utf-8') as f:
                    for item in json.load(f):
                        self.catalog_map[item['key']] = item
            except Exception as e:
                print(f"Error loading catalog in widget: {e}")

        self.icon_cache = {}

        # 1. Left Icon
        self.lbl_icon = ctk.CTkLabel(self, text="", width=38, height=38)
        self.lbl_icon.pack(side="left", padx=(6, 8), pady=4)

        # 2. Middle Text Block
        self.f_text = ctk.CTkFrame(self, fg_color="transparent")
        self.f_text.pack(side="left", fill="both", expand=True, pady=4)

        self.lbl_name = ctk.CTkLabel(self.f_text, text="None (无技能)", font=("Arial", 12, "bold"), text_color="#94a3b8", anchor="w")
        self.lbl_name.pack(fill="x", anchor="w")

        self.lbl_code = ctk.CTkLabel(self.f_text, text="点击右侧更换技能", font=("Arial", 9), text_color="#64748b", anchor="w")
        self.lbl_code.pack(fill="x", anchor="w")

        # 3. Right Pick Button
        self.btn_pick = ctk.CTkButton(
            self,
            text="更换 ▾",
            width=58,
            height=26,
            font=("Arial", 11),
            fg_color="#334155",
            hover_color="#475569",
            command=self.open_picker
        )
        self.btn_pick.pack(side="right", padx=(4, 8), pady=10)

        # Bind hover and click events
        for w in [self, self.lbl_icon, self.f_text, self.lbl_name, self.lbl_code]:
            w.bind("<Button-1>", lambda e: self.open_picker())
            w.bind("<Enter>", lambda e: self.on_mouse_enter())
            w.bind("<Leave>", lambda e: self.on_mouse_leave())

    def get_icon(self, key, size=(36, 36)):
        if not key or key == 'None':
            return None
        cache_k = f"{key}_{size[0]}"
        if cache_k in self.icon_cache:
            return self.icon_cache[cache_k]

        png_path = os.path.join(self.icons_dir, f"{key}.png")
        if not os.path.exists(png_path):
            png_path = self.fallback_path

        if os.path.exists(png_path):
            try:
                pil_img = Image.open(png_path).convert("RGBA")
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
                self.icon_cache[cache_k] = ctk_img
                return ctk_img
            except Exception:
                pass
        return None

    def get(self):
        return self.current_value

    def set(self, val):
        if not val or val.startswith("None"):
            self.current_value = "None"
        elif "(" in val and val.endswith(")"):
            import re
            m = re.search(r'\(([^)]+)\)', val)
            self.current_value = m.group(1).strip() if m else val.strip()
        else:
            self.current_value = str(val).strip()
        self.update_display()

    def configure(self, **kwargs):
        kwargs.pop('values', None) # ignore legacy dropdown values list
        if 'state' in kwargs:
            self.state = kwargs['state']
            if self.state == 'disabled':
                self.btn_pick.configure(state='disabled', fg_color="#1e293b", text_color="#64748b")
                super().configure(border_color="#1e293b", fg_color="#0f172a")
                self.lbl_name.configure(text_color="#64748b")
                self.lbl_code.configure(text_color="#475569")
            else:
                self.btn_pick.configure(state='normal', fg_color="#334155", text_color="#f8fafc")
                super().configure(border_color="#334155", fg_color="#182234")
                if self.current_value != "None":
                    self.lbl_name.configure(text_color="#f8fafc")
                    self.lbl_code.configure(text_color="#94a3b8")
                else:
                    self.lbl_name.configure(text_color="#94a3b8")
                    self.lbl_code.configure(text_color="#64748b")
            kwargs.pop('state')
        if kwargs:
            super().configure(**kwargs)

    def cget(self, attribute_name):
        if attribute_name == 'state':
            return self.state
        return super().cget(attribute_name)

    def update_display(self):
        k = self.current_value
        if not k or k == "None":
            self.lbl_icon.configure(image=None)
            self.lbl_name.configure(text="None (未选择)", text_color="#64748b" if self.state == 'disabled' else "#94a3b8")
            self.lbl_code.configure(text="空槽位", text_color="#475569")
            # Unbind tooltip
            GameTooltip.get_instance().hide()
        else:
            item = self.catalog_map.get(k, {})
            cn_name = item.get('name') or k
            self.lbl_name.configure(text=cn_name, text_color="#64748b" if self.state == 'disabled' else "#f8fafc")
            self.lbl_code.configure(text=k, text_color="#475569" if self.state == 'disabled' else "#94a3b8")
            
            icon = self.get_icon(k, size=(36, 36))
            self.lbl_icon.configure(image=icon)

            # Bind tooltip for hover
            item_data = item or {'key': k, 'name': cn_name, 'desc': ''}
            tooltip = GameTooltip.get_instance()
            for w in [self, self.lbl_icon, self.f_text, self.lbl_name, self.lbl_code]:
                tooltip.bind_widget(w, item_data, get_icon_func=self.get_icon)

    def on_mouse_enter(self):
        if self.state == 'normal':
            self.configure(border_color="#6366f1")

    def on_mouse_leave(self):
        if self.state == 'normal':
            self.configure(border_color="#334155")
        GameTooltip.get_instance().hide()

    def open_picker(self):
        if self.state == 'disabled':
            return

        parent_win = self.winfo_toplevel()
        cat_class = None
        if self.get_current_class_func:
            cat_class = self.get_current_class_func()

        title = "选择战斗法术" if self.catalog_type == "ability" else ("选择疾病缺陷 (Disorder)" if self.catalog_type == "disorder" else "选择被动特质")
        dlg = UniversalGridPickerDialog(
            parent_win,
            title=title,
            catalog_type=self.catalog_type,
            current_value=self.current_value,
            initial_category=cat_class,
            on_select_callback=self.on_picker_selected
        )

    def on_picker_selected(self, chosen_val):
        self.set(chosen_val)
        if self.command:
            self.command(chosen_val)
