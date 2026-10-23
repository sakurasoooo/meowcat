"""突变图标选择器：真实游戏手绘贴图网格 + 搜索 + 翻页 + 正/负/特效/缺陷分类 + 悬停效果说明。
贴图来源于游戏 catparts.swf 矢量资源提取（755+ 真实外观）。
"""
import os
import sys
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont
from mewgenics_core import format_mutation_markup

# ---- 磁贴样式 ----
CATEGORY_COLORS = {
    'positive': '#22c55e',   # 正面：绿
    'negative': '#ef4444',   # 负面：红
    'effect':   '#38bdf8',   # 中性/特效：蓝
    'defect':   '#f59e0b',   # 出生缺陷：橙
    'normal':   '#64748b',   # 无突变：灰
    'missing':  '#7f1d1d',   # 部位缺失：暗红
}
CATEGORY_LABELS = {
    'positive': '✔ 正面', 'negative': '✖ 负面', 'effect': '⚡ 特效',
    'defect': '🐣 缺陷', 'normal': 'Ø 无突变', 'missing': '🚫 缺失',
}
TILE_BG = '#1e293b'
STAT_ZH = {'str': '力量', 'dex': '敏捷', 'con': '体质', 'int': '智力', 'spd': '速度', 'cha': '魅力', 'lck': '运气'}

_font_cache = {}
_MUT_TILE_CACHE = {}

def _font(size, bold=True):
    key = (size, bold)
    if key not in _font_cache:
        for name in ('arialbd.ttf' if bold else 'arial.ttf', 'arial.ttf'):
            try:
                _font_cache[key] = ImageFont.truetype(os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', name), size)
                break
            except Exception:
                continue
        else:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


def classify_mutation(entry, defect_ids):
    """正面/负面/特效/缺陷 分类：缺陷优先，其余按净属性值。"""
    if entry.get('id') == -2:
        return 'missing'
    if entry.get('id', 0) < 300:
        return 'normal'
    if entry.get('id') in defect_ids:
        return 'defect'
    net = sum((entry.get('stats') or {}).values())
    if net > 0:
        return 'positive'
    if net < 0:
        return 'negative'
    return 'effect'


# 手臂与腿共用 legs.gon / CatLeg 帧（同一突变 ID），没有独立 arms 贴图目录
_MUTATION_ICON_SLOT_ALIAS = {
    'arms': 'legs',
}


def get_mutation_icon_path(slot_key, mid):
    if not slot_key or mid is None:
        return None
    icon_slot = _MUTATION_ICON_SLOT_ALIAS.get(slot_key, slot_key)
    base_dirs = []
    if hasattr(sys, '_MEIPASS'):
        base_dirs.append(sys._MEIPASS)
    exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else None
    if exe_dir:
        base_dirs.append(exe_dir)
    base_dirs.append(os.path.dirname(os.path.abspath(__file__)))
    base_dirs.append(os.getcwd())

    for b in base_dirs:
        p = os.path.join(b, "assets", "icons", "mutations", icon_slot, f"{mid}.png")
        if os.path.exists(p):
            return p
    return None


def make_tile(entry, category, size=72, slot_key=None):
    """生成突变磁贴：
    若有游戏原生贴图 (assets/icons/mutations/<slot_key>/<id>.png)，合成真实手绘原画；
    否则平滑回退为程序生成分类色块磁贴。
    包含：分类色边框 + 真实图/ID + 净属性徽章。
    """
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    border = CATEGORY_COLORS.get(category, '#64748b')
    w = max(2, size // 16)
    d.rounded_rectangle([1, 1, size - 2, size - 2], radius=size // 8, fill=TILE_BG, outline=border, width=w)

    mid = entry.get('id', 0)
    
    # 尝试加载官方贴图
    icon_path = None
    if category == 'normal':
        # 针对无突变，尝试加载基准外观 (100 或 246)
        norm_id = 246 if slot_key == 'texture' else 100
        icon_path = get_mutation_icon_path(slot_key, mid if mid and mid >= 0 else norm_id)
        if not icon_path and mid != norm_id:
            icon_path = get_mutation_icon_path(slot_key, norm_id)
    elif category != 'missing' and mid and mid >= 300:
        icon_path = get_mutation_icon_path(slot_key, mid)

    has_texture = False
    if icon_path and os.path.exists(icon_path):
        try:
            with Image.open(icon_path) as raw_icon:
                icon_rgba = raw_icon.convert('RGBA')
                pad = max(3, size // 12)
                inner = size - pad * 2
                scale = min(inner / icon_rgba.width, inner / icon_rgba.height)
                nw = max(1, int(icon_rgba.width * scale))
                nh = max(1, int(icon_rgba.height * scale))
                res_icon = icon_rgba.resize((nw, nh), Image.Resampling.LANCZOS)
                px = (size - nw) // 2
                py = (size - nh) // 2
                img.paste(res_icon, (px, py), res_icon)
                has_texture = True
        except Exception:
            has_texture = False

    # 若无贴图，绘制符号或文本 ID 回退
    if not has_texture:
        if category == 'normal':
            txt = 'Ø'
        elif category == 'missing':
            txt = '✕'
        else:
            txt = f'#{mid}'
        f = _font(int(size * 0.30))
        bbox = d.textbbox((0, 0), txt, font=f)
        d.text(((size - bbox[2] + bbox[0]) / 2, size * 0.28 - (bbox[3] - bbox[1]) / 2), txt, font=f, fill='#f8fafc')
    else:
        # 有贴图时，如果在较大尺寸 (>= 48)，在左上角附带极简 #mid 标识
        if size >= 48 and category not in ('normal', 'missing'):
            idf = _font(max(8, int(size * 0.13)))
            id_txt = f'#{mid}'
            d.text((4, 3), id_txt, font=idf, fill='#94a3b8')

    # 属性角标 (净属性值)
    if category in ('positive', 'negative', 'effect', 'defect'):
        net = sum((entry.get('stats') or {}).values())
        badge = (f'+{net}' if net > 0 else str(net)) if net != 0 else 'FX'
        bc = '#22c55e' if net > 0 else ('#ef4444' if net < 0 else '#38bdf8')
        
        if size >= 44:
            # 大中图标绘制右下角药丸徽章
            bf = _font(int(size * 0.18))
            bb = d.textbbox((0, 0), badge, font=bf)
            bw, bh = bb[2] - bb[0], bb[3] - bb[1]
            pill_pad = 2
            pill_x1 = size - bw - pill_pad * 2 - 4
            pill_y1 = size - bh - pill_pad * 2 - 4
            d.rounded_rectangle([pill_x1, pill_y1, size - 3, size - 3], radius=3, fill='#0f172a', outline=bc, width=1)
            d.text((pill_x1 + pill_pad, pill_y1 + pill_pad - 1), badge, font=bf, fill=bc)
        elif not has_texture:
            bf = _font(int(size * 0.20))
            bbox = d.textbbox((0, 0), badge, font=bf)
            d.text(((size - bbox[2] + bbox[0]) / 2, size * 0.68), badge, font=bf, fill=bc)

    return img


class MutationPicker(ctk.CTkToplevel):
    """突变图标选择面板。
    entries: mutations_detailed 该部位条目列表 (id/name/stats/stat_str/desc/display)
    defect_ids: 出生缺陷 id 集合
    current_id: 当前部件 id（用于高亮）
    on_pick(mutation_id): 选择回调（普通外观传 norm_id，缺失传 -2）
    slot_key: 部位标识（head, ears, tail, body, legs, eyes, mouth, eyebrows, texture）
    """
    COLS = 6
    ROWS = 4
    PER_PAGE = COLS * ROWS
    CATEGORIES = [('all', '全部'), ('positive', '✔ 正面'), ('negative', '✖ 负面'),
                  ('effect', '⚡ 特效'), ('defect', '🐣 缺陷')]

    def __init__(self, parent, title, entries, defect_ids, current_id, norm_id, on_pick, slot_key=None):
        super().__init__(parent)
        self.title(title)
        self.geometry('1180x620')
        self.minsize(1100, 580)
        self.resizable(True, True)
        self.configure(fg_color='#0f172a')
        self.transient(parent.winfo_toplevel())

        self.entries_all = list(entries)
        self.defect_ids = defect_ids
        self.on_pick = on_pick
        self.norm_id = norm_id
        self.current_id = current_id
        self.slot_key = slot_key
        self.page = 0
        self.category = 'all'
        self.query = ''

        # 伪条目：无突变 / 部位缺失
        self.special_entries = [
            {'id': norm_id, 'name': '无突变 Pure', 'stats': {}, 'stat_str': '', 'desc': '普通原版外观', '_cat': 'normal'},
            {'id': -2, 'name': '部位缺失 Missing', 'stats': {}, 'stat_str': '', 'desc': '该部位完全缺失（出生缺陷 -2）', '_cat': 'missing'},
        ]

        # ---- 顶部：搜索 + 分类 ----
        top = ctk.CTkFrame(self, fg_color='transparent')
        top.pack(fill='x', padx=12, pady=(10, 4))
        self.search_var = tk.StringVar()
        se = ctk.CTkEntry(top, placeholder_text='🔍 搜索名称 / 描述 / 属性...', textvariable=self.search_var, width=320)
        se.pack(side='left', padx=(0, 10))
        se.bind('<KeyRelease>', lambda e: self._schedule_filter())
        se.bind('<Return>', lambda e: self._on_filter())
        self.seg = ctk.CTkSegmentedButton(top, values=[lbl for _, lbl in self.CATEGORIES], command=self._on_category)
        self.seg.set('全部')
        self.seg.pack(side='left')

        # ---- 主体：左网格 + 右详情（详情列固定宽度，不被格子挤掉） ----
        DETAIL_W = 300
        body = ctk.CTkFrame(self, fg_color='transparent')
        body.pack(fill='both', expand=True, padx=12, pady=4)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0, minsize=DETAIL_W)
        body.grid_rowconfigure(0, weight=1)

        self.grid_frame = ctk.CTkFrame(body, fg_color='#111827', corner_radius=8)
        self.grid_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        for c in range(self.COLS):
            self.grid_frame.grid_columnconfigure(c, weight=1, uniform='mutcol')
        for r in range(self.ROWS):
            self.grid_frame.grid_rowconfigure(r, weight=1)
        self._slots = []
        for i in range(self.PER_PAGE):
            btn = ctk.CTkButton(
                self.grid_frame, text='', compound='top',
                width=88, height=108, font=('Arial', 9),
                fg_color='#1e293b', border_width=2, border_color='#64748b',
                hover_color='#475569',
            )
            self._slots.append(btn)

        self.detail = ctk.CTkFrame(body, fg_color='#111827', corner_radius=8, width=DETAIL_W)
        self.detail.grid(row=0, column=1, sticky='nsew')
        self.detail.grid_propagate(False)
        self._d_hint = ctk.CTkLabel(self.detail, text='🖱 悬停查看详情\n点击图标直接选用',
                                   font=('Arial', 12), text_color='#64748b', justify='center')
        self._d_cat = ctk.CTkLabel(self.detail, text='', font=('Arial', 12, 'bold'))
        self._d_img = ctk.CTkLabel(self.detail, text='')
        self._d_name = ctk.CTkLabel(self.detail, text='', font=('Arial', 13, 'bold'),
                                   text_color='#f8fafc', wraplength=DETAIL_W - 28)
        self._d_stat = ctk.CTkLabel(self.detail, text='', font=('Arial', 12, 'bold'),
                                   text_color='#fbbf24', wraplength=DETAIL_W - 28)
        self._d_desc = ctk.CTkLabel(self.detail, text='', font=('Arial', 11), text_color='#cbd5e1',
                                   wraplength=DETAIL_W - 28, justify='left')
        self._d_id = ctk.CTkLabel(self.detail, text='', font=('Arial', 10), text_color='#64748b')
        self._detail_widgets = (self._d_cat, self._d_img, self._d_name, self._d_stat, self._d_desc, self._d_id)

        # ---- 底部翻页 ----
        nav = ctk.CTkFrame(self, fg_color='transparent')
        nav.pack(fill='x', padx=12, pady=(4, 10))
        self.btn_prev = ctk.CTkButton(nav, text='‹ 上一页', width=90, command=lambda: self._turn(-1))
        self.btn_prev.pack(side='left')
        self.lbl_page = ctk.CTkLabel(nav, text='1/1', font=('Arial', 12, 'bold'))
        self.lbl_page.pack(side='left', expand=True)
        self.btn_next = ctk.CTkButton(nav, text='下一页 ›', width=90, command=lambda: self._turn(1))
        self.btn_next.pack(side='right')

        self._show_detail(None)
        self._refresh()
        se.focus_set()

    # ---------- 数据 ----------
    def _classified(self):
        out = []
        for e in self.special_entries + self.entries_all:
            cat = e.get('_cat') or classify_mutation(e, self.defect_ids)
            out.append((e, cat))
        return out

    def _filtered(self):
        items = self._classified()
        if self.category != 'all':
            if self.category == 'defect':
                items = [(e, c) for e, c in items if c in ('defect', 'missing')]
            else:
                items = [(e, c) for e, c in items if c == self.category]
        q = self.query.strip().lower()
        if q:
            def hit(e):
                hay = f"{e.get('id')} {e.get('name','')} {e.get('name_en','')} {e.get('desc','')} {e.get('stat_str','')}".lower()
                return q in hay
            items = [(e, c) for e, c in items if hit(e)]
        return items

    # ---------- UI ----------
    def _tile(self, entry, category, size):
        key = (self.slot_key, entry.get('id'), category, size)
        hit = _MUT_TILE_CACHE.get(key)
        if hit is not None:
            return hit
        img = ctk.CTkImage(make_tile(entry, category, size, slot_key=self.slot_key), size=(size, size))
        _MUT_TILE_CACHE[key] = img
        return img

    def _schedule_filter(self):
        job = getattr(self, '_filter_job', None)
        if job:
            try:
                self.after_cancel(job)
            except Exception:
                pass
        self._filter_job = self.after(200, self._on_filter)

    def _on_filter(self):
        self._filter_job = None
        self.query = self.search_var.get()
        self.page = 0
        self._refresh()

    def _on_category(self, lbl):
        self.category = dict((l, k) for k, l in self.CATEGORIES).get(lbl, 'all')
        self.page = 0
        self._refresh()

    def _turn(self, d):
        items = self._filtered()
        max_page = max(0, (len(items) - 1) // self.PER_PAGE)
        self.page = min(max(0, self.page + d), max_page)
        self._refresh()

    def _refresh(self):
        items = self._filtered()
        max_page = max(0, (len(items) - 1) // self.PER_PAGE)
        self.page = min(self.page, max_page)
        page_items = items[self.page * self.PER_PAGE : (self.page + 1) * self.PER_PAGE]

        for i, btn in enumerate(self._slots):
            if i >= len(page_items):
                btn.grid_remove()
                continue
            e, cat = page_items[i]
            is_cur = (e.get('id') == self.current_id)
            mid = e.get('id', 0)
            if mid >= 300:
                short = f'#{mid}'
            else:
                short = (e.get('name') or '')[:8]
            btn.configure(
                text=short, image=self._tile(e, cat, 56),
                fg_color='#334155' if is_cur else '#1e293b',
                border_color='#f8fafc' if is_cur else CATEGORY_COLORS.get(cat, '#64748b'),
                command=lambda ent=e: self._pick(ent),
            )
            btn.unbind('<Enter>')
            btn.bind('<Enter>', lambda ev, ent=e, cc=cat: self._show_detail(ent, cc))
            r, c = divmod(i, self.COLS)
            btn.grid(row=r, column=c, padx=6, pady=6, sticky='nsew')

        self.lbl_page.configure(text=f'{self.page + 1}/{max_page + 1} 页  (共 {len(items)} 项)')
        self.btn_prev.configure(state='normal' if self.page > 0 else 'disabled')
        self.btn_next.configure(state='normal' if self.page < max_page else 'disabled')

    def _show_detail(self, e, cat=None):
        for w in self._detail_widgets:
            w.pack_forget()
        self._d_hint.pack_forget()
        if not e:
            self._d_hint.pack(expand=True)
            return
        cat = cat or e.get('_cat') or classify_mutation(e, self.defect_ids)
        self._d_cat.configure(text=CATEGORY_LABELS.get(cat, cat),
                             text_color=CATEGORY_COLORS.get(cat, '#94a3b8'))
        self._d_cat.pack(pady=(14, 2))
        self._d_img.configure(image=self._tile(e, cat, 108))
        self._d_img.pack(pady=4)
        name = format_mutation_markup(e.get('name') or e.get('name_en') or '')
        desc = format_mutation_markup(e.get('desc') or '')
        if name:
            self._d_name.configure(text=name)
            self._d_name.pack(pady=(2, 0), padx=12)
        stat_str = e.get('stat_str') or ''
        if stat_str:
            self._d_stat.configure(text=stat_str)
            self._d_stat.pack(pady=(2, 0))
        name_key = name.rstrip('。. ')
        desc_key = desc.replace('\n', ' ').rstrip('。. ')
        if desc and desc_key != name_key:
            self._d_desc.configure(text=desc)
            self._d_desc.pack(padx=12, pady=(8, 4), anchor='w')
        elif not desc and not stat_str:
            self._d_desc.configure(text='（无特殊效果）')
            self._d_desc.pack(padx=12, pady=(8, 4), anchor='w')
        if e.get('id', 0) >= 300:
            self._d_id.configure(text=f"ID: #{e['id']}")
            self._d_id.pack(pady=(4, 10))

    def _pick(self, e):
        try:
            self.on_pick(e.get('id'))
        finally:
            self.destroy()
