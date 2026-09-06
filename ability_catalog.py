"""技能图鉴：从本地 abilities_combined.json 加载，筛选与卡池标签对齐 mewcodex Ability Viewer。"""
import json
import os
import sys

DEFAULT_HIDDEN_FILES = (
    'armor_abilities.gon',
    'consumable_item_abilities.gon',
    'contextual_abilities.gon',
    'disorder_abilities.gon',
    'event_abilities.gon',
    'finalboss_abilities.gon',
    'guillotina_abilities.gon',
    'item_abilities.gon',
    'kaiju_abilities.gon',
    'misc_abilities.gon',
    'rifthead_abilities.gon',
    'special_enemy_abilities.gon',
    'terminator_abilities.gon',
    'test_abilities.gon',
    'throbbing_king_abilities.gon',
    'util_abilities.gon',
)

CLASS_ORDER = (
    'Colorless', 'Fighter', 'Hunter', 'Mage', 'Tank', 'Medic', 'Thief',
    'Necromancer', 'Butcher', 'Druid', 'Monk', 'Psychic', 'Tinkerer', 'Jester',
)

CLASS_LABELS = {
    'fighter': '战士',
    'thief': '盗贼',
    'tank': '坦克',
    'mage': '法师',
    'medic': '牧师',
    'hunter': '猎人',
    'necromancer': '死灵法师',
    'butcher': '屠夫',
    'monk': '武僧',
    'druid': '德鲁伊',
    'psychic': '灵能者',
    'tinkerer': '工匠',
    'jester': '小丑',
    'colorless': '无项圈',
}

POOL_LABELS = {
    'BasicAttackPool': '默认/基础攻击',
    'CatAbilityPool': '默认',
    'CatGenAbilityPool': '默认/生成能力',
    'ColorlessAbilities': '默认/无项圈能力',
}

GROUP_LABELS = {
    'attack': '攻击',
    'defense': '防御',
    'move': '移动',
    'misc': '其他',
}

FORMULA_ZH = (
    "bonus_melee_damage = str-5    "
    "bonus_melee_ability_damage = (str-5)/2    "
    "bonus_ranged_damage = (dex-5)/2    "
    "bonus_basic_spell_damage 多数情况下为 0    "
    "clamp(x, a, b) = min(max(x, a), b)    "
    "乘除向零取整"
)

_CATALOG = None
_JSON_CACHE = {}


def _search_bases():
    bases = [getattr(sys, '_MEIPASS', None), os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
    if getattr(sys, 'frozen', False):
        bases.insert(1, os.path.dirname(sys.executable))
    return [b for b in bases if b]


def _find_resource(*parts):
    for base in _search_bases():
        p = os.path.join(base, *parts)
        if os.path.exists(p):
            return p
    return None


def _load_json(rel_parts):
    key = tuple(rel_parts)
    if key in _JSON_CACHE:
        return _JSON_CACHE[key]
    path = _find_resource(*rel_parts)
    if not path:
        _JSON_CACHE[key] = None
        return None
    with open(path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    _JSON_CACHE[key] = data
    return data


def _loc(texts, fallback=''):
    if isinstance(texts, dict):
        t = (texts.get('zh') or texts.get('en') or '').strip()
        if t:
            return t
    return (fallback or '').strip()


def _has_rendered_text(texts, fallback):
    if isinstance(fallback, str) and fallback.strip():
        return True
    if not isinstance(texts, dict):
        return False
    return any(isinstance(v, str) and v.strip() for v in texts.values())


def class_label(class_name):
    if not class_name:
        return '其他（无职业）'
    return CLASS_LABELS.get(str(class_name).lower(), class_name)


def is_file_pool_tag(tag):
    return str(tag or '').startswith('file:')


def localize_pool_tag(tag):
    if not tag:
        return ''
    direct = POOL_LABELS.get(tag)
    if direct:
        return direct
    parts = str(tag).split('.')
    if len(parts) < 2:
        return tag
    cls, section = parts[0], parts[1]
    if section == 'ability_groups' and len(parts) > 2:
        group = GROUP_LABELS.get(parts[2], parts[2])
        return f"{class_label(cls)}/{group}"
    if section == 'ability_pool':
        return class_label(cls)
    if section == 'attack_pool':
        return f"{class_label(cls)}/基础攻击"
    if is_file_pool_tag(tag):
        return str(tag).split(':', 1)[-1]
    return tag


def visible_pools(pools, show_file_pools=False):
    tags = list(pools or [])
    grouped = {str(t).split('.')[0] for t in tags if str(t).split('.')[1:2] == ['ability_groups']}
    out = []
    for tag in tags:
        if not show_file_pools and is_file_pool_tag(tag):
            continue
        parts = str(tag).split('.')
        if len(parts) >= 2 and parts[1] == 'ability_pool' and parts[0] in grouped:
            continue
        out.append(tag)
    return out


def _dmg_text(damage):
    if not isinstance(damage, dict):
        return ''
    val = damage.get('value')
    if val is None or val == '':
        heal = damage.get('heal_value')
        return '' if heal is None else str(heal)
    return str(val)


def _catalog_name_map():
    rows = _load_json(('assets', 'abilities_catalog.json')) or []
    return {r.get('key'): r for r in rows if r.get('key')}


def _source_name(source_file):
    return str(source_file or '').replace('\\', '/').split('/')[-1]


def _is_default_hidden_file(source_file):
    src = _source_name(source_file)
    return any(src.endswith(fn) for fn in DEFAULT_HIDDEN_FILES)


def _editor_notes():
    notes = _load_json(('wiki_data', 'editor_notes.json')) or {}
    return notes if isinstance(notes, dict) else {}


def normalize_ability(raw, catalog_row=None, notes=None):
    catalog_row = catalog_row or {}
    key = raw.get('ability_code') or ''
    wiki_class = raw.get('ability_class') or ''
    name = _loc(raw.get('ability_name_texts'), raw.get('ability_name') or key)
    cat_name = catalog_row.get('name') or ''
    if cat_name and any('\u4e00' <= c <= '\u9fff' for c in cat_name):
        name = cat_name
    name_en = _loc({'en': (raw.get('ability_name_texts') or {}).get('en')}, raw.get('ability_name') or key)
    name_up = _loc(raw.get('ability_name_texts_upgraded'), raw.get('ability_name_upgraded') or '')
    desc = _loc(raw.get('description_texts'), raw.get('description') or catalog_row.get('desc') or '')
    desc_up = _loc(raw.get('description2_texts'), raw.get('description_2') or '')
    cost = raw.get('cost') or {}
    cost_up = raw.get('cost_upgraded') or {}
    dmg = raw.get('damage') or {}
    dmg_up = raw.get('damage_upgraded') or {}
    frame = raw.get('frame_number')
    has_icon = frame is not None
    has_title = _has_rendered_text(raw.get('ability_name_texts'), raw.get('ability_name'))
    has_desc = (
        _has_rendered_text(raw.get('description_texts'), raw.get('description'))
        or _has_rendered_text(raw.get('description2_texts'), raw.get('description_2'))
    )
    file_hidden = _is_default_hidden_file(raw.get('source_file'))
    wiki_hidden = file_hidden or not (has_icon and has_title and has_desc)
    pools = list(raw.get('ability_pools') or [])
    display_class = wiki_class or catalog_row.get('class') or ''
    note = ''
    if isinstance(notes, dict):
        note = str(notes.get(key) or '').strip()
    return {
        'key': key,
        'name': name or key,
        'name_en': name_en or key,
        'name_up': name_up,
        'code_up': raw.get('ability_code_upgraded') or '',
        'desc': desc,
        'desc_up': desc_up,
        'desc_notes': raw.get('desc_notes') or '',
        'desc2_notes': raw.get('desc2_notes') or '',
        'editor_note': note,
        'class': display_class,
        'wiki_class': wiki_class,
        'pools': pools,
        'tags': [str(t) for t in (raw.get('tags') or []) if t],
        'elements': [str(e).lower() for e in (raw.get('elements') or []) if e],
        'elements_up': [str(e).lower() for e in (raw.get('elements_upgraded') or []) if e],
        'type_icon': raw.get('type_icon') or catalog_row.get('type_icon') or '',
        'type_icon_up': raw.get('type_icon_upgraded') or '',
        'mana': cost.get('mana') if isinstance(cost, dict) else 0,
        'mana_up': cost_up.get('mana') if isinstance(cost_up, dict) else None,
        'act_points': cost.get('act_points') if isinstance(cost, dict) else None,
        'damage': _dmg_text(dmg) or catalog_row.get('damage') or '',
        'damage_up': _dmg_text(dmg_up),
        'heal': '' if not isinstance(dmg, dict) or dmg.get('heal_value') in (None, '') else str(dmg.get('heal_value')),
        'damage_type': (dmg.get('type') if isinstance(dmg, dict) else '') or '',
        'has_icon': bool(has_icon),
        'frame': frame,
        'source': _source_name(raw.get('source_file')),
        'wiki_hidden': wiki_hidden,
        'file_hidden': file_hidden,
        'unlock': raw.get('unlock_requirements') or '',
        'refs': list(raw.get('refs') or []) + list(raw.get('refs_upgraded') or []),
        'template': raw.get('template') or '',
        'target_text': raw.get('target_text') or '',
        'icon_key': catalog_row.get('icon_key') or raw.get('ability_icon') or '',
    }


def load_ability_catalog():
    """规范化技能列表（懒加载缓存）。"""
    global _CATALOG
    if _CATALOG is not None:
        return _CATALOG
    raw = _load_json(('wiki_data', 'abilities_combined.json')) or {}
    rows = raw.get('abilities') or []
    cmap = _catalog_name_map()
    notes = _editor_notes()
    out = []
    seen = set()
    for w in rows:
        key = w.get('ability_code')
        if not key or key in seen or key == 'None':
            continue
        seen.add(key)
        out.append(normalize_ability(w, cmap.get(key), notes))
    if not out:
        for row in cmap.values():
            key = row.get('key')
            if not key or key in seen or key == 'None':
                continue
            seen.add(key)
            out.append({
                'key': key,
                'name': row.get('name') or key,
                'name_en': row.get('name_en') or key,
                'name_up': '',
                'code_up': row.get('variant_of') or '',
                'desc': row.get('desc') or '',
                'desc_up': '',
                'desc_notes': '',
                'desc2_notes': '',
                'editor_note': '',
                'class': row.get('class') or '',
                'wiki_class': row.get('class') if row.get('class') in CLASS_ORDER else '',
                'pools': [],
                'tags': [],
                'elements': list(row.get('elements') or []),
                'elements_up': [],
                'type_icon': row.get('type_icon') or '',
                'type_icon_up': '',
                'mana': row.get('mana') or 0,
                'mana_up': None,
                'act_points': None,
                'damage': row.get('damage') or '',
                'damage_up': '',
                'heal': '',
                'damage_type': '',
                'has_icon': bool(row.get('has_icon')),
                'frame': None,
                'source': row.get('source') or '',
                'wiki_hidden': bool(row.get('picker_hidden')),
                'file_hidden': bool(row.get('picker_hidden')),
                'unlock': '',
                'refs': [],
                'template': '',
                'target_text': '',
                'icon_key': row.get('icon_key') or '',
            })
    _CATALOG = out
    return _CATALOG


def list_ability_classes(items=None):
    items = items if items is not None else load_ability_catalog()
    present = {it.get('wiki_class') for it in items if it.get('wiki_class')}
    return [c for c in CLASS_ORDER if c in present]


def list_ability_pools(items=None, show_file_pools=False):
    items = items if items is not None else load_ability_catalog()
    tags = {}
    for it in items:
        for tag in it.get('pools') or []:
            if not show_file_pools and is_file_pool_tag(tag):
                continue
            if tag not in tags:
                tags[tag] = localize_pool_tag(tag)
    return sorted(tags.items(), key=lambda kv: kv[1])


def _parse_hash_query(raw):
    s = (raw or '').strip()
    if not s.startswith('#'):
        return ''
    s = s[1:].strip()
    if s.startswith('('):
        end = s.find(')')
        if end > 1:
            return s[1:end].strip()
        return ''
    return s


def filter_abilities(query='', class_key='', pool_key='', show_hidden=False, show_file_pools=False, items=None):
    items = items if items is not None else load_ability_catalog()
    q = (query or '').strip()
    q_low = q.lower()
    pool_search = _parse_hash_query(q).lower() if q.startswith('#') else ''
    out = []
    for it in items:
        if not show_hidden and it.get('wiki_hidden'):
            continue
        if class_key == '__null__':
            if it.get('wiki_class'):
                continue
        elif class_key and it.get('wiki_class') != class_key:
            continue
        pools = it.get('pools') or []
        if pool_key and pool_key not in pools:
            continue
        if pool_search:
            hit = False
            for tag in pools:
                if pool_search in str(tag).lower() or pool_search in localize_pool_tag(tag).lower():
                    hit = True
                    break
            if not hit:
                continue
        elif q_low:
            hay = f"{it.get('name','')} {it.get('name_en','')} {it.get('key','')} {it.get('desc','')} {it.get('desc_up','')}".lower()
            if q_low not in hay:
                continue
        out.append(it)
    return out
