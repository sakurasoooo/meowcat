import os
import sys
import json
import csv
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

try:
    from PIL import Image
except ImportError:
    Image = None

from mewgenics_core import MewgenicsSaveManager, CatRecord, MUTATION_SLOTS, get_ability_upgrade, get_base_ability, get_shop_progress, storage_capacity, parse_class_zone_records, MAJOR_CHECKMARK_ZONES
from mutation_picker import MutationPicker, make_tile, classify_mutation, CATEGORY_COLORS
from skill_card_widget import SkillCardWidget
from picker_dialog import UniversalGridPickerDialog
from tooltip_manager import GameTooltip

# Set CustomTkinter theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        p = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(p):
            return p
    exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(exe_dir, relative_path)
    if os.path.exists(p):
        return p
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

class SaveSlotDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_select_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.on_select_callback = on_select_callback
        self.selected_path = None

        self.title("Mewgenics 战役存档选择 (Campaign Save Slots)")
        self.geometry("960x620")
        self.minsize(900, 580)
        self.resizable(False, False)

        # Modal configuration
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        try:
            px = parent.winfo_x()
            py = parent.winfo_y()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = px + (pw - 960) // 2
            y = py + (ph - 620) // 2
            self.geometry(f"+{max(50, x)}+{max(50, y)}")
        except Exception:
            pass

        self.init_ui()

    def init_ui(self):
        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))
        
        ctk.CTkLabel(header, text="🧪 喵星人战役存档槽位选择", font=("Arial", 20, "bold"), text_color="#f8fafc").pack(anchor="w")
        ctk.CTkLabel(
            header, 
            text="仿游戏原版培养皿存档界面，请选择要载入的战役槽位，或点击底部选择外部任意存档文件", 
            font=("Arial", 12), 
            text_color="#94a3b8"
        ).pack(anchor="w", pady=(3, 0))

        # 2. Main 3 Slots Container
        slots_container = ctk.CTkFrame(self, fg_color="transparent")
        slots_container.pack(fill="both", expand=True, padx=20, pady=5)
        slots_container.grid_columnconfigure((0, 1, 2), weight=1, uniform="slot")
        slots_container.grid_rowconfigure(0, weight=1)

        slots_info = MewgenicsSaveManager.get_all_slots_info()

        themes = [
            {
                'name': '槽位 1 (Slot 1)',
                'accent': '#f43f5e',
                'accent_hover': '#e11d48',
                'bg_card': '#1f1523',
                'tube_border': '#f43f5e',
                'tube_bg': '#2b1428',
                'glow_text': '#fda4af'
            },
            {
                'name': '槽位 2 (Slot 2)',
                'accent': '#eab308',
                'accent_hover': '#ca8a04',
                'bg_card': '#1c1917',
                'tube_border': '#eab308',
                'tube_bg': '#292211',
                'glow_text': '#fef08a'
            },
            {
                'name': '槽位 3 (Slot 3)',
                'accent': '#0ea5e9',
                'accent_hover': '#0284c7',
                'bg_card': '#0f172a',
                'tube_border': '#0ea5e9',
                'tube_bg': '#12263a',
                'glow_text': '#bae6fd'
            }
        ]

        for i in range(3):
            info = slots_info[i] if i < len(slots_info) else {'has_data': False}
            th = themes[i]
            self.build_slot_card(slots_container, col=i, info=info, theme=th)

        # 3. Bottom Action Bar
        bottom_bar = ctk.CTkFrame(self, fg_color="#1e293b", height=60, corner_radius=10)
        bottom_bar.pack(fill="x", padx=25, pady=(10, 20))

        btn_browse = ctk.CTkButton(
            bottom_bar, 
            text="📂 手动浏览选择外部存档 (.sav)...", 
            font=("Arial", 12, "bold"),
            fg_color="#0284c7", 
            hover_color="#0369a1",
            height=36,
            command=self.on_browse_external
        )
        btn_browse.pack(side="left", padx=15, pady=12)

        saves_dir = MewgenicsSaveManager.get_saves_dir()
        ctk.CTkLabel(
            bottom_bar, 
            text=f"默认目录: {saves_dir if len(saves_dir) < 45 else '...' + saves_dir[-42:]}", 
            font=("Arial", 11), 
            text_color="#64748b"
        ).pack(side="left", padx=5)

        btn_close = ctk.CTkButton(
            bottom_bar, 
            text="保持当前 / 关闭", 
            font=("Arial", 12),
            fg_color="#334155", 
            hover_color="#475569",
            height=36,
            width=120,
            command=self.destroy
        )
        btn_close.pack(side="right", padx=15, pady=12)

    def build_slot_card(self, parent, col, info, theme):
        card = ctk.CTkFrame(parent, fg_color=theme['bg_card'], corner_radius=12, border_width=1, border_color="#334155")
        card.grid(row=0, column=col, sticky="nsew", padx=8, pady=5)

        has_data = info.get('has_data', False)

        # 1. Retro TV Screen Frame
        tv_frame = ctk.CTkFrame(card, fg_color="#090d16", corner_radius=8, border_width=2, border_color="#475569")
        tv_frame.pack(fill="x", padx=12, pady=(12, 8))

        screen = ctk.CTkFrame(tv_frame, fg_color="#f1f5f9" if has_data else "#e2e8f0", corner_radius=6)
        screen.pack(fill="both", expand=True, padx=6, pady=6)

        if has_data:
            # Game style text: Location / Completion% / Timer
            ctk.CTkLabel(screen, text=info.get('location', '家'), font=("Arial", 17, "bold"), text_color="#0f172a").pack(pady=(6, 1))
            ctk.CTkLabel(screen, text=f"完成度 {info.get('percent', 0)}%", font=("Arial", 13, "bold"), text_color="#334155").pack(pady=1)
            ctk.CTkLabel(screen, text=info.get('time_str', '00:00:00'), font=("Arial", 13, "bold"), text_color="#1e293b").pack(pady=(1, 6))
        else:
            ctk.CTkLabel(screen, text="无数据", font=("Arial", 16, "bold"), text_color="#64748b").pack(pady=22)

        # 2. Incubator Tube (Capsule) Frame
        tube_border = theme['tube_border'] if has_data else "#334155"
        tube_bg = theme['tube_bg'] if has_data else "#141b26"
        tube = ctk.CTkFrame(card, fg_color=tube_bg, corner_radius=10, border_width=2, border_color=tube_border)
        tube.pack(fill="both", expand=True, padx=12, pady=6)

        if has_data:
            # Floating cat icon & stats
            ctk.CTkLabel(tube, text="🐱 🫧", font=("Arial", 30)).pack(pady=(6, 2))
            
            stats_frame = ctk.CTkFrame(tube, fg_color="transparent")
            stats_frame.pack(fill="x", padx=10, pady=2)

            def add_stat_line(f, left, right):
                r = ctk.CTkFrame(f, fg_color="transparent")
                r.pack(fill="x", pady=2)
                ctk.CTkLabel(r, text=left, font=("Arial", 11), text_color="#94a3b8", width=70, anchor="w").pack(side="left")
                ctk.CTkLabel(r, text=right, font=("Arial", 11, "bold"), text_color="#f8fafc", anchor="w").pack(side="left")

            add_stat_line(stats_frame, "游戏天数:", f"第 {info.get('day', 0)} 天")
            add_stat_line(stats_frame, "猫咪总数:", f"{info.get('cat_count', 0)} 只")
            add_stat_line(stats_frame, "家园资源:", f"🪙 {info.get('gold', 0)}  🍖 {info.get('food', 0)}")
            add_stat_line(stats_frame, "最后修改:", f"{info.get('mtime_str', '--')}")

            ctk.CTkLabel(
                tube, 
                text=f"steamcampaign0{info.get('slot', 1)}.sav", 
                font=("Arial", 10), 
                text_color=theme['glow_text']
            ).pack(pady=(4, 2))

        else:
            # Empty tube placeholder
            ctk.CTkLabel(tube, text="🧪", font=("Arial", 32)).pack(pady=(18, 4))
            ctk.CTkLabel(tube, text="槽位未启用", font=("Arial", 13, "bold"), text_color="#64748b").pack(pady=2)
            ctk.CTkLabel(tube, text="无存档数据\n可在游戏内开启新战役建立", font=("Arial", 11), text_color="#475569", justify="center").pack(pady=4)

        # 3. Bottom Button for Slot
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(8, 12))

        if has_data:
            btn = ctk.CTkButton(
                btn_frame,
                text=f"▶ 载入此战役 (槽位 {info.get('slot', col+1)})",
                font=("Arial", 12, "bold"),
                fg_color=theme['accent'],
                hover_color=theme['accent_hover'],
                height=34,
                command=lambda p=info['path']: self.select_path(p)
            )
            btn.pack(fill="x")
        else:
            btn = ctk.CTkButton(
                btn_frame,
                text="无数据 (槽位未激活)",
                font=("Arial", 11),
                fg_color="#242c38",
                text_color_disabled="#64748b",
                state="disabled",
                height=34
            )
            btn.pack(fill="x")

    def select_path(self, path):
        self.selected_path = path
        if self.on_select_callback:
            self.on_select_callback(path)
        self.destroy()

    def on_browse_external(self):
        f = filedialog.askopenfilename(
            title="选择 Mewgenics 战役存档文件 (.sav)",
            filetypes=[("Mewgenics Save (*.sav)", "*.sav"), ("All Files (*.*)", "*.*")],
            initialdir=MewgenicsSaveManager.get_saves_dir()
        )
        if f:
            self.select_path(f)

class MewgenicsApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mewgenics Cat Editor & Save Modifier (喵星人猫咪属性修改器)")
        self.geometry("1180x820")
        self.minsize(1050, 720)

        # Load game data cache if exists
        self.game_data = self.load_game_data()

        # Save manager
        self.save_mgr = MewgenicsSaveManager()
        self.current_cat = None
        self.cat_cards = {}
        self.mut_mod_labels = {}
        self.mutation_combos = {}
        self.right_combos = {}
        self.mutation_badge_labels = {}
        self.active_combos = []
        self.upgrade_checkboxes = []
        self.innate_combos = []
        self.innate_lock_btns = []
        self.innate_locked = [True, True, True, True]
        self.upgrade_combos = self.innate_combos
        self.class_passive_combos = []
        self.disorder_combos = []
        self.passive_combos = []
        self.class_passive_lookup = {}
        self.class_passive_key_to_str = {}
        self.disorder_lookup = {}
        self.disorder_key_to_str = {}
        self.disorder_display_list = []

        self.init_ui()
        self.populate_cat_list()
        self.update_save_header_info()

        if not self.save_mgr.file_path or not os.path.exists(self.save_mgr.file_path):
            self.status_bar.configure(text="提示: 未检测到默认存档，请点击上方「切换战役槽位...」或「浏览...」手动选择存档", text_color="#f59e0b")

        if not getattr(sys, '_running_test', False):
            self.after(120, self.open_slot_selector)

    def load_game_data(self):
        json_path = get_resource_path("mewgenics_game_data.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            'classes': ['Colorless', 'Fighter', 'Mage', 'Hunter', 'Tank', 'Medic', 'Thief', 'Necromancer', 'Butcher', 'Druid', 'Monk', 'Psychic', 'Tinkerer', 'Jester'],
            'abilities': [{'key': 'BasicMelee', 'name': 'Basic Melee'}, {'key': 'BasicShortRanged', 'name': 'Basic Ranged'}],
            'passives': [{'key': 'SelfAssured', 'name': 'Self Assured'}, {'key': 'HotBlooded', 'name': 'Hot Blooded'}],
            'voices': ['male55', 'male109', 'male53', 'male59', 'female50', 'female57', 'spidercat', 'robotom']
        }

    def init_ui(self):
        # 1. Top Bar
        self.top_frame = ctk.CTkFrame(self, height=50)
        self.top_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.btn_switch_slot = ctk.CTkButton(
            self.top_frame, 
            text="🔄 切换战役槽位...", 
            width=140, 
            fg_color="#6366f1", 
            hover_color="#4f46e5", 
            font=("Arial", 12, "bold"),
            command=self.open_slot_selector
        )
        self.btn_switch_slot.pack(side="left", padx=(10, 4))

        self.lbl_slot_badge = ctk.CTkLabel(
            self.top_frame, 
            text="[槽位 1]", 
            font=("Arial", 12, "bold"), 
            text_color="#38bdf8",
            fg_color="#1e293b",
            corner_radius=6,
            padx=8,
            pady=3
        )
        self.lbl_slot_badge.pack(side="left", padx=4)

        self.lbl_path = ctk.CTkLabel(self.top_frame, text=f"路径: {self.save_mgr.file_path}", font=("Arial", 11), text_color="#94a3b8")
        self.lbl_path.pack(side="left", padx=6)

        self.btn_browse = ctk.CTkButton(self.top_frame, text="浏览...", width=65, command=self.on_browse)
        self.btn_browse.pack(side="left", padx=3)

        self.btn_reload = ctk.CTkButton(self.top_frame, text="重新加载", width=75, fg_color="#334155", command=self.on_reload)
        self.btn_reload.pack(side="left", padx=3)

        self.btn_save_all = ctk.CTkButton(self.top_frame, text="保存所有更改 (自动备份)", width=170, fg_color="#28a745", hover_color="#218838", font=("Arial", 12, "bold"), command=self.on_save)
        self.btn_save_all.pack(side="right", padx=10)

        # 2. Navigation Router (Cats / Items / Furniture)
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=10, pady=(0, 3))
        self.nav_seg = ctk.CTkSegmentedButton(
            self.nav_frame,
            values=["🐱 猫咪编辑", "🎒 仓库道具", "🪑 家具管理", "🏅 职业通关"],
            command=self.on_nav_switch,
            font=("Arial", 13, "bold"),
            height=34
        )
        self.nav_seg.set("🐱 猫咪编辑")
        self.nav_seg.pack(pady=2)

        # 3. Main Body (three parallel views, one visible at a time)
        self.main_body = ctk.CTkFrame(self)
        self.main_body.pack(fill="both", expand=True, padx=10, pady=5)

        self.view_cats = ctk.CTkFrame(self.main_body, fg_color="transparent")
        self.view_items = ctk.CTkFrame(self.main_body, fg_color="transparent")
        self.view_furniture = ctk.CTkFrame(self.main_body, fg_color="transparent")
        self.view_completion = ctk.CTkFrame(self.main_body, fg_color="transparent")

        self.setup_left_sidebar()
        self.setup_right_content()
        self.build_items_view()
        self.build_furniture_view()
        self.build_completion_view()

        self.current_view = None
        self.on_nav_switch("🐱 猫咪编辑")

        # 4. Bottom Status Bar
        self.status_bar = ctk.CTkLabel(self, text="就绪 - 已成功读取存档", anchor="w", font=("Arial", 11), text_color="#aaa")
        self.status_bar.pack(fill="x", padx=15, pady=(2, 5))

    def setup_left_sidebar(self):
        self.left_pane = ctk.CTkFrame(self.view_cats, width=330)
        self.left_pane.pack(side="left", fill="y", padx=(5, 5), pady=5)

        # Global Resources Card
        self.res_frame = ctk.CTkFrame(self.left_pane)
        self.res_frame.pack(fill="x", padx=8, pady=5)

        ctk.CTkLabel(self.res_frame, text="全局家园资源 (House Resources)", font=("Arial", 13, "bold"), text_color="#38bdf8").pack(anchor="w", padx=8, pady=(5, 2))
        
        row_res = ctk.CTkFrame(self.res_frame, fg_color="transparent")
        row_res.pack(fill="x", padx=8, pady=3)
        
        ctk.CTkLabel(row_res, text="金币 (Gold):").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_gold = ctk.CTkEntry(row_res, width=80)
        self.entry_gold.insert(0, str(self.save_mgr.properties.get('house_gold', 0)))
        self.entry_gold.grid(row=0, column=1, padx=5, pady=2)

        ctk.CTkLabel(row_res, text="食物 (Food):").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_food = ctk.CTkEntry(row_res, width=80)
        self.entry_food.insert(0, str(self.save_mgr.properties.get('house_food', 0)))
        self.entry_food.grid(row=1, column=1, padx=5, pady=2)

        ctk.CTkLabel(row_res, text="天数 (Day):").grid(row=2, column=0, sticky="w", pady=2)
        self.entry_day = ctk.CTkEntry(row_res, width=80)
        self.entry_day.insert(0, str(self.save_mgr.properties.get('current_day', 0)))
        self.entry_day.grid(row=2, column=1, padx=5, pady=2)

        self.btn_max_res = ctk.CTkButton(self.res_frame, text="一键满资源 (+999999)", height=24, font=("Arial", 11), fg_color="#0284c7", command=self.on_max_resources)
        self.btn_max_res.pack(fill="x", padx=8, pady=(4, 6))

        # Search Bar
        self.search_entry = ctk.CTkEntry(self.left_pane, placeholder_text="搜索猫咪名称、ID或房间...")
        self.search_entry.pack(fill="x", padx=8, pady=(8, 4))
        self.search_entry.bind("<KeyRelease>", self.on_search)
        self.search_entry.bind("<Return>", lambda e: self.do_search_immediate())

        # Category Filter Tabs (Living in House vs All vs History)
        self.filter_mode = "house"  # Default to house living cats!
        self.filter_frame = ctk.CTkFrame(self.left_pane, fg_color="transparent")
        self.filter_frame.pack(fill="x", padx=8, pady=(2, 4))

        n_house = len(getattr(self.save_mgr, 'house_cat_ids', set()))
        n_total = len(self.save_mgr.cats)

        self.btn_flt_house = ctk.CTkButton(
            self.filter_frame,
            text=f"家园在生 ({n_house})",
            height=26,
            font=("Arial", 11, "bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=lambda: self.set_filter_mode("house")
        )
        self.btn_flt_house.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.btn_flt_all = ctk.CTkButton(
            self.filter_frame,
            text=f"全部 ({n_total})",
            height=26,
            font=("Arial", 11),
            fg_color="#334155",
            hover_color="#475569",
            command=lambda: self.set_filter_mode("all")
        )
        self.btn_flt_all.pack(side="left", fill="x", expand=True, padx=2)

        self.btn_flt_hist = ctk.CTkButton(
            self.filter_frame,
            text=f"历史谱系 ({max(0, n_total - n_house)})",
            height=26,
            font=("Arial", 11),
            fg_color="#334155",
            hover_color="#475569",
            command=lambda: self.set_filter_mode("history")
        )
        self.btn_flt_hist.pack(side="left", fill="x", expand=True, padx=(2, 0))

        # Action Buttons for Cats
        btn_row = ctk.CTkFrame(self.left_pane, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=3)
        self.btn_new_cat = ctk.CTkButton(btn_row, text="+ 新建猫咪", width=95, fg_color="#10b981", hover_color="#059669", command=self.on_create_cat_dialog)
        self.btn_new_cat.pack(side="left", padx=(0, 4))

        self.btn_clone_cat = ctk.CTkButton(btn_row, text="克隆复制", width=95, fg_color="#6366f1", hover_color="#4f46e5", command=self.on_clone_cat)
        self.btn_clone_cat.pack(side="left", padx=4)

        self.btn_del_cat = ctk.CTkButton(btn_row, text="删除", width=65, fg_color="#ef4444", hover_color="#dc2626", command=self.on_delete_cat)
        self.btn_del_cat.pack(side="right")

        # Scrollable Cat List
        self.cat_list_frame = ctk.CTkScrollableFrame(self.left_pane, label_text=f"家园在生猫咪 (共 {n_house} 只)")
        self.cat_list_frame.pack(fill="both", expand=True, padx=8, pady=5)

    def setup_right_content(self):
        self.right_pane = ctk.CTkFrame(self.view_cats)
        self.right_pane.pack(side="right", fill="both", expand=True, padx=(5, 5), pady=5)

        # Cat Header
        self.cat_header = ctk.CTkFrame(self.right_pane, height=45, fg_color="#1e293b")
        self.cat_header.pack(fill="x", padx=10, pady=5)

        self.lbl_cat_title = ctk.CTkLabel(self.cat_header, text="请从左侧选择一只猫咪进行编辑", font=("Arial", 16, "bold"), text_color="#f8fafc")
        self.lbl_cat_title.pack(side="left", padx=12, pady=8)

        self.lbl_cat_guid = ctk.CTkLabel(self.cat_header, text="", font=("Arial", 11), text_color="#94a3b8")
        self.lbl_cat_guid.pack(side="right", padx=12, pady=8)

        # 1. Empty State Frame (Shown when no cat is selected)
        self.empty_state_frame = ctk.CTkFrame(self.right_pane, fg_color="#111827", corner_radius=10)

        center_f = ctk.CTkFrame(self.empty_state_frame, fg_color="transparent")
        center_f.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(center_f, text="🐱", font=("Arial", 56)).pack(pady=(0, 10))
        ctk.CTkLabel(center_f, text="未选择猫咪", font=("Arial", 20, "bold"), text_color="#f8fafc").pack(pady=(0, 8))
        ctk.CTkLabel(
            center_f, 
            text="👈 请从左侧列表中点击选择一只猫咪开始查看与编辑其属性\n或点击左下方「+ 新建猫咪」生成全新定制猫咪", 
            font=("Arial", 13), 
            text_color="#94a3b8",
            justify="center"
        ).pack(pady=(0, 22))

        feat_card = ctk.CTkFrame(center_f, fg_color="#1e293b", corner_radius=10)
        feat_card.pack(padx=20, pady=5)
        
        features = [
            ("🧬 15 物理部位基因突变", "10 部位类型，眼/耳/眉/臂/腿左右独立可调，支持不对称变异与部位缺失"),
            ("⚔️ 7+7 战斗属性", "遗传底数(Base 1~7) + 后天加成(Bonus 0~7) + 突变实时计算，支持解锁99"),
            ("🌟 技能被动与疾病", "4 主动法术 + 4 附魔进阶 + 2 职业专属被动 + 125 种疾病一键净除/特化搭配"),
            ("🏠 房间调配与繁衍", "一层大厅/侧卧/阁楼/谱系自由调配，支持改名、性取向与繁衍欲望")
        ]
        for title, desc in features:
            row = ctk.CTkFrame(feat_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=7)
            ctk.CTkLabel(row, text=title, font=("Arial", 12, "bold"), text_color="#38bdf8", width=155, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=desc, font=("Arial", 12), text_color="#cbd5e1", anchor="w").pack(side="left", padx=5)

        # 2. Tabview (Constructed and ready, but packed only when a cat is selected)
        self.tabview = ctk.CTkTabview(self.right_pane)

        self.tab_stats = self.tabview.add("战斗与7+7属性 (Stats)")
        self.tab_mutations = self.tabview.add("🧬 身体与基因突变 (Mutations)")
        self.tab_breeding = self.tabview.add("生理繁衍与生活 (Breeding & Life)")
        self.tab_abilities = self.tabview.add("技能与外观 (Abilities)")

        self.build_stats_tab()
        self.build_mutations_tab()
        self.build_breeding_tab()
        self.build_abilities_tab()

        # Initial view: show empty state, hide tabview
        self.show_empty_state()

    def show_empty_state(self):
        self.current_cat = None
        self.lbl_cat_title.configure(text="请从左侧选择一只猫咪进行编辑")
        self.lbl_cat_guid.configure(text="")
        if hasattr(self, 'cat_cards'):
            for k, btn in self.cat_cards.items():
                c = self.save_mgr.cats.get(k)
                btn.configure(fg_color="#143026" if (c and getattr(c, 'is_in_house', False)) else "#1e293b")
        if hasattr(self, 'tabview'):
            self.tabview.pack_forget()
        if hasattr(self, 'empty_state_frame'):
            self.empty_state_frame.pack(fill="both", expand=True, padx=10, pady=5)

    def build_stats_tab(self):
        # Quick Presets Header
        preset_frame = ctk.CTkFrame(self.tab_stats, fg_color="#0f172a")
        preset_frame.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(preset_frame, text="属性预设:", font=("Arial", 12, "bold"), text_color="#38bdf8").pack(side="left", padx=(10, 4), pady=6)
        
        ctk.CTkButton(preset_frame, text="纯种满遗传(全7)", width=105, height=26, fg_color="#059669", hover_color="#047857", command=lambda: self.apply_stat_preset(7, 0)).pack(side="left", padx=3)
        ctk.CTkButton(preset_frame, text="极品战神(7+7)", width=95, height=26, fg_color="#2563eb", hover_color="#1d4ed8", command=lambda: self.apply_stat_preset(7, 7)).pack(side="left", padx=3)
        ctk.CTkButton(preset_frame, text="偏科狂战(力体7+7)", width=120, height=26, fg_color="#dc2626", hover_color="#b91c1c", command=lambda: self.apply_special_preset("str_con")).pack(side="left", padx=3)
        ctk.CTkButton(preset_frame, text="偏科法师(智敏7+7)", width=120, height=26, fg_color="#7c3aed", hover_color="#6d28d9", command=lambda: self.apply_special_preset("int_dex")).pack(side="left", padx=3)

        # Unlock switch
        self.var_unlock_limits = tk.BooleanVar(value=False)
        self.chk_unlock = ctk.CTkCheckBox(
            preset_frame,
            text="解除安全限制 (自由模式 0~99)",
            variable=self.var_unlock_limits,
            font=("Arial", 11, "bold"),
            text_color="#f59e0b",
            fg_color="#f59e0b",
            hover_color="#d97706",
            command=self.on_toggle_safe_limits
        )
        self.chk_unlock.pack(side="right", padx=10)

        # Tip banner
        tip_frame = ctk.CTkFrame(self.tab_stats, fg_color="#1e293b", corner_radius=6)
        tip_frame.pack(fill="x", padx=10, pady=(0, 6))
        tip_text = "💡 [游戏机制] 最终实效 = 遗传基础(Base 1~7) + 突变修正(Mutations +/-) + 后天加成(Bonus 0~7)"
        ctk.CTkLabel(tip_frame, text=tip_text, font=("Arial", 11), text_color="#94a3b8").pack(padx=10, pady=5)

        # Stats Grid
        self.stat_sliders = {}
        self.stat_labels = {}
        self.mut_mod_labels = {}
        self.bonus_sliders = {}
        self.bonus_labels = {}
        self.total_labels = {}

        grid_frame = ctk.CTkFrame(self.tab_stats, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=10, pady=2)

        names_cn = {
            'str': '力量 (STR / Strength)',
            'dex': '敏捷 (DEX / Dexterity)',
            'con': '体质 (CON / Constitution)',
            'int': '智力 (INT / Intelligence)',
            'spd': '速度 (SPD / Speed)',
            'cha': '魅力 (CHA / Charisma)',
            'lck': '幸运 (LCK / Luck)'
        }

        for i, k in enumerate(CatRecord.STAT_NAMES):
            row = ctk.CTkFrame(grid_frame)
            row.pack(fill="x", pady=3)

            # Name Label
            lbl = ctk.CTkLabel(row, text=names_cn[k], width=155, anchor="w", font=("Arial", 12, "bold"))
            lbl.pack(side="left", padx=6)

            # Base Stat Tag
            ctk.CTkLabel(row, text="遗传:", font=("Arial", 11), text_color="#38bdf8").pack(side="left", padx=(4, 2))

            # Base Slider (default 1~7)
            slider = ctk.CTkSlider(row, from_=1, to=7, number_of_steps=6, width=130, progress_color="#0284c7", command=lambda v, key=k: self.on_stat_slide(key, v))
            slider.pack(side="left", padx=3)
            self.stat_sliders[k] = slider

            # Base Value Display
            val_lbl = ctk.CTkLabel(row, text="7", width=22, font=("Arial", 13, "bold"), text_color="#38bdf8")
            val_lbl.pack(side="left", padx=2)
            self.stat_labels[k] = val_lbl

            # Mutation Stat Modifier Badge
            mut_lbl = ctk.CTkLabel(row, text="[突变: 0]", width=70, font=("Arial", 11, "bold"), text_color="#64748b")
            mut_lbl.pack(side="left", padx=4)
            self.mut_mod_labels[k] = mut_lbl

            # Bonus Stat Tag
            ctk.CTkLabel(row, text="+加成:", font=("Arial", 11), text_color="#10b981").pack(side="left", padx=(6, 2))

            # Bonus Slider (default 0~7)
            b_slider = ctk.CTkSlider(row, from_=0, to=7, number_of_steps=7, width=110, fg_color="#334155", progress_color="#10b981", command=lambda v, key=k: self.on_bonus_slide(key, v))
            b_slider.pack(side="left", padx=3)
            self.bonus_sliders[k] = b_slider

            # Bonus Value Display
            b_val_lbl = ctk.CTkLabel(row, text="+0", width=25, font=("Arial", 13, "bold"), text_color="#10b981")
            b_val_lbl.pack(side="left", padx=2)
            self.bonus_labels[k] = b_val_lbl

            # Total Effective Badge
            tot_lbl = ctk.CTkLabel(row, text="[实效: 7]", width=85, font=("Arial", 12, "bold"), text_color="#fbbf24")
            tot_lbl.pack(side="left", padx=(6, 4))
            self.total_labels[k] = tot_lbl

    def build_mutations_tab(self):
        container = ctk.CTkScrollableFrame(self.tab_mutations)
        container.pack(fill="both", expand=True, padx=10, pady=5)

        # 1. Quick Presets Header + 计数摘要（与游戏内徽章一致）
        preset_frame = ctk.CTkFrame(container, fg_color="#0f172a", corner_radius=8)
        preset_frame.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(preset_frame, text="突变预设:", font=("Arial", 12, "bold"), text_color="#a855f7").pack(side="left", padx=(12, 6), pady=6)
        ctk.CTkButton(preset_frame, text="✨ 一键极品正面突变全满", width=170, height=26, fg_color="#7c3aed", hover_color="#6d28d9", command=self.on_apply_god_mutations).pack(side="left", padx=4)
        ctk.CTkButton(preset_frame, text="🧼 一键清除全部突变 (纯血统)", width=170, height=26, fg_color="#334155", hover_color="#475569", command=self.on_clear_all_mutations).pack(side="left", padx=4)

        self.lbl_mutation_summary = ctk.CTkLabel(preset_frame, text="", font=("Arial", 11, "bold"), text_color="#4ade80")
        self.lbl_mutation_summary.pack(side="right", padx=12)

        # Tip Banner
        tip_frame = ctk.CTkFrame(container, fg_color="#1e293b", corner_radius=6)
        tip_frame.pack(fill="x", padx=10, pady=(0, 6))
        tip_text = ("💡 [真实机制·逆向验证] 猫有 15 个物理部位槽：眼/耳/眉/臂/腿 5 个成对部位左右独立（可为不同变异）。"
                    "局内事件可打出不对称变异（上限15）；繁殖时左右统一，后代最多 10 种变异。"
                    "游戏内 >10 个变异时会关闭详情悬浮列表（只显示计数徽章），此处始终完整显示。")
        ctk.CTkLabel(tip_frame, text=tip_text, font=("Arial", 11), text_color="#94a3b8", wraplength=1020, justify="left").pack(padx=10, pady=5)

        # 2. 10 Mutation Cards (Left + Right physical parts)
        mut_detailed = self.game_data.get('mutations_detailed', {})
        self.mutation_combos = {}
        self.right_combos = {}
        self.mutation_badge_labels = {}

        slot_display_names = {
            'body': '身体 (Body)',
            'eyebrows': '眉毛 (Eyebrows)',
            'head': '头部 (Head)',
            'ears': '耳部 (Ears)',
            'tail': '尾部 (Tail)',
            'mouth': '嘴部 (Mouth)',
            'legs': '腿部 (Legs)',
            'texture': '毛皮 (Fur)',
            'arms': '手臂 (Arms)',
            'eyes': '眼部 (Eyes)'
        }

        f_grid = ctk.CTkFrame(container, fg_color="#1e293b", corner_radius=8)
        f_grid.pack(fill="x", padx=10, pady=6)

        for slot_key, slot_cn, off1, off2 in MUTATION_SLOTS:
            row = ctk.CTkFrame(f_grid, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=4)

            title = slot_display_names.get(slot_key, f"{slot_cn} ({slot_key})")
            ctk.CTkLabel(row, text=f"{title}:", width=105, anchor="w", font=("Arial", 12, "bold"), text_color="#f8fafc").pack(side="left", padx=(2, 4))

            slot_entries = mut_detailed.get(slot_key, [])

            # 左侧部件（图标按钮，点击打开图标选择器）
            lbl_left = "左侧:" if off2 else "部件:"
            ctk.CTkLabel(row, text=lbl_left, font=("Arial", 11, "bold"), text_color="#38bdf8").pack(side="left", padx=(2, 2))
            cb = ctk.CTkButton(
                row,
                width=245, height=34, font=("Arial", 11),
                fg_color="#0f172a", hover_color="#334155", anchor="w",
                text="无突变 (普通外观 / Pure)",
                command=lambda sk=slot_key: self.open_mutation_picker(sk, 'left')
            )
            cb.pack(side="left", padx=3)
            self.mutation_combos[slot_key] = cb

            if off2:
                # 右侧部件（可与左侧不同 = 局内 asymmetric 变异）
                ctk.CTkLabel(row, text="右侧:", font=("Arial", 11, "bold"), text_color="#c084fc").pack(side="left", padx=(6, 2))
                cb_right = ctk.CTkButton(
                    row,
                    width=245, height=34, font=("Arial", 11),
                    fg_color="#0f172a", hover_color="#334155", anchor="w",
                    text="无突变 (普通外观 / Pure)",
                    command=lambda sk=slot_key: self.open_mutation_picker(sk, 'right')
                )
                cb_right.pack(side="left", padx=3)
                self.right_combos[slot_key] = cb_right

                badge = ctk.CTkLabel(row, text="[对称]", font=("Arial", 11, "bold"), text_color="#10b981", width=85, anchor="w")
                badge.pack(side="left", padx=5)
                self.mutation_badge_labels[slot_key] = badge
            else:
                badge = ctk.CTkLabel(row, text="[单部件]", font=("Arial", 11), text_color="#64748b", width=85, anchor="w")
                badge.pack(side="left", padx=5)
                self.mutation_badge_labels[slot_key] = badge

    def build_breeding_tab(self):
        container = ctk.CTkScrollableFrame(self.tab_breeding)
        container.pack(fill="both", expand=True, padx=10, pady=5)

        # 1. 生活与繁衍属性 (Living & Breeding Section)
        f_breed = ctk.CTkFrame(container, fg_color="#1e293b", corner_radius=8)
        f_breed.pack(fill="x", padx=10, pady=6)
        
        ctk.CTkLabel(f_breed, text="🏠 生活环境与繁衍属性 (Living, Room & Breeding)", font=("Arial", 13, "bold"), text_color="#38bdf8").pack(anchor="w", padx=15, pady=(10, 8))

        # Room selection
        f_room = ctk.CTkFrame(f_breed, fg_color="transparent")
        f_room.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(f_room, text="所在房间 (Room):", width=140, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.combo_room = ctk.CTkComboBox(f_room, width=280, values=[
            'Floor1_Large (一层大厅)',
            'Floor1_Small (一层侧卧)',
            'Attic (阁楼)',
            '移出家园 (转入历史谱系)'
        ])
        self.combo_room.pack(side="left", padx=5)
        ctk.CTkLabel(f_room, text="*可直接将历史谱系猫召回家园或移出家园", font=("Arial", 10), text_color="#94a3b8").pack(side="left", padx=8)

        # Sexuality (性取向)
        f_sex = ctk.CTkFrame(f_breed, fg_color="transparent")
        f_sex.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(f_sex, text="性取向 (Sexuality):", width=140, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.combo_sexuality = ctk.CTkComboBox(f_sex, width=280, values=[
            "Straight (异性恋)",
            "Bisexual (双性恋)",
            "Gay (同性恋)"
        ])
        self.combo_sexuality.pack(side="left", padx=5)
        ctk.CTkLabel(f_sex, text="*影响同居繁殖配对逻辑 (0.0=异, <0.33=双, >=0.33=同)", font=("Arial", 10), text_color="#94a3b8").pack(side="left", padx=8)

        # Libido (繁衍欲望)
        f_lib = ctk.CTkFrame(f_breed, fg_color="transparent")
        f_lib.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(f_lib, text="繁衍欲望 (Libido):", width=140, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.combo_libido = ctk.CTkComboBox(f_lib, width=280, values=[
            "Low (冷淡)",
            "Mid (正常)",
            "High (旺盛)"
        ])
        self.combo_libido.pack(side="left", padx=5)

        # Aggression (性格攻击性)
        f_agg = ctk.CTkFrame(f_breed, fg_color="transparent")
        f_agg.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(f_agg, text="性格偏向 (Aggression):", width=140, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.combo_aggression = ctk.CTkComboBox(f_agg, width=280, values=[
            "Low (温顺友好)",
            "Mid (适中平衡)",
            "High (暴躁攻击)"
        ])
        self.combo_aggression.pack(side="left", padx=5)

        # Inbred level (近亲繁殖度)
        f_inb = ctk.CTkFrame(f_breed, fg_color="transparent")
        f_inb.pack(fill="x", padx=15, pady=(4, 12))
        ctk.CTkLabel(f_inb, text="近亲系数 (Inbred):", width=140, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.combo_inbred = ctk.CTkComboBox(f_inb, width=280, values=[
            "0% (纯净血统)",
            "25% (轻度近亲)",
            "50% (中度近亲)",
            "75% (重度近亲)"
        ])
        self.combo_inbred.pack(side="left", padx=5)

        # 2. 身份与外貌声音 (Identity & Voice Section)
        f_ident = ctk.CTkFrame(container, fg_color="#1e293b", corner_radius=8)
        f_ident.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(f_ident, text="🐱 身份与声音外貌 (Identity, Appearance & Voice)", font=("Arial", 13, "bold"), text_color="#10b981").pack(anchor="w", padx=15, pady=(10, 8))

        # Name
        f_name = ctk.CTkFrame(f_ident, fg_color="transparent")
        f_name.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(f_name, text="猫咪名称 (Name):", width=140, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.entry_name = ctk.CTkEntry(f_name, width=280)
        self.entry_name.pack(side="left", padx=5)
        ctk.CTkLabel(f_name, text="*UTF-16LE编码，支持中英文", font=("Arial", 10), text_color="#94a3b8").pack(side="left", padx=8)

        # Class
        f_class = ctk.CTkFrame(f_ident, fg_color="transparent")
        f_class.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(f_class, text="职业 (Class):", width=140, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.combo_class = ctk.CTkComboBox(f_class, width=280,
                                           values=[self._class_to_label(c) for c in self.game_data.get('classes', [])],
                                           command=self.on_class_changed)
        self.combo_class.pack(side="left", padx=5)

        # Voice / Gender
        f_voice = ctk.CTkFrame(f_ident, fg_color="transparent")
        f_voice.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(f_voice, text="声音/性别 (Voice):", width=140, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.combo_voice = ctk.CTkComboBox(f_voice, width=280, values=self.game_data.get('voices', ['male55', 'female50']))
        self.combo_voice.pack(side="left", padx=5)

        # Pitch
        f_pitch = ctk.CTkFrame(f_ident, fg_color="transparent")
        f_pitch.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(f_pitch, text="声音音调 (Pitch):", width=140, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.slider_pitch = ctk.CTkSlider(f_pitch, from_=0.2, to=2.5, width=220, command=self.on_pitch_slide)
        self.slider_pitch.pack(side="left", padx=5)
        self.lbl_pitch_val = ctk.CTkLabel(f_pitch, text="1.00", width=45)
        self.lbl_pitch_val.pack(side="left", padx=3)

        # 3. 出生天赋标记 (Boon) —— 独立栏：疑似废弃机制，仅作展示/收藏
        f_boon_sec = ctk.CTkFrame(container, fg_color="#29221e", corner_radius=8)
        f_boon_sec.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(f_boon_sec, text="🎲 出生天赋标记 (Boon) - ⚠️ 疑似废弃机制", font=("Arial", 13, "bold"), text_color="#f59e0b").pack(anchor="w", padx=15, pady=(10, 4))

        f_boon = ctk.CTkFrame(f_boon_sec, fg_color="transparent")
        f_boon.pack(fill="x", padx=15, pady=(2, 4))
        ctk.CTkLabel(f_boon, text="偏好属性 (Boon):", width=140, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.combo_boon = ctk.CTkComboBox(f_boon, width=280, values=['none', 'str', 'dex', 'con', 'int', 'spd', 'cha', 'lck'])
        self.combo_boon.pack(side="left", padx=5)

        ctk.CTkLabel(f_boon_sec, text="⚠️ 出生时的随机天赋标记：不遗传、不影响升级属性成长，游戏内无明显实际效果（逆向分析判定为疑似废弃机制）。修改它仅改变存档记录，不会让猫变得更强。",
                     font=("Arial", 11), text_color="#94a3b8", wraplength=1000, justify="left").pack(anchor="w", padx=15, pady=(0, 10))

    def build_abilities_tab(self):
        container = ctk.CTkScrollableFrame(self.tab_abilities)
        container.pack(fill="both", expand=True, padx=10, pady=5)

        ab_names = sorted(list(set([a['key'] for a in self.game_data.get('abilities', [])]))) or ['BasicMelee', 'DefaultMove']

        # 1. Basic Attack & Move
        f_base = ctk.CTkFrame(container, fg_color="#1e293b", corner_radius=8)
        f_base.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(f_base, text="⚔️ 基础行动与普通攻击 (Basic Moves & Attack)", font=("Arial", 13, "bold"), text_color="#38bdf8").pack(anchor="w", padx=15, pady=(8, 4))

        f_atk = ctk.CTkFrame(f_base, fg_color="transparent")
        f_atk.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(f_atk, text="普通攻击 (Basic Attack):", width=180, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.combo_atk = SkillCardWidget(
            f_atk,
            catalog_type="ability",
            width=340,
            height=48,
            command=lambda v: self.save_current_cat_fields() if self.current_cat else None,
            get_current_class_func=lambda: getattr(self.current_cat, 'cat_class', 'Colorless') if self.current_cat else None
        )
        self.combo_atk.pack(side="left", padx=5)

        f_mov = ctk.CTkFrame(f_base, fg_color="transparent")
        f_mov.pack(fill="x", padx=15, pady=(3, 8))
        ctk.CTkLabel(f_mov, text="移动方式 (Move Ability):", width=180, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.combo_move = SkillCardWidget(
            f_mov,
            catalog_type="ability",
            width=340,
            height=48,
            command=lambda v: self.save_current_cat_fields() if self.current_cat else None,
            get_current_class_func=lambda: getattr(self.current_cat, 'cat_class', 'Colorless') if self.current_cat else None
        )
        self.combo_move.pack(side="left", padx=5)

        # 2. 4 Active Abilities + 4 Innate Genetic Abilities (Double-Line Mini-Cards)
        f_acts = ctk.CTkFrame(container, fg_color="#1e293b", corner_radius=8)
        f_acts.pack(fill="x", padx=10, pady=6)
        
        f_act_head = ctk.CTkFrame(f_acts, fg_color="transparent")
        f_act_head.pack(fill="x", padx=15, pady=(10, 4))
        
        f_head_left = ctk.CTkFrame(f_act_head, fg_color="transparent")
        f_head_left.pack(side="left")
        ctk.CTkLabel(f_head_left, text="🔮 战斗法术与先天遗传底表 (Active Spells & Innate Genetic Abilities):", font=("Arial", 13, "bold"), text_color="#a855f7").pack(anchor="w")
        ctk.CTkLabel(f_head_left, text="💡 战斗仅执行【战斗法术】；配种繁育时，后代从【遗传底表】中抽取继承技能", font=("Arial", 11), text_color="#94a3b8").pack(anchor="w", pady=(2, 0))

        f_head_right = ctk.CTkFrame(f_act_head, fg_color="transparent")
        f_head_right.pack(side="right", padx=5)
        ctk.CTkButton(f_head_right, text="🔄 全槽位与基础技能同步", height=26, font=("Arial", 11), fg_color="#0284c7", hover_color="#0369a1", command=self.sync_all_innate_to_combat).pack(side="right", padx=3)
        ctk.CTkButton(f_head_right, text="✨ 一键神级育种基因", height=26, font=("Arial", 11), fg_color="#8b5cf6", hover_color="#7c3aed", command=self.apply_god_innate_preset).pack(side="right", padx=3)

        self.active_combos = []
        self.upgrade_checkboxes = []
        self.innate_combos = []
        self.innate_lock_btns = []
        self.innate_locked = [True, True, True, True]
        self.upgrade_combos = self.innate_combos

        for i in range(4):
            # Mini-Card container
            f_card = ctk.CTkFrame(f_acts, fg_color="#182234", corner_radius=6)
            f_card.pack(fill="x", padx=15, pady=4)

            # Row 1: Combat active spell + Tier 2 upgrade checkbox
            f_r1 = ctk.CTkFrame(f_card, fg_color="transparent")
            f_r1.pack(fill="x", padx=12, pady=(6, 2))

            ctk.CTkLabel(f_r1, text=f"⚔️ 战斗法术 {i+1}:", width=95, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
            cb_act = SkillCardWidget(
                f_r1,
                catalog_type="ability",
                width=280,
                height=48,
                command=lambda val, idx=i: self.on_active_spell_changed(idx, val),
                get_current_class_func=lambda: getattr(self.current_cat, 'cat_class', 'Colorless') if self.current_cat else None
            )
            cb_act.pack(side="left", padx=(0, 15))
            self.active_combos.append(cb_act)

            chk_upg = ctk.CTkCheckBox(f_r1, text="进阶强化 (未选择法术)", font=("Arial", 12), text_color="#64748b", fg_color="#a855f7", hover_color="#9333ea", command=lambda idx=i: self.on_upgrade_checkbox_toggled(idx))
            chk_upg.pack(side="left", padx=(0, 10))
            chk_upg.configure(state="disabled")
            self.upgrade_checkboxes.append(chk_upg)

            # Row 2: Innate genetic abilities base table
            f_r2 = ctk.CTkFrame(f_card, fg_color="transparent")
            f_r2.pack(fill="x", padx=12, pady=(2, 6))

            ctk.CTkLabel(f_r2, text=f"🧬 遗传底表 {i+1}:", width=95, anchor="w", font=("Arial", 12), text_color="#38bdf8").pack(side="left")
            cb_innate = SkillCardWidget(
                f_r2,
                catalog_type="ability",
                width=280,
                height=48,
                command=lambda val, idx=i: self.on_innate_changed(idx, val),
                get_current_class_func=lambda: getattr(self.current_cat, 'cat_class', 'Colorless') if self.current_cat else None
            )
            cb_innate.set('None')
            cb_innate.pack(side="left", padx=(0, 15))
            self.innate_combos.append(cb_innate)

            btn_lock = ctk.CTkButton(f_r2, text="🔒 默认与基础技能同步", width=195, height=24, font=("Arial", 11), fg_color="#334155", hover_color="#475569", command=lambda idx=i: self.toggle_innate_lock(idx))
            btn_lock.pack(side="left", padx=(0, 10))
            self.innate_lock_btns.append(btn_lock)

            ctk.CTkLabel(f_r2, text="[繁育遗传基因池]", font=("Arial", 11), text_color="#64748b").pack(side="left")

        # 3. 2 Class Passives (正面职业被动)
        f_cp = ctk.CTkFrame(container, fg_color="#1e293b", corner_radius=8)
        f_cp.pack(fill="x", padx=10, pady=6)

        f_cp_head = ctk.CTkFrame(f_cp, fg_color="transparent")
        f_cp_head.pack(fill="x", padx=15, pady=(8, 4))
        ctk.CTkLabel(f_cp_head, text="🌟 职业正面被动特性 (Class Passives - 2 Slots):", font=("Arial", 13, "bold"), text_color="#10b981").pack(side="left")
        ctk.CTkButton(f_cp_head, text="✨ 自动满配本职业极品被动", height=26, fg_color="#059669", hover_color="#047857", command=self.on_apply_best_class_passives).pack(side="right")

        self.class_passive_combos = []
        for i in range(2):
            f_row = ctk.CTkFrame(f_cp, fg_color="transparent")
            f_row.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(f_row, text=f"职业被动 {i+1}:", width=100, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
            cb = SkillCardWidget(
                f_row,
                catalog_type="passive",
                width=580,
                height=48,
                command=lambda val, idx=i: self.on_class_passive_changed(idx, val)
            )
            cb.pack(side="left", padx=5)
            self.class_passive_combos.append(cb)

        # 4. 2 Disorders / Negative Passives (疾病/心理缺陷)
        f_dis = ctk.CTkFrame(container, fg_color="#1e293b", corner_radius=8)
        f_dis.pack(fill="x", padx=10, pady=(6, 12))

        f_dis_head = ctk.CTkFrame(f_dis, fg_color="transparent")
        f_dis_head.pack(fill="x", padx=15, pady=(8, 4))
        ctk.CTkLabel(f_dis_head, text="🦠 生理与心理疾病缺陷 (Disorders - 2 Slots):", font=("Arial", 13, "bold"), text_color="#f87171").pack(side="left")
        
        ctk.CTkButton(f_dis_head, text="✨ 搭配特化变异疾病", height=26, fg_color="#8b5cf6", hover_color="#7c3aed", command=self.on_apply_synergistic_disorders).pack(side="right", padx=5)
        ctk.CTkButton(f_dis_head, text="🧼 一键祛除全部疾病 (健康)", height=26, fg_color="#10b981", hover_color="#059669", command=self.on_cure_all_disorders).pack(side="right")

        self.disorder_combos = []
        self.init_disorder_options()

        for i in range(2):
            f_row = ctk.CTkFrame(f_dis, fg_color="transparent")
            f_row.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(f_row, text=f"疾病槽位 {i+1}:", width=100, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
            cb = SkillCardWidget(
                f_row,
                catalog_type="disorder",
                width=580,
                height=48,
                command=lambda val, idx=i: self.on_disorder_changed(idx, val)
            )
            cb.pack(side="left", padx=5)
            self.disorder_combos.append(cb)

        # Compatibility alias
        self.passive_combos = self.upgrade_combos + self.class_passive_combos + self.disorder_combos

    def on_disorder_changed(self, idx, val):
        if self.current_cat:
            self.save_current_cat_fields()

    def on_active_spell_changed(self, idx, val):
        val = val.strip()
        chk = self.upgrade_checkboxes[idx]
        if val == 'None':
            chk.deselect()
            chk.configure(state="disabled", text="进阶强化 (未选择法术)", text_color="#64748b")
            if self.innate_locked[idx]:
                self.innate_combos[idx].configure(state="normal")
                self.innate_combos[idx].set('None')
                self.innate_combos[idx].configure(state="disabled")
        else:
            upg_target = get_ability_upgrade(val)
            chk.configure(state="normal", text=f"✨ 进阶强化 (Tier 2: {upg_target})", text_color="#e2e8f0")
            if self.innate_locked[idx]:
                self.innate_combos[idx].configure(state="normal")
                self.innate_combos[idx].set(val)
                self.innate_combos[idx].configure(state="disabled")
        if self.current_cat:
            self.save_current_cat_fields()

    def on_upgrade_checkbox_toggled(self, idx):
        if self.current_cat:
            self.save_current_cat_fields()

    def on_innate_changed(self, idx, val):
        if self.current_cat:
            self.save_current_cat_fields()

    def on_class_passive_changed(self, idx, val):
        if self.current_cat:
            self.save_current_cat_fields()
            self.status_bar.configure(text=f"已更新猫咪 #{self.current_cat.key} 的职业被动 {idx+1} 为: {val}", text_color="#10b981")

    def toggle_innate_lock(self, idx):
        self.innate_locked[idx] = not self.innate_locked[idx]
        if self.innate_locked[idx]:
            combat_base = get_base_ability(self.active_combos[idx].get())
            self.innate_combos[idx].configure(state="normal")
            self.innate_combos[idx].set(combat_base)
        self.update_innate_lock_ui(idx)
        if self.current_cat:
            self.save_current_cat_fields()

    def update_innate_lock_ui(self, idx):
        is_locked = self.innate_locked[idx]
        btn = self.innate_lock_btns[idx]
        cb = self.innate_combos[idx]
        if is_locked:
            btn.configure(text="🔒 默认与基础技能同步", fg_color="#334155", hover_color="#475569")
            cb.configure(state="disabled")
        else:
            btn.configure(text="🔓 已解锁: 自由定制后代遗传", fg_color="#6366f1", hover_color="#4f46e5")
            cb.configure(state="normal")

    def sync_all_innate_to_combat(self):
        for i in range(4):
            self.innate_locked[i] = True
            combat_base = get_base_ability(self.active_combos[i].get())
            self.innate_combos[i].configure(state="normal")
            self.innate_combos[i].set(combat_base)
            self.update_innate_lock_ui(i)
        if self.current_cat:
            self.save_current_cat_fields()
        self.status_bar.configure(text="已将全部 4 个遗传底表槽位与当前战斗技能基础形态重置同步", text_color="#38bdf8")

    def apply_god_innate_preset(self):
        god_genes = ['DivineProtection', 'HolyLight', 'CircleOfProtection', 'MeteorStorm']
        for i in range(4):
            self.innate_locked[i] = False
            self.innate_combos[i].configure(state="normal")
            self.innate_combos[i].set(god_genes[i])
            self.update_innate_lock_ui(i)
        if self.current_cat:
            self.save_current_cat_fields()
        self.status_bar.configure(text="已一键为猫咪装配神级繁育基因库 [神圣守护/神圣之光/守护之圈/流星风暴]，后代将以此为基因模板！", text_color="#10b981")

    def init_disorder_options(self):
        self.disorder_lookup = {}
        self.disorder_key_to_str = {}
        self.disorder_display_list = ["None (无疾病 - 身体健康)"]
        self.disorder_lookup["None (无疾病 - 身体健康)"] = "None"
        self.disorder_lookup["None"] = "None"
        self.disorder_key_to_str["None"] = "None (无疾病 - 身体健康)"

        disorders = self.game_data.get('disorders', [])
        for d in disorders:
            k = d['key']
            name = d.get('name', k)
            raw_desc = d.get('desc', '').strip('"\r\n\t ')
            clean_desc = raw_desc.replace('\r', ' ').replace('\n', ' ')
            if len(clean_desc) > 35:
                clean_desc = clean_desc[:35] + "..."
            disp = f"{name} ({k}) - {clean_desc}" if clean_desc else f"{name} ({k})"
            self.disorder_display_list.append(disp)
            self.disorder_lookup[disp] = k
            self.disorder_lookup[k] = k
            self.disorder_key_to_str[k] = disp

    def update_class_passive_options(self, cat_class):
        self.class_passive_lookup = {}
        self.class_passive_key_to_str = {}
        
        none_str = "None (无被动)"
        display_list = [none_str]
        self.class_passive_lookup[none_str] = "None"
        self.class_passive_lookup["None"] = "None"
        self.class_passive_key_to_str["None"] = none_str

        all_cp = self.game_data.get('class_passives', {})
        # Put current class passives first with special indicator
        current_list = all_cp.get(cat_class, [])
        for p in current_list:
            k = p['key']
            name = p.get('name', k)
            raw_desc = p.get('desc', '').strip('"\r\n\t ')
            clean_desc = raw_desc.replace('\r', ' ').replace('\n', ' ')
            if len(clean_desc) > 32:
                clean_desc = clean_desc[:32] + "..."
            disp = f"★ [{self._class_zh(cat_class)}] {name} ({k}) - {clean_desc}"
            display_list.append(disp)
            self.class_passive_lookup[disp] = k
            self.class_passive_lookup[k] = k
            self.class_passive_key_to_str[k] = disp

        # Then passives from other classes
        for other_cls, o_list in all_cp.items():
            if other_cls == cat_class:
                continue
            for p in o_list:
                k = p['key']
                if k in self.class_passive_key_to_str:
                    continue
                name = p.get('name', k)
                raw_desc = p.get('desc', '').strip('"\r\n\t ')
                clean_desc = raw_desc.replace('\r', ' ').replace('\n', ' ')
                if len(clean_desc) > 30:
                    clean_desc = clean_desc[:30] + "..."
                disp = f"[{other_cls}] {name} ({k}) - {clean_desc}"
                display_list.append(disp)
                self.class_passive_lookup[disp] = k
                self.class_passive_lookup[k] = k
                self.class_passive_key_to_str[k] = disp

        for cb in self.class_passive_combos:
            cb.configure(values=display_list)

    def get_class_passive_key_from_val(self, val):
        if not val or val.startswith("None"):
            return "None"
        if val in self.class_passive_lookup:
            return self.class_passive_lookup[val]
        m = re.search(r'\(([^)]+)\)', val)
        if m:
            return m.group(1).strip()
        return val.strip()

    def get_disorder_key_from_val(self, val):
        if not val or val.startswith("None"):
            return "None"
        if val in self.disorder_lookup:
            return self.disorder_lookup[val]
        m = re.search(r'\(([^)]+)\)', val)
        if m:
            return m.group(1).strip()
        return val.strip()

    def on_cure_all_disorders(self):
        if not self.current_cat:
            return
        self.current_cat.cure_all_disorders()
        none_disp = self.disorder_key_to_str.get('None', 'None (无疾病 - 身体健康)')
        for cb in self.disorder_combos:
            cb.set(none_disp)
        self.status_bar.configure(text=f"已一键清除猫咪 #{self.current_cat.key} ({self.current_cat.name}) 的所有疾病缺陷，完全恢复健康！", text_color="#10b981")

    def on_apply_synergistic_disorders(self):
        if not self.current_cat:
            return
        self.current_cat.apply_synergistic_disorders()
        for i in range(2):
            k = self.current_cat.disorders[i]
            disp = self.disorder_key_to_str.get(k, k)
            self.disorder_combos[i].set(disp)
        self.status_bar.configure(text=f"已为猫咪 #{self.current_cat.key} ({self.current_cat.name}) 智能搭配适合 [{self.current_cat.cat_class}] 的特化变异疾病！", text_color="#a855f7")

    def on_apply_best_class_passives(self):
        if not self.current_cat:
            return
        self.current_cat.apply_best_class_passives()
        for i in range(2):
            k = self.current_cat.class_passives[i]
            disp = self.class_passive_key_to_str.get(k, k)
            self.class_passive_combos[i].set(disp)
        self.status_bar.configure(text=f"已为猫咪 #{self.current_cat.key} ({self.current_cat.name}) 自动满配 [{self.current_cat.cat_class}] 的顶级正面被动特性！", text_color="#10b981")

    def on_class_changed(self, new_class):
        cls = self._label_to_class(new_class)  # 下拉显示为官方中文，内部始终保存代码
        if self.current_cat:
            self.current_cat.cat_class = cls
        self.update_class_passive_options(cls)

    def populate_cat_list(self, filter_text=""):
        # Clear existing buttons
        for w in self.cat_list_frame.winfo_children():
            w.destroy()
        self.cat_cards.clear()

        # Update button counts in filter tabs
        n_house = len(getattr(self.save_mgr, 'house_cat_ids', set()))
        n_total = len(self.save_mgr.cats)
        if hasattr(self, 'btn_flt_house'):
            self.btn_flt_house.configure(text=f"🏠 家园 ({n_house})")
            self.btn_flt_all.configure(text=f"全部 ({n_total})")
            self.btn_flt_hist.configure(text=f"📜 谱系 ({max(0, n_total - n_house)})")

        # Sort cats by key descending (newest on top)
        sorted_keys = sorted(self.save_mgr.cats.keys(), reverse=True)
        count = 0
        ft = filter_text.lower() if filter_text else ""

        for k in sorted_keys:
            cat = self.save_mgr.cats[k]
            is_in_house = getattr(cat, 'is_in_house', False)
            room_str = getattr(cat, 'house_room', '')

            # 1. Mode filter
            if self.filter_mode == "house" and not is_in_house:
                continue
            elif self.filter_mode == "history" and is_in_house:
                continue

            # 2. Search filter（支持中文职业名/房间名）
            if ft:
                match_pool = [cat.name.lower(), str(k), cat.cat_class.lower(), room_str.lower(),
                              self._class_zh(cat.cat_class).lower(), self._room_zh(room_str).lower()]
                if not any(ft in s for s in match_pool):
                    continue

            # Limit display to max 100 items when showing all to guarantee silky smooth performance
            if count >= 100:
                more_lbl = ctk.CTkLabel(
                    self.cat_list_frame, 
                    text="... 还有更多猫咪未列出 (请输入精确名称/ID搜索) ...", 
                    font=("Arial", 11), 
                    text_color="#94a3b8"
                )
                more_lbl.pack(pady=6)
                break

            # Card text & styling（职业/房间显示官方中文）
            cls_disp = self._class_zh(cat.cat_class)
            if is_in_house:
                room_disp = self._room_zh(cat.house_room) if cat.house_room else "在生"
                card_text = f"#{k:3d}  {cat.name:<8} [{cls_disp}] [{room_disp}]"
                btn_fg = "#143026"
                btn_hover = "#1b4d3e"
            else:
                card_text = f"#{k:3d}  {cat.name:<8} [{cls_disp}] [历史]"
                btn_fg = "#1e293b"
                btn_hover = "#334155"

            # Card Button
            is_selected = bool(self.current_cat and self.current_cat.key == k)
            card = ctk.CTkButton(
                self.cat_list_frame,
                text=card_text,
                anchor="w",
                font=("Consolas", 11),
                height=30,
                fg_color="#0284c7" if is_selected else btn_fg,
                hover_color=btn_hover,
                command=lambda key=k: self.select_cat(key)
            )
            card.pack(fill="x", pady=2)
            self.cat_cards[k] = card
            count += 1

        lbl_filter = "家园在生" if self.filter_mode == "house" else ("全部" if self.filter_mode == "all" else "历史谱系")
        self.cat_list_frame.configure(label_text=f"猫咪列表 [{lbl_filter}] (显示: {count} / 总数: {len(self.save_mgr.cats)})")

        # Scroll to top automatically so results are never hidden off-screen!
        try:
            self.cat_list_frame._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    def select_cat(self, key):
        if self.current_cat:
            self.save_current_cat_fields()

        cat = self.save_mgr.cats[key]
        self.current_cat = cat

        # Hide empty state, show tabview
        if hasattr(self, 'empty_state_frame'):
            self.empty_state_frame.pack_forget()
        if hasattr(self, 'tabview'):
            self.tabview.pack(fill="both", expand=True, padx=10, pady=5)

        # Highlight selected card
        for k, btn in self.cat_cards.items():
            if k == key:
                btn.configure(fg_color="#0284c7")
            else:
                c = self.save_mgr.cats.get(k)
                btn.configure(fg_color="#143026" if (c and getattr(c, 'is_in_house', False)) else "#1e293b")

        # Update Header
        self.lbl_cat_title.configure(text=f"猫咪 #{cat.key} - {cat.name} ({self._class_zh(cat.cat_class)} · {cat.cat_class})")
        self.lbl_cat_guid.configure(text=f"GUID: {hex(cat.guid)}")

        # Check if values exceed safe limits, auto unlock if needed
        exceeds_safe = any(b < 1 or b > 7 for b in cat.base_stats) or any(bon < 0 or bon > 7 for bon in cat.bonus_stats)
        if exceeds_safe and not self.var_unlock_limits.get():
            self.var_unlock_limits.set(True)
            self.on_toggle_safe_limits()

        # Update Stats Tab
        for i, k in enumerate(CatRecord.STAT_NAMES):
            b_val = cat.base_stats[i]
            bon_val = cat.bonus_stats[i]
            self.stat_sliders[k].set(b_val)
            self.bonus_sliders[k].set(bon_val)
            self.update_stat_display(k)

        # Update Mutations Tab
        self.refresh_mutation_ui()

        # Update Breeding Tab
        # Room
        curr_room = getattr(cat, 'house_room', '')
        if not getattr(cat, 'is_in_house', False) or not curr_room:
            room_str = '移出家园 (转入历史谱系)'
        elif curr_room == 'Floor1_Large':
            room_str = 'Floor1_Large (一层大厅)'
        elif curr_room == 'Floor1_Small':
            room_str = 'Floor1_Small (一层侧卧)'
        elif curr_room == 'Attic':
            room_str = 'Attic (阁楼)'
        else:
            room_str = curr_room
        self.combo_room.set(room_str)

        # Sexuality
        self.combo_sexuality.set(getattr(cat, 'sexuality', 'Straight (异性恋)'))
        self.combo_libido.set(getattr(cat, 'libido', 'Mid (正常)'))
        self.combo_aggression.set(getattr(cat, 'aggression', 'Mid (适中平衡)'))

        inbred_pct = f"{getattr(cat, 'inbred_level', 0) * 25}%"
        for opt in ["0% (纯净血统)", "25% (轻度近亲)", "50% (中度近亲)", "75% (重度近亲)"]:
            if inbred_pct in opt:
                self.combo_inbred.set(opt)
                break
        else:
            self.combo_inbred.set("0% (纯净血统)")

        # Identity
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, cat.name)
        self.combo_class.set(self._class_to_label(cat.cat_class))
        self.combo_voice.set(cat.voice)
        self.slider_pitch.set(cat.pitch)
        self.lbl_pitch_val.configure(text=f"{cat.pitch:.2f}")
        self.combo_boon.set(cat.boon)

        # Update Abilities Tab
        self.combo_atk.set(cat.attack_ability)
        self.combo_move.set(getattr(cat, 'move_ability', 'DefaultMove'))
        for i in range(4):
            base_spell, is_tier2, innate_skill, is_locked = cat.get_spell_state(i)
            self.active_combos[i].set(base_spell)

            chk = self.upgrade_checkboxes[i]
            if base_spell == 'None':
                chk.deselect()
                chk.configure(state="disabled", text="进阶强化 (未选择法术)", text_color="#64748b")
            else:
                upg_target = get_ability_upgrade(base_spell)
                chk.configure(state="normal", text=f"✨ 进阶强化 (Tier 2: {upg_target})", text_color="#e2e8f0")
                if is_tier2:
                    chk.select()
                else:
                    chk.deselect()

            self.innate_locked[i] = is_locked
            self.innate_combos[i].configure(state="normal")
            self.innate_combos[i].set(innate_skill)
            self.update_innate_lock_ui(i)

        self.update_class_passive_options(cat.cat_class)

        for i in range(2):
            k = cat.class_passives[i] if i < len(cat.class_passives) else 'None'
            disp = self.class_passive_key_to_str.get(k, k)
            self.class_passive_combos[i].set(disp)

        for i in range(2):
            k = cat.disorders[i] if i < len(cat.disorders) else 'None'
            disp = self.disorder_key_to_str.get(k, k)
            self.disorder_combos[i].set(disp)

        self.status_bar.configure(text=f"已选中猫咪 #{cat.key}: {cat.name} - 可直接修改各项属性", text_color="#38bdf8")

    def save_current_cat_fields(self):
        if not self.current_cat:
            return
        cat = self.current_cat
        cat.name = self.entry_name.get().strip() or "Unnamed"
        cat.cat_class = self._label_to_class(self.combo_class.get())
        cat.voice = self.combo_voice.get()
        cat.pitch = float(self.slider_pitch.get())
        cat.boon = self.combo_boon.get()

        for i, k in enumerate(CatRecord.STAT_NAMES):
            cat.base_stats[i] = int(self.stat_sliders[k].get())
            cat.bonus_stats[i] = int(self.bonus_sliders[k].get())

        # Breeding & Life fields
        cat.sexuality = self.combo_sexuality.get()
        cat.libido = self.combo_libido.get()
        cat.aggression = self.combo_aggression.get()
        
        inb_text = self.combo_inbred.get()
        if "25%" in inb_text:
            cat.inbred_level = 1
        elif "50%" in inb_text:
            cat.inbred_level = 2
        elif "75%" in inb_text:
            cat.inbred_level = 3
        else:
            cat.inbred_level = 0

        # Room change
        room_disp = self.combo_room.get()
        target_room = ""
        if "Floor1_Large" in room_disp:
            target_room = "Floor1_Large"
        elif "Floor1_Small" in room_disp:
            target_room = "Floor1_Small"
        elif "Attic" in room_disp:
            target_room = "Attic"
        elif "移出" in room_disp:
            target_room = ""

        if target_room != getattr(cat, 'house_room', ''):
            self.save_mgr.set_cat_room(cat.key, target_room)

        # Abilities
        cat.attack_ability = self.combo_atk.get()
        cat.move_ability = self.combo_move.get()
        for i in range(4):
            base_spell = self.active_combos[i].get()
            is_upg = (self.upgrade_checkboxes[i].get() == 1) if base_spell != 'None' else False
            if self.innate_locked[i]:
                innate_val = base_spell if base_spell != 'None' else 'None'
            else:
                innate_val = self.innate_combos[i].get()
            cat.set_spell_state(i, base_spell, is_upgraded=is_upg, innate_skill=innate_val)

        for i in range(2):
            raw = self.class_passive_combos[i].get()
            cat.class_passives[i] = self.get_class_passive_key_from_val(raw)

        for i in range(2):
            raw = self.disorder_combos[i].get()
            cat.disorders[i] = self.get_disorder_key_from_val(raw)

        cat.sync_legacy_passives()

        # 突变（左侧/右侧部件）在图标选择器中已实时写入 cat，无需在此同步

        cat.is_modified = True

    def update_stat_display(self, key):
        b = int(self.stat_sliders[key].get())
        bon = int(self.bonus_sliders[key].get())

        mut_mod = 0
        if self.current_cat:
            idx = CatRecord.STAT_NAMES.index(key)
            self.current_cat.base_stats[idx] = b
            self.current_cat.bonus_stats[idx] = bon
            mut_mods = self.current_cat.mutation_stat_modifiers
            mut_mod = mut_mods.get(key, 0)

        tot = b + mut_mod + bon
        self.stat_labels[key].configure(text=str(b))
        self.bonus_labels[key].configure(text=f"+{bon}" if bon >= 0 else str(bon))

        if key in self.mut_mod_labels:
            if mut_mod > 0:
                self.mut_mod_labels[key].configure(text=f"[突变: +{mut_mod}]", text_color="#10b981")
            elif mut_mod < 0:
                self.mut_mod_labels[key].configure(text=f"[突变: {mut_mod}]", text_color="#ef4444")
            else:
                self.mut_mod_labels[key].configure(text="[突变: 0]", text_color="#64748b")

        self.total_labels[key].configure(text=f"[实效: {tot}]")

    def update_mutation_summary(self):
        """顶部计数摘要：与游戏内 mutationcount / birthdefectcount 徽章口径一致。"""
        if not self.current_cat or not hasattr(self, 'lbl_mutation_summary'):
            return
        counts = self.current_cat.mutation_counts()
        txt = f"🧬 变异 ×{counts['mutations']}   🐣 出生缺陷 ×{counts['birth_defects']}"
        if counts['asymmetric']:
            txt += f"   ⚡不对称: {len(counts['asymmetric'])} 部位"
        self.lbl_mutation_summary.configure(text=txt)

    def refresh_mutation_ui(self):
        if not self.current_cat:
            return
        cat = self.current_cat

        for slot_key, slot_cn, off1, off2 in MUTATION_SLOTS:
            mid = cat.mutations.get(slot_key, 0)
            cb = self.mutation_combos.get(slot_key)
            badge = self.mutation_badge_labels.get(slot_key)
            cb_right = self.right_combos.get(slot_key)

            # 1. Left side / single part
            if cb:
                cb.configure(text=self._mutation_display_text(slot_key, mid),
                             image=self._mutation_btn_image(slot_key, mid))

            # 2. Right side (paired parts)
            if off2 and cb_right:
                r_id = getattr(cat, 'right_mutations', {}).get(slot_key, mid)
                if r_id is None:
                    r_id = mid
                cb_right.configure(text=self._mutation_display_text(slot_key, r_id),
                                   image=self._mutation_btn_image(slot_key, r_id))

                if badge:
                    if mid == r_id:
                        badge.configure(text="[对称]", text_color="#10b981")
                    else:
                        badge.configure(text="[⚡不对称]", text_color="#f59e0b")
            elif not off2 and badge:
                badge.configure(text="[单部件]", text_color="#64748b")

        self.update_mutation_summary()

    def _mutation_btn_image(self, slot_key, mid):
        """按钮小图标（22px 磁贴），带缓存。"""
        if not hasattr(self, '_mut_btn_img_cache'):
            self._mut_btn_img_cache = {}
        key = (slot_key, mid)
        if key not in self._mut_btn_img_cache:
            img = None
            if Image is not None:
                try:
                    mut_detailed = self.game_data.get('mutations_detailed', {})
                    entries = mut_detailed.get(slot_key, [])
                    entry = next((e for e in entries if e.get('id') == mid), None)
                    if entry is None:
                        if mid == -2:
                            entry = {'id': -2, 'name': '部位缺失', 'stats': {}}
                        elif mid is not None and mid < 300:
                            entry = {'id': mid, 'name': '无突变', 'stats': {}}
                        else:
                            entry = {'id': mid, 'name': f'#{mid}', 'stats': {}}
                    cat = classify_mutation(entry, CatRecord.get_birth_defect_ids())
                    img = ctk.CTkImage(make_tile(entry, cat, 44, slot_key=slot_key), size=(24, 24))
                except Exception:
                    img = None
            self._mut_btn_img_cache[key] = img
        return self._mut_btn_img_cache[key]

    def _mutation_display_text(self, slot_key, mid):
        mut_detailed = self.game_data.get('mutations_detailed', {})
        entries = mut_detailed.get(slot_key, [])
        if mid == -2:
            return "🚫 部位缺失 (-2)"
        if mid is None or mid < 300:
            return "无突变 (普通外观 / Pure)"
        match = next((e for e in entries if e.get('id') == mid), None)
        return match['display'] if match else f"#{mid} 未知部件"

    def open_mutation_picker(self, slot_key, side):
        """打开图标选择器；side = 'left' / 'right'。"""
        if not self.current_cat:
            return
        cat = self.current_cat
        mut_detailed = self.game_data.get('mutations_detailed', {})
        entries = mut_detailed.get(slot_key, [])
        slot_cn = dict((sk, cn) for sk, cn, _, _ in MUTATION_SLOTS).get(slot_key, slot_key)
        side_label = '左侧' if side == 'left' else '右侧'
        current = cat.mutations.get(slot_key, 0) if side == 'left' else cat.right_mutations.get(slot_key, 0)
        norm_id = 246 if slot_key == 'texture' else 100

        def on_pick(mid, sk=slot_key, sd=side):
            if sd == 'left':
                cat.set_mutation(sk, mid, sync_right=False)
            else:
                cat.set_right_mutation(sk, mid)
            self.refresh_mutation_ui()
            for k in CatRecord.STAT_NAMES:
                self.update_stat_display(k)
            self.status_bar.configure(
                text=f"已更新 {sk} {side_label}部件: {self._mutation_display_text(sk, mid)}",
                text_color="#a855f7" if sd == 'left' else "#c084fc")

        MutationPicker(self, f"选择突变 - {slot_cn} ({side_label})",
                       entries, CatRecord.get_birth_defect_ids(), current, norm_id, on_pick, slot_key=slot_key)

    def on_apply_god_mutations(self):
        if not self.current_cat:
            return
        self.current_cat.apply_god_mutations()
        self.refresh_mutation_ui()
        for k in CatRecord.STAT_NAMES:
            self.update_stat_display(k)
        self.status_bar.configure(text="✨ 已为当前猫咪配置全套极品正面突变！左右对称写入，繁殖时统一遗传。", text_color="#a855f7")

    def on_clear_all_mutations(self):
        if not self.current_cat:
            return
        self.current_cat.clear_all_mutations()
        self.refresh_mutation_ui()
        for k in CatRecord.STAT_NAMES:
            self.update_stat_display(k)
        self.status_bar.configure(text="🧼 已清除当前猫咪全部突变，15 个物理部件回归原版纯种外观！", text_color="#38bdf8")

    def on_stat_slide(self, key, val):
        self.update_stat_display(key)

    def on_bonus_slide(self, key, val):
        self.update_stat_display(key)

    def on_toggle_safe_limits(self):
        unlocked = self.var_unlock_limits.get()
        for k in CatRecord.STAT_NAMES:
            curr_b = int(self.stat_sliders[k].get())
            curr_bon = int(self.bonus_sliders[k].get())
            if unlocked:
                self.stat_sliders[k].configure(from_=0, to=99, number_of_steps=99)
                self.bonus_sliders[k].configure(from_=0, to=99, number_of_steps=99)
            else:
                self.stat_sliders[k].configure(from_=1, to=7, number_of_steps=6)
                self.bonus_sliders[k].configure(from_=0, to=7, number_of_steps=7)
                curr_b = max(1, min(7, curr_b))
                curr_bon = max(0, min(7, curr_bon))
            self.stat_sliders[k].set(curr_b)
            self.bonus_sliders[k].set(curr_bon)
            self.update_stat_display(k)
        mode_str = "自由模式 (0~99)" if unlocked else "原版安全模式 (基础1~7, 加成0~7)"
        self.status_bar.configure(text=f"属性编辑模式已切换为: {mode_str}", text_color="#f59e0b" if unlocked else "#10b981")

    def on_pitch_slide(self, val):
        self.lbl_pitch_val.configure(text=f"{float(val):.2f}")
        if self.current_cat:
            self.current_cat.pitch = float(val)

    def apply_stat_preset(self, base_val, bonus_val):
        if not self.current_cat:
            return
        if base_val > 7 or bonus_val > 7:
            if not self.var_unlock_limits.get():
                self.var_unlock_limits.set(True)
                self.on_toggle_safe_limits()

        for k in CatRecord.STAT_NAMES:
            self.stat_sliders[k].set(base_val)
            self.bonus_sliders[k].set(bonus_val)
            self.update_stat_display(k)
        self.status_bar.configure(text=f"已应用预设: 基础={base_val}, 加成={bonus_val}, 实效={base_val+bonus_val}", text_color="#10b981")

    def apply_special_preset(self, mode):
        if not self.current_cat:
            return
        for k in CatRecord.STAT_NAMES:
            if mode == "str_con":
                b = 7
                bon = 7 if k in ('str', 'con') else 0
            elif mode == "int_dex":
                b = 7
                bon = 7 if k in ('int', 'dex') else 0
            else:
                b = 7
                bon = 0
            self.stat_sliders[k].set(b)
            self.bonus_sliders[k].set(bon)
            self.update_stat_display(k)
        self.status_bar.configure(text=f"已应用特化预设: {mode}", text_color="#10b981")

    def set_filter_mode(self, mode):
        self.filter_mode = mode
        self.btn_flt_house.configure(fg_color="#0284c7" if mode == "house" else "#334155")
        self.btn_flt_all.configure(fg_color="#0284c7" if mode == "all" else "#334155")
        self.btn_flt_hist.configure(fg_color="#0284c7" if mode == "history" else "#334155")
        self.populate_cat_list(self.search_entry.get().strip())

    def on_search(self, event=None):
        if hasattr(self, '_search_job') and self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(200, self._do_search)

    def do_search_immediate(self):
        if hasattr(self, '_search_job') and self._search_job:
            self.after_cancel(self._search_job)
            self._search_job = None
        self._do_search()

    def _do_search(self):
        self._search_job = None
        text = self.search_entry.get().strip()
        self.populate_cat_list(text)

    def on_max_resources(self):
        self.entry_gold.delete(0, "end")
        self.entry_gold.insert(0, "999999")
        self.entry_food.delete(0, "end")
        self.entry_food.insert(0, "999999")
        self.status_bar.configure(text="金币与食物已调整为 999,999，点击右上角保存即可写入存档！", text_color="#10b981")

    def on_create_cat_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("新建定制猫咪 (Create New Cat)")
        dialog.geometry("450x520")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="创建一只全新的猫咪", font=("Arial", 16, "bold"), text_color="#10b981").pack(pady=12)

        # Name
        f1 = ctk.CTkFrame(dialog, fg_color="transparent")
        f1.pack(fill="x", padx=25, pady=5)
        ctk.CTkLabel(f1, text="猫咪名称:", width=90, anchor="w").pack(side="left")
        e_name = ctk.CTkEntry(f1, width=240)
        e_name.insert(0, "战神喵")
        e_name.pack(side="left")

        # Class
        f2 = ctk.CTkFrame(dialog, fg_color="transparent")
        f2.pack(fill="x", padx=25, pady=5)
        ctk.CTkLabel(f2, text="职业:", width=90, anchor="w").pack(side="left")
        cb_cls = ctk.CTkComboBox(f2, width=240,
                                 values=[self._class_to_label(c) for c in self.game_data.get('classes', [])])
        cb_cls.set(self._class_to_label("Mage"))
        cb_cls.pack(side="left")

        # Gender / Voice
        f3 = ctk.CTkFrame(dialog, fg_color="transparent")
        f3.pack(fill="x", padx=25, pady=5)
        ctk.CTkLabel(f3, text="性别/声音:", width=90, anchor="w").pack(side="left")
        cb_gen = ctk.CTkComboBox(f3, width=240, values=["male", "female"])
        cb_gen.set("female")
        cb_gen.pack(side="left")

        # Room selection
        f_room = ctk.CTkFrame(dialog, fg_color="transparent")
        f_room.pack(fill="x", padx=25, pady=5)
        ctk.CTkLabel(f_room, text="入住房间:", width=90, anchor="w").pack(side="left")
        cb_room = ctk.CTkComboBox(f_room, width=240, values=[
            'Floor1_Large (一层大厅)',
            'Floor1_Small (一层侧卧)',
            'Attic (阁楼)',
            '移出家园 (谱系)'
        ])
        cb_room.set('Floor1_Large (一层大厅)')
        cb_room.pack(side="left")

        # Sexuality
        f_sex = ctk.CTkFrame(dialog, fg_color="transparent")
        f_sex.pack(fill="x", padx=25, pady=5)
        ctk.CTkLabel(f_sex, text="性取向:", width=90, anchor="w").pack(side="left")
        cb_sex = ctk.CTkComboBox(f_sex, width=240, values=[
            "Straight (异性恋)",
            "Bisexual (双性恋)",
            "Gay (同性恋)"
        ])
        cb_sex.set("Straight (异性恋)")
        cb_sex.pack(side="left")

        # Initial Stats Preset
        f4 = ctk.CTkFrame(dialog, fg_color="transparent")
        f4.pack(fill="x", padx=25, pady=5)
        ctk.CTkLabel(f4, text="初始属性:", width=90, anchor="w").pack(side="left")
        cb_stats = ctk.CTkComboBox(f4, width=240, values=[
            "极品战神 (Base 7 + Bonus 7)",
            "纯种满遗传 (Base 7 + Bonus 0)",
            "全99神猫 (Base 99 + Bonus 99)",
            "原版标准 (Base 4 + Bonus 0)"
        ])
        cb_stats.set("极品战神 (Base 7 + Bonus 7)")
        cb_stats.pack(side="left")

        def do_create():
            c_name = e_name.get().strip() or "NewCat"
            c_class = self._label_to_class(cb_cls.get())
            c_gen = cb_gen.get()
            
            # parse room
            r_str = cb_room.get()
            target_room = "Floor1_Large"
            if "Floor1_Small" in r_str:
                target_room = "Floor1_Small"
            elif "Attic" in r_str:
                target_room = "Attic"
            elif "移出" in r_str:
                target_room = ""

            # parse sexuality
            target_sex = cb_sex.get()

            # parse preset stats
            choice = cb_stats.get()
            if "7 + Bonus 7" in choice:
                b_val, bon_val = 7, 7
            elif "满遗传" in choice:
                b_val, bon_val = 7, 0
            elif "99" in choice:
                b_val, bon_val = 99, 99
            else:
                b_val, bon_val = 4, 0
            
            stats_dict = {k: b_val for k in CatRecord.STAT_NAMES}
            new_cat = self.save_mgr.create_new_cat(
                name=c_name, 
                gender=c_gen, 
                cat_class=c_class, 
                stats=stats_dict,
                room=target_room,
                sexuality=target_sex
            )
            new_cat.bonus_stats = [bon_val] * 7

            dialog.destroy()
            
            self.populate_cat_list()
            self.select_cat(new_cat.key)
            messagebox.showinfo("创建成功", f"成功创建全新猫咪: #{new_cat.key} - {new_cat.name} [{new_cat.cat_class}]!\n所在房间: {target_room or '历史谱系'}\n请点击右上角「保存所有更改」写入存档。")

        ctk.CTkButton(dialog, text="立即生成并加入家园", fg_color="#10b981", hover_color="#059669", height=38, command=do_create).pack(pady=20, padx=25, fill="x")

    def on_clone_cat(self):
        if not self.current_cat:
            messagebox.showwarning("提示", "请先在左侧选择要克隆的猫咪！")
            return
        
        self.save_current_cat_fields()
        src = self.current_cat
        clone_cat = self.save_mgr.create_new_cat(
            name=f"{src.name}_Clone",
            gender="male" if "male" in src.voice else "female",
            cat_class=src.cat_class,
            template_id=src.key,
            room=getattr(src, 'house_room', 'Floor1_Large'),
            sexuality=getattr(src, 'sexuality', 'Straight (异性恋)')
        )
        clone_cat.bonus_stats = list(src.bonus_stats)
        clone_cat.attack_ability = src.attack_ability
        clone_cat.move_ability = getattr(src, 'move_ability', 'DefaultMove')
        clone_cat.active_abilities = list(src.active_abilities)
        clone_cat.ability_upgrades = list(src.ability_upgrades)
        clone_cat.class_passives = list(src.class_passives)
        clone_cat.disorders = list(src.disorders)
        clone_cat.sync_legacy_passives()
        
        self.populate_cat_list()
        self.select_cat(clone_cat.key)
        self.status_bar.configure(text=f"成功克隆猫咪 #{src.key} 为 #{clone_cat.key}: {clone_cat.name}", text_color="#10b981")

    def on_delete_cat(self):
        if not self.current_cat:
            return
        cat_id = self.current_cat.key
        if messagebox.askyesno("确认删除", f"确定要从存档中彻底删除猫咪 #{cat_id} ({self.current_cat.name}) 吗？"):
            del self.save_mgr.cats[cat_id]
            self.populate_cat_list()
            self.show_empty_state()
            self.status_bar.configure(text=f"已删除猫咪 #{cat_id}", text_color="#ef4444")

    def update_save_header_info(self):
        fp = getattr(self.save_mgr, 'file_path', '') or ''
        fn = os.path.basename(fp)
        
        m = re.search(r'steamcampaign0([1-3])\.sav', fn)
        if m:
            slot_num = int(m.group(1))
            info = MewgenicsSaveManager.get_slot_info(fp, slot_num=slot_num)
            if info.get('has_data'):
                badge_text = f"🧪 槽位 {slot_num}: {info.get('location', '家')} ({info.get('percent', 0)}%)"
            else:
                badge_text = f"🧪 槽位 {slot_num}: 空白"
        else:
            badge_text = f"📂 外部: {fn}" if fn else "未选择存档"

        if hasattr(self, 'lbl_slot_badge'):
            self.lbl_slot_badge.configure(text=badge_text)
        
        if hasattr(self, 'lbl_path'):
            short_fp = fp if len(fp) <= 45 else "..." + fp[-42:]
            self.lbl_path.configure(text=f"路径: {short_fp}")

        if hasattr(self, 'entry_gold') and hasattr(self, 'entry_food') and hasattr(self, 'entry_day'):
            self.entry_gold.delete(0, "end")
            self.entry_gold.insert(0, str(self.save_mgr.properties.get('house_gold', 0)))
            self.entry_food.delete(0, "end")
            self.entry_food.insert(0, str(self.save_mgr.properties.get('house_food', 0)))
            self.entry_day.delete(0, "end")
            self.entry_day.insert(0, str(self.save_mgr.properties.get('current_day', 0)))

    def switch_to_save(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return
        self.save_mgr = MewgenicsSaveManager(file_path)
        self.update_save_header_info()
        self.populate_cat_list()
        self.show_empty_state()
        fn = os.path.basename(file_path)
        self.status_bar.configure(text=f"已成功加载战役存档: {fn}", text_color="#10b981")

    # ================================================================
    # 顶层路由 (猫咪 / 仓库道具 / 家具)
    # ================================================================

    ITEM_BOXES = [("仓库 (Storage)", "storage"), ("背包 (Backpack)", "backpack"), ("回收站 (Trash)", "trash")]
    FURNITURE_ROOMS = ["Floor1_Large", "Floor1_Small", "Attic", "(墙面/无房间)"]

    def on_nav_switch(self, choice):
        if getattr(self, 'current_view', None) == choice:
            return
        self.current_view = choice
        for v in (self.view_cats, self.view_items, self.view_furniture, self.view_completion):
            v.pack_forget()
        if choice == "🎒 仓库道具":
            self.refresh_item_list()
            self.view_items.pack(fill="both", expand=True)
        elif choice == "🪑 家具管理":
            self.refresh_furniture_list()
            self.view_furniture.pack(fill="both", expand=True)
        elif choice == "🏅 职业通关":
            self.refresh_completion_grid()
            self.view_completion.pack(fill="both", expand=True)
        else:
            self.view_cats.pack(fill="both", expand=True)

    # ================================================================
    # Wiki 图鉴数据（图标 + 中文名）加载
    # ================================================================

    def load_wiki_csv(self, name, key_col):
        """加载 wiki_data/csv/<name>，返回 {key: row}。文件缺失时返回 {} 并优雅降级。"""
        path = get_resource_path(os.path.join('wiki_data', 'csv', name))
        if not os.path.exists(path):
            return {}
        try:
            with open(path, encoding='utf-8-sig', newline='') as f:
                return {r[key_col]: r for r in csv.DictReader(f) if r.get(key_col)}
        except Exception:
            return {}

    def get_wiki_icon(self, row, size=(28, 28)):
        """按行的 icon_local 字段加载 wiki 图标为 CTkImage；缺失返回 None。"""
        if Image is None or not row:
            return None
        rel = row.get('icon_local', '')
        if not rel:
            return None
        full = get_resource_path(os.path.join('wiki_data', rel))
        if not os.path.exists(full):
            return None
        cache_key = (full, size)
        if cache_key not in self._icon_cache:
            try:
                img = Image.open(full)
                self._icon_cache[cache_key] = ctk.CTkImage(light_image=img, dark_image=img, size=size)
            except Exception:
                self._icon_cache[cache_key] = None
        return self._icon_cache[cache_key]

    # ================================================================
    # 仓库道具视图
    # ================================================================

    def build_items_view(self):
        self._icon_cache = getattr(self, '_icon_cache', {})
        self.items_db = self.load_wiki_csv('items.csv', 'item_code')
        self.item_label_to_code = {}
        for code, row in self.items_db.items():
            zh = row.get('name_zh') or row.get('name_en') or code
            self.item_label_to_code[f"{zh} [{code}]"] = code
        self.item_labels_sorted = sorted(self.item_label_to_code.keys())
        self.selected_item = None  # (box, index)

        v = self.view_items

        # 左侧：箱子切换 + 道具列表
        left = ctk.CTkFrame(v, width=400)
        left.pack(side="left", fill="y", padx=5, pady=5)
        left.pack_propagate(False)

        self.item_box_seg = ctk.CTkSegmentedButton(
            left, values=[b[0] for b in self.ITEM_BOXES],
            command=lambda _: self.refresh_item_list())
        self.item_box_seg.set(self.ITEM_BOXES[0][0])
        self.item_box_seg.pack(fill="x", padx=8, pady=(8, 4))

        self.item_list = ctk.CTkScrollableFrame(left, label_text="道具列表")
        self.item_list.pack(fill="both", expand=True, padx=8, pady=5)

        # 右侧：编辑面板
        right = ctk.CTkFrame(v)
        right.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # 🏪 商店与家园升级进度卡（只读）
        self.shop_card = ctk.CTkFrame(right, fg_color="#14202e", corner_radius=8)
        self.shop_card.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(self.shop_card, text="🏪 商店与家园升级进度（存档只读信息）",
                     font=("Arial", 13, "bold"), text_color="#f59e0b").pack(anchor="w", padx=12, pady=(8, 2))
        self.shop_info_lbl = ctk.CTkLabel(self.shop_card, text="", font=("Arial", 12), text_color="#cbd5e1",
                                          anchor="nw", justify="left", wraplength=560)
        self.shop_info_lbl.pack(fill="x", padx=12, pady=(0, 8))
        self.refresh_shop_progress()

        head = ctk.CTkFrame(right, fg_color="#1e293b", corner_radius=8)
        head.pack(fill="x", padx=10, pady=8)
        self.item_icon_lbl = ctk.CTkLabel(head, text="🎒", font=("Arial", 36), width=72, height=72)
        self.item_icon_lbl.pack(side="left", padx=12, pady=10)
        self.item_name_lbl = ctk.CTkLabel(head, text="请选择左侧道具", font=("Arial", 15, "bold"), anchor="w", justify="left")
        self.item_name_lbl.pack(side="left", padx=8, pady=10)

        self.item_info_lbl = ctk.CTkLabel(right, text="", font=("Arial", 12), text_color="#cbd5e1",
                                          anchor="nw", justify="left", wraplength=560)
        self.item_info_lbl.pack(fill="x", padx=14, pady=4)
        self.item_detail_lbl = ctk.CTkLabel(right, text="", font=("Consolas", 11), text_color="#64748b", anchor="w")
        self.item_detail_lbl.pack(fill="x", padx=14, pady=2)

        f_type = ctk.CTkFrame(right, fg_color="transparent")
        f_type.pack(fill="x", padx=14, pady=(10, 3))
        ctk.CTkLabel(f_type, text="道具类型:", font=("Arial", 12, "bold")).pack(side="left")
        self.item_type_combo = ctk.CTkComboBox(f_type, width=420, values=self.item_labels_sorted or ['(wiki 数据缺失)'])
        self.item_type_combo.pack(side="left", padx=8)

        f_btns = ctk.CTkFrame(right, fg_color="transparent")
        f_btns.pack(fill="x", padx=14, pady=4)
        ctk.CTkButton(f_btns, text="✅ 更换类型", fg_color="#0284c7", hover_color="#0369a1",
                      command=self.on_item_change_type).pack(side="left", padx=4)
        ctk.CTkButton(f_btns, text="🗑 删除该道具", fg_color="#ef4444", hover_color="#dc2626",
                      command=self.on_item_delete).pack(side="left", padx=4)

        ctk.CTkFrame(right, height=2, fg_color="#334155").pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(right, text="➕ 添加新道具到当前箱子", font=("Arial", 13, "bold"), text_color="#10b981").pack(anchor="w", padx=14)
        f_add = ctk.CTkFrame(right, fg_color="transparent")
        f_add.pack(fill="x", padx=14, pady=4)
        self.item_add_combo = ctk.CTkComboBox(f_add, width=420, values=self.item_labels_sorted or ['(wiki 数据缺失)'])
        self.item_add_combo.pack(side="left", padx=(0, 8))
        ctk.CTkButton(f_add, text="➕ 添加", fg_color="#059669", hover_color="#047857",
                      command=self.on_item_add).pack(side="left")

        ctk.CTkLabel(right, text="💡 所有修改先作用于内存，点击右上角「保存所有更改」写入存档（自动备份）。",
                     font=("Arial", 11), text_color="#94a3b8").pack(anchor="w", padx=14, pady=(10, 4))

    def _current_box_key(self):
        label = self.item_box_seg.get()
        return dict(self.ITEM_BOXES).get(label, 'storage')

    TINK_SERVICE_ZH = {
        'tink_prettybow': '蝴蝶结礼物', 'tink_basestats': '基础属性查看', 'tink_inbreeding': '近亲繁殖查看',
        'tink_sexuality': '性取向查看', 'tink_tags': '标签查看', 'tink_aggression': '攻击性查看',
        'tink_relationships': '关系查看',
    }
    HOUSE_UNLOCK_ZH = {
        'Default': '初始小屋', 'SmallHouse_Attic': '阁楼', 'MediumHouse': '中型房屋',
        'MediumHouse_SmallRoom': '一层侧卧', 'LargeHouse': '大房屋',
        'LargeHouse_Floor2Large': '二层大厅', 'LargeHouse_Floor2Small': '二层小房间',
        'BasementUpgrade': '地下室1层', 'BasementUpgrade2': '地下室2层', 'BasementUpgrade3': '地下室3层',
        'BasementUpgrade4': '地下室4层', 'BasementUpgrade5': '地下室5层',
    }

    def _item_is_quest(self, it_or_code):
        """任务道具（主线/支线）判定：wiki items.csv 的 rarity ∈ {'quest', 'sidequest'}
        （如 ScaldingOrb=quest、Stopwatch=sidequest）。
        任务道具存放在仓库 blob 中但不占用普通容量格子（游戏内实测）。"""
        code = it_or_code if isinstance(it_or_code, str) else getattr(it_or_code, 'name', '')
        row = self.items_db.get(code, {})
        return row.get('rarity', '') in ('quest', 'sidequest')

    def _storage_counts(self):
        """返回 (普通道具数, 任务道具数)——只有普通道具占仓库容量。"""
        blob = self.save_mgr.inventories.get('storage')
        items = blob.items if blob else []
        normal = sum(1 for it in items if not self._item_is_quest(it))
        quest = len(items) - normal
        return normal, quest

    def refresh_shop_progress(self):
        """刷新商店与家园升级进度卡（只读信息）。"""
        sp = get_shop_progress(self.save_mgr.properties, self.save_mgr.npc_records, self.save_mgr.house_unlocks)
        used, quest_n = self._storage_counts()
        cap = sp['storage_capacity']
        usage = f"{used}/{cap}" + (" ⚠️ 已超容量！" if used > cap else "")
        if quest_n:
            usage += f"（另有任务道具 {quest_n} 件，不占格子）"
        house = [self.HOUSE_UNLOCK_ZH.get(h) for h in sp['house_unlocks']]
        house = [h for h in house if h] or ['初始小屋']
        tink = '、'.join(self.TINK_SERVICE_ZH.get(k, k) for k in sp['tink_unlocks']) or '无'
        lines = [
            f"📦 仓库商店 (Butch)：仓库 Lv.{sp['storage_level']} → 容量 {cap} 格，当前 {usage}",
            f"🪑 家具店 (Jack)：店铺 Lv.{sp['jack_level']} / 4",
            f"🍖 食品店 (Tracy)：食物柜 Lv.{sp['tracy_foodstorage']}/10 · 空白项圈 Lv.{sp['tracy_blankcollar']} · 神像 Lv.{sp['tracy_idol']}",
            f"🔧 信息店 (Tink)：服务 {len(sp['tink_unlocks'])}/7 项（{tink}）",
            f"🫀 器官店 (Organ)：{'已解锁' if sp['organ_unlocked'] else '未解锁'} · 升级 Lv.{sp['organ_level']}/2",
            f"🏠 房屋：{' → '.join(house)}",
            f"🎩 Beanies 任务：{'已开启' if sp['beanies_intro_done'] else '未开启'} · 重复任务 x{sp['beanies_repeat_count']}",
        ]
        self.shop_info_lbl.configure(text="\n".join(lines))

    def _durability_text(self, it, row_db):
        """道具磨损度显示：m1=-1 为无磨损概念，否则为当前耐久；最大值取自 wiki 数据。"""
        if it.m1 == -1:
            return "♾️ 无磨损"
        dmax = None
        d = (row_db or {}).get('durability', '')
        if d:
            try:
                v = json.loads(d) if d.strip().startswith('[') else int(d)
                dmax = max(v) if isinstance(v, list) else v
            except Exception:
                pass
        return f"耐久 {it.m1}/{dmax}" if dmax else f"耐久 {it.m1}"

    def refresh_item_list(self):
        for w in self.item_list.winfo_children():
            w.destroy()
        box = self._current_box_key()
        blob = self.save_mgr.inventories.get(box)
        items = blob.items if blob else []
        if box == 'storage':
            cap = storage_capacity(self.save_mgr.properties.get('house_storage_upgrades', 0))
            normal, quest_n = self._storage_counts()
            self.item_list.configure(label_text=f"道具列表（普通 {normal}/{cap} 件 · 任务 {quest_n} 件）")
            groups = [
                (f"🎒 普通道具（占容量格，{normal}/{cap}）", "#38bdf8",
                 [(i, it) for i, it in enumerate(items) if not self._item_is_quest(it)]),
                (f"📜 任务道具（主线/支线，不占格子，{quest_n} 件）", "#f59e0b",
                 [(i, it) for i, it in enumerate(items) if self._item_is_quest(it)]),
            ]
        else:
            self.item_list.configure(label_text=f"道具列表（{len(items)} 件）")
            groups = [("📦 全部道具", "#38bdf8", list(enumerate(items)))]

        for title, color, group_items in groups:
            if not group_items:
                continue
            section = ctk.CTkFrame(self.item_list, fg_color="transparent")
            section.pack(fill="x", padx=2, pady=(8, 0))
            ctk.CTkLabel(section, text=title, font=("Arial", 12, "bold"), text_color=color,
                         fg_color="#0f172a", corner_radius=6, anchor="w").pack(fill="x", padx=4, pady=(0, 2))
            for idx, it in group_items:
                row_db = self.items_db.get(it.name, {})
                zh = row_db.get('name_zh') or row_db.get('name_en') or it.name
                icon = self.get_wiki_icon(row_db)
                dur = self._durability_text(it, row_db)
                btn = ctk.CTkButton(
                    section, text=f"{zh}  [{it.name}]  #{it.serial}  ·{dur}",
                    image=icon, compound="left", anchor="w",
                    font=("Arial", 12), fg_color="#1e293b", hover_color="#334155",
                    command=lambda b=box, i=idx: self.on_select_item(b, i))
                btn.pack(fill="x", padx=4, pady=2)

    def on_select_item(self, box, index):
        blob = self.save_mgr.inventories.get(box)
        if not blob or not (0 <= index < len(blob.items)):
            return
        self.selected_item = (box, index)
        it = blob.items[index]
        row_db = self.items_db.get(it.name, {})
        zh = row_db.get('name_zh') or ''
        en = row_db.get('name_en') or it.name
        self.item_name_lbl.configure(text=f"{zh} ({en})\n[{it.name}]" if zh else en)
        icon = self.get_wiki_icon(row_db, size=(64, 64))
        if icon:
            self.item_icon_lbl.configure(image=icon, text="")
        else:
            self.item_icon_lbl.configure(image=None, text="🎒")
        info_lines = []
        if row_db:
            info_lines.append(f"部位: {row_db.get('kind', '?')}    稀有度: {row_db.get('rarity', '?')}"
                              + (f"    套装: {row_db.get('sets')}" if row_db.get('sets') else ""))
            if row_db.get('stats'):
                info_lines.append(f"属性: {row_db['stats']}")
            if row_db.get('desc_zh'):
                info_lines.append(f"效果: {row_db['desc_zh']}")
        else:
            info_lines.append("（wiki 图鉴中无此道具资料）")
        self.item_info_lbl.configure(text="\n".join(info_lines))
        extra = f"  扩展标记: {it.extra}" if it.extra else ""
        dur = self._durability_text(it, row_db)
        self.item_detail_lbl.configure(
            text=f"实例序列号 #{it.serial}  {dur}  unk=({it.unk_a},{it.unk_b})  flags=({it.flag1},{it.flag2}){extra}")
        label = f"{zh or en} [{it.name}]"
        if label in self.item_label_to_code:
            self.item_type_combo.set(label)

    def on_item_change_type(self):
        if not self.selected_item:
            self.status_bar.configure(text="请先在左侧选择一个道具！", text_color="#f59e0b")
            return
        code = self.item_label_to_code.get(self.item_type_combo.get())
        if not code:
            self.status_bar.configure(text="无效的道具类型选择！", text_color="#f59e0b")
            return
        box, idx = self.selected_item
        self.save_mgr.inventories[box].items[idx].name = code
        self.refresh_item_list()
        self.on_select_item(box, idx)
        self.status_bar.configure(text=f"道具类型已更换为 {code}（内存中），保存后生效。", text_color="#38bdf8")

    def on_item_delete(self):
        if not self.selected_item:
            self.status_bar.configure(text="请先在左侧选择一个道具！", text_color="#f59e0b")
            return
        box, idx = self.selected_item
        it = self.save_mgr.inventories[box].remove_item(idx)
        self.selected_item = None
        self.refresh_item_list()
        self.refresh_shop_progress()
        self.item_name_lbl.configure(text="请选择左侧道具")
        self.item_info_lbl.configure(text="")
        self.item_detail_lbl.configure(text="")
        self.status_bar.configure(text=f"已删除道具 [{it.name}]（内存中），保存后生效。", text_color="#38bdf8")

    def on_item_add(self):
        code = self.item_label_to_code.get(self.item_add_combo.get())
        if not code:
            self.status_bar.configure(text="请选择要添加的道具类型！", text_color="#f59e0b")
            return
        box = self._current_box_key()
        if box == 'storage' and not self._item_is_quest(code):
            lv = self.save_mgr.properties.get('house_storage_upgrades', 0)
            cap = storage_capacity(lv)
            cur, quest_n = self._storage_counts()
            if cur >= cap:
                messagebox.showwarning(
                    "仓库已满",
                    f"仓库等级 Lv.{lv} 的最大容量为 {cap} 件，当前已有 {cur} 件普通道具。\n\n"
                    "（任务道具不占容量）请先在游戏中找 Butch 升级仓库，或删除部分道具后再添加。")
                self.status_bar.configure(text=f"添加被拒绝：仓库容量已满（{cur}/{cap}）", text_color="#ef4444")
                return
        it = self.save_mgr.inventories[box].add_item(code)
        self.refresh_item_list()
        self.refresh_shop_progress()
        self.on_select_item(box, len(self.save_mgr.inventories[box].items) - 1)
        self.status_bar.configure(text=f"已添加道具 [{code}]（内存中），保存后生效。", text_color="#38bdf8")

    # ================================================================
    # 家具管理视图
    # ================================================================

    def build_furniture_view(self):
        self.furniture_db = self.load_wiki_csv('furniture.csv', 'furniture_code')
        self.furn_label_to_code = {}
        for code, row in self.furniture_db.items():
            zh = row.get('name_zh') or row.get('name_en') or code
            self.furn_label_to_code[f"{zh} [{code}]"] = code
        self.furn_labels_sorted = sorted(self.furn_label_to_code.keys())
        self.selected_furniture = None  # key

        v = self.view_furniture

        left = ctk.CTkFrame(v, width=400)
        left.pack(side="left", fill="y", padx=5, pady=5)
        left.pack_propagate(False)
        self.furn_list = ctk.CTkScrollableFrame(left, label_text="已放置家具")
        self.furn_list.pack(fill="both", expand=True, padx=8, pady=8)

        right = ctk.CTkFrame(v)
        right.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        head = ctk.CTkFrame(right, fg_color="#1e293b", corner_radius=8)
        head.pack(fill="x", padx=10, pady=8)
        self.furn_icon_lbl = ctk.CTkLabel(head, text="🪑", font=("Arial", 36), width=72, height=72)
        self.furn_icon_lbl.pack(side="left", padx=12, pady=10)
        self.furn_name_lbl = ctk.CTkLabel(head, text="请选择左侧家具", font=("Arial", 15, "bold"), anchor="w", justify="left")
        self.furn_name_lbl.pack(side="left", padx=8, pady=10)

        self.furn_info_lbl = ctk.CTkLabel(right, text="", font=("Arial", 12), text_color="#cbd5e1",
                                          anchor="nw", justify="left", wraplength=560)
        self.furn_info_lbl.pack(fill="x", padx=14, pady=4)
        self.furn_detail_lbl = ctk.CTkLabel(right, text="", font=("Consolas", 11), text_color="#64748b", anchor="w")
        self.furn_detail_lbl.pack(fill="x", padx=14, pady=2)

        f_type = ctk.CTkFrame(right, fg_color="transparent")
        f_type.pack(fill="x", padx=14, pady=(10, 3))
        ctk.CTkLabel(f_type, text="家具类型:", width=90, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.furn_type_combo = ctk.CTkComboBox(f_type, width=420, values=self.furn_labels_sorted or ['(wiki 数据缺失)'])
        self.furn_type_combo.pack(side="left", padx=8)

        f_room = ctk.CTkFrame(right, fg_color="transparent")
        f_room.pack(fill="x", padx=14, pady=3)
        ctk.CTkLabel(f_room, text="所在房间:", width=90, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.furn_room_combo = ctk.CTkComboBox(f_room, width=200, values=self.FURNITURE_ROOMS)
        self.furn_room_combo.pack(side="left", padx=8)
        ctk.CTkLabel(f_room, text="X:", font=("Arial", 12)).pack(side="left", padx=(12, 2))
        self.furn_x_entry = ctk.CTkEntry(f_room, width=60)
        self.furn_x_entry.pack(side="left")
        ctk.CTkLabel(f_room, text="Y:", font=("Arial", 12)).pack(side="left", padx=(12, 2))
        self.furn_y_entry = ctk.CTkEntry(f_room, width=60)
        self.furn_y_entry.pack(side="left")

        self.furn_lock_note = ctk.CTkLabel(right, text="", font=("Arial", 11), text_color="#f59e0b", anchor="w")
        self.furn_lock_note.pack(fill="x", padx=14, pady=(2, 0))

        f_btns = ctk.CTkFrame(right, fg_color="transparent")
        f_btns.pack(fill="x", padx=14, pady=4)
        self.furn_apply_btn = ctk.CTkButton(f_btns, text="✅ 更换类型", fg_color="#0284c7", hover_color="#0369a1",
                      command=self.on_furniture_apply)
        self.furn_apply_btn.pack(side="left", padx=4)
        self.furn_del_btn = ctk.CTkButton(f_btns, text="🗑 移除该家具", fg_color="#ef4444", hover_color="#dc2626",
                      command=self.on_furniture_delete)
        self.furn_del_btn.pack(side="left", padx=4)

        ctk.CTkFrame(right, height=2, fg_color="#334155").pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(right, text="➕ 添加新家具（放入家具仓库，进入游戏后自由摆放）", font=("Arial", 13, "bold"), text_color="#10b981").pack(anchor="w", padx=14)
        f_add = ctk.CTkFrame(right, fg_color="transparent")
        f_add.pack(fill="x", padx=14, pady=4)
        self.furn_add_combo = ctk.CTkComboBox(f_add, width=420, values=self.furn_labels_sorted or ['(wiki 数据缺失)'])
        self.furn_add_combo.pack(side="left", padx=(0, 8))
        ctk.CTkButton(f_add, text="➕ 放入仓库", fg_color="#059669", hover_color="#047857",
                      command=self.on_furniture_add).pack(side="left")

        ctk.CTkLabel(right, text="💡 家具仓库中的家具可更换类型/移除；已放置到房间的家具（含阁楼）仅展示属性，请在游戏中调整位置。\n所有修改先作用于内存，点击右上角「保存所有更改」写入存档（自动备份）。",
                     font=("Arial", 11), text_color="#94a3b8", justify="left").pack(anchor="w", padx=14, pady=(10, 4))

    FURN_STAT_ZH = {
        'comfort': ('🛋️', '舒适度'), 'stimulation': ('⚡', '刺激度'), 'appeal': ('💖', '吸引力'),
        'health': ('❤️', '健康'), 'breed_suppression': ('🚫', '繁殖抑制'), 'evolution': ('🧬', '变异促进'),
        'fight_bonus_rewards': ('🎁', '战斗奖励'), 'fight_risk': ('⚔️', '战斗风险'),
        'food_storage': ('🍖', '食物储存'),
    }

    @staticmethod
    def _is_warehouse_furniture(rec):
        """家具仓库（未放置）= 无房间且坐标 (0,0)。无房间但有坐标的是墙面装饰（视为已放置）。"""
        return rec.room == '' and rec.x == 0 and rec.y == 0

    def _format_furniture_stats(self, stats_str):
        """家具属性 JSON → 映射中文标签（舒适度/刺激度等）。"""
        if not stats_str:
            return ''
        try:
            d = json.loads(stats_str)
        except Exception:
            return str(stats_str)
        parts = []
        for k, v in d.items():
            icon, zh = self.FURN_STAT_ZH.get(k, ('▫️', k))
            if isinstance(v, (int, float)):
                parts.append(f"{icon} {zh} {v:+g}")
            else:
                parts.append(f"{icon} {zh} {v}")
        return "   ".join(parts)

    def _set_furniture_editable(self, editable):
        st = "normal" if editable else "disabled"
        self.furn_type_combo.configure(state="normal" if editable else "disabled")
        self.furn_apply_btn.configure(state=st)
        self.furn_del_btn.configure(state=st)
        self.furn_room_combo.configure(state="disabled")
        self.furn_x_entry.configure(state="disabled")
        self.furn_y_entry.configure(state="disabled")

    def _room_to_display(self, room):
        return room if room else "(墙面/无房间)"

    def _display_to_room(self, disp):
        return "" if disp == "(墙面/无房间)" else disp

    def refresh_furniture_list(self):
        for w in self.furn_list.winfo_children():
            w.destroy()
        furn = self.save_mgr.furniture
        warehouse_keys = sorted(k for k, r in furn.items() if self._is_warehouse_furniture(r))
        placed_keys = [k for k in furn if k not in warehouse_keys]
        self.furn_list.configure(label_text=f"家具（仓库 {len(warehouse_keys)} · 已放置 {len(placed_keys)}）")

        def add_row(key, editable):
            rec = furn[key]
            row_db = self.furniture_db.get(rec.name, {})
            zh = row_db.get('name_zh') or row_db.get('name_en') or rec.name
            icon = self.get_wiki_icon(row_db)
            mark = "" if editable else "🔒 "
            btn = ctk.CTkButton(
                self.furn_list, text=f"{mark}{zh}  [{rec.name}]  ({rec.x},{rec.y})",
                image=icon, compound="left", anchor="w",
                font=("Arial", 12), fg_color="#1e293b", hover_color="#334155",
                command=lambda k=key: self.on_select_furniture(k))
            btn.pack(fill="x", padx=4, pady=2)

        # 1. 家具仓库（可编辑）—— 主展示区
        ctk.CTkLabel(self.furn_list, text=f"📦 家具仓库 · 未放置（{len(warehouse_keys)} 件，可编辑）",
                     font=("Arial", 12, "bold"), text_color="#10b981", anchor="w").pack(fill="x", padx=6, pady=(6, 2))
        for key in warehouse_keys:
            add_row(key, True)

        # 2. 已放置家具（只读，按房间分组）
        room_order = ['Floor1_Large', 'Floor1_Small', 'Attic', '']
        rooms = sorted({furn[k].room for k in placed_keys},
                       key=lambda r: room_order.index(r) if r in room_order else 99)
        room_zh = {'Floor1_Large': '一层大厅', 'Floor1_Small': '一层侧卧', 'Attic': '阁楼', '': '墙面装饰'}
        for room in rooms:
            keys = sorted(k for k in placed_keys if furn[k].room == room)
            ctk.CTkLabel(self.furn_list, text=f"🔒 {room_zh.get(room, room)}（{len(keys)} 件，仅展示）",
                         font=("Arial", 12, "bold"), text_color="#64748b", anchor="w").pack(fill="x", padx=6, pady=(10, 2))
            for key in keys:
                add_row(key, False)

    def on_select_furniture(self, key):
        rec = self.save_mgr.furniture.get(key)
        if not rec:
            return
        self.selected_furniture = key
        editable = self._is_warehouse_furniture(rec)
        row_db = self.furniture_db.get(rec.name, {})
        zh = row_db.get('name_zh') or ''
        en = row_db.get('name_en') or rec.name
        self.furn_name_lbl.configure(text=f"{zh} ({en})\n[{rec.name}]" if zh else en)
        icon = self.get_wiki_icon(row_db, size=(64, 64))
        if icon:
            self.furn_icon_lbl.configure(image=icon, text="")
        else:
            self.furn_icon_lbl.configure(image=None, text="🪑")
        info_lines = []
        if row_db:
            if row_db.get('set'):
                info_lines.append(f"套装: {row_db['set']}")
            mapped = self._format_furniture_stats(row_db.get('stats'))
            if mapped:
                info_lines.append(f"属性: {mapped}")
            if row_db.get('special'):
                info_lines.append(f"特殊: {row_db['special']}")
            if row_db.get('desc_zh'):
                info_lines.append(f"效果: {row_db['desc_zh']}")
        else:
            info_lines.append("（wiki 图鉴中无此家具资料）")
        self.furn_info_lbl.configure(text="\n".join(info_lines))
        self.furn_detail_lbl.configure(text=f"key={key}  variant={rec.variant}  flags=({rec.flag1},{rec.flag2})")
        label = f"{zh or en} [{rec.name}]"
        if label in self.furn_label_to_code:
            self.furn_type_combo.set(label)
        self.furn_room_combo.set("家具仓库" if editable else self._room_to_display(rec.room))
        self.furn_x_entry.configure(state="normal")
        self.furn_y_entry.configure(state="normal")
        self.furn_x_entry.delete(0, "end"); self.furn_x_entry.insert(0, str(rec.x))
        self.furn_y_entry.delete(0, "end"); self.furn_y_entry.insert(0, str(rec.y))
        self._set_furniture_editable(editable)
        if editable:
            self.furn_lock_note.configure(text="📦 家具仓库中的未放置家具：可更换类型 / 移除；进入游戏后自由摆放。")
        else:
            self.furn_lock_note.configure(text="🔒 已放置到房间的家具仅展示属性，不提供修改（请在游戏中调整位置）。")

    def on_furniture_apply(self):
        if self.selected_furniture is None:
            self.status_bar.configure(text="请先在左侧选择一件家具！", text_color="#f59e0b")
            return
        rec = self.save_mgr.furniture.get(self.selected_furniture)
        if not rec:
            return
        if not self._is_warehouse_furniture(rec):
            self.status_bar.configure(text="已放置的家具不提供修改，仅家具仓库中的家具可编辑！", text_color="#f59e0b")
            return
        code = self.furn_label_to_code.get(self.furn_type_combo.get())
        if not code:
            self.status_bar.configure(text="无效的家具类型选择！", text_color="#f59e0b")
            return
        rec.name = code
        self.refresh_furniture_list()
        self.on_select_furniture(self.selected_furniture)
        self.status_bar.configure(text=f"家具类型已更换为 [{code}]（内存中），保存后生效。", text_color="#38bdf8")

    def on_furniture_delete(self):
        if self.selected_furniture is None:
            self.status_bar.configure(text="请先在左侧选择一件家具！", text_color="#f59e0b")
            return
        rec = self.save_mgr.remove_furniture(self.selected_furniture)
        self.selected_furniture = None
        self.refresh_furniture_list()
        self.furn_name_lbl.configure(text="请选择左侧家具")
        self.furn_info_lbl.configure(text="")
        self.furn_detail_lbl.configure(text="")
        if rec:
            self.status_bar.configure(text=f"已移除家具 [{rec.name}]（内存中），保存后生效。", text_color="#38bdf8")

    def on_furniture_add(self):
        code = self.furn_label_to_code.get(self.furn_add_combo.get())
        if not code:
            self.status_bar.configure(text="请选择要添加的家具类型！", text_color="#f59e0b")
            return
        rec = self.save_mgr.add_furniture(code, room='', x=0, y=0)  # 放入家具仓库
        self.refresh_furniture_list()
        self.on_select_furniture(rec.key)
        self.status_bar.configure(text=f"已添加家具 [{code}] 到家具仓库（内存中），保存后生效。", text_color="#38bdf8")

    # ================================================================
    # 职业通关角标视图（只读）
    # ================================================================

    CLASS_ZH = {
        'Colorless': '无项圈', 'Fighter': '战士', 'Mage': '法师', 'Hunter': '猎人',
        'Tank': '坦克', 'Medic': '牧师', 'Thief': '盗贼', 'Necromancer': '死灵法师',
        'Butcher': '屠夫', 'Druid': '德鲁伊', 'Monk': '武僧', 'Psychic': '灵能者',
        'Tinkerer': '工匠', 'Jester': '小丑',
    }
    CLASS_EN = {
        'Colorless': 'Collarless', 'Medic': 'Cleric', 'Psychic': 'Psychic',
        'Tinkerer': 'Tinkerer', 'Jester': 'Jester',
    }
    BADGE_ZONE_ZH = {
        'caves': ('🕳️', '洞穴'), 'boneyard': ('💀', '白骨墓园'), 'moon': ('🌙', '月球'),
        'core': ('🌋', '地核'), 'jurassic': ('🦖', '侏罗纪'), 'theend': ('💥', '终点'),
        'meatworld': ('🥩', '搏动领域'), 'dimensionx': ('🌀', '裂隙'), 'endoftime': ('⏳', '无限界'),
    }

    ROOM_ZH = {
        'Floor1_Large': '一层大厅', 'Floor1_Small': '一层侧卧', 'Attic': '阁楼',
        'Floor2_Large': '二层大厅', 'Floor2_Small': '二层小房间',
        'Basement0': '地下0层', 'Basement1': '地下1层', 'Basement2': '地下2层',
        'Basement3': '地下3层', 'Basement4': '地下4层',
    }

    def _room_zh(self, room):
        if not room:
            return ''
        return self.ROOM_ZH.get(room, room)

    def _official_text(self):
        """懒加载游戏官方文本 combined.csv，返回 {key: (en, zh)}；不可用时返回 {}。

        查找顺序: 仓库内 game_assets 解包副本 → Steam 默认游戏目录（官方中文补丁就地更新此文件）。
        """
        if hasattr(self, '_official_text_cache'):
            return self._official_text_cache
        candidates = [
            get_resource_path(os.path.join('game_assets', 'data', 'text', 'combined.csv')),
            r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\data\text\combined.csv',
        ]
        result = {}
        for path in candidates:
            if os.path.exists(path):
                try:
                    with open(path, encoding='utf-8-sig', newline='') as f:
                        rows = list(csv.reader(f))
                    if len(rows) > 1 and rows[0][-1].strip().lower() == 'zh':
                        for r in rows[1:]:
                            if len(r) >= len(rows[0]) and r[0] and not r[0].startswith('//'):
                                result[r[0]] = (r[1].strip(), r[-1].strip())
                        break
                except Exception:
                    pass
        self._official_text_cache = result
        return result

    def _official_name(self, key, fallback_en='', fallback_zh=''):
        """取官方本地化 (en, zh)；官方文本不可用时用内置兜底。"""
        entry = self._official_text().get(key)
        if entry and entry[1]:
            return entry
        return (fallback_en, fallback_zh)

    # ---- 职业名称：官方中文 ↔ 代码 转换 ----
    def _init_class_labels(self):
        self.CLASS_CODE_TO_LABEL = {}
        self.CLASS_LABEL_TO_CODE = {}
        for cls in self.game_data.get('classes', []):
            lbl = self._class_label(cls)
            self.CLASS_CODE_TO_LABEL[cls] = lbl
            self.CLASS_LABEL_TO_CODE[lbl] = cls

    def _class_zh(self, cls):
        o_en, o_zh = self._official_name(f"CAT_CLASS_{str(cls).upper()}_NAME", '', self.CLASS_ZH.get(cls, cls))
        return o_zh

    def _class_label(self, cls):
        """下拉框显示文本：官方中文 + 原代码。"""
        return f"{self._class_zh(cls)} ({cls})"

    def _class_to_label(self, cls):
        if not hasattr(self, 'CLASS_CODE_TO_LABEL'):
            self._init_class_labels()
        return self.CLASS_CODE_TO_LABEL.get(cls, cls)

    def _label_to_class(self, label):
        if not hasattr(self, 'CLASS_LABEL_TO_CODE'):
            self._init_class_labels()
        return self.CLASS_LABEL_TO_CODE.get(label, label)

    def build_completion_view(self):
        v = self.view_completion
        card = ctk.CTkFrame(v, fg_color="#14202e", corner_radius=10)
        card.pack(fill="both", expand=True, padx=10, pady=8)

        ctk.CTkLabel(card, text="🏅 职业通关进度（9 大章节角标）",
                     font=("Arial", 15, "bold"), text_color="#f59e0b").pack(anchor="w", padx=15, pady=(12, 2))
        ctk.CTkLabel(card, text="对应游戏内职业页面的 9 个角标（chapter_id_enum.gon: major_class_checkmarks）。\n"
                                "职业与章节名称对齐游戏官方中文补丁。数据来源：存档 npc_progress（只读）。✔ = 已通关此章节。",
                     font=("Arial", 11), text_color="#94a3b8", justify="left").pack(anchor="w", padx=15, pady=(0, 8))

        grid_holder = ctk.CTkScrollableFrame(card, fg_color="transparent")
        grid_holder.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.completion_grid = grid_holder

    def refresh_completion_grid(self):
        for w in self.completion_grid.winfo_children():
            w.destroy()
        recs = self.save_mgr.class_zone_records

        # 表头
        head = ctk.CTkFrame(self.completion_grid, fg_color="transparent")
        head.pack(fill="x", padx=4, pady=(2, 4))
        ctk.CTkLabel(head, text="职业", width=130, anchor="w", font=("Arial", 12, "bold"), text_color="#38bdf8").pack(side="left")
        for zone in MAJOR_CHECKMARK_ZONES:
            icon, zh_fb = self.BADGE_ZONE_ZH.get(zone, ('▫️', zone))
            _, zh = self._official_name(f"AREA_NAME_{zone.upper()}", '', zh_fb)
            ctk.CTkLabel(head, text=f"{icon}\n{zh}", width=86, font=("Arial", 11),
                         text_color="#38bdf8", justify="center").pack(side="left", padx=2)
        ctk.CTkLabel(head, text="进度", width=60, font=("Arial", 12, "bold"), text_color="#38bdf8").pack(side="left", padx=(8, 0))

        classes = ['Colorless', 'Fighter', 'Mage', 'Hunter', 'Tank', 'Medic', 'Thief',
                   'Necromancer', 'Butcher', 'Druid', 'Monk', 'Psychic', 'Tinkerer', 'Jester']
        for cls in classes:
            row = ctk.CTkFrame(self.completion_grid, fg_color="#1e293b", corner_radius=6)
            row.pack(fill="x", padx=4, pady=2)
            zh_fb = self.CLASS_ZH.get(cls, cls)
            en_fb = self.CLASS_EN.get(cls, cls)
            o_en, o_zh = self._official_name(f"CAT_CLASS_{cls.upper()}_NAME", en_fb, zh_fb)
            ctk.CTkLabel(row, text=f"{o_zh}\n{o_en}", width=130, anchor="w", justify="left",
                         font=("Arial", 11, "bold")).pack(side="left", padx=4, pady=3)
            cleared_n = 0
            for zone in MAJOR_CHECKMARK_ZONES:
                r = recs.get((cls, zone))
                cleared = bool(r and r[0] == -1)
                visits = r[2] if r else 0
                if cleared:
                    cleared_n += 1
                    cell = ctk.CTkLabel(row, text="✔", width=86, height=34, corner_radius=6,
                                        fg_color="#14532d", text_color="#4ade80", font=("Arial", 15, "bold"))
                else:
                    tip = f"（已进入 x{visits}，未通关）" if visits else ""
                    cell = ctk.CTkLabel(row, text="·", width=86, height=34, corner_radius=6,
                                        fg_color="#0f172a", text_color="#475569", font=("Arial", 13))
                cell.pack(side="left", padx=2, pady=3)
            pct = f"{cleared_n}/9"
            color = "#4ade80" if cleared_n == 9 else ("#f59e0b" if cleared_n else "#64748b")
            ctk.CTkLabel(row, text=pct, width=60, font=("Arial", 12, "bold"), text_color=color).pack(side="left", padx=(8, 0))

    def open_slot_selector(self):
        SaveSlotDialog(self, on_select_callback=self.switch_to_save)

    def on_browse(self):
        f = filedialog.askopenfilename(
            title="选择 Mewgenics 存档文件 (.sav)",
            filetypes=[("Mewgenics Save (*.sav)", "*.sav"), ("All Files (*.*)", "*.*")],
            initialdir=MewgenicsSaveManager.get_saves_dir()
        )
        if f:
            self.switch_to_save(f)

    def on_reload(self):
        self.save_mgr.load()
        self.update_save_header_info()
        self.populate_cat_list()
        self.show_empty_state()
        if hasattr(self, 'item_list'):
            self.refresh_item_list()
            self.refresh_furniture_list()
            self.refresh_shop_progress()
            self.refresh_completion_grid()
        self.status_bar.configure(text="已重新从磁盘加载存档数据！", text_color="#38bdf8")

    def on_save(self):
        self.save_current_cat_fields()
        self.populate_cat_list(self.search_entry.get().strip())
        
        # Update global resources
        try:
            self.save_mgr.properties['house_gold'] = int(self.entry_gold.get())
            self.save_mgr.properties['house_food'] = int(self.entry_food.get())
            self.save_mgr.properties['current_day'] = int(self.entry_day.get())
        except ValueError:
            messagebox.showerror("格式错误", "金币/食物/天数必须为有效整数！")
            return

        try:
            bk = self.save_mgr.save()
            messagebox.showinfo("保存成功", f"修改已成功写入游戏存档！\n\n系统已自动备份原存档至:\n{bk}")
            self.status_bar.configure(text="存档保存成功！原存档已安全备份。", text_color="#10b981")
        except Exception as e:
            messagebox.showerror("保存失败", f"写入存档时出错: {e}")

if __name__ == "__main__":
    app = MewgenicsApp()
    app.mainloop()
