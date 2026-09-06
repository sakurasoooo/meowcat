import os
import sys
import json
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

from mewgenics_core import MewgenicsSaveManager, CatRecord, MUTATION_SLOTS

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
        self.recessive_combos = {}
        self.mutation_badge_labels = {}
        self.active_combos = []
        self.upgrade_combos = []
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

        # 2. Main Body (Split Pane: Left Sidebar & Right Content)
        self.main_body = ctk.CTkFrame(self)
        self.main_body.pack(fill="both", expand=True, padx=10, pady=5)

        self.setup_left_sidebar()
        self.setup_right_content()

        # 3. Bottom Status Bar
        self.status_bar = ctk.CTkLabel(self, text="就绪 - 已成功读取存档", anchor="w", font=("Arial", 11), text_color="#aaa")
        self.status_bar.pack(fill="x", padx=15, pady=(2, 5))

    def setup_left_sidebar(self):
        self.left_pane = ctk.CTkFrame(self.main_body, width=330)
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
        self.right_pane = ctk.CTkFrame(self.main_body)
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
            ("🧬 10 大部位基因突变", "身体/头部/尾部/四肢等 10 部位突变，显性表达与隐性遗传双轨可调"),
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

        # 1. Quick Presets Header
        preset_frame = ctk.CTkFrame(container, fg_color="#0f172a", corner_radius=8)
        preset_frame.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(preset_frame, text="突变预设:", font=("Arial", 12, "bold"), text_color="#a855f7").pack(side="left", padx=(12, 6), pady=6)
        ctk.CTkButton(preset_frame, text="✨ 一键极品正面突变全满", width=170, height=26, fg_color="#7c3aed", hover_color="#6d28d9", command=self.on_apply_god_mutations).pack(side="left", padx=4)
        ctk.CTkButton(preset_frame, text="🧼 一键清除全部突变 (纯血统)", width=170, height=26, fg_color="#334155", hover_color="#475569", command=self.on_clear_all_mutations).pack(side="left", padx=4)

        # Unlock Recessive Toggle Checkbox (Default: Locked / Read-Only)
        self.var_unlock_recessive = tk.BooleanVar(value=False)
        self.chk_unlock_recessive = ctk.CTkCheckBox(
            preset_frame,
            text="🔓 解锁修改隐性基因 (默认只读)",
            variable=self.var_unlock_recessive,
            font=("Arial", 11, "bold"),
            text_color="#c084fc",
            fg_color="#a855f7",
            hover_color="#9333ea",
            command=self.on_toggle_recessive_lock
        )
        self.chk_unlock_recessive.pack(side="right", padx=10)

        # Tip Banner
        tip_frame = ctk.CTkFrame(container, fg_color="#1e293b", corner_radius=6)
        tip_frame.pack(fill="x", padx=10, pady=(0, 6))
        tip_text = "💡 [等位基因机制] 显性基因决定当前外观与战斗属性；隐性基因携带在基因链中用于遗传给子代。隐性基因默认只读显示（不可修改），勾选右上角可解锁编辑！"
        ctk.CTkLabel(tip_frame, text=tip_text, font=("Arial", 11), text_color="#94a3b8").pack(padx=10, pady=5)

        # 2. 10 Mutation Cards (Dominant + Recessive)
        mut_detailed = self.game_data.get('mutations_detailed', {})
        self.mutation_combos = {}
        self.recessive_combos = {}
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
            option_values = ['无突变 (普通外观 / Pure)'] + [e['display'] for e in slot_entries]

            # Dominant Allele
            ctk.CTkLabel(row, text="显性:", font=("Arial", 11, "bold"), text_color="#38bdf8").pack(side="left", padx=(2, 2))
            cb = ctk.CTkComboBox(
                row,
                width=245,
                values=option_values,
                command=lambda val, sk=slot_key: self.on_mutation_selected(sk, val)
            )
            cb.pack(side="left", padx=3)
            self.mutation_combos[slot_key] = cb

            # Recessive Allele
            ctk.CTkLabel(row, text="隐性:", font=("Arial", 11, "bold"), text_color="#c084fc" if off2 else "#64748b").pack(side="left", padx=(6, 2))

            if off2:
                cb_rec = ctk.CTkComboBox(
                    row,
                    width=245,
                    values=option_values,
                    state="disabled",  # 默认不可修改！
                    command=lambda val, sk=slot_key: self.on_recessive_mutation_selected(sk, val)
                )
                cb_rec.pack(side="left", padx=3)
                self.recessive_combos[slot_key] = cb_rec

                badge = ctk.CTkLabel(row, text="[纯合显性]", font=("Arial", 11, "bold"), text_color="#10b981", width=75, anchor="w")
                badge.pack(side="left", padx=5)
                self.mutation_badge_labels[slot_key] = badge
            else:
                lbl_single = ctk.CTkLabel(row, text="[单等位基因 - 无隐性携带]", font=("Arial", 11), text_color="#64748b", width=245, anchor="w")
                lbl_single.pack(side="left", padx=3)

                badge = ctk.CTkLabel(row, text="[单基因]", font=("Arial", 11), text_color="#64748b", width=75, anchor="w")
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
        self.combo_class = ctk.CTkComboBox(f_class, width=280, values=self.game_data.get('classes', []), command=self.on_class_changed)
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

        # Boon
        f_boon = ctk.CTkFrame(f_ident, fg_color="transparent")
        f_boon.pack(fill="x", padx=15, pady=(4, 12))
        ctk.CTkLabel(f_boon, text="偏好属性 (Boon):", width=140, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.combo_boon = ctk.CTkComboBox(f_boon, width=280, values=['none', 'str', 'dex', 'con', 'int', 'spd', 'cha', 'lck'])
        self.combo_boon.pack(side="left", padx=5)

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
        self.combo_atk = ctk.CTkComboBox(f_atk, width=320, values=ab_names)
        self.combo_atk.pack(side="left", padx=5)

        f_mov = ctk.CTkFrame(f_base, fg_color="transparent")
        f_mov.pack(fill="x", padx=15, pady=(3, 8))
        ctk.CTkLabel(f_mov, text="移动方式 (Move Ability):", width=180, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        self.combo_move = ctk.CTkComboBox(f_mov, width=320, values=['DefaultMove'] + ab_names)
        self.combo_move.pack(side="left", padx=5)

        # 2. 4 Active Abilities + 4 Ability Upgrades
        f_acts = ctk.CTkFrame(container, fg_color="#1e293b", corner_radius=8)
        f_acts.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(f_acts, text="🔮 主动战斗技能与进阶附魔 (Active Spells & Ability Upgrades 1 - 4):", font=("Arial", 13, "bold"), text_color="#a855f7").pack(anchor="w", padx=15, pady=(8, 4))

        self.active_combos = []
        self.upgrade_combos = []
        for i in range(4):
            f_row = ctk.CTkFrame(f_acts, fg_color="transparent")
            f_row.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(f_row, text=f"主动法术 {i+1}:", width=95, anchor="w", font=("Arial", 12)).pack(side="left")
            cb_act = ctk.CTkComboBox(f_row, width=250, values=['None'] + ab_names)
            cb_act.pack(side="left", padx=(0, 15))
            self.active_combos.append(cb_act)

            ctk.CTkLabel(f_row, text=f"进阶附魔 {i+1}:", width=95, anchor="w", font=("Arial", 12)).pack(side="left")
            cb_upg = ctk.CTkComboBox(f_row, width=250, values=['None'] + ab_names)
            cb_upg.pack(side="left", padx=(0, 5))
            self.upgrade_combos.append(cb_upg)

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
            cb = ctk.CTkComboBox(f_row, width=580, values=['None (无被动)'])
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
            cb = ctk.CTkComboBox(f_row, width=580, values=self.disorder_display_list)
            cb.pack(side="left", padx=5)
            self.disorder_combos.append(cb)

        # Compatibility alias
        self.passive_combos = self.upgrade_combos + self.class_passive_combos + self.disorder_combos

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
            disp = f"★ [{cat_class}] {name} ({k}) - {clean_desc}"
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
        if self.current_cat:
            self.current_cat.cat_class = new_class
        self.update_class_passive_options(new_class)

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

            # 2. Search filter
            if ft:
                if (ft not in cat.name.lower() and 
                    ft not in str(k) and 
                    ft not in cat.cat_class.lower() and 
                    ft not in room_str.lower()):
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

            # Card text & styling
            if is_in_house:
                room_display = f" [{cat.house_room}]" if cat.house_room else " [在生]"
                card_text = f"#{k:3d}  {cat.name:<8} [{cat.cat_class}]{room_display}"
                btn_fg = "#143026"
                btn_hover = "#1b4d3e"
            else:
                card_text = f"#{k:3d}  {cat.name:<8} [{cat.cat_class}] [历史]"
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
        self.lbl_cat_title.configure(text=f"猫咪 #{cat.key} - {cat.name} ({cat.cat_class})")
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
        self.combo_class.set(cat.cat_class)
        self.combo_voice.set(cat.voice)
        self.slider_pitch.set(cat.pitch)
        self.lbl_pitch_val.configure(text=f"{cat.pitch:.2f}")
        self.combo_boon.set(cat.boon)

        # Update Abilities Tab
        self.combo_atk.set(cat.attack_ability)
        self.combo_move.set(getattr(cat, 'move_ability', 'DefaultMove'))
        for i in range(4):
            val = cat.active_abilities[i] if i < len(cat.active_abilities) else 'None'
            self.active_combos[i].set(val)

        for i in range(4):
            val = cat.ability_upgrades[i] if i < len(cat.ability_upgrades) else 'None'
            self.upgrade_combos[i].set(val)

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
        cat.cat_class = self.combo_class.get()
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
            cat.active_abilities[i] = self.active_combos[i].get()

        for i in range(4):
            cat.ability_upgrades[i] = self.upgrade_combos[i].get()

        for i in range(2):
            raw = self.class_passive_combos[i].get()
            cat.class_passives[i] = self.get_class_passive_key_from_val(raw)

        for i in range(2):
            raw = self.disorder_combos[i].get()
            cat.disorders[i] = self.get_disorder_key_from_val(raw)

        cat.sync_legacy_passives()

        # Ensure dominant mutations are synced
        for slot_key, slot_cn, off1, off2 in MUTATION_SLOTS:
            cb = self.mutation_combos.get(slot_key)
            if cb:
                val = cb.get()
                if "无突变" in val:
                    norm_id = 246 if slot_key == 'texture' else 100
                    if cat.mutations.get(slot_key) != norm_id:
                        cat.set_mutation(slot_key, norm_id)
                else:
                    m = re.search(r'#(\d+)', val)
                    if m:
                        mid = int(m.group(1))
                        if cat.mutations.get(slot_key) != mid:
                            cat.set_mutation(slot_key, mid)

        # Ensure recessive mutations are synced if unlocked
        if getattr(self, 'var_unlock_recessive', None) and self.var_unlock_recessive.get():
            for slot_key, cb in self.recessive_combos.items():
                val = cb.get()
                if "无突变" in val:
                    norm_id = 100
                    if getattr(cat, 'recessive_mutations', {}).get(slot_key) != norm_id:
                        cat.set_recessive_mutation(slot_key, norm_id)
                else:
                    m = re.search(r'#(\d+)', val)
                    if m:
                        mid = int(m.group(1))
                        if getattr(cat, 'recessive_mutations', {}).get(slot_key) != mid:
                            cat.set_recessive_mutation(slot_key, mid)

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

    def on_toggle_recessive_lock(self):
        unlocked = self.var_unlock_recessive.get()
        state = "normal" if unlocked else "disabled"
        for sk, cb in self.recessive_combos.items():
            cb.configure(state=state)
        msg = "已解锁隐性基因编辑模式，可自由定制后代遗传携带库！" if unlocked else "隐性基因已锁定为只读查看模式。"
        self.status_bar.configure(text=msg, text_color="#c084fc" if unlocked else "#94a3b8")

    def refresh_mutation_ui(self):
        if not self.current_cat:
            return
        cat = self.current_cat
        mut_detailed = self.game_data.get('mutations_detailed', {})

        for slot_key, slot_cn, off1, off2 in MUTATION_SLOTS:
            mid = cat.mutations.get(slot_key, 0)
            cb = self.mutation_combos.get(slot_key)
            badge = self.mutation_badge_labels.get(slot_key)
            cb_rec = self.recessive_combos.get(slot_key)
            entries = mut_detailed.get(slot_key, [])

            # 1. Update Dominant
            if cb:
                if mid < 300:
                    cb.set("无突变 (普通外观 / Pure)")
                else:
                    match_entry = next((e for e in entries if e.get('id') == mid), None)
                    if match_entry:
                        cb.set(match_entry['display'])
                    else:
                        cb.set(f"#{mid} 基因突变")

            # 2. Update Recessive (if paired slot)
            if off2 and cb_rec:
                r_id = getattr(cat, 'recessive_mutations', {}).get(slot_key, mid)
                if r_id is None:
                    r_id = mid
                if r_id < 300:
                    val_to_set = "无突变 (普通外观 / Pure)"
                else:
                    match_r = next((e for e in entries if e.get('id') == r_id), None)
                    if match_r:
                        val_to_set = match_r['display']
                    else:
                        val_to_set = f"#{r_id} 基因突变"

                was_disabled = (cb_rec.cget('state') == 'disabled')
                if was_disabled:
                    cb_rec.configure(state='normal')
                cb_rec.set(val_to_set)
                if was_disabled:
                    cb_rec.configure(state='disabled')

                # Badge status: Homozygous vs Heterozygous
                if badge:
                    if mid == r_id:
                        if mid >= 300:
                            badge.configure(text="[纯合显性]", text_color="#10b981")
                        else:
                            badge.configure(text="[纯正外观]", text_color="#94a3b8")
                    else:
                        if r_id >= 300 and mid < 300:
                            badge.configure(text="[隐性携带]", text_color="#c084fc")
                        elif mid >= 300 and r_id < 300:
                            badge.configure(text="[杂合表达]", text_color="#f59e0b")
                        else:
                            badge.configure(text="[双突杂合]", text_color="#38bdf8")
            elif not off2 and badge:
                badge.configure(text="[单基因]", text_color="#64748b")

    def on_mutation_selected(self, slot_key, val):
        if not self.current_cat:
            return
        cat = self.current_cat
        if "无突变" in val:
            norm_id = 246 if slot_key == 'texture' else 100
            cat.set_mutation(slot_key, norm_id, sync_recessive=False)
        else:
            m = re.search(r'#(\d+)', val)
            if m:
                mid = int(m.group(1))
                cat.set_mutation(slot_key, mid, sync_recessive=False)

        self.refresh_mutation_ui()
        for k in CatRecord.STAT_NAMES:
            self.update_stat_display(k)
        self.status_bar.configure(text=f"已更新 {slot_key} 显性突变: {val}，属性面板已实时联动刷新！", text_color="#a855f7")

    def on_recessive_mutation_selected(self, slot_key, val):
        if not self.current_cat:
            return
        cat = self.current_cat
        if "无突变" in val:
            norm_id = 100
            cat.set_recessive_mutation(slot_key, norm_id)
        else:
            m = re.search(r'#(\d+)', val)
            if m:
                mid = int(m.group(1))
                cat.set_recessive_mutation(slot_key, mid)
        self.refresh_mutation_ui()
        self.status_bar.configure(text=f"已更新 {slot_key} 隐性携带基因: {val} (用于遗传给子代，不改变当前外观与属性)", text_color="#c084fc")

    def on_apply_god_mutations(self):
        if not self.current_cat:
            return
        self.current_cat.apply_god_mutations()
        self.refresh_mutation_ui()
        for k in CatRecord.STAT_NAMES:
            self.update_stat_display(k)
        self.status_bar.configure(text="✨ 已为当前猫咪配置全套极品正面突变！双等位基因纯合显性，配种 100% 稳定遗传。", text_color="#a855f7")

    def on_clear_all_mutations(self):
        if not self.current_cat:
            return
        self.current_cat.clear_all_mutations()
        self.refresh_mutation_ui()
        for k in CatRecord.STAT_NAMES:
            self.update_stat_display(k)
        self.status_bar.configure(text="🧼 已清除当前猫咪全部突变，10 大部位回归纯血纯正外观！", text_color="#38bdf8")

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
        cb_cls = ctk.CTkComboBox(f2, width=240, values=self.game_data.get('classes', []))
        cb_cls.set("Mage")
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
            c_class = cb_cls.get()
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
