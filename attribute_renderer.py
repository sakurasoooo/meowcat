"""
attribute_renderer.py
---------------------
通用属性与状态效果渲染模块 (Universal Attribute & Icon System)
负责提供《Mewgenics》全量解包属性图标管理、结构化属性药丸徽章 (Pill Badge) 生成，
以及富文本标签解析（替换 [img:shield]、[img:int]、+N Brace 等）。
"""

import os
import sys
import json
import re
from PIL import Image
import customtkinter as ctk

# Base and asset path resolution (support PyInstaller _MEIPASS)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    BASE_DIR = getattr(sys, '_MEIPASS', BASE_DIR)

STATS_ICONS_DIR = os.path.join(BASE_DIR, "assets", "icons", "stats")

# 1. 属性元数据注册表
ATTRIBUTE_META = {
    'shield': {
        'name_zh': '护盾',
        'name_en': 'Shield',
        'icon_file': 'shield.png',
        'color': '#38bdf8',          # 护盾浅蓝
        'border_color': '#0284c7',
        'bg_color': '#0c2738',
        'emoji': '🛡️',
    },
    'divineshield': {
        'name_zh': '神圣护盾',
        'name_en': 'Divine Shield',
        'icon_file': 'divineshield.png',
        'color': '#c084fc',          # 神圣晶紫
        'border_color': '#9333ea',
        'bg_color': '#24143a',
        'emoji': '✨',
    },
    'brace': {
        'name_zh': '招架',
        'name_en': 'Brace',
        'icon_file': 'brace.png',
        'color': '#f59e0b',          # 琥珀金黄
        'border_color': '#b45309',
        'bg_color': '#2a1a08',
        'emoji': '🐾',
    },
    'str': {
        'name_zh': '力量',
        'name_en': 'Strength',
        'icon_file': 'str.png',
        'color': '#ef4444',          # 绯红
        'border_color': '#b91c1c',
        'bg_color': '#2a0c0c',
        'emoji': '💪',
    },
    'dex': {
        'name_zh': '敏捷',
        'name_en': 'Dexterity',
        'icon_file': 'dex.png',
        'color': '#10b981',          # 翠绿
        'border_color': '#047857',
        'bg_color': '#07271c',
        'emoji': '🏹',
    },
    'con': {
        'name_zh': '体质',
        'name_en': 'Constitution',
        'icon_file': 'con.png',
        'color': '#f43f5e',          # 玫瑰红
        'border_color': '#be123c',
        'bg_color': '#290914',
        'emoji': '💖',
    },
    'int': {
        'name_zh': '智力',
        'name_en': 'Intelligence',
        'icon_file': 'int.png',
        'color': '#60a5fa',          # 睿智蓝
        'border_color': '#2563eb',
        'bg_color': '#0d1f3b',
        'emoji': '💡',
    },
    'spd': {
        'name_zh': '速度',
        'name_en': 'Speed',
        'icon_file': 'spd.png',
        'color': '#fbbf24',          # 飞奔黄
        'border_color': '#d97706',
        'bg_color': '#2d2106',
        'emoji': '👟',
    },
    'cha': {
        'name_zh': '魅力',
        'name_en': 'Charisma',
        'icon_file': 'cha.png',
        'color': '#ec4899',          # 魅力粉
        'border_color': '#be185d',
        'bg_color': '#2a091c',
        'emoji': '👄',
    },
    'lck': {
        'name_zh': '幸运',
        'name_en': 'Luck',
        'icon_file': 'lck.png',
        'color': '#22c55e',          # 幸运绿
        'border_color': '#15803d',
        'bg_color': '#092512',
        'emoji': '🍀',
    },
    'health': {
        'name_zh': '生命',
        'name_en': 'Health',
        'icon_file': 'health.png',
        'color': '#f87171',
        'border_color': '#dc2626',
        'bg_color': '#2b0c0c',
        'emoji': '❤️',
    },
    'mana': {
        'name_zh': '魔能',
        'name_en': 'Mana',
        'icon_file': 'mana.png',
        'color': '#60a5fa',
        'border_color': '#2563eb',
        'bg_color': '#0d1f3b',
        'emoji': '💧',
    },
    'damage': {
        'name_zh': '伤害',
        'name_en': 'Damage',
        'icon_file': 'sword.png',
        'color': '#f87171',
        'border_color': '#dc2626',
        'bg_color': '#2b0c0c',
        'emoji': '⚔️',
    },
    'range': {
        'name_zh': '射程',
        'name_en': 'Range',
        'icon_file': 'dex.png',
        'color': '#fbbf24',
        'border_color': '#d97706',
        'bg_color': '#2d2106',
        'emoji': '🎯',
    },
    'comfort': {
        'name_zh': '舒适度',
        'name_en': 'Comfort',
        'icon_file': 'comfort.png',
        'color': '#38bdf8',
        'border_color': '#0284c7',
        'bg_color': '#0c2738',
        'emoji': '🛋️',
    },
    'stimulation': {
        'name_zh': '刺激度',
        'name_en': 'Stimulation',
        'icon_file': 'stimulation.png',
        'color': '#f59e0b',
        'border_color': '#b45309',
        'bg_color': '#2a1a08',
        'emoji': '⚡',
    },
    'appeal': {
        'name_zh': '吸引力',
        'name_en': 'Appeal',
        'icon_file': 'appeal.png',
        'color': '#ec4899',
        'border_color': '#be185d',
        'bg_color': '#2a091c',
        'emoji': '💖',
    },
    'evolution': {
        'name_zh': '变异促进',
        'name_en': 'Evolution',
        'icon_file': 'evolution.png',
        'color': '#a855f7',
        'border_color': '#7e22ce',
        'bg_color': '#200d38',
        'emoji': '🧬',
    },
    'breed_suppression': {
        'name_zh': '繁殖抑制',
        'name_en': 'Breed Suppression',
        'icon_file': None,
        'color': '#94a3b8',
        'border_color': '#475569',
        'bg_color': '#1e293b',
        'emoji': '🚫',
    },
    'fight_bonus_rewards': {
        'name_zh': '战斗奖励',
        'name_en': 'Fight Rewards',
        'icon_file': None,
        'color': '#fbbf24',
        'border_color': '#d97706',
        'bg_color': '#2d2106',
        'emoji': '🎁',
    },
    'fight_risk': {
        'name_zh': '战斗风险',
        'name_en': 'Fight Risk',
        'icon_file': 'sword.png',
        'color': '#f87171',
        'border_color': '#dc2626',
        'bg_color': '#2b0c0c',
        'emoji': '⚔️',
    },
    'food_storage': {
        'name_zh': '食物储存',
        'name_en': 'Food Storage',
        'icon_file': None,
        'color': '#f97316',
        'border_color': '#c2410c',
        'bg_color': '#281105',
        'emoji': '🍖',
    },
}

# 别名映射
KEY_ALIASES = {
    'divine_shield': 'divineshield',
    'speed': 'spd',
    'strength': 'str',
    'dexterity': 'dex',
    'constitution': 'con',
    'intelligence': 'int',
    'charisma': 'cha',
    'luck': 'lck',
    'sword': 'damage',
    'dmg': 'damage',
    'atk': 'damage',
    '攻击': 'damage',
    '伤害': 'damage',
    '魔能': 'mana',
    '法力': 'mana',
    '生命': 'health',
    '血量': 'health',
    '护盾': 'shield',
    '神圣护盾': 'divineshield',
    '招架': 'brace',
    '坚守': 'brace',
    '护甲': 'brace',
    '舒适度': 'comfort',
    '刺激度': 'stimulation',
    '吸引力': 'appeal',
    '变异促进': 'evolution',
}

# 图标缓存
_CTK_ICON_CACHE = {}

def normalize_attribute_key(raw_key: str) -> str:
    """标准化属性键名"""
    if not raw_key:
        return ""
    k = str(raw_key).strip().lower().replace(" ", "").replace("_", "")
    if raw_key in KEY_ALIASES:
        return KEY_ALIASES[raw_key]
    if k in KEY_ALIASES:
        return KEY_ALIASES[k]
    if k in ATTRIBUTE_META:
        return k
    return raw_key.strip().lower()

def get_attribute_meta(key: str) -> dict:
    """获取属性元数据"""
    norm = normalize_attribute_key(key)
    meta = ATTRIBUTE_META.get(norm)
    if meta:
        return meta
    return {
        'name_zh': key,
        'name_en': key.title(),
        'icon_file': None,
        'color': '#34d399',
        'border_color': '#059669',
        'bg_color': '#06261c',
        'emoji': '📊',
    }

def get_stat_icon(key: str, size=(20, 20)) -> ctk.CTkImage:
    """获取指定属性的高清 CTkImage 图标"""
    meta = get_attribute_meta(key)
    icon_fn = meta.get('icon_file')
    if not icon_fn:
        return None
    cache_k = f"{icon_fn}_{size[0]}x{size[1]}"
    if cache_k in _CTK_ICON_CACHE:
        return _CTK_ICON_CACHE[cache_k]
    
    icon_path = os.path.join(STATS_ICONS_DIR, icon_fn)
    if not os.path.exists(icon_path):
        return None
    try:
        pil_img = Image.open(icon_path).convert("RGBA")
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        _CTK_ICON_CACHE[cache_k] = ctk_img
        return ctk_img
    except Exception as e:
        print(f"[attribute_renderer] Error loading icon {icon_fn}: {e}")
        return None

def create_attribute_pill(parent, key: str, value=None, size=(18, 18), font_size=11) -> ctk.CTkFrame:
    """
    创建单个高质感的属性胶囊徽章 (Pill Badge)
    外观：[ 图标 (18x18) ] [ 属性名 +数值 ]
    """
    meta = get_attribute_meta(key)
    name_zh = meta['name_zh']
    color = meta['color']
    border_color = meta['border_color']
    bg_color = meta['bg_color']
    emoji = meta['emoji']

    pill = ctk.CTkFrame(
        parent,
        fg_color=bg_color,
        border_color=border_color,
        border_width=1,
        corner_radius=6
    )

    icon_img = get_stat_icon(key, size=size)
    if icon_img:
        lbl_ico = ctk.CTkLabel(pill, text="", image=icon_img, width=size[0], height=size[1])
        lbl_ico.pack(side="left", padx=(5, 3), pady=2)
    else:
        lbl_ico = ctk.CTkLabel(pill, text=emoji, font=("Segoe UI Emoji", font_size))
        lbl_ico.pack(side="left", padx=(5, 3), pady=2)

    if value is not None:
        if isinstance(value, (int, float)):
            val_str = f"{value:+g}" if value != 0 else "0"
            text_str = f"{name_zh} {val_str}"
        else:
            text_str = f"{name_zh} {value}"
    else:
        text_str = name_zh

    lbl_txt = ctk.CTkLabel(
        pill,
        text=text_str,
        font=("Arial", font_size, "bold"),
        text_color=color
    )
    lbl_txt.pack(side="left", padx=(1, 6), pady=2)

    return pill

def parse_stats_data(stats_input) -> list:
    """解析各种格式属性输入为 [(key, val), ...]"""
    if not stats_input:
        return []
    if isinstance(stats_input, dict):
        return list(stats_input.items())
    if isinstance(stats_input, list):
        return stats_input
    if isinstance(stats_input, str):
        stats_input = stats_input.strip()
        if stats_input.startswith('{') and stats_input.endswith('}'):
            try:
                d = json.loads(stats_input)
                return list(d.items())
            except Exception:
                pass
        res = []
        for pair in stats_input.replace('{', '').replace('}', '').split(','):
            if ':' in pair:
                parts = pair.split(':', 1)
                k = parts[0].strip().strip('\'"')
                v = parts[1].strip().strip('\'"')
                try:
                    v = int(v)
                except ValueError:
                    pass
                res.append((k, v))
        return res
    return []

CORE_STAT_KEYS = ('str', 'dex', 'con', 'int', 'spd', 'cha', 'lck')
_IMG_CORE_STAT_RE = re.compile(r'\[img:(str|dex|con|int|spd|cha|lck)\]', re.IGNORECASE)
_DMG_CORE_STAT_RE = re.compile(r'(?:bonus_)?(str|dex|con|int|spd|cha|lck)\b', re.IGNORECASE)


def extract_core_stat_keys(item_row: dict) -> list:
    """从描述 [img:str] 与伤害公式中提取七项核心属性，保序去重。"""
    if not item_row:
        return []
    found = []
    seen = set()

    def add(key):
        k = str(key).lower()
        if k in CORE_STAT_KEYS and k not in seen:
            seen.add(k)
            found.append(k)

    for m in _IMG_CORE_STAT_RE.finditer(item_row.get('desc') or ''):
        add(m.group(1))
    for m in _DMG_CORE_STAT_RE.finditer(str(item_row.get('damage') or '')):
        add(m.group(1))
    return found


def extract_stats_from_item(item_row: dict) -> list:
    """从道具字典中提取全量属性（包括 JSON stats 字段与描述中的 Brace/招架）"""
    stats_list = []
    raw_stats = item_row.get('stats')
    if raw_stats:
        stats_list.extend(parse_stats_data(raw_stats))

    desc_en = item_row.get('desc_en') or ''
    desc_zh = item_row.get('desc_zh') or ''
    combined_desc = f"{desc_en}\n{desc_zh}"

    has_brace = any(normalize_attribute_key(k) == 'brace' for k, _ in stats_list)
    if not has_brace:
        m_en = re.search(r'([+-]?\d+)\s*Brace', combined_desc, re.IGNORECASE)
        m_zh = re.search(r'【?招架】?\s*([+-]?\d+)', combined_desc)
        if not m_zh:
            m_zh = re.search(r'([+-]?\d+)\s*层?【?招架】?', combined_desc)
        
        brace_val = None
        if m_en:
            try:
                brace_val = int(m_en.group(1))
            except ValueError:
                pass
        elif m_zh:
            try:
                brace_val = int(m_zh.group(1))
            except ValueError:
                pass

        if brace_val is not None:
            stats_list.append(('brace', brace_val))

    return stats_list

def create_stat_badges_bar(parent, stats_list, extra_items=None, max_per_row=4) -> ctk.CTkFrame:
    """创建属性徽章流 Frame 容器"""
    if isinstance(stats_list, (dict, str)):
        stats_list = parse_stats_data(stats_list)
    
    all_items = []
    if extra_items:
        all_items.extend(extra_items)
    if stats_list:
        all_items.extend(stats_list)

    if not all_items:
        return None

    f_bar = ctk.CTkFrame(parent, fg_color="transparent")
    
    row_frame = ctk.CTkFrame(f_bar, fg_color="transparent")
    row_frame.pack(fill="x", pady=1)
    
    col_count = 0
    for k, v in all_items:
        if v is None or v == '' or (v == 0 and k not in ('mana', 'damage')):
            continue
        if col_count >= max_per_row:
            row_frame = ctk.CTkFrame(f_bar, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)
            col_count = 0

        pill = create_attribute_pill(row_frame, k, v)
        pill.pack(side="left", padx=3, pady=2)
        col_count += 1

    return f_bar

def format_rich_description(text: str) -> str:
    """将 [img:xxx] 和 +1 Brace 转换为易读的图文富文本字符串"""
    if not text:
        return ""

    out = text

    tag_map = {
        '[img:shield]': ' [🛡️护盾] ',
        '[img:divineshield]': ' [✨神圣护盾] ',
        '[img:brace]': ' [🐾招架] ',
        '[img:str]': ' [💪力量] ',
        '[img:dex]': ' [🏹敏捷] ',
        '[img:con]': ' [💖体质] ',
        '[img:int]': ' [💡智力] ',
        '[img:spd]': ' [👟速度] ',
        '[img:cha]': ' [👄魅力] ',
        '[img:lck]': ' [🍀幸运] ',
        '[img:health]': ' [❤️生命] ',
        '[img:mana]': ' [💧魔能] ',
        '[img:sword]': ' [⚔️伤害] ',
        '[img:comfort]': ' [🛋️舒适度] ',
        '[img:stimulation]': ' [⚡刺激度] ',
        '[img:appeal]': ' [💖吸引力] ',
        '[img:evolution]': ' [🧬变异促进] ',
    }
    for tag, rep in tag_map.items():
        out = out.replace(tag, rep)

    out = re.sub(r'([+-]?\d+)\s*Brace\.?', r'\1 [🐾招架]', out, flags=re.IGNORECASE)
    out = re.sub(r'\bBrace\s*([+-]?\d+)', r'[🐾招架] \1', out, flags=re.IGNORECASE)
    out = re.sub(r'【招架】', '[🐾招架]', out)
    out = re.sub(r'【坚守】', '[🐾坚守]', out)
    out = re.sub(r'[ \t]{2,}', ' ', out)

    return out.strip()