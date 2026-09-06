import os
import sys
import json
import math
import tkinter as tk
import customtkinter as ctk
from PIL import Image

from tooltip_manager import GameTooltip

class UniversalGridPickerDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        title="选择技能",
        catalog_type="ability", # 'ability' or 'passive'
        current_value="None",
        initial_category=None,
        on_select_callback=None
    ):
        super().__init__(parent)
        self.title(title)
        self.geometry("980x700")
        self.minsize(860, 600)
        self.transient(parent)
        self.grab_set()

        self.catalog_type = catalog_type
        self.current_value = current_value or "None"
        self.selected_value = self.current_value
        self.initial_category = initial_category
        self.on_select_callback = on_select_callback

        # 8 columns x 4 rows = 32 per page
        self.COLS = 8
        self.ROWS = 4
        self.PAGE_SIZE = self.COLS * self.ROWS
        self.current_page = 1

        # Icon Cache
        self.icon_cache = {}
        self.fallback_icon = None

        # Data paths
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        if getattr(sys, 'frozen', False):
            self.base_dir = sys._MEIPASS

        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.icons_dir = os.path.join(self.assets_dir, "icons", "abilities" if catalog_type == "ability" else "passives")
        self.fallback_path = os.path.join(self.assets_dir, "icons", "fallback.png")

        # Load catalog
        self.full_catalog = self.load_catalog()
        self.filtered_catalog = list(self.full_catalog)

        # Setup UI
        self.init_ui()

        # Apply initial filters
        if self.initial_category and self.initial_category in self.categories:
            self.select_category(self.initial_category)
        else:
            self.select_category("全部")

        # Locate initial page if current_value is set
        self.locate_current_value()

    def load_catalog(self):
        cat_fn = "abilities_catalog.json" if self.catalog_type == "ability" else "passives_catalog.json"
        cat_path = os.path.join(self.assets_dir, cat_fn)
        if os.path.exists(cat_path):
            try:
                with open(cat_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading catalog {cat_path}: {e}")
        return []

    def get_icon(self, key, size=(48, 48)):
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

    def init_ui(self):
        # 1. Top Filter Area (Search Bar & Category Pills)
        self.f_top = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=0)
        self.f_top.pack(fill="x", padx=0, pady=0)

        # Row 1: Search & Info
        f_search_row = ctk.CTkFrame(self.f_top, fg_color="transparent")
        f_search_row.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(f_search_row, text="🔍 搜索技能:", font=("Arial", 13, "bold"), text_color="#38bdf8").pack(side="left", padx=(0, 8))
        self.entry_search = ctk.CTkEntry(f_search_row, width=320, placeholder_text="输入中文名称、英文代码或效果关键词...")
        self.entry_search.pack(side="left", padx=4)
        self.entry_search.bind("<KeyRelease>", self.on_search_changed)

        btn_clear_search = ctk.CTkButton(f_search_row, text="✕", width=28, height=28, fg_color="#334155", hover_color="#475569", command=self.clear_search)
        btn_clear_search.pack(side="left", padx=(2, 10))

        self.lbl_count = ctk.CTkLabel(f_search_row, text="", font=("Arial", 12), text_color="#94a3b8")
        self.lbl_count.pack(side="right", padx=10)

        # Row 2: Category Tabs (Pill Buttons)
        f_cat_row = ctk.CTkScrollableFrame(self.f_top, fg_color="transparent", height=42, orientation="horizontal")
        f_cat_row.pack(fill="x", padx=12, pady=(0, 8))

        if self.catalog_type == "ability":
            self.categories = [
                '全部', 'Colorless', 'Fighter', 'Mage', 'Hunter', 'Tank', 'Medic',
                'Thief', 'Necromancer', 'Butcher', 'Druid', 'Monk', 'Psychic',
                'Tinkerer', 'Jester'
            ]
            cat_cn = {
                '全部': '🌟 全部',
                'Colorless': '⚪ 通用',
                'Fighter': '⚔️ 战士',
                'Mage': '🔮 法师',
                'Hunter': '🏹 猎人',
                'Tank': '🛡️ 肉盾',
                'Medic': '💉 医者',
                'Thief': '🗡️ 盗贼',
                'Necromancer': '💀 死灵',
                'Butcher': '🥩 屠夫',
                'Druid': '🌿 德鲁伊',
                'Monk': '🥋 武僧',
                'Psychic': '👁️ 灵能',
                'Tinkerer': '⚙️ 工匠',
                'Jester': '🃏 小丑'
            }
        else:
            self.categories = ['全部']
            cat_cn = {'全部': '🌟 全部被动'}

        self.cat_buttons = {}
        self.current_category = '全部'

        for cat in self.categories:
            label = cat_cn.get(cat, cat)
            btn = ctk.CTkButton(
                f_cat_row,
                text=label,
                height=26,
                font=("Arial", 11, "bold"),
                fg_color="#1e293b",
                hover_color="#334155",
                corner_radius=13,
                command=lambda c=cat: self.select_category(c)
            )
            btn.pack(side="left", padx=3)
            self.cat_buttons[cat] = btn

        # 2. Center Grid View Area
        self.f_grid_container = ctk.CTkFrame(self, fg_color="#090d16")
        self.f_grid_container.pack(fill="both", expand=True, padx=14, pady=8)

        # Pre-build 32 card slots for smooth instant switching
        self.card_slots = []
        for r in range(self.ROWS):
            self.f_grid_container.rowconfigure(r, weight=1)
            for c in range(self.COLS):
                self.f_grid_container.columnconfigure(c, weight=1)
                card = ctk.CTkFrame(self.f_grid_container, fg_color="#131d2e", border_color="#1e293b", border_width=1, corner_radius=6)
                card.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")

                lbl_icon = ctk.CTkLabel(card, text="", width=48, height=48)
                lbl_icon.pack(padx=2, pady=(6, 2))

                lbl_name = ctk.CTkLabel(card, text="", font=("Arial", 11), text_color="#cbd5e1", width=96, anchor="center")
                lbl_name.pack(padx=2, pady=(0, 6))

                slot_data = {
                    'card': card,
                    'icon': lbl_icon,
                    'name': lbl_name,
                    'item': None
                }
                self.card_slots.append(slot_data)

        # 3. Bottom Control & Confirmation Bar
        self.f_bottom = ctk.CTkFrame(self, fg_color="#0f172a", height=60, corner_radius=0)
        self.f_bottom.pack(fill="x", padx=0, pady=0)

        # Left: Selected Item preview
        f_sel_info = ctk.CTkFrame(self.f_bottom, fg_color="transparent")
        f_sel_info.pack(side="left", padx=16, pady=8)

        self.lbl_sel_icon = ctk.CTkLabel(f_sel_info, text="", width=40, height=40)
        self.lbl_sel_icon.pack(side="left", padx=(0, 8))

        f_sel_text = ctk.CTkFrame(f_sel_info, fg_color="transparent")
        f_sel_text.pack(side="left")
        ctk.CTkLabel(f_sel_text, text="当前选中:", font=("Arial", 10), text_color="#94a3b8", anchor="w").pack(anchor="w")
        self.lbl_sel_title = ctk.CTkLabel(f_sel_text, text="未选择", font=("Arial", 13, "bold"), text_color="#38bdf8", anchor="w")
        self.lbl_sel_title.pack(anchor="w")

        # Center: Pagination
        f_page = ctk.CTkFrame(self.f_bottom, fg_color="transparent")
        f_page.pack(side="left", expand=True)

        self.btn_prev = ctk.CTkButton(f_page, text="◀ 上一页", width=75, height=28, command=self.prev_page)
        self.btn_prev.pack(side="left", padx=5)

        self.lbl_page = ctk.CTkLabel(f_page, text="1 / 1", font=("Arial", 12, "bold"), width=80)
        self.lbl_page.pack(side="left", padx=5)

        self.btn_next = ctk.CTkButton(f_page, text="下一页 ▶", width=75, height=28, command=self.next_page)
        self.btn_next.pack(side="left", padx=5)

        # Right: Action Buttons
        f_actions = ctk.CTkFrame(self.f_bottom, fg_color="transparent")
        f_actions.pack(side="right", padx=16, pady=8)

        btn_none = ctk.CTkButton(f_actions, text="设为 None (清空)", width=110, height=32, fg_color="#475569", hover_color="#64748b", command=self.set_none_and_close)
        btn_none.pack(side="left", padx=5)

        btn_cancel = ctk.CTkButton(f_actions, text="取消", width=75, height=32, fg_color="#334155", hover_color="#475569", command=self.destroy)
        btn_cancel.pack(side="left", padx=5)

        btn_confirm = ctk.CTkButton(f_actions, text="✅ 选定此技能", width=120, height=32, font=("Arial", 12, "bold"), fg_color="#10b981", hover_color="#059669", command=self.confirm_and_close)
        btn_confirm.pack(side="left", padx=5)

    def select_category(self, cat):
        self.current_category = cat
        for c, btn in self.cat_buttons.items():
            if c == cat:
                btn.configure(fg_color="#6366f1", hover_color="#4f46e5")
            else:
                btn.configure(fg_color="#1e293b", hover_color="#334155")
        self.apply_filter()

    def on_search_changed(self, event=None):
        self.apply_filter()

    def clear_search(self):
        self.entry_search.delete(0, 'end')
        self.apply_filter()

    def apply_filter(self):
        query = self.entry_search.get().strip().lower()
        res = []
        for item in self.full_catalog:
            # Class filter
            if self.current_category != '全部':
                if item.get('class') != self.current_category:
                    continue
            
            # Text search filter
            if query:
                k = item.get('key', '').lower()
                name = item.get('name', '').lower()
                name_en = item.get('name_en', '').lower()
                desc = item.get('desc', '').lower()
                if query not in k and query not in name and query not in name_en and query not in desc:
                    continue
            res.append(item)

        self.filtered_catalog = res
        self.current_page = 1
        self.render_grid()

    def locate_current_value(self):
        if self.current_value and self.current_value != 'None':
            for idx, item in enumerate(self.filtered_catalog):
                if item.get('key') == self.current_value:
                    self.current_page = (idx // self.PAGE_SIZE) + 1
                    break
        self.render_grid()
        self.update_selected_preview(self.current_value)

    def render_grid(self):
        total_items = len(self.filtered_catalog)
        total_pages = max(1, math.ceil(total_items / self.PAGE_SIZE))
        self.current_page = min(max(1, self.current_page), total_pages)

        # Update counter & pagination
        self.lbl_count.configure(text=f"共找到 {total_items} 项")
        self.lbl_page.configure(text=f"{self.current_page} / {total_pages}")
        self.btn_prev.configure(state="normal" if self.current_page > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.current_page < total_pages else "disabled")

        start_idx = (self.current_page - 1) * self.PAGE_SIZE
        page_items = self.filtered_catalog[start_idx : start_idx + self.PAGE_SIZE]

        tooltip = GameTooltip.get_instance()

        for i in range(self.PAGE_SIZE):
            slot = self.card_slots[i]
            card = slot['card']
            lbl_icon = slot['icon']
            lbl_name = slot['name']

            if i < len(page_items):
                item = page_items[i]
                slot['item'] = item
                k = item['key']
                cn_name = item.get('name') or k

                # Truncate for display if too long
                disp_name = cn_name if len(cn_name) <= 6 else cn_name[:5] + '..'
                lbl_name.configure(text=disp_name)

                # Icon
                icon_img = self.get_icon(k, size=(48, 48))
                lbl_icon.configure(image=icon_img)

                # Highlight selected
                if k == self.selected_value:
                    card.configure(fg_color="#143026", border_color="#10b981", border_width=2)
                else:
                    card.configure(fg_color="#131d2e", border_color="#1e293b", border_width=1)

                card.grid() # make visible

                # Bind events
                self.bind_card_events(card, lbl_icon, lbl_name, item)
            else:
                slot['item'] = None
                card.grid_remove() # hide empty slot

    def bind_card_events(self, card, lbl_icon, lbl_name, item):
        tooltip = GameTooltip.get_instance()
        k = item['key']

        def on_click(e):
            self.on_card_selected(k)

        def on_double_click(e):
            self.on_card_selected(k)
            self.confirm_and_close()

        for w in [card, lbl_icon, lbl_name]:
            w.bind("<Button-1>", on_click)
            w.bind("<Double-Button-1>", on_double_click)
            tooltip.bind_widget(w, item, get_icon_func=self.get_icon)

    def on_card_selected(self, key):
        self.selected_value = key
        self.update_selected_preview(key)
        # Update borders
        for slot in self.card_slots:
            if slot['item']:
                card = slot['card']
                if slot['item']['key'] == key:
                    card.configure(fg_color="#143026", border_color="#10b981", border_width=2)
                else:
                    card.configure(fg_color="#131d2e", border_color="#1e293b", border_width=1)

    def update_selected_preview(self, key):
        if not key or key == 'None':
            self.lbl_sel_icon.configure(image=None)
            self.lbl_sel_title.configure(text="None (无技能/清空)", text_color="#94a3b8")
            return

        item = next((x for x in self.full_catalog if x['key'] == key), None)
        icon = self.get_icon(key, size=(40, 40))
        self.lbl_sel_icon.configure(image=icon)

        cn_name = item.get('name') if item else key
        self.lbl_sel_title.configure(text=f"{cn_name} ({key})", text_color="#38bdf8")

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_grid()

    def next_page(self):
        total_pages = max(1, math.ceil(len(self.filtered_catalog) / self.PAGE_SIZE))
        if self.current_page < total_pages:
            self.current_page += 1
            self.render_grid()

    def set_none_and_close(self):
        GameTooltip.get_instance().hide()
        if self.on_select_callback:
            self.on_select_callback('None')
        self.destroy()

    def confirm_and_close(self):
        GameTooltip.get_instance().hide()
        if self.on_select_callback:
            self.on_select_callback(self.selected_value)
        self.destroy()

    def destroy(self):
        GameTooltip.get_instance().hide()
        super().destroy()
