import os
import sys
import json
import math
import tkinter as tk
import customtkinter as ctk
from PIL import Image

from tooltip_manager import GameTooltip
import class_theme
import attribute_renderer as ar
from mewgenics_core import (
    GAME_CODE_ALIAS, get_canonical_passive_code, dedupe_catalog_items,
    BASIC_ATTACK_ABILITIES, BASIC_MOVE_ABILITIES, get_game_data_cache,
)

_BASIC_ACTION_KEYS = set(BASIC_ATTACK_ABILITIES) | set(BASIC_MOVE_ABILITIES)


def _is_basic_action_key(key):
    if not key or key == 'None':
        return False
    return key.startswith('Basic') or key in _BASIC_ACTION_KEYS

RARITY_COLORS = {
    'common': '#94a3b8',
    'uncommon': '#22c55e',
    'rare': '#38bdf8',
    'very_rare': '#a855f7',
    'epic': '#a855f7',
    'quest': '#f59e0b',
    'sidequest': '#f59e0b',
}

# 稀有度对应的卡片深色背景（低亮度色调，暗色 UI 下作为底色）
RARITY_BG = {
    'common': '#1c2531',
    'uncommon': '#12291c',
    'rare': '#0f2739',
    'very_rare': '#241634',
    'epic': '#241634',
    'quest': '#2d2416',
    'sidequest': '#2d2416',
    'cursed': '#2a1424',
}

_rarity_shape_cache = {}

def load_rarity_shape(rarity):
    """加载 wiki 稀有度形状贴图 (wiki_data/images/rarity/<r>.png, 119x119 半透明)。

    游戏内道具图标即绘制在这些形状底图上（灰圆=uncommon / 黄三角=rare / 红菱形=very_rare）。
    找不到返回 None。
    """
    if not rarity:
        return None
    if rarity in _rarity_shape_cache:
        return _rarity_shape_cache[rarity]
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    shape = None
    for base in [base_dir, os.getcwd()]:
        p = os.path.join(base, 'wiki_data', 'images', 'rarity', f'{rarity}.png')
        if os.path.exists(p):
            try:
                shape = Image.open(p).convert('RGBA')
            except Exception:
                shape = None
            break
    _rarity_shape_cache[rarity] = shape
    return shape


def rarity_shape_name(rarity, cursed=False):
    """选稀有度形状底图文件名（含诅咒组合）。

    映射（来自 mewcodex wiki CSS）：
      cursed            -> cursed.png
      quest+cursed      -> questcursed.png
      sidequest+cursed  -> sidequestcursed.png
      quest / sidequest -> quest.png / sidequest.png
      其它稀有度        -> <rarity>.png
    空稀有度且非诅咒    -> None（无形状）
    """
    r = (rarity or '').lower()
    if cursed:
        if r == 'quest':
            return 'questcursed'
        if r == 'sidequest':
            return 'sidequestcursed'
        return 'cursed'
    return r or None


def compose_item_icon(icon_pil, rarity, cursed=False, size=None):
    """把道具图标合成到稀有度形状底图上（还原游戏内渲染，含诅咒组合形状）。"""
    shape = load_rarity_shape(rarity_shape_name(rarity, cursed))
    if shape is None or icon_pil is None:
        if size and icon_pil is not None:
            icon_pil = icon_pil.resize(size, Image.Resampling.LANCZOS)
        return icon_pil
    canvas = shape.copy()
    inner = (int(shape.width * 0.52), int(shape.height * 0.52))
    icon = icon_pil.resize(inner, Image.Resampling.LANCZOS)
    canvas.alpha_composite(icon, ((shape.width - inner[0]) // 2, (shape.height - inner[1]) // 2))
    if size:
        canvas = canvas.resize(size, Image.Resampling.LANCZOS)
    return canvas


_part_icon_cache = {}
_part_ctk_cache = {}

def load_part_icon(kind, size=None):
    """加载 wiki 物品部位/槽位图标 (wiki_data/images/parts/<kind>.png, 38x32)。

    返回 PIL RGBA 或 None。
    """
    if not kind:
        return None
    key = (kind, size)
    if key in _part_icon_cache:
        return _part_icon_cache[key]
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    icon = None
    for base in [base_dir, os.getcwd()]:
        p = os.path.join(base, 'wiki_data', 'images', 'parts', f'{kind}.png')
        if os.path.exists(p):
            try:
                icon = Image.open(p).convert('RGBA')
                if size:
                    icon = icon.resize(size, Image.Resampling.LANCZOS)
            except Exception:
                icon = None
            break
    _part_icon_cache[key] = icon
    return icon


_class_icon_cache = {}

def load_class_icon(cls_name, size=(20, 20)):
    """加载 assets/icons/classes/<cls_name>.png 为 CTkImage 图标。"""
    if not cls_name or cls_name == '全部':
        return None
    key = (cls_name, size)
    if key in _class_icon_cache:
        return _class_icon_cache[key]
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    icon = None
    for base in [base_dir, os.getcwd()]:
        p = os.path.join(base, 'assets', 'icons', 'classes', f'{cls_name}.png')
        if os.path.exists(p):
            try:
                pil_img = Image.open(p).convert('RGBA')
                icon = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            except Exception:
                icon = None
            break
    _class_icon_cache[key] = icon
    return icon


MAJOR_CHECKMARK_ZONES = [
    'caves', 'boneyard', 'meatworld', 'moon', 'core',
    'dimensionx', 'jurassic', 'theend', 'endoftime'
]

def get_class_cleared_count(class_progress, cls):
    """根据 npc_progress 中的 (cls, zone) 记录计算 9 大章节已通关总数。"""
    if not class_progress:
        return None
    cleared = 0
    for zone in MAJOR_CHECKMARK_ZONES:
        r = class_progress.get((cls, zone))
        if r is not None:
            cleared += 1
    return cleared


_icon_dir_norm_cache = {}
_alias_norm_cache = {}
_blank_ctk_images = {}
_CATALOG_CACHE = {}
_CATALOG_MAPS = {}
_PICKER_ICON_CACHE = {}
_TYPE_ICON_CACHE = {}
_TAG_ICON_CACHE = {}
_PICKER_ELEM_POOL = 3
_PICKER_STAT_POOL = 4
_PICKER_STAT_PREVIEW_POOL = 7
_OPEN_PICKER = None
_CATALOG_FN = {
    'disorder': 'disorders_catalog.json',
    'ability': 'abilities_catalog.json',
    'item': 'items_catalog.json',
    'furniture': 'furniture_catalog.json',
    'passive': 'passives_catalog.json',
}


def runtime_base_dir():
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.dirname(os.path.abspath(__file__))


_PASSIVE_CLASS_BY_KEY = None
_PASSIVE_GON_CLASS = {
    'colorless_passives.gon': 'Colorless',
    'fighter_passives.gon': 'Fighter',
    'mage_passives.gon': 'Mage',
    'hunter_passives.gon': 'Hunter',
    'tank_passives.gon': 'Tank',
    'medic_passives.gon': 'Medic',
    'thief_passives.gon': 'Thief',
    'necromancer_passives.gon': 'Necromancer',
    'butcher_passives.gon': 'Butcher',
    'druid_passives.gon': 'Druid',
    'monk_passives.gon': 'Monk',
    'psychic_passives.gon': 'Psychic',
    'tinkerer_passives.gon': 'Tinkerer',
    'jester_passives.gon': 'Jester',
    'disorders.gon': 'Disorder',
}


def _class_from_passive_gon(src, pools, declared):
    """用游戏 data2/passives/*.gon（SWF 解包同源）判断职业。"""
    valid = set(class_theme.CLASS_PALETTE)
    fn = (src or '').replace('\\', '/').split('/')[-1].lower()
    if fn in _PASSIVE_GON_CLASS:
        return _PASSIVE_GON_CLASS[fn]
    for cls in valid:
        if fn.startswith(cls.lower() + '_'):
            return cls
    if declared == 'Disorder' or declared in valid:
        return declared
    for p in pools or []:
        head = str(p).split('.')[0]
        if head in valid or head == 'Disorder':
            return head
    return None


def _passive_class_lookup():
    """passive_code -> 职业。来源：passives_combined（data2/passives/*.gon + SWF 帧表），再补 class_passives。"""
    global _PASSIVE_CLASS_BY_KEY
    if _PASSIVE_CLASS_BY_KEY is not None:
        return _PASSIVE_CLASS_BY_KEY
    out = {}
    valid = set(class_theme.CLASS_PALETTE)
    comb_p = os.path.join(runtime_base_dir(), 'wiki_data', 'passives_combined.json')
    if os.path.exists(comb_p):
        try:
            with open(comb_p, encoding='utf-8') as f:
                data = json.load(f)
            for row in data.get('passives') or []:
                code = (row.get('passive_code') or row.get('passive_name') or '').strip()
                if not code:
                    continue
                k = get_canonical_passive_code(code)
                cls = _class_from_passive_gon(
                    row.get('source_file'),
                    row.get('passive_pools'),
                    (row.get('passive_class') or '').strip(),
                )
                if cls:
                    out[k] = cls
                    if code != k:
                        out[code] = cls
        except Exception:
            pass
    try:
        for cls, lst in (get_game_data_cache().get('class_passives') or {}).items():
            if cls not in valid:
                continue
            for p in lst or []:
                k = get_canonical_passive_code(p.get('key') or '')
                if k and k != 'None' and k not in out:
                    out[k] = cls
    except Exception:
        pass
    _PASSIVE_CLASS_BY_KEY = out
    return out


def _attach_passive_classes(items):
    """给被动目录补 class，并去掉疾病（疾病走独立选择器）。"""
    lookup = _passive_class_lookup()
    valid = set(class_theme.CLASS_PALETTE)
    out = []
    for it in items:
        k = it.get('key') or ''
        if str(k).startswith('STARTER_PLACEHOLDER'):
            continue
        mapped = lookup.get(k) or lookup.get(get_canonical_passive_code(k))
        cls = mapped or it.get('class')
        if cls == 'Disorder':
            continue
        if cls not in valid:
            cls = 'Colorless'
        it['class'] = cls
        out.append(it)
    return out


def get_shared_catalog(catalog_type):
    """Process-wide catalog list. Callers must not mutate the returned list."""
    assets_dir = os.path.join(runtime_base_dir(), 'assets')
    cache_k = (catalog_type, assets_dir)
    cached = _CATALOG_CACHE.get(cache_k)
    if cached is not None:
        return cached
    cat_fn = _CATALOG_FN.get(catalog_type, 'passives_catalog.json')
    cat_path = os.path.join(assets_dir, cat_fn)
    items = []
    if os.path.exists(cat_path):
        try:
            with open(cat_path, 'r', encoding='utf-8') as f:
                items = json.load(f)
            if catalog_type == 'passive':
                items = _attach_passive_classes(
                    dedupe_catalog_items(items, canonicalize=get_canonical_passive_code)
                )
            else:
                items = dedupe_catalog_items(items)
        except Exception as e:
            print(f"Error loading catalog {cat_path}: {e}")
            items = []
    _CATALOG_CACHE[cache_k] = items
    return items


def get_shared_catalog_maps(catalog_type):
    """Shared {key: item} plus normalized-key map."""
    hit = _CATALOG_MAPS.get(catalog_type)
    if hit is not None:
        return hit
    catalog_map = {}
    catalog_norm = {}
    for item in get_shared_catalog(catalog_type):
        k = item.get('key')
        if not k:
            continue
        catalog_map[k] = item
        nk = ''.join(c for c in k.lower() if c.isalnum())
        prev = catalog_norm.get(nk)
        if prev is None or (item.get('has_icon') and not prev.get('has_icon')):
            catalog_norm[nk] = item
    _CATALOG_MAPS[catalog_type] = (catalog_map, catalog_norm)
    return catalog_map, catalog_norm


def get_shared_skill_icon(catalog_type, key, size=(36, 36)):
    """Shared CTkImage for ability / passive / disorder keys."""
    if not key or key == 'None':
        return None
    cache_k = (catalog_type, key, int(size[0]), int(size[1]))
    if cache_k in _PICKER_ICON_CACHE:
        return _PICKER_ICON_CACHE[cache_k]
    assets = os.path.join(runtime_base_dir(), 'assets')
    fallback = os.path.join(assets, 'icons', 'fallback.png')
    extra = [(get_shared_catalog_maps(catalog_type)[0].get(key) or {}).get('icon_key')]
    dirs = [
        os.path.join(assets, 'icons', 'abilities'),
        os.path.join(assets, 'icons', 'passives'),
    ]
    if catalog_type != 'ability':
        dirs.reverse()
    png_path = None
    for cand in _icon_candidates(key, extra):
        nk = _norm_key(cand)
        for d in dirs:
            png_path = _icon_dir_index(d).get(nk)
            if png_path:
                break
        if png_path:
            break
    if not png_path:
        png_path = fallback if os.path.exists(fallback) else None
    img = None
    if png_path and os.path.exists(png_path):
        try:
            pil_img = Image.open(png_path).convert('RGBA')
            img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        except Exception:
            img = None
    _PICKER_ICON_CACHE[cache_k] = img
    return img


def get_part_ctk_icon(kind, size=(30, 26)):
    if not kind:
        return None
    cache_k = (kind, int(size[0]), int(size[1]))
    hit = _part_ctk_cache.get(cache_k)
    if cache_k in _part_ctk_cache:
        return hit
    pil = load_part_icon(kind)
    img = None
    if pil is not None:
        img = ctk.CTkImage(light_image=pil, dark_image=pil, size=size)
    _part_ctk_cache[cache_k] = img
    return img


def blank_ctk_image(size=(36, 36)):
    """Transparent CTkImage used to clear labels (configure(image=None) is a no-op)."""
    key = (int(size[0]), int(size[1]))
    img = _blank_ctk_images.get(key)
    if img is None:
        pil = Image.new("RGBA", key, (0, 0, 0, 0))
        img = ctk.CTkImage(light_image=pil, dark_image=pil, size=key)
        _blank_ctk_images[key] = img
    return img


def set_label_image(label, img, size=(36, 36)):
    """Assign or clear a CTkLabel image. Never pass None — CTk keeps the last PhotoImage."""
    if img is None:
        img = blank_ctk_image(size)
    label.configure(image=img)
    return img

def _norm_key(s):
    return ''.join(c for c in s.lower() if c.isalnum())

def _alias_by_norm(alias):
    """FIGHTERSOUL 与 FighterSoul 规范化后相同，都能映射到 FightersSoul。"""
    cache_id = id(alias)
    m = _alias_norm_cache.get(cache_id)
    if m is None:
        m = {}
        for ak, av in alias.items():
            m[_norm_key(ak)] = av
            m.setdefault(_norm_key(av), av)
        _alias_norm_cache[cache_id] = m
    return m


_ICON_SUFFIXES = (
    '2', '3', '_Impl', '_Auto', '_chained', '_Enemy', '_sub',
    '_Fighter', '_Hunter', '_Thief', '_1DMG', '_Familiar', '_Manaless',
    '_BasicMove', '_WideLoad', '_EldritchVisage',
)
_ICON_PREFIXES = ('SM_', 'cm_', 'wp_', 'tk_', 'head_')
_ICON_CLASS_PREFIXES = ('DC', 'NC', 'TC', 'MC')
_ICON_ALIAS = {
    'Taunt': 'FighterTaunt',
    'Purge': 'ButcherPurge',
    'TeslaBolt': 'TeslaCoil',
    'BowlDash': 'BowlOver',
    'MedicObey': 'ThouShaltObey',
    'ToadJump_BasicMove': 'SummonToad',
    'MechExplode': 'MechSuit',
    'DecoySwap': 'SpawnDecoy',
    'DecoyExplode': 'SpawnDecoy',
    'RandomSoulLink': 'SoulLink',
    'RandomDualSoulLink': 'SoulLink',
    'BonusToss': 'Toss',
    'NubbyToss': 'Toss',
    'BasicTwoHitMelee': 'BasicMelee',
    'Double': 'DoubleThrow',
    'DoubleLoot': 'DoubleThrow',
    'ReflexPunchJab': 'ReflexPunch',
    'FollowUpDash': 'FollowUp',
    'RapidFlowSpin': 'RapidFlow',
    'Indigestion_Fart': 'Indigestion',
}
_GENERIC_ICON_STEMS = {
    'dash', 'spin', 'step', 'heal', 'armor', 'melee', 'swap', 'fire', 'ice',
    'body', 'back', 'form', 'jump', 'shot', 'punch', 'move', 'basic', 'holy',
    'auto', 'sub', 'impl', 'test', 'part', 'two', 'cat', 'bot', 'load', 'wide',
    'air', 'water', 'plants', 'guard', 'loot', 'obey', 'fart', 'bolt', 'coil',
}


def _camel_parts(name):
    parts, buf = [], []
    for ch in str(name).replace('_', ' '):
        if ch == ' ':
            if buf:
                parts.append(''.join(buf))
                buf = []
            continue
        if buf and ch.isupper() and not buf[-1].isupper():
            parts.append(''.join(buf))
            buf = [ch]
        else:
            buf.append(ch)
    if buf:
        parts.append(''.join(buf))
    return parts


def _icon_candidates(key, extra_keys=None, alias=None):
    seeds = []
    for k in (key, *(extra_keys or ())):
        if k and k not in ('None',) and k not in seeds:
            seeds.append(k)
    alias = GAME_CODE_ALIAS if alias is None else alias
    out = []

    def _add(name):
        if name and name not in ('None',) and name not in out:
            out.append(name)

    for seed in list(seeds):
        _add(seed)
        mapped = _ICON_ALIAS.get(seed)
        if mapped:
            _add(mapped)
        if alias:
            _add(alias.get(seed) or _alias_by_norm(alias).get(_norm_key(seed)))
        stem = seed
        for _ in range(6):
            trimmed = False
            for suf in _ICON_SUFFIXES:
                if stem.endswith(suf) and len(stem) > len(suf) + 2:
                    stem = stem[:-len(suf)]
                    _add(stem)
                    trimmed = True
                    break
            if trimmed:
                continue
            for pref in _ICON_PREFIXES:
                if stem.startswith(pref) and len(stem) > len(pref) + 2:
                    stem = stem[len(pref):]
                    _add(stem)
                    trimmed = True
                    break
            if trimmed:
                continue
            for pref in _ICON_CLASS_PREFIXES:
                if stem.startswith(pref) and len(stem) > len(pref) + 2 and stem[len(pref)].isupper():
                    stem = stem[len(pref):]
                    _add(stem)
                    trimmed = True
                    break
            if not trimmed:
                break
        parts = _camel_parts(seed)
        for i in range(len(parts) - 1, 0, -1):
            name = ''.join(parts[:i])
            if _usable_icon_stem(name):
                _add(name)
        if len(parts) >= 2 and _usable_icon_stem(''.join(parts[-2:])):
            _add(''.join(parts[-2:]))
        if parts and _usable_icon_stem(parts[-1]):
            _add(parts[-1])
        mapped = _ICON_ALIAS.get(stem)
        if mapped:
            _add(mapped)
    return out


def _usable_icon_stem(name):
    if not name or _norm_key(name) in _GENERIC_ICON_STEMS:
        return False
    return len(name) >= 6


def _icon_dir_index(icons_dir):
    di = _icon_dir_norm_cache.get(icons_dir)
    if di is None:
        di = {}
        if os.path.isdir(icons_dir):
            for fn in os.listdir(icons_dir):
                if fn.endswith('.png'):
                    di.setdefault(_norm_key(os.path.splitext(fn)[0]), os.path.join(icons_dir, fn))
        _icon_dir_norm_cache[icons_dir] = di
    return di


def resolve_icon_path(icons_dir, key, fallback_path=None, alias=None, extra_keys=None):
    """按游戏命名解析图标：精确 key → ability_icon → 变体去后缀/前缀 → 别名 → 规范化名。"""
    if not key or key == 'None':
        return fallback_path if (fallback_path and os.path.exists(fallback_path)) else None
    di = _icon_dir_index(icons_dir)
    for cand in _icon_candidates(key, extra_keys, alias):
        hit = di.get(_norm_key(cand))
        if hit:
            return hit
    return fallback_path if (fallback_path and os.path.exists(fallback_path)) else None


def focus_existing_picker():
    """If a picker is already open, raise it instead of stacking another modal."""
    global _OPEN_PICKER
    dlg = _OPEN_PICKER
    if dlg is None:
        return False
    try:
        if dlg.winfo_exists():
            dlg.lift()
            dlg.focus_force()
            return True
    except Exception:
        pass
    _OPEN_PICKER = None
    return False


def open_grid_picker(parent, **kwargs):
    GameTooltip.get_instance().hide()
    if focus_existing_picker():
        return _OPEN_PICKER
    return UniversalGridPickerDialog(parent, **kwargs)


class UniversalGridPickerDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        title="选择项",
        catalog_type="ability", # 'ability', 'passive', 'disorder', 'item', 'furniture'
        current_value="None",
        initial_category=None,
        on_select_callback=None,
        allowed_keys=None,
        class_progress=None
    ):
        global _OPEN_PICKER
        GameTooltip.get_instance().hide()
        super().__init__(parent)
        self.title(title)
        self.geometry("1020x760")
        self.minsize(900, 650)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        try:
            self.grab_set()
        except Exception:
            pass
        _OPEN_PICKER = self

        self.catalog_type = catalog_type
        self.current_value = current_value or "None"
        self.selected_value = self.current_value
        self.initial_category = initial_category
        self.on_select_callback = on_select_callback
        self.allowed_keys = set(allowed_keys) if allowed_keys else None

        # 尝试自动获取 class_progress
        if class_progress is None:
            top = parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent
            if hasattr(top, 'save_mgr') and top.save_mgr:
                class_progress = getattr(top.save_mgr, 'class_zone_records', None)
        self.class_progress = class_progress

        # 8 columns x 4 rows = 32 per page
        self.COLS = 8
        self.ROWS = 4
        self.PAGE_SIZE = self.COLS * self.ROWS
        self.current_page = 1
        self.current_rarity = 'all'

        self.fallback_icon = None

        # Data paths
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        if getattr(sys, 'frozen', False):
            self.base_dir = sys._MEIPASS

        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.icons_dir = os.path.join(self.assets_dir, "icons", "abilities" if self.catalog_type == "ability" else "passives")
        self.fallback_path = os.path.join(self.assets_dir, "icons", "fallback.png")
        self.type_dir = os.path.join(self.assets_dir, "icons", "abilitytype")
        self.tag_dir = os.path.join(self.assets_dir, "icons", "tags")

        # Load catalog
        self.full_catalog = self.load_catalog()
        if self.allowed_keys is not None:
            # 只显示允许的技能（如普攻栏仅攻击技能、移动栏仅移动技能）
            self.full_catalog = [it for it in self.full_catalog if it.get('key') in self.allowed_keys]
        self.catalog_map = {item['key']: item for item in self.full_catalog}
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

    def _type_path(self, type_icon):
        if not type_icon:
            return None
        p = os.path.join(self.type_dir, f"{type_icon}.png")
        return p if os.path.exists(p) else None

    def load_catalog(self):
        return list(get_shared_catalog(self.catalog_type))

    def _type_icon(self, type_icon, size=(30, 26)):
        if not type_icon:
            return None
        cache_k = (type_icon, size)
        if cache_k in _TYPE_ICON_CACHE:
            return _TYPE_ICON_CACHE[cache_k]
        p = self._type_path(type_icon)
        img = None
        if p:
            try:
                pil = Image.open(p).convert("RGBA")
                img = ctk.CTkImage(light_image=pil, dark_image=pil, size=size)
            except Exception:
                img = None
        _TYPE_ICON_CACHE[cache_k] = img
        return img

    def _tag_icon(self, name, size=(16, 16)):
        if not name:
            return None
        name = str(name).lower()
        cache_k = (name, int(size[0]), int(size[1]))
        if cache_k in _TAG_ICON_CACHE:
            return _TAG_ICON_CACHE[cache_k]
        p = os.path.join(self.tag_dir, f"{name}.png")
        img = None
        if os.path.exists(p):
            try:
                pil = Image.open(p).convert("RGBA")
                img = ctk.CTkImage(light_image=pil, dark_image=pil, size=size)
            except Exception:
                img = None
        _TAG_ICON_CACHE[cache_k] = img
        return img

    def _set_elem_icons(self, labels, elements, size=(16, 16)):
        elems = [str(e).lower() for e in (elements or []) if e][:len(labels)]
        for i, lbl in enumerate(labels):
            if i < len(elems):
                set_label_image(lbl, self._tag_icon(elems[i], size=size), size=size)
                if not lbl.winfo_ismapped():
                    lbl.place(x=3 + i * (size[0] + 1), y=3)
            else:
                set_label_image(lbl, None, size=size)
                lbl.place_forget()

    def _set_stat_icons(self, labels, stats, size=(14, 14), y=20):
        keys = [k for k in (stats or []) if k][:len(labels)]
        for i, lbl in enumerate(labels):
            if i < len(keys):
                set_label_image(lbl, ar.get_stat_icon(keys[i], size=size), size=size)
                if not lbl.winfo_ismapped():
                    lbl.place(x=3 + i * (size[0] + 1), y=y)
            else:
                set_label_image(lbl, None, size=size)
                lbl.place_forget()

    def _pack_preview_icons(self, labels, images, size=(16, 16)):
        for i, lbl in enumerate(labels):
            if i < len(images) and images[i]:
                set_label_image(lbl, images[i], size=size)
                if not lbl.winfo_ismapped():
                    lbl.pack(side="left", padx=(0, 1))
            else:
                set_label_image(lbl, None, size=size)
                lbl.pack_forget()

    def get_icon(self, key, size=(48, 48)):
        if not key or key == 'None':
            return None
        if self.catalog_type not in ("item", "furniture"):
            return get_shared_skill_icon(self.catalog_type, key, size)
        cache_k = (self.catalog_type, key, size[0], size[1])
        if cache_k in _PICKER_ICON_CACHE:
            return _PICKER_ICON_CACHE[cache_k]

        item = self.catalog_map.get(key, {})
        png_path = None
        if self.catalog_type in ("item", "furniture"):
            icon_rel = item.get('icon_rel', '')
            if icon_rel:
                for base in [self.base_dir, os.path.dirname(os.path.abspath(__file__)), os.getcwd()]:
                    p = os.path.join(base, "wiki_data", icon_rel)
                    if os.path.exists(p):
                        png_path = p
                        break
        else:
            p = resolve_icon_path(self.icons_dir, key, self.fallback_path)
            if p:
                png_path = p

        if not png_path or not os.path.exists(png_path):
            png_path = self.fallback_path

        if png_path and os.path.exists(png_path):
            try:
                pil_img = Image.open(png_path).convert("RGBA")
                if self.catalog_type == "item":
                    # 道具：合成稀有度形状底图（还原游戏内渲染，含诅咒组合形状）
                    pil_img = compose_item_icon(pil_img, item.get('rarity', ''), bool(item.get('cursed', False)), size=size) or pil_img
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
                _PICKER_ICON_CACHE[cache_k] = ctk_img
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

        search_titles = {
            'ability': "🔍 搜索法术:",
            'passive': "🔍 搜索被动:",
            'disorder': "🔍 搜索疾病:",
            'item': "🔍 搜索道具:",
            'furniture': "🔍 搜索家具:",
        }
        ctk.CTkLabel(f_search_row, text=search_titles.get(self.catalog_type, "🔍 搜索:"),
                     font=("Arial", 13, "bold"), text_color="#38bdf8").pack(side="left", padx=(0, 8))
        self.entry_search = ctk.CTkEntry(f_search_row, width=280, placeholder_text="输入中文名称、英文代码或属性效果...")
        self.entry_search.pack(side="left", padx=4)
        self.entry_search.bind("<KeyRelease>", self.on_search_changed)
        self.entry_search.bind("<Return>", lambda e: self.apply_filter())

        btn_clear_search = ctk.CTkButton(f_search_row, text="✕", width=28, height=28, fg_color="#334155", hover_color="#475569", command=self.clear_search)
        btn_clear_search.pack(side="left", padx=(2, 10))

        # Secondary Rarity filter for items
        if self.catalog_type == "item":
            ctk.CTkLabel(f_search_row, text="品质:", font=("Arial", 12, "bold"), text_color="#a855f7").pack(side="left", padx=(6, 4))
            self.rarity_opts = [("全部", "all"), ("⚪普通", "common"), ("🟢罕见", "uncommon"), ("🔵稀有", "rare"), ("🟣史诗", "epic"), ("📜任务", "quest")]
            self.seg_rarity = ctk.CTkSegmentedButton(
                f_search_row,
                values=[lbl for lbl, _ in self.rarity_opts],
                command=self.on_rarity_changed,
                height=26,
                font=("Arial", 11)
            )
            self.seg_rarity.set("全部")
            self.seg_rarity.pack(side="left", padx=4)

        self.lbl_count = ctk.CTkLabel(f_search_row, text="", font=("Arial", 12), text_color="#94a3b8")
        self.lbl_count.pack(side="right", padx=10)

        # Row 2: Category Tabs (Pill Buttons) - 无需横向滚动条的紧凑网格布局
        f_cat_container = ctk.CTkFrame(self.f_top, fg_color="transparent")
        f_cat_container.pack(fill="x", padx=12, pady=(0, 8))

        self.cat_buttons = {}
        self.current_category = '全部'

        if self.catalog_type in ("ability", "passive"):
            # 4 列 × 4 行九宫格形态，严格按通关进度顺序排列
            # 14 个职业 + 全部 = 15 个按钮
            class_matrix = [
                ['全部', 'Colorless', 'Fighter', 'Mage'],
                ['Hunter', 'Tank', 'Medic', 'Thief'],
                ['Necromancer', 'Butcher', 'Druid', 'Monk'],
                ['Psychic', 'Tinkerer', 'Jester', None]
            ]
            self.categories = [c for row in class_matrix for c in row if c is not None]
            cat_cn = {
                '全部': '🌟 全部技能',
                'Colorless': '通用 Colorless',
                'Fighter': '战士 Fighter',
                'Mage': '法师 Mage',
                'Hunter': '猎人 Hunter',
                'Tank': '肉盾 Tank',
                'Medic': '医者 Medic',
                'Thief': '盗贼 Thief',
                'Necromancer': '死灵 Necro',
                'Butcher': '屠夫 Butcher',
                'Druid': '德鲁伊 Druid',
                'Monk': '武僧 Monk',
                'Psychic': '灵能 Psychic',
                'Tinkerer': '工匠 Tinkerer',
                'Jester': '小丑 Jester'
            }
            for col_i in range(4):
                f_cat_container.columnconfigure(col_i, weight=1)

            for r_i, row in enumerate(class_matrix):
                for c_i, cat in enumerate(row):
                    if cat is None:
                        continue
                    label = cat_cn.get(cat, cat)
                    txt_col = class_theme.ui_color(cat) if cat in class_theme.CLASS_PALETTE else None
                    ic = load_class_icon(cat, size=(20, 20))

                    # 职业通关进度角标
                    cleared_n = get_class_cleared_count(self.class_progress, cat)
                    if cleared_n is not None and cat != '全部':
                        if cleared_n == 9:
                            prog_txt = " 🏆9/9"
                        elif cleared_n > 0:
                            prog_txt = f" {cleared_n}/9"
                        else:
                            prog_txt = " 0/9"
                    else:
                        prog_txt = ""

                    btn = ctk.CTkButton(
                        f_cat_container,
                        text=f"{label}{prog_txt}",
                        image=ic,
                        compound="left",
                        height=28,
                        font=("Arial", 11, "bold"),
                        fg_color="#1e293b",
                        hover_color="#334155",
                        border_color="#334155",
                        border_width=1,
                        text_color=txt_col or "#f8fafc",
                        corner_radius=6,
                        command=lambda c=cat: self.select_category(c)
                    )
                    btn.grid(row=r_i, column=c_i, padx=3, pady=2, sticky="ew")
                    self.cat_buttons[cat] = btn

        elif self.catalog_type == "item":
            # 4 列 × 2 行紧凑网格（含新增的诅咒道具 Cursed 分类）
            item_matrix = [
                ['全部', 'weapon', 'head', 'face'],
                ['neck', 'trinket', 'modifier', 'cursed']
            ]
            self.categories = [c for row in item_matrix for c in row if c is not None]
            cat_cn = {
                '全部': '🌟 全部部位',
                'weapon': '⚔️ 武器 Weapon',
                'head': '🧢 头部 Head',
                'face': '👓 面部 Face',
                'neck': '🧣 颈部 Neck',
                'trinket': '💍 饰品 Trinket',
                'modifier': '🧪 强化/消耗 Modifier',
                'cursed': '☠️ 诅咒道具 Cursed'
            }
            for col_i in range(4):
                f_cat_container.columnconfigure(col_i, weight=1)

            for r_i, row in enumerate(item_matrix):
                for c_i, cat in enumerate(row):
                    label = cat_cn.get(cat, cat)
                    btn = ctk.CTkButton(
                        f_cat_container,
                        text=label,
                        height=28,
                        font=("Arial", 11, "bold"),
                        fg_color="#1e293b",
                        hover_color="#334155",
                        border_color="#334155",
                        border_width=1,
                        text_color="#f8fafc" if cat != 'cursed' else "#f43f5e",
                        corner_radius=6,
                        command=lambda c=cat: self.select_category(c)
                    )
                    btn.grid(row=r_i, column=c_i, padx=3, pady=2, sticky="ew")
                    self.cat_buttons[cat] = btn

        elif self.catalog_type == "furniture":
            # 7 列 × 2 行紧凑平铺（全部 + 12 风格套装）
            furn_matrix = [
                ['全部', 'cute', 'cat', 'retro', 'gothic', 'crystal', 'robo'],
                ['mushroom', 'monster', 'angelic', 'elegant', 'modern', 'junk', None]
            ]
            self.categories = [c for row in furn_matrix for c in row if c is not None]
            cat_cn = {
                '全部': '🌟 全部风格',
                'cute': '🎀 可爱 Cute',
                'cat': '🐱 喵星 Cat',
                'retro': '📼 复古 Retro',
                'gothic': '🏰 哥特 Gothic',
                'crystal': '💎 水晶 Crystal',
                'robo': '🤖 机械 Robo',
                'mushroom': '🍄 蘑菇 Mushroom',
                'monster': '🦴 惊悚 Monster',
                'angelic': '🪽 天使 Angelic',
                'elegant': '👑 优雅 Elegant',
                'modern': '🪵 现代 Modern',
                'junk': '📦 废品 Junk'
            }
            for col_i in range(7):
                f_cat_container.columnconfigure(col_i, weight=1)

            for r_i, row in enumerate(furn_matrix):
                for c_i, cat in enumerate(row):
                    if cat is None:
                        continue
                    label = cat_cn.get(cat, cat)
                    btn = ctk.CTkButton(
                        f_cat_container,
                        text=label,
                        height=28,
                        font=("Arial", 11, "bold"),
                        fg_color="#1e293b",
                        hover_color="#334155",
                        border_color="#334155",
                        border_width=1,
                        text_color="#f8fafc",
                        corner_radius=6,
                        command=lambda c=cat: self.select_category(c)
                    )
                    btn.grid(row=r_i, column=c_i, padx=2, pady=2, sticky="ew")
                    self.cat_buttons[cat] = btn

        else:
            self.categories = ['全部']
            cat_cn = {'全部': '🦠 全部疾病缺陷' if self.catalog_type == "disorder" else '🌟 全部被动'}
            f_cat_container.columnconfigure(0, weight=1)
            btn = ctk.CTkButton(
                f_cat_container,
                text=cat_cn['全部'],
                height=28,
                font=("Arial", 11, "bold"),
                fg_color="#1e293b",
                hover_color="#334155",
                border_color="#334155",
                border_width=1,
                text_color="#f8fafc",
                corner_radius=6,
                command=lambda: self.select_category('全部')
            )
            btn.grid(row=0, column=0, padx=3, pady=2, sticky="ew")
            self.cat_buttons['全部'] = btn

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
                card.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")

                lbl_icon = ctk.CTkLabel(card, text="", width=48, height=48)
                lbl_icon.pack(side="top", pady=(5, 1))

                # 部位角标（右上角，道具品类 / 技能类型）
                lbl_part = ctk.CTkLabel(card, text="", width=30, height=26)
                lbl_part.place(relx=1.0, x=-3, y=3, anchor="ne")
                # 元素标签（左上角）
                elem_lbls = []
                for j in range(2):
                    el = ctk.CTkLabel(card, text="", width=16, height=16)
                    elem_lbls.append(el)
                # 七项属性（元素下方）
                stat_lbls = []
                for j in range(_PICKER_STAT_POOL):
                    sl = ctk.CTkLabel(card, text="", width=14, height=14)
                    stat_lbls.append(sl)

                lbl_name = ctk.CTkLabel(card, text="", font=("Arial", 10, "bold"), text_color="#e2e8f0", wraplength=96)
                lbl_name.pack(side="top", fill="x", padx=2, pady=(0, 4))

                self.card_slots.append({
                    'card': card,
                    'icon': lbl_icon,
                    'name': lbl_name,
                    'part': lbl_part,
                    'elems': elem_lbls,
                    'stats': stat_lbls,
                    'item': None
                })

        # 3. Bottom Control & Preview Bar
        self.f_bottom = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=0, height=56)
        self.f_bottom.pack(fill="x", side="bottom", padx=0, pady=0)

        # Selected preview block
        self.f_preview = ctk.CTkFrame(self.f_bottom, fg_color="transparent")
        self.f_preview.pack(side="left", padx=16, pady=8)

        self.lbl_sel_icon = ctk.CTkLabel(self.f_preview, text="", width=36, height=36)
        self.lbl_sel_icon.pack(side="left", padx=(0, 8))

        f_sel_text = ctk.CTkFrame(self.f_preview, fg_color="transparent")
        f_sel_text.pack(side="left")

        self.lbl_sel_prefix = ctk.CTkLabel(f_sel_text, text="当前选中:", font=("Arial", 10), text_color="#94a3b8", anchor="w")
        self.lbl_sel_prefix.pack(anchor="w")

        self.lbl_sel_title = ctk.CTkLabel(f_sel_text, text="None", font=("Arial", 12, "bold"), text_color="#38bdf8", anchor="w")
        self.lbl_sel_title.pack(anchor="w")

        self.f_sel_tags = ctk.CTkFrame(self.f_preview, fg_color="transparent")
        self.f_sel_tags.pack(side="left", padx=(8, 0))
        self.lbl_sel_type = ctk.CTkLabel(self.f_sel_tags, text="", width=20, height=20)
        self.lbl_sel_type.pack(side="left", padx=(0, 2))
        self.sel_elem_lbls = []
        for _ in range(_PICKER_ELEM_POOL):
            el = ctk.CTkLabel(self.f_sel_tags, text="", width=16, height=16)
            self.sel_elem_lbls.append(el)
        self.sel_stat_lbls = []
        for _ in range(_PICKER_STAT_PREVIEW_POOL):
            sl = ctk.CTkLabel(self.f_sel_tags, text="", width=16, height=16)
            self.sel_stat_lbls.append(sl)
        self.f_sel_badges = ctk.CTkFrame(self.f_preview, fg_color="transparent")
        self.f_sel_badges.pack(side="left", padx=(10, 0))

        # Pagination block
        f_page = ctk.CTkFrame(self.f_bottom, fg_color="transparent")
        f_page.pack(side="left", expand=True)

        btn_prev = ctk.CTkButton(f_page, text="◀ 上一页", width=80, height=28, fg_color="#1e293b", hover_color="#334155", command=self.prev_page)
        btn_prev.pack(side="left", padx=6)

        self.lbl_page = ctk.CTkLabel(f_page, text="1 / 1", font=("Arial", 12, "bold"), text_color="#f8fafc")
        self.lbl_page.pack(side="left", padx=10)

        btn_next = ctk.CTkButton(f_page, text="下一页 ▶", width=80, height=28, fg_color="#1e293b", hover_color="#334155", command=self.next_page)
        btn_next.pack(side="left", padx=6)

        # Action Buttons
        f_actions = ctk.CTkFrame(self.f_bottom, fg_color="transparent")
        f_actions.pack(side="right", padx=16, pady=8)

        btn_none = ctk.CTkButton(f_actions, text="设为 None (清空)", width=110, height=32, fg_color="#334155", hover_color="#475569", command=self.set_none_and_close)
        btn_none.pack(side="left", padx=5)

        btn_cancel = ctk.CTkButton(f_actions, text="取消", width=70, height=32, fg_color="#1e293b", hover_color="#334155", command=self.destroy)
        btn_cancel.pack(side="left", padx=5)

        btn_confirm = ctk.CTkButton(f_actions, text="✅ 选定此项", width=120, height=32, font=("Arial", 12, "bold"), fg_color="#10b981", hover_color="#059669", command=self.confirm_and_close)
        btn_confirm.pack(side="left", padx=5)

    def select_category(self, cat):
        self.current_category = cat
        for c, btn in self.cat_buttons.items():
            txt_col = class_theme.ui_color(c) if (self.catalog_type in ("ability", "passive") and c in class_theme.CLASS_PALETTE) else None
            if c == cat:
                btn.configure(
                    fg_color="#3730a3" if self.catalog_type in ("ability", "passive") else "#6366f1",
                    hover_color="#312e81" if self.catalog_type in ("ability", "passive") else "#4f46e5",
                    border_color=txt_col or "#818cf8",
                    border_width=2
                )
            else:
                btn.configure(
                    fg_color="#1e293b",
                    hover_color="#334155",
                    border_color="#334155",
                    border_width=1
                )
        self.apply_filter()

    def on_rarity_changed(self, val):
        m = dict(self.rarity_opts)
        self.current_rarity = m.get(val, 'all')
        self.apply_filter()

    def on_search_changed(self, event=None):
        job = getattr(self, '_search_job', None)
        if job:
            try:
                self.after_cancel(job)
            except Exception:
                pass
        self._search_job = self.after(200, self._apply_filter_debounced)

    def _apply_filter_debounced(self):
        self._search_job = None
        self.apply_filter()

    def clear_search(self):
        self.entry_search.delete(0, 'end')
        self.apply_filter()

    def apply_filter(self):
        query = self.entry_search.get().strip().lower()
        res = []
        for item in self.full_catalog:
            # 战斗法术槽：Basic 普攻/移动只留给基础栏；敌人技等仍需搜索才出现
            if self.catalog_type == "ability" and self.allowed_keys is None:
                key = str(item.get("key") or "")
                if _is_basic_action_key(key) and key != self.current_value:
                    continue
                if item.get("picker_hidden") and not query and key != self.current_value:
                    continue
            # Primary filter (kind / set / class / cursed)
            if self.current_category != '全部':
                if self.catalog_type == 'item':
                    if self.current_category == 'cursed':
                        if not (item.get('cursed') or item.get('rarity') == 'cursed' or 'cursed' in str(item.get('rarity', '')).lower()):
                            continue
                    else:
                        if item.get('kind') != self.current_category:
                            continue
                elif self.catalog_type == 'furniture':
                    if item.get('set') != self.current_category:
                        continue
                elif self.catalog_type in ('ability', 'passive'):
                    if (item.get('class') or 'Colorless') != self.current_category:
                        continue
                elif item.get('class') != self.current_category:
                    continue

            # Secondary Rarity filter for items
            if self.catalog_type == 'item' and self.current_rarity != 'all':
                item_rar = item.get('rarity', '').lower()
                if self.current_rarity == 'epic':
                    if item_rar not in ('epic', 'very_rare'):
                        continue
                elif self.current_rarity == 'quest':
                    if item_rar not in ('quest', 'sidequest'):
                        continue
                elif item_rar != self.current_rarity:
                    continue
            
            # Text search filter
            if query:
                k = item.get('key', '').lower()
                name = item.get('name', '').lower()
                name_en = item.get('name_en', '').lower()
                desc = item.get('desc', '').lower()
                sets = str(item.get('sets') or item.get('set') or '').lower()
                stats = str(item.get('stats', '')).lower()
                if query not in k and query not in name and query not in name_en and query not in desc and query not in sets and query not in stats:
                    continue
            res.append(item)

        self.filtered_catalog = res
        self.current_page = 1
        self.render_grid()

    def _card_chrome(self, item):
        """格子底色/描边：物品看稀有度，法术和被动看职业色。"""
        border_col = "#1e293b"
        bg_col = "#131d2e"
        if self.catalog_type == "item":
            r = (item.get('rarity') or '').lower()
            border_col = RARITY_COLORS.get(r, '#1e293b')
            bg_col = RARITY_BG.get(r, '#131d2e')
        elif self.catalog_type == "furniture":
            border_col = "#334155"
        elif self.catalog_type in ("ability", "passive"):
            border_col = class_theme.ui_color(item.get('class'))
        return bg_col, border_col

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

        start_idx = (self.current_page - 1) * self.PAGE_SIZE
        page_items = self.filtered_catalog[start_idx : start_idx + self.PAGE_SIZE]

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
                set_label_image(lbl_icon, icon_img, size=(48, 48))

                # 角标（右上角）: 物品=品类图标, 技能=能力类型图标
                part_img = None
                if self.catalog_type == "item":
                    part_img = get_part_ctk_icon(item.get('kind', ''), size=(30, 26))
                elif self.catalog_type == "ability":
                    part_img = self._type_icon(item.get('type_icon'))
                set_label_image(slot['part'], part_img, size=(30, 26))
                if self.catalog_type == "ability":
                    self._set_elem_icons(slot['elems'], item.get('elements'))
                else:
                    self._set_elem_icons(slot['elems'], None)
                self._set_stat_icons(slot['stats'], ar.extract_core_stat_keys(item))

                bg_col, border_col = self._card_chrome(item)

                # Highlight selected
                if k == self.selected_value:
                    card.configure(fg_color="#143026", border_color="#10b981", border_width=2)
                else:
                    card.configure(fg_color=bg_col, border_color=border_col, border_width=1)

                card.grid() # make visible

                if slot.get('bound_key') != k:
                    self.bind_card_events(card, lbl_icon, lbl_name, item)
                    slot['bound_key'] = k
            else:
                slot['item'] = None
                slot['bound_key'] = None
                set_label_image(slot['part'], None, size=(30, 26))
                self._set_elem_icons(slot.get('elems') or [], None)
                self._set_stat_icons(slot.get('stats') or [], None)
                set_label_image(lbl_icon, None, size=(48, 48))
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
                item = slot['item']
                if item['key'] == key:
                    card.configure(fg_color="#143026", border_color="#10b981", border_width=2)
                else:
                    bg_col, border_col = self._card_chrome(item)
                    card.configure(fg_color=bg_col, border_color=border_col, border_width=1)

    def update_selected_preview(self, key):
        for child in self.f_sel_badges.winfo_children():
            child.destroy()

        if not key or key == 'None':
            set_label_image(self.lbl_sel_icon, None, size=(36, 36))
            self.lbl_sel_title.configure(text="None (未选择)", text_color="#94a3b8")
            set_label_image(self.lbl_sel_type, None, size=(20, 20))
            self._pack_preview_icons(self.sel_elem_lbls, [])
            self._pack_preview_icons(self.sel_stat_lbls, [])
            return

        icon_img = self.get_icon(key, size=(36, 36))
        set_label_image(self.lbl_sel_icon, icon_img, size=(36, 36))

        item = self.catalog_map.get(key)
        cn_name = item.get('name') if item else key
        self.lbl_sel_title.configure(text=f"{cn_name} ({key})", text_color="#38bdf8")

        if item:
            if self.catalog_type == "ability":
                set_label_image(self.lbl_sel_type, self._type_icon(item.get('type_icon'), size=(20, 20)), size=(20, 20))
                elems = [str(e).lower() for e in (item.get('elements') or []) if e][:_PICKER_ELEM_POOL]
                self._pack_preview_icons(self.sel_elem_lbls, [self._tag_icon(e) for e in elems])
            else:
                set_label_image(self.lbl_sel_type, None, size=(20, 20))
                self._pack_preview_icons(self.sel_elem_lbls, [])
            core_stats = ar.extract_core_stat_keys(item)[:_PICKER_STAT_PREVIEW_POOL]
            self._pack_preview_icons(self.sel_stat_lbls, [ar.get_stat_icon(k, size=(16, 16)) for k in core_stats])
            extra_items = []
            if self.catalog_type == "ability":
                mana = item.get('mana', 0)
                dmg = item.get('damage', '')
                rng = item.get('range', 0)
                if mana > 0:
                    extra_items.append(('mana', f"消耗 {mana}"))
                if dmg:
                    extra_items.append(('damage', str(dmg)))
                if rng > 0:
                    extra_items.append(('range', str(rng)))
                stats_list = []
            elif self.catalog_type == "item":
                stats_list = ar.extract_stats_from_item(item)
            else:
                stats_list = ar.parse_stats_data(item.get('stats'))

            badges = ar.create_stat_badges_bar(self.f_sel_badges, stats_list, extra_items=extra_items, max_per_row=3)
            if badges:
                badges.pack(side="left")
        else:
            set_label_image(self.lbl_sel_type, None, size=(20, 20))
            self._pack_preview_icons(self.sel_elem_lbls, [])
            self._pack_preview_icons(self.sel_stat_lbls, [])

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
        global _OPEN_PICKER
        GameTooltip.get_instance().hide()
        try:
            self.grab_release()
        except Exception:
            pass
        if _OPEN_PICKER is self:
            _OPEN_PICKER = None
        super().destroy()
