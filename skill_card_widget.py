import os
import sys
import json
import re
import tkinter as tk
import customtkinter as ctk
from PIL import Image

from tooltip_manager import GameTooltip
from picker_dialog import (
    open_grid_picker, set_label_image,
    get_shared_catalog_maps, get_shared_skill_icon,
)
from mewgenics_core import (
    get_canonical_passive_code, BASIC_ATTACK_ABILITIES, BASIC_MOVE_ABILITIES,
    get_passive_upgrade_desc,
)
import class_theme
import attribute_renderer as ar

_BADGE_CACHE = {}
_TAG_LABEL_POOL = 3
_STAT_LABEL_POOL = 4

# 显示字符串形如 "★ [牧师] 不可杀生 (ThouShaltNotKill) - 敌人击倒..."，代码在括号内，后面还有描述。
_SKILL_CODE_RE = re.compile(r'\(([A-Za-z][A-Za-z0-9_]*)\)')


def extract_skill_code(val):
    """从原始 key 或完整显示字符串中取出游戏代码。"""
    if val is None:
        return "None"
    s = str(val).strip()
    if not s or s.startswith("None"):
        return "None"
    m = _SKILL_CODE_RE.search(s)
    return m.group(1) if m else s

class SkillCardWidget(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        catalog_type="ability",
        width=300,
        height=48,
        command=None,
        get_current_class_func=None,
        allowed_keys=None,
        **kwargs
    ):
        super().__init__(parent, fg_color="#182234", border_color="#334155", border_width=1, corner_radius=6, width=width, height=height, **kwargs)
        self.pack_propagate(False)
        
        self.catalog_type = catalog_type
        self.command = command
        self.get_current_class_func = get_current_class_func
        self.allowed_keys = list(allowed_keys) if allowed_keys else None
        self.current_value = "None"
        self.state = "normal"
        self.show_upgraded = False

        # Assets & Catalog
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        if getattr(sys, 'frozen', False):
            self.base_dir = sys._MEIPASS
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.icons_dir = os.path.join(self.assets_dir, "icons", "abilities" if catalog_type == "ability" else "passives")
        self.fallback_path = os.path.join(self.assets_dir, "icons", "fallback.png")
        self.catalog_map, self._catalog_norm = get_shared_catalog_maps(catalog_type)

        # 0. 顶部徽标行：能力类型图标 + 元素标签图标 + 伤害文本
        self.f_badges = ctk.CTkFrame(self, fg_color="transparent", height=16)
        self.f_badges.pack(fill="x", padx=(6, 8), pady=(2, 0))
        self.f_badges.pack_propagate(False)
        self.lbl_type_icon = ctk.CTkLabel(self.f_badges, text="", width=16, height=16)
        self.lbl_type_icon.pack(side="left")
        self.f_tags = ctk.CTkFrame(self.f_badges, fg_color="transparent")
        self.f_tags.pack(side="left", padx=(2, 0))
        self._tag_lbls = [ctk.CTkLabel(self.f_tags, text="", width=16, height=16) for _ in range(_TAG_LABEL_POOL)]
        self._stat_lbls = [ctk.CTkLabel(self.f_tags, text="", width=16, height=16) for _ in range(_STAT_LABEL_POOL)]
        self.lbl_dmg = ctk.CTkLabel(self.f_badges, text="", font=("Arial", 9), text_color="#cbd5e1", anchor="w")
        self.lbl_dmg.pack(side="left", padx=(4, 0))

        # 1. Left Icon
        self.lbl_icon = ctk.CTkLabel(self, text="", width=38, height=38)
        self.lbl_icon.pack(side="left", padx=(6, 8), pady=(0, 4))

        # 2. Middle Text Block
        self.f_text = ctk.CTkFrame(self, fg_color="transparent")
        self.f_text.pack(side="left", fill="both", expand=True, pady=(0, 4))

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
        self.btn_pick.pack(side="right", padx=(4, 8), pady=8)

        self.type_dir = os.path.join(self.assets_dir, "icons", "abilitytype")
        self.tag_dir = os.path.join(self.assets_dir, "icons", "tags")

        # Bind hover and click events
        for w in [self, self.lbl_icon, self.f_text, self.lbl_name, self.lbl_code]:
            w.bind("<Button-1>", lambda e: self.open_picker())
            w.bind("<Enter>", lambda e: self.on_mouse_enter())
            w.bind("<Leave>", lambda e: self.on_mouse_leave())

    def _get_badge(self, kind, name, size=(16, 16)):
        """加载 abilitytype/tags 徽标图像（resolve 路径，缺失返回 None）。"""
        if not name:
            return None
        cache_k = (kind, name, int(size[0]), int(size[1]))
        if cache_k in _BADGE_CACHE:
            return _BADGE_CACHE[cache_k]
        d = self.type_dir if kind == "type" else self.tag_dir
        p = os.path.join(d, f"{name}.png")
        img = None
        if os.path.exists(p):
            try:
                pil_img = Image.open(p).convert("RGBA")
                img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            except Exception:
                img = None
        _BADGE_CACHE[cache_k] = img
        return img

    def _update_badges(self, item):
        """设置类型/元素/七项属性/伤害 徽标（技能卡顶部）。"""
        for lbl in self._tag_lbls:
            lbl.pack_forget()
        for lbl in self._stat_lbls:
            lbl.pack_forget()
        if not item or item.get('key') in (None, 'None'):
            set_label_image(self.lbl_type_icon, None, size=(16, 16))
            self.lbl_dmg.configure(text="")
            return
        # 类型图标
        type_icon = item.get('type_icon')
        set_label_image(self.lbl_type_icon, self._get_badge("type", type_icon) if type_icon else None, size=(16, 16))
        # 元素标签图标
        for i, e in enumerate((item.get('elements') or [])[:_TAG_LABEL_POOL]):
            lbl = self._tag_lbls[i]
            set_label_image(lbl, self._get_badge("tag", str(e).lower()), size=(16, 16))
            lbl.pack(side="left", padx=(0, 1))
        # 七项属性图标
        for i, k in enumerate(ar.extract_core_stat_keys(item)[:_STAT_LABEL_POOL]):
            lbl = self._stat_lbls[i]
            set_label_image(lbl, ar.get_stat_icon(k, size=(16, 16)), size=(16, 16))
            lbl.pack(side="left", padx=(0, 1))
        # 伤害文本
        dmg = item.get('damage')
        dmg_txt = ""
        if dmg:
            dmg_txt = str(dmg)
            if 'bonus_' in dmg_txt:
                dmg_txt = dmg_txt.split('bonus_')[0].rstrip('+')
            if len(dmg_txt) > 10:
                dmg_txt = dmg_txt[:9] + '…'
            dmg_txt = f"⚔ {dmg_txt}"
        self.lbl_dmg.configure(text=dmg_txt)

    def get_icon(self, key, size=(36, 36)):
        return get_shared_skill_icon(self.catalog_type, key, size)

    def get(self):
        return self.current_value

    def set(self, val):
        self.current_value = extract_skill_code(val)
        if self.catalog_type == "passive" and self.current_value != "None":
            self.current_value = get_canonical_passive_code(self.current_value)
        self.update_display()

    def set_upgraded(self, flag):
        flag = bool(flag)
        if flag == getattr(self, 'show_upgraded', False):
            return
        self.show_upgraded = flag
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
            self._update_badges(None)
            set_label_image(self.lbl_icon, None, size=(36, 36))
            self.lbl_name.configure(text="None (未选择)", text_color="#64748b" if self.state == 'disabled' else "#94a3b8")
            self.lbl_code.configure(text="空槽位", text_color="#475569")
            super().configure(border_color="#334155")
            GameTooltip.get_instance().hide()
            self._bind_card_chrome(item_data=None)
        else:
            item = self.catalog_map.get(k) or self._catalog_norm.get(
                ''.join(c for c in k.lower() if c.isalnum()), {}
            )
            cn_name = item.get('name') or k
            desc_up = ''
            if self.show_upgraded and self.catalog_type in ("passive", "disorder"):
                desc_up = (item.get('desc_up') or get_passive_upgrade_desc(k) or '').strip()
                if desc_up and not cn_name.endswith('+'):
                    cn_name = cn_name + '+'

            # 技能卡按所属职业主题色显示（名称 + 边框）
            cls = item.get('class') if self.catalog_type in ("ability", "passive") else None
            if cls not in class_theme.CLASS_PALETTE:
                cls = None
            cls_col = class_theme.ui_color(cls) if cls else None
            if self.state == 'disabled':
                name_col, code_col, border_col = "#64748b", "#475569", "#1e293b"
            elif cls_col:
                name_col, code_col, border_col = cls_col, "#94a3b8", cls_col
            else:
                name_col, code_col, border_col = "#f8fafc", "#94a3b8", "#334155"

            self.lbl_name.configure(text=cn_name, text_color=name_col)
            self.lbl_code.configure(text=k, text_color=code_col)
            super().configure(border_color=border_col)
            self._update_badges(item or {'key': k})

            icon = self.get_icon(k, size=(36, 36))
            set_label_image(self.lbl_icon, icon, size=(36, 36))
            item_data = dict(item) if item else {'key': k, 'name': cn_name, 'desc': ''}
            if desc_up:
                item_data['name'] = cn_name
                item_data['desc'] = desc_up
            self._bind_card_chrome(item_data=item_data)

    def _hover_targets(self):
        return [self, self.lbl_icon, self.f_text, self.lbl_name, self.lbl_code]

    def _bind_card_chrome(self, item_data=None):
        """只更新悬浮详情数据，不再重复 bind（CTk add=True 会叠加上次技能）。"""
        tip = GameTooltip.get_instance()
        for w in self._hover_targets():
            if item_data:
                tip.bind_widget(w, item_data, get_icon_func=self.get_icon)
            else:
                tip.clear_widget(w)

    def _current_border_color(self):
        if self.state == 'disabled':
            return "#1e293b"
        if not self.current_value or self.current_value == "None":
            return "#334155"
        item = self.catalog_map.get(self.current_value) or {}
        cls = item.get('class') if self.catalog_type in ("ability", "passive") else None
        if cls not in class_theme.CLASS_PALETTE:
            cls = None
        return class_theme.ui_color(cls) if cls else "#334155"

    def on_mouse_enter(self):
        if self.state == 'normal':
            self.configure(border_color="#6366f1")

    def on_mouse_leave(self):
        if self.state == 'normal':
            super().configure(border_color=self._current_border_color())
        GameTooltip.get_instance().hide()

    def open_picker(self):
        if self.state == 'disabled':
            return
        parent_win = self.winfo_toplevel()
        cat_class = None
        if self.get_current_class_func:
            cat_class = self.get_current_class_func()

        if self.catalog_type == "ability":
            allow = set(self.allowed_keys or [])
            if allow and allow <= set(BASIC_ATTACK_ABILITIES):
                title = "选择普通攻击"
            elif allow and allow <= set(BASIC_MOVE_ABILITIES):
                title = "选择移动方式"
            else:
                title = "选择战斗法术"
        elif self.catalog_type == "disorder":
            title = "选择疾病缺陷 (Disorder)"
        else:
            title = "选择被动特质"
        open_grid_picker(
            parent_win,
            title=title,
            catalog_type=self.catalog_type,
            current_value=self.current_value,
            initial_category=cat_class,
            on_select_callback=self.on_picker_selected,
            allowed_keys=self.allowed_keys,
        )

    def on_picker_selected(self, chosen_val):
        self.set(chosen_val)
        if self.command:
            self.command(self.current_value)
