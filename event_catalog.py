"""事件图鉴：从本地游戏事件定义（wiki_data/events_combined.json，源自 data/events/*.gon）
加载标题/选项/奖惩，解析方式对齐 mewcodex Events Viewer。
"""
import json
import os
import re
import sys

EVENT_TYPE_LABELS = {
    'alley_events': '小巷',
    'boneyard_events': '白骨墓园',
    'build_a_boss': '打造首领',
    'bunker_events': '地堡',
    'caves_events': '洞窟',
    'core_events': '地核',
    'crater_events': '陨坑',
    'dead_body': '尸体',
    'debug_events': '调试',
    'desert_events': '沙漠',
    'future_events': '德·未来',
    'iceage_events': '冰河',
    'junkyard_events': '垃圾场',
    'jurassic_events': '侏罗纪',
    'lab_events': '实验室',
    'legacy_events': '遗产',
    'misc_events': '杂项',
    'monster': '怪物',
    'moon_events': '月球',
    'npc_events': 'NPC',
    'quest_events': '任务',
    'sequence_event_continuations': '序列',
    'sewer_events': '下水道',
    'special_events': '特殊',
    'specific_events': '特定',
    'theend_events': '终点',
    'treasure_box': '宝箱',
    'wip_events': '未完成',
}

STAT_LABELS = {
    'str': '力量', 'dex': '敏捷', 'con': '体质', 'int': '智力',
    'spd': '速度', 'cha': '魅力', 'lck': '运气', 'coins': '金币',
    'none': '无检定',
}

CAT_CHOICE_LABELS = {
    'random': '随机',
    'choose': '选择',
    'none': '无',
}

RARITY_LABELS = {
    'common': '普通',
    'uncommon': '罕见',
    'rare': '稀有',
    'very_rare': '超稀有',
    'medium': '中等',
    'quest': '任务',
    'sidequest': '支线任务',
}

STRUCTURAL_TITLES = {
    'random_pool': '随机选取一项',
    'random_pool_consider_luck': '随机选取一项（受幸运影响）',
    'random_chance': '随机概率',
    'conditional_reward': '条件奖励',
    'legacy_token_conditional_reward': '条件奖励',
    'requirements': '条件',
    'else': '否则',
}

_TOKEN_MAP = {
    '{catname}': '猫名', '{his}': '他的', '{His}': '他的',
    '{him}': '他', '{he}': '他', '{He}': '他',
}

_RICH_RE = re.compile(r'\[/?[a-zA-Z](?::[^\]]+)?\]')

_CATALOG = None
_NAME_INDEX = None
_EVENT_ZH = None

# 游戏内汉化与 wiki 旧译的常见用字差（毕皮斯 / 比皮斯）
_SEARCH_FOLD = str.maketrans({
    '毕': '比',
    '…': '.',
    '“': '"',
    '”': '"',
    '‘': "'",
    '’': "'",
})


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


_JSON_CACHE = {}


def _load_json(rel_parts):
    key = tuple(rel_parts)
    if key in _JSON_CACHE:
        return _JSON_CACHE[key]
    path = _find_resource(*rel_parts)
    if not path:
        _JSON_CACHE[key] = None
        return None
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    _JSON_CACHE[key] = data
    return data


def clean_text(text):
    if not text:
        return ''
    s = str(text).replace('\r\n', '\n').replace('\r', '\n')
    for k, v in _TOKEN_MAP.items():
        s = s.replace(k, v)
    s = _RICH_RE.sub('', s)
    s = s.replace('[/i]', '').replace('[/b]', '').replace('[/a]', '')
    return s.strip()


def _loc(texts, fallback=''):
    if not isinstance(texts, dict):
        return fallback
    return (texts.get('zh') or texts.get('en') or fallback or '').strip()


def _event_zh_map():
    global _EVENT_ZH
    if _EVENT_ZH is None:
        data = _load_json(('wiki_data', 'event_zh.json'))
        _EVENT_ZH = data if isinstance(data, dict) else {}
    return _EVENT_ZH


def _event_zh(key, fallback=''):
    if key:
        zh = _event_zh_map().get(key)
        if zh:
            return zh
    return fallback


def _loc_overlay(key, texts, fallback=''):
    return _event_zh(key, _loc(texts, fallback))


def _norm_search(text):
    s = (text or '').replace('\r\n', '\n').replace('\r', '\n').lower()
    s = s.translate(_SEARCH_FOLD)
    return ' '.join(s.split())


def type_key_from_source(source_file):
    if not source_file:
        return ''
    name = str(source_file).replace('\\', '/').split('/')[-1]
    return re.sub(r'\.gon$', '', name, flags=re.I)


def type_label(type_key):
    return EVENT_TYPE_LABELS.get(type_key, (type_key or '').replace('_', ' ') or '未知')


_KIND_NAME_KEYS = {
    'item': ('ARMOR_{}_NAME', 'ITEM_{}_NAME'),
    'passive': ('PASSIVE_{}_NAME', 'DISORDER_{}_NAME'),
    'ability': ('ABILITY_{}_NAME',),
}

_PROMPT_KEY_RE = re.compile(r'(?:prompt|label)\s+"([^"]+)"')


def _patch_name(kind, code):
    if not code:
        return ''
    up = str(code).strip().upper()
    for tmpl in _KIND_NAME_KEYS.get(kind, ()):
        zh = _event_zh(tmpl.format(up))
        if zh:
            return clean_text(zh)
    return ''


def _name_index():
    global _NAME_INDEX
    if _NAME_INDEX is not None:
        return _NAME_INDEX
    idx = {'item': {}, 'passive': {}, 'ability': {}, 'event': {}}
    for kind, rel in (
        ('item', ('assets', 'items_catalog.json')),
        ('passive', ('assets', 'passives_catalog.json')),
        ('ability', ('assets', 'abilities_catalog.json')),
    ):
        data = _load_json(rel)
        if not isinstance(data, list):
            continue
        for row in data:
            key = row.get('key')
            if key:
                idx[kind][key] = _patch_name(kind, key) or row.get('name') or row.get('name_en') or key
    ev = _load_json(('wiki_data', 'events_combined.json')) or {}
    for e in ev.get('events') or []:
        k = e.get('event_key')
        if k:
            idx['event'][k] = clean_text(_loc_overlay(e.get('title_key'), e.get('title_texts'), k))
    _NAME_INDEX = idx
    return idx


def lookup_name(kind, code):
    if not code:
        return ''
    return _patch_name(kind, code) or _name_index().get(kind, {}).get(code, code)


def _keyword_maps():
    reward = _load_json(('wiki_data', 'event_reward_keywords.json')) or {}
    non = _load_json(('wiki_data', 'event_non_result_keywords.json')) or {}
    meta = {}
    for entry in reward.get('result_keywords') or []:
        key = entry.get('key')
        if key:
            meta[key] = {
                'tone': entry.get('tone') or 'neutral',
                'title': (entry.get('labels') or {}).get('zh') or (entry.get('labels') or {}).get('en') or key,
            }
    ignored = set(non.get('ignored_keywords') or [])
    ignored.update(('set_frame', 'animation', 'animation_fail', 'play_animation', 'play_sound'))
    structural = set(non.get('non_result_keywords') or [])
    structural.update(STRUCTURAL_TITLES)
    return meta, ignored, structural


def _strip_comment(line):
    return line.split('//', 1)[0]


def build_block_tree(code):
    root = {'name': 'root', 'lines': [], 'children': []}
    stack = [root]
    for raw in (code or '').split('\n'):
        trimmed = _strip_comment(raw).strip()
        if not trimmed:
            continue
        m = re.match(r'^([A-Za-z0-9_]+)\s*\{\s*$', trimmed)
        if m:
            node = {'name': m.group(1), 'lines': [], 'children': []}
            stack[-1]['children'].append(node)
            stack.append(node)
            continue
        m = re.match(r'^([A-Za-z0-9_]+)\s*\[\s*$', trimmed)
        if m:
            node = {'name': m.group(1), 'lines': [], 'children': []}
            stack[-1]['children'].append(node)
            stack.append(node)
            continue
        if trimmed == '{':
            node = {'name': 'entry', 'lines': [], 'children': []}
            stack[-1]['children'].append(node)
            stack.append(node)
            continue
        if trimmed == '[':
            node = {'name': 'list', 'lines': [], 'children': []}
            stack[-1]['children'].append(node)
            stack.append(node)
            continue
        if trimmed in ('}', ']'):
            if len(stack) > 1:
                stack.pop()
            continue
        stack[-1]['lines'].append(trimmed)
    return root


def _quoted(text):
    m = re.search(r'"([^"]+)"', text or '')
    return m.group(1) if m else ''


def _prompt_from_map(key, prompt_map):
    if not key:
        return ''
    overlay = _event_zh(key)
    if overlay:
        return clean_text(overlay)
    texts = (prompt_map or {}).get(key)
    if isinstance(texts, dict):
        return clean_text(_loc(texts, key))
    return clean_text(key)


def _loc_keys_in_code(*codes):
    keys = []
    seen = set()
    for code in codes:
        for k in _PROMPT_KEY_RE.findall(code or ''):
            if k in seen:
                continue
            if not (k.startswith('EVENT_') or k.startswith('QEVENT_')):
                continue
            seen.add(k)
            keys.append(k)
    return keys


def _texts_for_keys(keys, prompt_map=None):
    out = []
    seen = set()
    for k in keys:
        text = _prompt_from_map(k, prompt_map)
        if not text or text == k or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _first_line_token(line):
    return (line.split(None, 1)[0] if line else '').lower()


def _localize_body(key, body):
    body = (body or '').strip()
    if not body:
        return ''
    tokens = body.split()
    item_keys = {'get_item', 'lose_item', 'lose_specific_item', 'get_and_equip_item', 'get_parasite'}
    item_pool_keys = {
        'get_item_from_pool', 'get_and_equip_item_from_pool',
        'get_full_item_set_from_pool', 'get_parasite_from_pool',
    }
    ability_keys = {'learn_ability', 'upgrade_ability'}
    ability_pool_keys = {'learn_ability_from_pool'}
    passive_keys = {'learn_passive', 'upgrade_passive', 'gain_disorder'}
    event_keys = {'event_now', 'event_now_same_cat'}
    if key in item_keys and tokens:
        tokens[0] = lookup_name('item', tokens[0].strip('[]{},'))
        return ' '.join(tokens)
    if key in item_pool_keys:
        pool = ''
        restrict = ''
        if tokens and tokens[0] not in ('pool', 'restrict'):
            pool = tokens[0]
        for i, tok in enumerate(tokens[:-1]):
            if tok == 'pool':
                pool = tokens[i + 1]
            if tok == 'restrict':
                restrict = tokens[i + 1]
        parts = []
        if pool:
            parts.append(f'来自池 {pool}')
        if restrict:
            parts.append(f'仅限 {restrict}')
        return ' '.join(parts) or body
    if key in ability_keys and tokens:
        tokens[0] = lookup_name('ability', tokens[0])
        return ' '.join(tokens)
    if key in ability_pool_keys:
        return body
    if key in passive_keys and tokens:
        tokens[0] = lookup_name('passive', tokens[0])
        return ' '.join(tokens)
    if key in event_keys and tokens:
        code = tokens[0].strip('[]{},')
        if code != 'random':
            tokens[0] = lookup_name('event', code)
        return ' '.join(tokens)
    return body


def _flatten_inline_block(node):
    bits = list(node.get('lines') or [])
    for child in node.get('children') or []:
        inner = _flatten_inline_block(child)
        if inner:
            bits.append(f"{child['name']} {inner}" if child.get('name') not in ('entry', 'list') else inner)
        elif child.get('name') not in ('entry', 'list', 'root'):
            bits.append(child['name'])
    return ' '.join(bits)


def summarize_node(node, prompt_map, meta, ignored, side='good', rarity=''):
    """把 gon 代码树压成 [{side, rarity, prompt, weight, actions}]。"""
    rows = []
    name = node.get('name') or ''
    if name in ('common', 'rare', 'uncommon', 'very_rare', 'medium'):
        rarity = name
    if name == 'good':
        side = 'good'
    elif name == 'bad':
        side = 'bad'

    prompt = ''
    weight = ''
    actions = []
    for line in node.get('lines') or []:
        tok = _first_line_token(line)
        rest = line[len(tok):].strip() if tok else ''
        if tok == 'prompt':
            prompt = _prompt_from_map(_quoted(rest) or rest.strip('"'), prompt_map) or prompt
            continue
        if tok == 'weight':
            weight = rest
            continue
        if tok in ignored:
            continue
        if tok in STRUCTURAL_TITLES:
            continue
        info = meta.get(tok)
        if info:
            actions.append({
                'key': tok,
                'title': info['title'],
                'tone': info['tone'],
                'body': _localize_body(tok, rest),
            })
        elif tok and tok not in ('label', 'stat', 'stat_min', 'stat_max', 'animation', 'hint_chapter_exit'):
            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', tok):
                actions.append({
                    'key': tok,
                    'title': tok,
                    'tone': 'neutral',
                    'body': rest,
                })

    child_rows = []
    for child in node.get('children') or []:
        cname = child.get('name') or ''
        if cname in ('get_item_from_pool', 'get_and_equip_item_from_pool', 'get_full_item_set_from_pool',
                     'get_parasite_from_pool', 'permanent_stats', 'party_permanent_stats',
                     'party_permanent_stats_exclude_self', 'mutation', 'self_status_next_fight',
                     'party_status_next_fight', 'next_event_from_set', 'global_effect_next_fight',
                     'random_mutation_from_set'):
            info = meta.get(cname) or {'title': STRUCTURAL_TITLES.get(cname, cname), 'tone': 'neutral'}
            actions.append({
                'key': cname,
                'title': info.get('title') or cname,
                'tone': info.get('tone') or 'neutral',
                'body': _localize_body(cname, _flatten_inline_block(child)),
            })
            extra = summarize_node(child, prompt_map, meta, ignored, side, rarity)
            for row in extra:
                if row.get('prompt') and not prompt:
                    prompt = row['prompt']
                for act in row.get('actions') or []:
                    if act not in actions:
                        actions.append(act)
            continue
        if cname in ('random_pool', 'random_pool_consider_luck', 'random_chance', 'list'):
            nested = []
            for entry in child.get('children') or []:
                nested.extend(summarize_node(entry, prompt_map, meta, ignored, side, rarity))
            if nested:
                child_rows.extend(nested)
            continue
        child_rows.extend(summarize_node(child, prompt_map, meta, ignored, side, rarity))

    if prompt or actions:
        rows.append({
            'side': side,
            'rarity': rarity or 'other',
            'prompt': prompt,
            'weight': weight,
            'actions': actions,
        })
    rows.extend(child_rows)
    return rows


def parse_option_outcomes(option, meta, ignored):
    prompt_map = option.get('prompt_texts') or {}
    out = []
    for side, field in (('good', 'good_code'), ('bad', 'bad_code')):
        code = option.get(field) or ''
        if not code.strip():
            continue
        tree = build_block_tree(code)
        rows = summarize_node(tree, prompt_map, meta, ignored, side=side)
        if not rows:
            prompt_key = option.get('good_prompt_key' if side == 'good' else 'bad_prompt_key')
            fallback_prompt = _loc_overlay(
                prompt_key,
                option.get('good_prompt_texts' if side == 'good' else 'bad_prompt_texts'),
            )
            if fallback_prompt:
                rows = [{
                    'side': side,
                    'rarity': 'other',
                    'prompt': clean_text(fallback_prompt),
                    'weight': '',
                    'actions': [],
                }]
        out.extend(rows)
    return out


def _format_stat(option):
    stat = (option.get('stat') or 'none') or 'none'
    label = STAT_LABELS.get(stat, stat)
    lo, hi = option.get('stat_min'), option.get('stat_max')
    extra = ''
    if stat == 'coins' and (lo is not None or hi is not None):
        if lo is not None and hi is not None and str(lo) == str(hi):
            extra = f' {lo}'
        else:
            extra = f' {lo or "?"}–{hi or "?"}'
    return stat, label + extra


def normalize_event(raw, meta, ignored):
    title = clean_text(_loc_overlay(raw.get('title_key'), raw.get('title_texts'), raw.get('event_key') or ''))
    title_en = (raw.get('title_texts') or {}).get('en') or ''
    hidden = not bool((_loc(raw.get('title_texts')) or '').strip())
    tkey = type_key_from_source(raw.get('source_file'))
    options = []
    for opt in raw.get('options') or []:
        stat, stat_zh = _format_stat(opt)
        options.append({
            'name': opt.get('name') or '',
            'label': clean_text(_loc_overlay(opt.get('label_key'), opt.get('label_texts'), opt.get('name') or '')),
            'label_en': ((opt.get('label_texts') or {}).get('en') or '').strip(),
            'stat': stat,
            'stat_zh': stat_zh,
            'outcomes': parse_option_outcomes(opt, meta, ignored),
        })
    if not options and (raw.get('outcome_code') or '').strip():
        fake = {
            'name': 'outcome',
            'label_key': '',
            'label_texts': {'zh': '固定结果', 'en': 'Outcome'},
            'stat': 'none',
            'good_code': raw.get('outcome_code') or '',
            'bad_code': '',
            'prompt_texts': raw.get('outcome_prompt_texts') or {},
        }
        options.append({
            'name': 'outcome',
            'label': '固定结果',
            'label_en': 'Outcome',
            'stat': 'none',
            'stat_zh': STAT_LABELS.get('none', '无检定'),
            'outcomes': parse_option_outcomes(fake, meta, ignored),
        })
    refs = []
    for ref in raw.get('refs') or []:
        kind = ref.get('type') or ''
        code = ref.get('code') or ''
        label_kind = {'item': 'item', 'passive': 'passive', 'ability': 'ability', 'event': 'event'}.get(kind)
        label = lookup_name(label_kind, code) if label_kind else code
        refs.append({'type': kind, 'code': code, 'label': label})
    prompt = clean_text(_loc_overlay(raw.get('main_prompt_key'), raw.get('main_prompt_texts')))
    ques_keys = [k for k in _loc_keys_in_code(raw.get('main_code'), raw.get('outcome_code')) if '_QUES' in k]
    ques_texts = _texts_for_keys(ques_keys)
    prompt_alts = [t for t in ques_texts if t != prompt]
    if not prompt and ques_texts:
        prompt = ques_texts[0]
        prompt_alts = ques_texts[1:]
    ev = {
        'key': raw.get('event_key') or '',
        'title': title or raw.get('event_key') or '',
        'title_en': title_en,
        'prompt': prompt,
        'prompt_alts': prompt_alts,
        'prompt_en': clean_text((raw.get('main_prompt_texts') or {}).get('en') or ''),
        'cat_choice': raw.get('cat_choice') or '',
        'cat_choice_zh': CAT_CHOICE_LABELS.get((raw.get('cat_choice') or '').lower(), raw.get('cat_choice') or ''),
        'type_key': tkey,
        'type_zh': type_label(tkey),
        'hidden': hidden,
        'source_file': raw.get('source_file') or '',
        'fixed_outcome': bool(raw.get('fixed_outcome')),
        'refs': refs,
        'options': options,
    }
    ev['_search'] = _event_search_blob(ev, raw)
    return ev


def _event_search_blob(ev, raw):
    bits = [
        ev.get('key') or '', ev.get('title') or '', ev.get('title_en') or '',
        ev.get('prompt') or '', ev.get('prompt_en') or '',
        ' '.join(ev.get('prompt_alts') or []),
        ev.get('type_zh') or '', ev.get('type_key') or '',
        _loc(raw.get('title_texts')), _loc(raw.get('main_prompt_texts')),
        (raw.get('main_prompt_texts') or {}).get('en') or '',
    ]
    for opt in ev.get('options') or []:
        bits.extend([opt.get('label') or '', opt.get('label_en') or '', opt.get('name') or ''])
        for row in opt.get('outcomes') or []:
            bits.append(row.get('prompt') or '')
            for act in row.get('actions') or []:
                bits.extend([act.get('title') or '', act.get('body') or '', act.get('key') or ''])
    for opt in raw.get('options') or []:
        bits.append(_loc(opt.get('label_texts')))
        bits.append((opt.get('label_texts') or {}).get('en') or '')
        for texts in (opt.get('prompt_texts') or {}).values():
            if isinstance(texts, dict):
                bits.extend([texts.get('zh') or '', texts.get('en') or ''])
    for texts in (raw.get('outcome_prompt_texts') or {}).values():
        if isinstance(texts, dict):
            bits.extend([texts.get('zh') or '', texts.get('en') or ''])
    for ref in ev.get('refs') or []:
        bits.extend([ref.get('label') or '', ref.get('code') or '', ref.get('type') or ''])
    return _norm_search(' '.join(str(b) for b in bits if b))


def load_event_catalog():
    """返回规范化后的事件列表（懒加载缓存）。"""
    global _CATALOG
    if _CATALOG is not None:
        return _CATALOG
    raw = _load_json(('wiki_data', 'events_combined.json')) or {}
    events = raw.get('events') or []
    meta, ignored, _structural = _keyword_maps()
    _name_index()
    _CATALOG = [normalize_event(e, meta, ignored) for e in events if e.get('event_key')]
    return _CATALOG


def list_event_types(events=None):
    events = events if events is not None else load_event_catalog()
    keys = []
    seen = set()
    for e in events:
        k = e.get('type_key') or ''
        if k and k not in seen:
            seen.add(k)
            keys.append(k)
    keys.sort(key=lambda k: type_label(k))
    return keys


def filter_events(events=None, query='', type_key='', show_hidden=False):
    events = events if events is not None else load_event_catalog()
    q = _norm_search(query)
    out = []
    for e in events:
        if not show_hidden and e.get('hidden'):
            continue
        if type_key and e.get('type_key') != type_key:
            continue
        if q:
            hay = e.get('_search') or ''
            if q not in hay:
                continue
        out.append(e)
    out.sort(key=lambda e: (e.get('type_zh') or '', e.get('title') or e.get('key') or ''))
    return out
