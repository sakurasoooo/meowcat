import sqlite3
import os
import sys
import json
import struct
import lz4.block
import re
import shutil
import random
import csv
from datetime import datetime

_GAME_DATA_CACHE = None
_OFFICIAL_TEXT_CACHE = None

# 官方文本突变描述部位键（手臂与腿共用 LEGS 文本，游戏 id/效果相同）
MUTATION_DESC_PART = {
    'body': 'BODY', 'head': 'HEAD', 'tail': 'TAIL',
    'legs': 'LEGS', 'arms': 'LEGS',
    'mouth': 'MOUTH', 'texture': 'TEXTURE',
    'ears': 'EARS', 'eyebrows': 'EYEBROWS', 'eyes': 'EYES',
}
MUTATION_SLOT_NAME_KEY = {
    'body': 'MUTATION_BODY_NAME',
    'head': 'MUTATION_HEAD_NAME',
    'tail': 'MUTATION_TAIL_NAME',
    'legs': 'MUTATION_LEG_NAME',
    'arms': 'MUTATION_ARM_NAME',
    'mouth': 'MUTATION_MOUTH_NAME',
    'texture': 'MUTATION_FUR_NAME',
    'ears': 'MUTATION_EAR_NAME',
    'eyebrows': 'MUTATION_EYEBROW_NAME',
    'eyes': 'MUTATION_EYE_NAME',
}


def _bundled_official_zh_paths():
    """只读编辑器自带 assets，不探测游戏安装目录。"""
    names = ('official_zh.json', 'official_mutation_zh.json')
    bases = [os.path.dirname(os.path.abspath(__file__))]
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        bases.append(meipass)
    if getattr(sys, 'frozen', False):
        bases.append(os.path.dirname(sys.executable))
    bases.append(os.getcwd())
    out = []
    seen = set()
    for base in bases:
        if not base:
            continue
        for name in names:
            p = os.path.join(base, 'assets', name)
            if p not in seen:
                seen.add(p)
                out.append(p)
    return out


def load_official_text_map():
    """加载打包的官方中文摘要，返回 {key: (en, zh)}。不读取游戏安装目录。"""
    global _OFFICIAL_TEXT_CACHE
    if _OFFICIAL_TEXT_CACHE is not None:
        return _OFFICIAL_TEXT_CACHE
    result = {}
    for path in _bundled_official_zh_paths():
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            for k, v in (data or {}).items():
                if k in result and result[k][1]:
                    continue
                if isinstance(v, dict):
                    result[k] = (v.get('en') or '', v.get('zh') or '')
                elif isinstance(v, str):
                    result[k] = ('', v)
        except Exception:
            continue
    _OFFICIAL_TEXT_CACHE = result
    return result


def official_zh(key, fallback=''):
    pair = load_official_text_map().get(key)
    if pair and pair[1]:
        return pair[1]
    return fallback


def mutation_slot_label(slot_key, fallback=''):
    return official_zh(MUTATION_SLOT_NAME_KEY.get(slot_key, ''), fallback or slot_key)


def format_mutation_display(entry):
    mid = entry.get('id')
    name = (entry.get('name') or '').strip()
    stat = (entry.get('stat_str') or '').strip()
    desc = (entry.get('desc') or '').replace('\r\n', '\n').replace('\n', ' ').strip()
    if desc:
        short = desc if len(desc) <= 40 else desc[:38] + '…'
        if stat and stat not in short:
            return f"#{mid} {short} ({stat})"
        return f"#{mid} {short}"
    if name and stat:
        return f"#{mid} {name} ({stat})"
    if name:
        return f"#{mid} {name}"
    if stat:
        return f"#{mid} ({stat})"
    return f"#{mid}"


def localize_mutations_detailed(game_data, official=None):
    """用官方中文补丁覆盖 mutations_detailed 的描述/显示名。"""
    if not game_data or game_data.get('_mutations_official_zh'):
        return game_data
    official = official if official is not None else load_official_text_map()
    md = game_data.get('mutations_detailed') or {}
    for slot, ents in md.items():
        part = MUTATION_DESC_PART.get(slot, str(slot).upper())
        for e in ents:
            if not e.get('name_en'):
                e['name_en'] = e.get('name') or ''
            mid = e.get('id')
            pair = official.get(f'MUTATION_{part}_{mid}_DESC') if mid is not None else None
            if pair and pair[1]:
                zh = pair[1].replace('\r\n', '\n').strip()
                e['desc'] = zh
                one = zh.replace('\n', ' ')
                if len(one) <= 32:
                    e['name'] = one.rstrip('。.')
            e['display'] = format_mutation_display(e)
    game_data['_mutations_official_zh'] = True
    return game_data


def get_game_data_cache():
    global _GAME_DATA_CACHE
    if _GAME_DATA_CACHE is None:
        try:
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            p = os.path.join(base_dir, 'mewgenics_game_data.json')
            if not os.path.exists(p):
                p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mewgenics_game_data.json')
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    _GAME_DATA_CACHE = json.load(f)
            else:
                _GAME_DATA_CACHE = {}
        except Exception:
            _GAME_DATA_CACHE = {}
        localize_mutations_detailed(_GAME_DATA_CACHE)
    return _GAME_DATA_CACHE

def get_ability_upgrade(base_code):
    if not base_code or base_code == 'None':
        return 'None'
    gd = get_game_data_cache()
    upg_map = gd.get('ability_upgrade_map', {})
    if base_code in upg_map:
        return upg_map[base_code]
    return f"{base_code}2"

def get_base_ability(code):
    if not code or code == 'None':
        return 'None'
    gd = get_game_data_cache()
    down_map = gd.get('ability_downgrade_map', {})
    if code in down_map:
        return down_map[code]
    if code.endswith('2'):
        return code[:-1]
    return code

# 15 个物理部位槽：10 个部位类型，其中 眉/耳/腿/臂/眼 5 个成对部位各占左(off1)、右(off2)两个独立槽位。
# 槽内为部件 id：<300 = 正常外观部件；>=300 = 变异部件；-2 = 部位完全缺失(出生缺陷)。
# 局内事件可用 asymmetric 变异打破左右对称(上限15)；繁殖时统一为单侧写入双槽(遗传上限10)。
# 注意：off2 是"右侧部件"，不是隐性基因——游戏数据里不存在隐性等位基因概念。
# 普通攻击 / 移动 技能清单（来源: data/abilities/basic_attacks.gon & basic_movement.gon）
BASIC_ATTACK_ABILITIES = [
    'BasicMelee', 'BasicMelee_Fighter', 'BasicBigMelee', 'BasicRanged', 'BasicRanged_Hunter',
    'BasicRanged_1DMG', 'BasicShortRanged', 'BasicMagicShortRanged', 'BasicShortLobbed',
    'BasicStraightShot', 'BasicStraightShot_Thief', 'BasicMedicMelee', 'BasicMedicRanged',
    'BasicTankMelee', 'BasicMonkMelee', 'BasicMonkRanged', 'BasicButcherMelee', 'BasicButcherMeleeWide',
    'BasicButcherMeleeWideSpin', 'BasicButcherMeleeWideDoubleSpin', 'BasicDruidAbility',
    'BasicDruidAbilityVersatile', 'TinkererCraft', 'TinkererThrow', 'BasicPsychicPull',
    'BasicNecroRanged', 'BasicDrainMelee', 'BasicHook', 'BasicMagicMissile', 'BasicSuplex',
    'BasicTwoHitMelee', 'BasicPuke', 'BasicExplosiveShot', 'BasicPoke', 'GerdShot', 'BasicSpin',
    'BasicMetronome',
]
BASIC_MOVE_ABILITIES = [
    'DefaultMove', 'BasicJump', 'Teleport', 'BasicDig', 'Shadowstep', 'SwapPositions',
    'SwimmerMove', 'TrampleMove', 'TrampleMoveOne', 'MaxTeleport', 'FloatMove',
]

# 一键特化疾病：只从「净收益为正」的池里按职业/法术/普攻打分再抽，不写死同一对。
_CLASS_DISORDER_TAGS = {
    'Necromancer': {'necro', 'minion', 'corpse', 'caster', 'spell'},
    'Butcher': {'butcher', 'eat', 'melee', 'corpse', 'kill', 'attack'},
    'Mage': {'caster', 'mage', 'spell'},
    'Psychic': {'caster', 'psychic', 'spell'},
    'Fighter': {'melee', 'fighter', 'kill', 'attack'},
    'Monk': {'melee', 'monk', 'attack'},
    'Tank': {'tank', 'melee', 'survive'},
    'Hunter': {'hunter', 'ranged', 'dodge', 'attack'},
    'Thief': {'thief', 'dodge', 'speed', 'attack'},
    'Tinkerer': {'tinkerer', 'item', 'weapon', 'attack'},
    'Medic': {'medic', 'support', 'healer', 'caster', 'spell'},
    'Druid': {'druid', 'minion', 'nature'},
    'Jester': {'jester', 'luck', 'attack'},
    'Colorless': {'universal'},
}
# key -> (基础分, 标签, 一句话理由)
_DISORDER_SYNERGY = {
    'Invincible': (30, {'tank', 'survive', 'universal'}, '受伤锁定为1'),
    'Premonitions': (28, {'attack', 'hunter', 'thief', 'fighter', 'jester', 'universal'}, '攻击必中'),
    'Brave': (22, {'speed', 'thief', 'hunter', 'fighter', 'jester'}, '更早出手'),
    'Cannibal': (24, {'corpse', 'butcher', 'necro', 'fighter', 'survive'}, '吃尸体回血加全属性'),
    'Phony': (24, {'caster', 'mage', 'psychic', 'medic', 'spell'}, '开场满魔'),
    'Nudist': (22, {'dodge', 'thief', 'hunter'}, '闪避+50%'),
    'Dwarfism': (16, {'dodge', 'thief', 'hunter'}, '闪避+10%'),
    'Anxiety': (20, {'dodge', 'thief', 'hunter', 'speed'}, '闪避+10%且受伤后撤'),
    'Tourettes': (24, {'caster', 'spell', 'mage', 'psychic', 'jester'}, '回合开始有概率免费施法'),
    'Triskaidekaphobia': (26, {'caster', 'spell', 'mage', 'psychic'}, '法术0费（第13次自尽）'),
    'Boils': (14, {'tank', 'survive'}, '招架+1'),
    'WilliamsSyndrome': (20, {'attack', 'jester', 'luck', 'melee'}, '攻击可能洗脑'),
    'TheHunger': (22, {'melee', 'butcher', 'fighter', 'survive', 'attack'}, '普攻吸血'),
    'BloodFrenzy': (24, {'melee', 'fighter', 'butcher', 'necro', 'kill'}, '击杀额外回合'),
    'Fidgety': (22, {'weapon', 'tinkerer', 'hunter', 'fighter', 'attack'}, '回合结束自动挥武器'),
    'FrozenKnee': (20, {'melee', 'fighter', 'monk', 'thief', 'speed'}, '移动变为突进攻击'),
    'FlamingFists': (20, {'melee', 'fighter', 'monk', 'attack'}, '普攻挂灼烧'),
    'FelineAids': (18, {'melee', 'attack', 'butcher'}, '普攻剧毒+虚弱'),
    'Lycanthropy': (16, {'druid', 'melee', 'nature'}, '概率变狼'),
    'Schizophrenia': (18, {'minion', 'psychic', 'druid', 'necro'}, '回合结束出幻觉'),
    'DarkOne': (22, {'necro', 'survive', 'aoe'}, '回合结束全体伤并回血'),
    'Gigantism': (18, {'tank', 'fighter', 'melee'}, '横冲直撞'),
    'Depression': (18, {'tank', 'aoe', 'control'}, '邻格全属性-2'),
    'Dyskinesia': (16, {'melee', 'fighter', 'monk'}, '移动结束击退邻格'),
    'Stinky': (14, {'tank', 'control'}, '邻格远离你'),
    'BrokenLimb': (12, {'tank'}, '尖刺+2（锁饰品/消耗品）'),
    'BrainDamage': (12, {'tank'}, '招架+2（锁物品行动）'),
    'Fossilized': (16, {'tank', 'survive'}, '招架+2'),
    'HeadTrauma': (8, {'colorless', 'caster', 'spell'}, '无色法术-2费'),
    'Autism': (8, {'innate', 'caster', 'spell'}, '出生法术-2费'),
    'Pacifist': (20, {'medic', 'support', 'caster'}, '不普攻则+7魔'),
    'Narcolepsy': (18, {'medic', 'caster', 'survive'}, '回合结束入睡回血+魔'),
    'Hypomania': (16, {'speed', 'jester', 'thief'}, '开场3个额外回合'),
    'OCD': (12, {'medic', 'support'}, '附赠梳毛'),
    'Toxoplasmosis': (18, {'minion', 'druid', 'necro', 'hunter'}, '开场老鼠跟班'),
    'Infestation': (16, {'minion', 'necro', 'druid', 'butcher'}, '回合开始出蛆'),
    'ExplosiveGas': (14, {'aoe', 'poison'}, '首回合超级屁'),
    'Gastritis': (14, {'aoe', 'poison', 'butcher'}, '回合结束邻格中毒'),
    'BlessingOfGlorg': (12, {'item', 'tinkerer'}, '可卸诅咒物品'),
    'BirdFlu': (14, {'druid', 'nature'}, '开场知更鸟形态'),
    'ASRFight': (14, {'fighter', 'survive'}, '残血力量+6'),
    'ASRFlight': (14, {'thief', 'speed'}, '残血速度+6'),
    'PTSD': (14, {'fighter', 'tank'}, '受伤伤害+2'),
    'Kamikazee': (12, {'tank', 'necro'}, '倒地爆炸'),
    'WobblyCat': (16, {'tank', 'survive'}, '概率挡下并击退'),
    'AcidReflux': (16, {'ranged', 'hunter', 'mage'}, '普攻变溅射抛射'),
    'EatingDisorder': (14, {'item', 'tinkerer', 'butcher'}, '消耗品效果翻倍'),
    'Scleroderma': (14, {'tank', 'survive'}, '开场1血换等量护盾'),
    'Rabies': (12, {'melee', 'fighter'}, '普攻强制近战'),
    'Charred': (10, {'survive'}, '免疫灼烧'),
}
_DISORDER_CONFLICTS = (
    frozenset({'Pacifist', 'BloodFrenzy'}),
    frozenset({'Pacifist', 'TheHunger'}),
    frozenset({'Autism', 'Triskaidekaphobia'}),
    frozenset({'Narcolepsy', 'Hypomania'}),
    frozenset({'Nudist', 'BorrowedTime'}),
    frozenset({'BrokenLimb', 'EatingDisorder'}),
    frozenset({'BrainDamage', 'EatingDisorder'}),
    frozenset({'BrainDamage', 'BlessingOfGlorg'}),
)
_ABILITY_CLASS_MAP = None
_DISORDER_ZH_MAP = None


def _ability_class_map():
    global _ABILITY_CLASS_MAP
    if _ABILITY_CLASS_MAP is None:
        m = {}
        for a in get_game_data_cache().get('abilities', []):
            k = a.get('key')
            if k:
                m[k] = a.get('class') or ''
        _ABILITY_CLASS_MAP = m
    return _ABILITY_CLASS_MAP


def disorder_display_name(key):
    global _DISORDER_ZH_MAP
    if _DISORDER_ZH_MAP is None:
        m = {}
        for d in get_game_data_cache().get('disorders', []):
            k = d.get('key')
            if k:
                m[k] = d.get('name') or k
        _DISORDER_ZH_MAP = m
    return _DISORDER_ZH_MAP.get(key, key)


def _disorder_pair_conflicts(a, b):
    pair = frozenset({a, b})
    return any(c <= pair for c in _DISORDER_CONFLICTS)

MUTATION_SLOTS = [
    ('body', '身体突变', 100 + 4, None),
    ('eyebrows', '眉毛突变', 280 + 4, 300 + 4),
    ('head', '头部突变', 120 + 4, None),
    ('ears', '耳部突变', 320 + 4, 340 + 4),
    ('tail', '尾部突变', 140 + 4, None),
    ('mouth', '嘴部突变', 360 + 4, None),
    ('legs', '腿部突变', 160 + 4, 180 + 4),
    ('texture', '毛皮突变', 80 + 12, None),
    ('arms', '手臂突变', 200 + 4, 220 + 4),
    ('eyes', '眼部突变', 240 + 4, 260 + 4)
]

_CANONICAL_PASSIVES = {}

# 目录/术语表遗留 key（全大写去撇号，或去撇号后的帕斯卡式）→ 游戏 SWF/存档真实代码。
# 例：FIGHTERSOUL / FighterSoul → FightersSoul（Fighter's Soul）。
GAME_CODE_ALIAS = {
    'FIGHTERSOUL': 'FightersSoul', 'HUNTERSOUL': 'HuntersSoul', 'MAGESOUL': 'MagesSoul',
    'CLERICSOUL': 'ClericsSoul', 'TANKSOUL': 'TanksSoul', 'THIEFSOUL': 'ThiefsSoul',
    'MONKSOUL': 'MonksSoul', 'BUTCHERSOUL': 'ButchersSoul', 'DRUIDSOUL': 'DruidsSoul',
    'TINKERERSOUL': 'TinkerersSoul', 'NECROMANCERSOUL': 'NecromancersSoul', 'PSYCHICSOUL': 'PsychicsSoul',
    'SOULBOND': 'SoulBound',
    'JAGGEDEDGE': 'JaggedEdges', 'FRENZY': 'BloodFrenzy', 'EMPTYVESSEL': 'EmptyVessels',
    'PROTECTIVE': 'ProtectiveAura', 'SWIFTLOOTER': 'Looter', 'IRONSKINTECHNIQUE': 'IronSkin',
    'STARTER_PLACEHOLDER': 'STARTER_PLACEHOLDER_Fighter',
}

def get_canonical_passive_code(key):
    """把被动技能代码（无论大小写或带标点）转换为游戏内部准确的帕斯卡式（PascalCase）真实代码。
    例如：'SELFASSURED' -> 'SelfAssured', 'thoushaltnotkill' -> 'ThouShaltNotKill'。
    """
    if not key or key == 'None':
        return 'None'
    global _CANONICAL_PASSIVES
    if not _CANONICAL_PASSIVES:
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        # 1. assets/passives_catalog.json
        for base in [base_dir, os.getcwd()]:
            cat_p = os.path.join(base, 'assets', 'passives_catalog.json')
            if os.path.exists(cat_p):
                try:
                    with open(cat_p, 'r', encoding='utf-8') as f:
                        for it in json.load(f):
                            k = it.get('key')
                            if k:
                                _CANONICAL_PASSIVES[k.lower()] = k
                                _CANONICAL_PASSIVES[''.join(c for c in k.lower() if c.isalnum())] = k
                    break
                except Exception:
                    pass
        # 2. wiki_data/csv/passives.csv
        for base in [base_dir, os.getcwd()]:
            csv_p = os.path.join(base, 'wiki_data', 'csv', 'passives.csv')
            if os.path.exists(csv_p):
                try:
                    with open(csv_p, 'r', encoding='utf-8') as f:
                        for row in csv.DictReader(f):
                            code = row.get('\ufeffpassive_code') or row.get('passive_code')
                            if code:
                                _CANONICAL_PASSIVES.setdefault(code.lower(), code)
                                _CANONICAL_PASSIVES.setdefault(''.join(c for c in code.lower() if c.isalnum()), code)
                    break
                except Exception:
                    pass
        # 3. 特殊别名映射（对齐官方 gon 配置块名）
        special_aliases = {
            'unscarred': 'Untouched', '180': 'OneEighty', 'hulkup': 'FasterWhenHit',
            'fervor': 'KillsHeal', 'merciless': 'Recoil', 'natureguidance': 'NaturesGuidance',
            'lovesong': 'SoothingSong', 'versatilevolcalist': 'VersatileVocalist',
            'superfriends': 'SpecialFriends', 'servusmortem': 'DeathIncarnate',
            'lastgrasp': 'LastGasp', 'stealthed': 'Shadow', 'bullseye': 'HawkEye',
            'forcefield': 'HolyMantel', 'fireaspect': 'FireArmor', 'iceaspect': 'IceArmor',
            'lightningaspect': 'LightningArmor', 'braingeyser': 'Radiation'
        }
        for ak, av in special_aliases.items():
            _CANONICAL_PASSIVES[ak.lower()] = av
            _CANONICAL_PASSIVES[''.join(c for c in ak.lower() if c.isalnum())] = av
        # 4. 目录遗留 key（FIGHTERSOUL / FighterSoul）覆盖为游戏真实代码；须在 catalog 之后写入
        for ak, av in GAME_CODE_ALIAS.items():
            _CANONICAL_PASSIVES[ak.lower()] = av
            _CANONICAL_PASSIVES[''.join(c for c in ak.lower() if c.isalnum())] = av

    clean_k = str(key).strip()
    norm = ''.join(c for c in clean_k.lower() if c.isalnum())
    return _CANONICAL_PASSIVES.get(clean_k.lower()) or _CANONICAL_PASSIVES.get(norm) or clean_k


def _catalog_text_better(field, new, old, new_key, old_key):
    """Prefer Chinese names and longer descriptions over raw code leftovers."""
    if not new:
        return False
    if not old:
        return True
    if field in ('name', 'name_en'):
        new_zh = any('\u4e00' <= c <= '\u9fff' for c in new)
        old_zh = any('\u4e00' <= c <= '\u9fff' for c in old)
        if new_zh != old_zh:
            return new_zh
        if new != (new_key or '') and old == (old_key or ''):
            return True
        if new == (new_key or '') and old != (old_key or ''):
            return False
    return len(new) > len(old)


def merge_catalog_entries(items):
    """Merge duplicate catalog rows; keep richest name/desc and any icon flag."""
    if not items:
        return None
    out = dict(items[0])
    for it in items[1:]:
        for field in ('name', 'name_en', 'desc', 'class', 'class_name'):
            old, new = out.get(field) or '', it.get(field) or ''
            if _catalog_text_better(field, new, old, it.get('key'), out.get('key')):
                out[field] = it[field]
        if it.get('has_icon') and not out.get('has_icon'):
            out['has_icon'] = True
        for k, v in it.items():
            if k in out and out[k] not in (None, '', False):
                continue
            if v not in (None, ''):
                out[k] = v
    return out


def dedupe_catalog_items(items, canonicalize=None):
    """Collapse exact-key duplicates and optional alias keys (FighterSoul → FightersSoul).

    `canonicalize(key)` if given maps leftover catalog keys to the game code; the
    first-seen canonical key order is preserved.
    """
    groups = {}
    order = []
    for it in items:
        if not isinstance(it, dict):
            continue
        raw = it.get('key')
        if not raw:
            continue
        key = canonicalize(raw) if canonicalize else raw
        if key not in groups:
            order.append(key)
            groups[key] = []
        groups[key].append(it)
    result = []
    for key in order:
        merged = merge_catalog_entries(groups[key])
        merged['key'] = key
        result.append(merged)
    return result


class CatRecord:
    STAT_NAMES = ['str', 'dex', 'con', 'int', 'spd', 'cha', 'lck']

    def __init__(self, key, raw_data):
        self.key = key
        self.raw_data = bytearray(raw_data)
        self.is_modified = False
        self.parse()

    def parse(self):
        raw = self.raw_data
        self.version = struct.unpack_from('<I', raw, 0)[0]
        self.guid = struct.unpack_from('<Q', raw, 4)[0]
        
        # Name
        self.name_len = struct.unpack_from('<Q', raw, 0x0c)[0]
        self.name = raw[0x14 : 0x14 + self.name_len * 2].decode('utf-16le', errors='ignore')
        
        # Find voice & stats
        m = re.search(rb'(?:male\d+|female\d+|robotom|spidercat|demoncat|robotcat)', raw)
        if not m:
            raise ValueError(f"Could not locate voice string in cat {self.key}")
            
        p_voice = m.start()
        self.p_voice_len = p_voice - 8
        self.voice_len = struct.unpack_from('<Q', raw, self.p_voice_len)[0]
        self.voice = raw[p_voice : p_voice + self.voice_len].decode('ascii', errors='ignore')
        
        # Everything before voice is the pre_voice_chunk (header, name, title, 368-byte parts)
        # Note: name is at 0x14..0x14+name_len*2
        self.p_name_end = 0x14 + self.name_len * 2
        self.pre_voice_body = bytearray(raw[self.p_name_end : self.p_voice_len])
        
        # Parse title & parts_chunk
        self.title_len = struct.unpack_from('<Q', self.pre_voice_body, 0)[0]
        self.title = self.pre_voice_body[8 : 8 + self.title_len].decode('ascii', errors='ignore')
        self.p_parts = 8 + self.title_len + 4
        self.parts_chunk = bytearray(self.pre_voice_body[self.p_parts:])

        # Parse 10 mutation slots (Left & Right physical parts for paired slots)
        self.mutations = {}
        self.right_mutations = {}
        for slot_key, slot_cn, off1, off2 in MUTATION_SLOTS:
            if off1 + 4 <= len(self.parts_chunk):
                m_id = struct.unpack_from('<i', self.parts_chunk, off1)[0]
                self.mutations[slot_key] = m_id
            else:
                self.mutations[slot_key] = 0

            if off2 and off2 + 4 <= len(self.parts_chunk):
                r_id = struct.unpack_from('<i', self.parts_chunk, off2)[0]
                self.right_mutations[slot_key] = r_id
            else:
                self.right_mutations[slot_key] = None
        
        # Voice pitch
        p = p_voice + self.voice_len
        self.pitch = struct.unpack_from('<d', raw, p)[0]; p += 8
        
        # Base stats & bonus stats
        self.base_stats = list(struct.unpack_from('<7i', raw, p)); p += 28
        self.bonus_stats = list(struct.unpack_from('<7i', raw, p)); p += 28
        
        # Scan remaining strings
        p_search = p
        strings = []
        while p_search < len(raw) - 8:
            slen = struct.unpack_from('<Q', raw, p_search)[0]
            if 1 <= slen <= 50 and p_search + 8 + slen <= len(raw):
                chunk = raw[p_search + 8 : p_search + 8 + slen]
                if all(32 <= b <= 126 for b in chunk) and any(chr(b).isalpha() for b in chunk):
                    s = chunk.decode('ascii')
                    strings.append((p_search, slen, s))
                    p_search += 8 + slen
                    continue
            p_search += 1
            
        self.str_records = strings
        str_vals = [s[2] for s in strings]
        self.str_gaps = []
        for i in range(len(strings) - 1):
            end = strings[i][0] + 8 + strings[i][1]
            self.str_gaps.append(bytes(raw[end:strings[i + 1][0]]))

        self.boon = str_vals[0] if len(str_vals) > 0 else 'none'
        self.move_ability = str_vals[1] if len(str_vals) > 1 else 'DefaultMove'
        self.attack_ability = str_vals[2] if len(str_vals) > 2 else 'BasicMelee'
        
        # Active abilities (up to 4)
        self.active_abilities = []
        for i in range(3, min(7, len(str_vals))):
            self.active_abilities.append(str_vals[i])
        while len(self.active_abilities) < 4:
            self.active_abilities.append('None')
            
        # Active ability upgrades / enchantments (up to 4)
        self.ability_upgrades = []
        for i in range(7, min(11, len(str_vals))):
            self.ability_upgrades.append(str_vals[i])
        while len(self.ability_upgrades) < 4:
            self.ability_upgrades.append('None')
        self.innate_abilities = self.ability_upgrades

        # 2 Class Passives (职业专属正面被动)
        self.class_passives = []
        for i in range(11, min(13, len(str_vals))):
            self.class_passives.append(str_vals[i])
        while len(self.class_passives) < 2:
            self.class_passives.append('None')

        # 2 Disorder Passives (疾病/心理缺陷负面被动)
        self.disorders = []
        for i in range(13, min(15, len(str_vals))):
            self.disorders.append(str_vals[i])
        while len(self.disorders) < 2:
            self.disorders.append('None')

        # Legacy passives list (8 items) for full backward compatibility
        self.passives = self.ability_upgrades + self.class_passives + self.disorders
            
        # Class is the last scanned string. Anything between disorder #2 and class
        # is equipped items (hats / bottles / parasites) and must be preserved.
        self.extra_strings = list(str_vals[15:-1]) if len(str_vals) > 16 else []
        self.cat_class = str_vals[-1] if str_vals else 'Colorless'
        
        # Save fixed byte segments between strings
        self.mid_flags = raw[p : self.str_records[0][0]] if self.str_records else raw[p:p+28]
        p_post_boon = self.str_records[0][0] + 8 + self.str_records[0][1]
        self.post_boon_flags = raw[p_post_boon : self.str_records[1][0]] if len(self.str_records) > 1 else b''
        
        # Post class tail & Sexuality
        last_str_end = self.str_records[-1][0] + 8 + self.str_records[-1][1]
        self.tail_data = bytearray(raw[last_str_end:])
        
        # Sexuality decoding from tail_data
        if len(self.tail_data) >= 12:
            self.sexuality_val = struct.unpack_from('<d', self.tail_data, 4)[0]
        else:
            self.sexuality_val = 0.0
            
        if self.sexuality_val <= 0.05:
            self.sexuality = "Straight (异性恋)"
        elif self.sexuality_val < 0.33:
            self.sexuality = "Bisexual (双性恋)"
        else:
            self.sexuality = "Gay (同性恋)"
        self._orig_sexuality = self.sexuality

        self.libido = "Mid (正常)"
        self.aggression = "Mid (适中)"
        self.inbred_level = 0

    @property
    def mutation_stat_modifiers(self):
        """变异属性加成：合并左右两侧物理部件（游戏按 15 个物理部件实体登记，计数徽章同口径）。
        注意：对称变异（左右同 id）会按两个物理部件计两次加成——与游戏计数器口径一致；
        若日后发现游戏在属性上按类型去重，仅需将成对部位改为取单侧。"""
        mods = {k: 0 for k in self.STAT_NAMES}
        gd = get_game_data_cache()
        mut_detailed = gd.get('mutations_detailed', {})

        def apply(slot_key, mid):
            if mid is None or mid < 300:
                return
            for e in mut_detailed.get(slot_key, []):
                if e.get('id') == mid:
                    for sk, sv in e.get('stats', {}).items():
                        if sk in mods:
                            mods[sk] += sv
                    break

        for slot_key, mid in self.mutations.items():
            apply(slot_key, mid)
        for slot_key, mid in self.right_mutations.items():
            apply(slot_key, mid)
        return mods

    @staticmethod
    def get_birth_defect_ids():
        """出生缺陷 id 集合（wiki mutations.csv 的 is_birth_defect 标记 ∪ {-2 部位缺失}）。"""
        if not hasattr(CatRecord, '_birth_defect_ids'):
            ids = {-2}
            try:
                import csv as _csv
                csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wiki_data', 'csv', 'mutations.csv')
                if os.path.exists(csv_path):
                    with open(csv_path, encoding='utf-8-sig') as f:
                        for row in _csv.DictReader(f):
                            if row.get('is_birth_defect') == 'True':
                                ids.add(int(row['mutation_id']))
            except Exception:
                pass
            CatRecord._birth_defect_ids = ids
        return CatRecord._birth_defect_ids

    def mutation_counts(self):
        """与游戏内徽章一致的计数：mutationcount(局内变异) / birthdefectcount(出生缺陷)。
        成对部位左右分开计数（上限15），缺陷单独计（对应游戏 mutationcount/birthdefectcount 双徽章）。"""
        defect_ids = self.get_birth_defect_ids()
        mut_count = 0
        defect_count = 0
        asymmetric = []
        for slot_key, slot_cn, off1, off2 in MUTATION_SLOTS:
            sides = [self.mutations.get(slot_key, 0)]
            if off2:
                sides.append(self.right_mutations.get(slot_key, 0))
            for mid in sides:
                if mid is None:
                    continue
                if mid == -2 or mid in defect_ids:
                    defect_count += 1
                elif mid >= 300:
                    mut_count += 1
            if off2 and self.mutations.get(slot_key) != self.right_mutations.get(slot_key):
                asymmetric.append(slot_key)
        return {'mutations': mut_count, 'birth_defects': defect_count, 'asymmetric': asymmetric}

    @property
    def effective_stats(self):
        mut_mods = self.mutation_stat_modifiers
        return [b + mut_mods[k] + bon for k, b, bon in zip(self.STAT_NAMES, self.base_stats, self.bonus_stats)]

    @property
    def total_stats(self):
        return self.effective_stats

    def set_mutation(self, slot_key, mutation_id, sync_right=False):
        """设置左侧部件；sync_right=True 时右侧同步（对称，与游戏默认变异行为一致）。"""
        self.mutations[slot_key] = mutation_id
        for sk, scn, off1, off2 in MUTATION_SLOTS:
            if sk == slot_key:
                if off1 + 4 <= len(self.parts_chunk):
                    struct.pack_into('<i', self.parts_chunk, off1, mutation_id)
                if sync_right and off2 and off2 + 4 <= len(self.parts_chunk):
                    struct.pack_into('<i', self.parts_chunk, off2, mutation_id)
                    self.right_mutations[slot_key] = mutation_id
                break
        self.pre_voice_body[self.p_parts : self.p_parts + len(self.parts_chunk)] = self.parts_chunk
        self.is_modified = True

    def set_right_mutation(self, slot_key, mutation_id):
        """设置成对部位的右侧部件（可与左侧不同，即局内 asymmetric 变异）。"""
        self.right_mutations[slot_key] = mutation_id
        for sk, scn, off1, off2 in MUTATION_SLOTS:
            if sk == slot_key:
                if off2 and off2 + 4 <= len(self.parts_chunk):
                    struct.pack_into('<i', self.parts_chunk, off2, mutation_id)
                break
        self.pre_voice_body[self.p_parts : self.p_parts + len(self.parts_chunk)] = self.parts_chunk
        self.is_modified = True

    def clear_all_mutations(self):
        default_normal_ids = {
            'texture': 246,
            'body': 100,
            'head': 100,
            'tail': 100,
            'legs': 100,
            'arms': 100,
            'eyes': 100,
            'eyebrows': 100,
            'ears': 100,
            'mouth': 100
        }
        for sk, norm_id in default_normal_ids.items():
            self.set_mutation(sk, norm_id, sync_right=True)

    def apply_god_mutations(self):
        """每个部位从正面突变池随机抽取一项（净属性>0、非缺陷、id>=300），左右对称写入。"""
        gd = get_game_data_cache()
        mut_detailed = gd.get('mutations_detailed', {})
        defect_ids = self.get_birth_defect_ids()
        for slot_key, _slot_cn, _off1, _off2 in MUTATION_SLOTS:
            pool = []
            for entry in mut_detailed.get(slot_key, []):
                mid = entry.get('id')
                if mid is None or mid < 300 or mid in defect_ids:
                    continue
                if sum((entry.get('stats') or {}).values()) > 0:
                    pool.append(mid)
            if pool:
                self.set_mutation(slot_key, random.choice(pool), sync_right=True)

    def cure_all_disorders(self):
        self.disorders = ['None', 'None']
        self.sync_legacy_passives()
        self.is_modified = True

    def _disorder_profile(self):
        cls = self.cat_class or 'Colorless'
        tags = set(_CLASS_DISORDER_TAGS.get(cls, {'universal'}))
        tags.add('universal')
        atk = self.attack_ability or ''
        if any(tok in atk for tok in ('Ranged', 'Shot', 'Lobbed', 'Throw', 'Missile', 'Magic')):
            tags.add('ranged')
        elif any(tok in atk for tok in ('Melee', 'Hook', 'Suplex', 'Poke', 'Spin', 'Drain', 'Punch')):
            tags.add('melee')
            tags.add('attack')
        spells = [k for k in (self.active_abilities or []) if k and k != 'None']
        amap = _ability_class_map()
        colorless_n = sum(1 for k in spells if amap.get(k) == 'Colorless')
        return {
            'cls': cls,
            'tags': tags,
            'spells': spells,
            'spell_n': len(spells),
            'colorless_n': colorless_n,
            'passives': {p for p in (self.class_passives or []) if p and p != 'None'},
        }

    def _score_synergy_disorder(self, key, base, tags, profile):
        overlap = len(tags & profile['tags'])
        score = base + overlap * 6
        cls = profile['cls']
        n = profile['spell_n']
        if key == 'HeadTrauma':
            score += profile['colorless_n'] * 10
            if profile['colorless_n'] == 0:
                score -= 18
        if key == 'Autism':
            if n == 0:
                score -= 20
            elif n == 1:
                score += 18
            elif n == 2:
                score += 10
            else:
                score -= 6
        if key == 'Tourettes':
            score += 8 if n >= 2 else (-16 if n == 0 else 0)
        if key == 'Triskaidekaphobia':
            score += 8 if n >= 2 else (-12 if n == 0 else 0)
        if key == 'Phony' and n == 0:
            score -= 12
        if key == 'Pacifist':
            if cls == 'Medic':
                score += 14
            elif cls in ('Fighter', 'Butcher', 'Hunter'):
                score -= 22
        if key in ('BrokenLimb', 'BrainDamage') and cls == 'Tinkerer':
            score -= 20
        if key == 'Fidgety' and cls == 'Tinkerer':
            score += 10
        if key == 'Cannibal' and cls in ('Necromancer', 'Butcher'):
            score += 10
        if key == 'Invincible' and cls == 'Tank':
            score += 8
        if key in ('TheHunger', 'FlamingFists', 'FelineAids', 'Rabies', 'FrozenKnee'):
            if 'ranged' in profile['tags'] and 'melee' not in profile['tags']:
                score -= 14
        if score < 8:
            return 0
        return score

    def pick_synergistic_disorders(self):
        """按当前职业/法术/普攻从正面疾病池打分，加权随机抽 2 个不冲突的。"""
        profile = self._disorder_profile()
        scored = []
        for key, (base, tags, _why) in _DISORDER_SYNERGY.items():
            s = self._score_synergy_disorder(key, base, tags, profile)
            if s > 0:
                scored.append((key, s))
        scored.sort(key=lambda x: -x[1])
        if not scored:
            return ['Invincible', 'Premonitions'], '通用保底：受伤锁定为1 + 攻击必中'

        best = scored[0][1]
        pool = [(k, s) for k, s in scored if s >= max(best * 0.55, 12)][:10]
        current = [d for d in (self.disorders or []) if d and d != 'None']
        picked = None
        for _ in range(8):
            remain = list(pool)
            choice = []
            while remain and len(choice) < 2:
                weights = [max(1, s) for _, s in remain]
                idx = random.choices(range(len(remain)), weights=weights, k=1)[0]
                key = remain[idx][0]
                choice.append(key)
                remain = [(k, s) for k, s in remain if k != key and not _disorder_pair_conflicts(choice[0] if choice else '', k)]
            if len(choice) < 2:
                for k, _s in scored:
                    if k not in choice and (not choice or not _disorder_pair_conflicts(choice[0], k)):
                        choice.append(k)
                    if len(choice) >= 2:
                        break
            if len(choice) >= 2 and set(choice[:2]) != set(current[:2]):
                picked = choice[:2]
                break
            if picked is None and len(choice) >= 2:
                picked = choice[:2]
        if not picked:
            picked = [scored[0][0], scored[1][0] if len(scored) > 1 else 'Premonitions']
            if picked[0] == picked[1] or _disorder_pair_conflicts(*picked):
                picked = ['Invincible', 'Premonitions']
        why_bits = [f"{disorder_display_name(k)}（{_DISORDER_SYNERGY.get(k, (0, set(), k))[2]}）" for k in picked]
        return picked, ' + '.join(why_bits)

    def apply_synergistic_disorders(self):
        picked, why = self.pick_synergistic_disorders()
        self.disorders = list(picked)
        while len(self.disorders) < 2:
            self.disorders.append('None')
        self.sync_legacy_passives()
        self.is_modified = True
        return self.disorders[:2], why

    def apply_best_class_passives(self):
        best_preset = {
            'Necromancer': ['CorpseConnoisseur', 'RelentlessDead'],
            'Mage': ['Micronaps', 'HolyMantel'],
            'Fighter': ['BloodLust', 'Avenger'],
            'Hunter': ['TakeAim', 'HuntersBoon'],
            'Tank': ['Thorns', 'HeavyHanded'],
            'Medic': ['HealingAura', 'NaturalHealer'],
            'Thief': ['Backstabber', 'GoldenClaws'],
            'Butcher': ['Putrefy', 'NeverFull'],
            'Druid': ['SuperCrow', 'NaturesGuidance'],
            'Monk': ['SafeSwitching', 'Mixup'],
            'Psychic': ['Flying', 'SoulShatter'],
            'Tinkerer': ['VersionTwo', 'WeaponProficiency'],
            'Jester': ['SuperLuck', 'Goofball'],
            'Colorless': ['SelfAssured', 'LuckDrain']
        }
        if self.cat_class in best_preset:
            self.class_passives = list(best_preset[self.cat_class])
        else:
            gd = get_game_data_cache()
            cp = gd.get('class_passives', {}).get(self.cat_class, [])
            if len(cp) >= 2:
                self.class_passives = [cp[0]['key'], cp[1]['key']]
            elif len(cp) == 1:
                self.class_passives = [cp[0]['key'], 'None']
            else:
                self.class_passives = ['None', 'None']
        self.sync_legacy_passives()
        self.is_modified = True

    def sync_legacy_passives(self):
        while len(self.ability_upgrades) < 4:
            self.ability_upgrades.append('None')
        while len(self.class_passives) < 2:
            self.class_passives.append('None')
        while len(self.disorders) < 2:
            self.disorders.append('None')
        self.class_passives = [get_canonical_passive_code(p) for p in self.class_passives[:2]]
        self.passives = self.ability_upgrades[:4] + self.class_passives[:2] + self.disorders[:2]

    def get_spell_state(self, slot_idx):
        if slot_idx >= len(self.active_abilities):
            return 'None', False, 'None', True
        act = self.active_abilities[slot_idx]
        innate = self.ability_upgrades[slot_idx] if slot_idx < len(self.ability_upgrades) else 'None'
        if not act or act == 'None':
            # Active is empty
            is_locked = (innate == 'None')
            return 'None', False, innate, is_locked
        
        base_from_act = get_base_ability(act)
        is_tier2 = (act != base_from_act) or (act.endswith('2'))
        base = base_from_act
        
        # Check if innate is locked to combat base
        # IMPORTANT: innate=='None' means "learned after birth, no birth gene" — NOT locked!
        # Only truly locked when innate exactly matches the combat base form.
        is_locked = (innate == base)
        display_innate = innate  # Always show the real value from save
        return base, is_tier2, display_innate, is_locked

    _INNATE_UNSET = object()  # sentinel: caller didn't specify innate

    def set_spell_state(self, slot_idx, base_spell, is_upgraded=False, innate_skill=_INNATE_UNSET):
        while len(self.active_abilities) <= slot_idx:
            self.active_abilities.append('None')
        while len(self.ability_upgrades) <= slot_idx:
            self.ability_upgrades.append('None')
            
        if not base_spell or base_spell == 'None':
            self.active_abilities[slot_idx] = 'None'
            if innate_skill is not self._INNATE_UNSET and innate_skill and innate_skill != 'None':
                self.ability_upgrades[slot_idx] = innate_skill
            else:
                self.ability_upgrades[slot_idx] = 'None'
        else:
            upg_target = get_ability_upgrade(base_spell)
            if is_upgraded:
                self.active_abilities[slot_idx] = upg_target
            else:
                self.active_abilities[slot_idx] = base_spell
                
            if innate_skill is self._INNATE_UNSET:
                # Not specified — default to base_spell (legacy behavior)
                self.ability_upgrades[slot_idx] = base_spell
            elif innate_skill and innate_skill != 'None':
                # Explicit custom innate gene
                self.ability_upgrades[slot_idx] = innate_skill
            else:
                # Explicitly set to 'None' — skill learned after birth, preserve empty gene
                self.ability_upgrades[slot_idx] = 'None'
                
        self.innate_abilities = self.ability_upgrades
        self.sync_legacy_passives()
        self.is_modified = True

    def _skill_string_list(self):
        """boon / move / attack / 4 actives / 4 upgrades / 2 class passives / 2 disorders / items / class."""
        act = list(self.active_abilities[:4])
        upg = list(self.ability_upgrades[:4])
        pas = list(self.class_passives[:2])
        dis = list(self.disorders[:2])
        while len(act) < 4:
            act.append('None')
        while len(upg) < 4:
            upg.append('None')
        while len(pas) < 2:
            pas.append('None')
        while len(dis) < 2:
            dis.append('None')
        extras = list(getattr(self, 'extra_strings', None) or [])
        return [
            self.boon or 'none',
            self.move_ability or 'DefaultMove',
            self.attack_ability or 'BasicMelee',
            *act, *upg, *pas, *dis, *extras,
            self.cat_class or 'Colorless',
        ]

    @staticmethod
    def _fallback_gap_after(index):
        """Only used if parse did not capture original interstitial bytes."""
        if index in (11, 12, 13):
            return struct.pack('<i', 1)
        if index == 14:
            return struct.pack('<i', 1) + b'\x05\x00\x00\x00\x00' * 5
        return b''

    def build_bytes(self):
        buf = bytearray()
        buf.extend(struct.pack('<I', self.version))
        buf.extend(struct.pack('<Q', self.guid))

        name_enc = self.name.encode('utf-16le')
        buf.extend(struct.pack('<Q', len(self.name)))
        buf.extend(name_enc)

        buf.extend(self.pre_voice_body)

        voice_enc = self.voice.encode('ascii')
        buf.extend(struct.pack('<Q', len(voice_enc)))
        buf.extend(voice_enc)

        buf.extend(struct.pack('<d', self.pitch))
        buf.extend(struct.pack('<7i', *self.base_stats))
        buf.extend(struct.pack('<7i', *self.bonus_stats))
        buf.extend(self.mid_flags)

        out_strings = self._skill_string_list()
        gaps = list(getattr(self, 'str_gaps', None) or [])
        for i, s in enumerate(out_strings):
            enc = (s or 'None').encode('ascii')
            buf.extend(struct.pack('<Q', len(enc)))
            buf.extend(enc)
            if i < len(out_strings) - 1:
                if i < len(gaps):
                    buf.extend(gaps[i])
                else:
                    buf.extend(self._fallback_gap_after(i))

        if (getattr(self, '_orig_sexuality', None) is not None
                and self.sexuality != self._orig_sexuality
                and len(self.tail_data) >= 12):
            if "Straight" in self.sexuality:
                s_val = 0.0
            elif "Bisexual" in self.sexuality:
                s_val = 0.25
            else:
                s_val = 0.45
            struct.pack_into('<d', self.tail_data, 4, s_val)

        buf.extend(self.tail_data)
        return bytes(buf)

# ============================================================
# Inventory (仓库道具) — files 表 inventory_storage/backpack/trash
# ============================================================

class InventoryItem:
    """单个道具实例。未知字段原样保留，保证 round-trip 字节一致。

    布局（已用 50/50 条存档样本验证）:
      [u32 head_type=5][u8 head_flag=1][u64 名字长][名字]
      [可选: u64 扩展串长 + 扩展串(如 "Unrestricted"/实例ID)  |  否则 8 字节零]
      [i32 m1 = 剩余使用次数(-1=无限；游戏内 "N uses left")][u32 a][u32 b (0；=4 时 flag2 恒为 0)]
      [u32 serial 实例序列号 (0x3e8 起递增)][u8 f1 (多 0xff，任务道具见 05/06)][u8 f2 = 磨损状态]

    f2 磨损状态（同名道具游戏内对照实测定案）:
      1 = 完好；3 = 磨损 Worn（冒险回家时 50% 概率损坏删除）；0 = 特殊状态
      （f2=0 的 9 件恰为 6 任务道具 + ToolBox/SuperheroHat/FetusInAJar，且 unk_b 恒=4）
    """
    def __init__(self):
        self.head_type = 5
        self.head_flag = 1
        self.name = 'None'
        self.extra = None          # None 或字符串
        self.mid_raw = None        # 扩展串区域无法解释时的原始字节（保底）
        self.m1 = -1
        self.unk_a = 0
        self.unk_b = 0
        self.serial = 0
        self.flag1 = 0xFF
        self.flag2 = 0x01

    @staticmethod
    def _printable(bs):
        return all(32 <= c <= 126 for c in bs)

    @classmethod
    def parse(cls, data, off):
        it = cls()
        it.head_type, it.head_flag = struct.unpack_from('<IB', data, off)
        nlen = struct.unpack_from('<Q', data, off + 5)[0]
        it.name = data[off + 13 : off + 13 + nlen].decode('ascii', errors='replace')
        p = off + 13 + nlen
        # 可选扩展串 / 8 字节零
        if p + 8 <= len(data):
            n2 = struct.unpack_from('<Q', data, p)[0]
            if 1 <= n2 <= 64 and p + 8 + n2 <= len(data) and cls._printable(data[p + 8 : p + 8 + n2]):
                it.extra = data[p + 8 : p + 8 + n2].decode('ascii')
                p += 8 + n2
            elif n2 == 0:
                it.extra = None
                p += 8
            else:
                # 无法解释：保留到尾部起点前的原始字节（理论上不出现）
                it.mid_raw = bytes(data[p : p + 8])
                p += 8
        # 固定 18 字节尾
        it.m1, it.unk_a, it.unk_b, it.serial = struct.unpack_from('<iIII', data, p)
        it.flag1, it.flag2 = struct.unpack_from('<BB', data, p + 16)
        return it, p + 18

    def build(self):
        buf = bytearray()
        buf.extend(struct.pack('<IB', self.head_type, self.head_flag))
        nb = self.name.encode('ascii')
        buf.extend(struct.pack('<Q', len(nb)))
        buf.extend(nb)
        if self.mid_raw is not None:
            buf.extend(self.mid_raw)
        elif self.extra is not None:
            eb = self.extra.encode('ascii')
            buf.extend(struct.pack('<Q', len(eb)))
            buf.extend(eb)
        else:
            buf.extend(b'\x00' * 8)
        buf.extend(struct.pack('<iIII', self.m1, self.unk_a, self.unk_b, self.serial))
        buf.extend(struct.pack('<BB', self.flag1, self.flag2))
        return bytes(buf)


class InventoryBlob:
    """一个库存箱子（storage/backpack/trash）的全部道具。"""
    def __init__(self):
        self.items = []
        self.dirty = False

    def mark_dirty(self):
        self.dirty = True

    @classmethod
    def parse(cls, data):
        blob = cls()
        if not data or len(data) < 4:
            return blob
        count = struct.unpack_from('<I', data, 0)[0]
        off = 4
        for _ in range(count):
            it, off = InventoryItem.parse(data, off)
            blob.items.append(it)
        blob.dirty = False
        return blob

    def build(self):
        buf = bytearray(struct.pack('<I', len(self.items)))
        for it in self.items:
            buf.extend(it.build())
        return bytes(buf)

    def next_serial(self):
        return (max((it.serial for it in self.items), default=1000) + 1)

    def add_item(self, name):
        """以仓库中最普通的道具为模板克隆尾巴，新建道具实例。"""
        it = InventoryItem()
        it.name = name
        tmpl = next((x for x in self.items
                     if x.m1 == -1 and x.unk_a == 0 and x.unk_b == 0
                     and x.flag1 == 0xFF and x.flag2 == 1 and x.extra is None
                     and x.mid_raw is None), None)
        if tmpl:
            it.m1, it.unk_a, it.unk_b = tmpl.m1, tmpl.unk_a, tmpl.unk_b
            it.flag1, it.flag2 = tmpl.flag1, tmpl.flag2
        it.serial = self.next_serial()
        self.items.append(it)
        self.mark_dirty()
        return it

    def remove_item(self, index):
        if 0 <= index < len(self.items):
            self.mark_dirty()
            return self.items.pop(index)
        return None


# ============================================================
# Furniture (家具) — furniture 表
# ============================================================

class FurnitureRecord:
    """单件已放置家具。

    布局（已用多条存档样本验证，blob 总长逐字节吻合）:
      [i32 head=1 (常量, 非表key)][u64 名字长][名字][8 字节零][u64 房间名长][房间名(可为空)]
      [i32 x][i32 y][u32 variant 变体][u32 flag1=1][u32 flag2=1]
    """
    def __init__(self, key=0):
        self.key = key
        self.head = 1
        self.name = ''
        self.mid8 = b'\x00' * 8
        self.room = ''
        self.x = 0
        self.y = 0
        self.variant = 0
        self.flag1 = 1
        self.flag2 = 1
        self.dirty = False

    def mark_dirty(self):
        self.dirty = True

    @classmethod
    def parse(cls, data, table_key=None):
        r = cls()
        r.head = struct.unpack_from('<i', data, 0)[0]
        if table_key is not None:
            r.key = table_key
        p = 4
        nlen = struct.unpack_from('<Q', data, p)[0]; p += 8
        r.name = data[p : p + nlen].decode('ascii', errors='replace'); p += nlen
        r.mid8 = bytes(data[p : p + 8]); p += 8
        rlen = struct.unpack_from('<Q', data, p)[0]; p += 8
        r.room = data[p : p + rlen].decode('ascii', errors='replace'); p += rlen
        r.x, r.y, r.variant, r.flag1, r.flag2 = struct.unpack_from('<iiIII', data, p)
        r.dirty = False
        return r

    def build(self):
        buf = bytearray(struct.pack('<i', self.head))
        nb = self.name.encode('ascii')
        buf.extend(struct.pack('<Q', len(nb))); buf.extend(nb)
        buf.extend(self.mid8)
        rb = self.room.encode('ascii')
        buf.extend(struct.pack('<Q', len(rb))); buf.extend(rb)
        buf.extend(struct.pack('<iiIII', self.x, self.y, self.variant, self.flag1, self.flag2))
        return bytes(buf)


# ============================================================
# NPC/商店进度 (npc_progress) 与 房屋解锁 (house_unlocks) — 只读解析
# ============================================================

def scan_string_value_records(data):
    """线性扫描 blob 中的 [u64 长度][ascii 字符串][u32 数值] 记录。

    npc_progress 的完整块结构未完全逆向，但商店/家园进度只需按名字前缀提取记录，
    线性扫描对只读展示足够稳健。返回 [(name, value), ...]（保持出现顺序）。
    """
    records = []
    p = 0
    n = len(data)
    while p + 12 <= n:
        slen = struct.unpack_from('<Q', data, p)[0]
        if 1 <= slen <= 48 and p + 8 + slen + 4 <= n:
            chunk = data[p + 8 : p + 8 + slen]
            if all(32 <= b <= 126 for b in chunk):
                val = struct.unpack_from('<I', data, p + 8 + slen)[0]
                records.append((chunk.decode('ascii'), val))
                p += 8 + slen + 4
                continue
        p += 1
    return records


def difficulty_progress_defaults():
    """默认难度进度：3 章(act1/2/3) × 4 难度，全未解锁(普通为基底恒真)。"""
    return {
        'hardpath_unlocked': False,
        'acts': {i: {'normal': True, 'hard': False, 'crazy': False, 'impossible': False} for i in (1, 2, 3)},
        'house_boss_difficulty': -1,      # 当前房间 Boss 难度(-1=无)
        'alien_invasion_count': 0,        # 异星入侵气象解锁次数
    }


def parse_difficulty_progress(data, properties):
    """解析 npc_progress / properties 中的难度推进进度。

    - npc_progress 存在性标志（[u64 长度][记录名] 无值）：difficulty_unlock_act{N}_{hard|crazy|impossible}
      （N=1..3）——某章某进阶难度已解锁；map_unlock_hardpath —— 困难路径已解锁。
    - properties.house_boss_difficulty：当前房间 Boss 难度(-1=无)。
    - properties.sfunlockcounter_weather_unlock_alieninvasion：异星入侵气象解锁次数。
    """
    out = difficulty_progress_defaults()
    try:
        # 存在性标志：u64 len + ascii 名，后面无 u32 值（下一记录的长度前缀）。
        p, n = 0, len(data)
        names = set()
        while p + 8 <= n:
            slen = struct.unpack_from('<Q', data, p)[0]
            if 4 <= slen <= 60 and p + 8 + slen <= n:
                chunk = data[p + 8 : p + 8 + slen]
                if all(32 <= b <= 126 for b in chunk):
                    names.add(chunk.decode('ascii'))
                    p += 8 + slen
                    continue
            p += 1
        for name in names:
            if name == 'map_unlock_hardpath':
                out['hardpath_unlocked'] = True
            else:
                m = re.match(r'difficulty_unlock_act(\d+)_(hard|crazy|impossible)$', name)
                if m:
                    out['acts'][int(m.group(1))][m.group(2)] = True
    except Exception:
        pass
    if properties:
        hb = properties.get('house_boss_difficulty', -1)
        try:
            out['house_boss_difficulty'] = int(hb)
        except Exception:
            pass
        try:
            out['alien_invasion_count'] = int(properties.get('sfunlockcounter_weather_unlock_alieninvasion', 0) or 0)
        except Exception:
            pass
    return out


_WEATHER_CATALOG = None

def load_weather_catalog(base_dir=None):
    """游戏天气表：wiki_data/csv/weather.csv（代码以 gon/官方文本为准）。"""
    global _WEATHER_CATALOG
    if _WEATHER_CATALOG is not None:
        return _WEATHER_CATALOG
    bases = []
    if base_dir:
        bases.append(base_dir)
    bases.append(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))))
    bases.append(os.path.dirname(os.path.abspath(__file__)))
    bases.append(os.getcwd())
    rows = []
    seen = set()
    for base in bases:
        csv_p = os.path.join(base, 'wiki_data', 'csv', 'weather.csv')
        if not os.path.exists(csv_p):
            continue
        try:
            with open(csv_p, 'r', encoding='utf-8-sig', newline='') as f:
                for r in csv.DictReader(f):
                    k = (r.get('weather_code') or '').strip()
                    if not k or k in seen:
                        continue
                    seen.add(k)
                    rows.append({
                        'key': k,
                        'name': (r.get('name_texts_zh') or r.get('weather_name') or k).strip(),
                        'name_en': (r.get('name_texts_en') or r.get('weather_name') or k).strip(),
                        'desc': (r.get('desc_texts_zh') or r.get('description') or '').strip(),
                    })
            break
        except Exception:
            continue
    _WEATHER_CATALOG = rows
    return rows


def parse_save_weather(properties):
    """从 properties 读取当前家园天气与已解锁天气。

    - current_house_weather：当前家园/战役天气代码（空=晴朗 None）
    - force_next_weather：强制下一场天气
    - {Code}Unlocked 或 sfunlockcounter_weather_unlock_{code}：解锁次数
    """
    props = properties or {}
    catalog = load_weather_catalog()
    unlocked = {}
    for w in catalog:
        k = w['key']
        cnt = 0
        flag = props.get(f'{k}Unlocked')
        if flag not in (None, '', 0, '0'):
            try:
                cnt = max(cnt, int(flag))
            except (TypeError, ValueError):
                cnt = max(cnt, 1)
        uk = f'sfunlockcounter_weather_unlock_{k.lower()}'
        raw = props.get(uk)
        if raw not in (None, '', 0, '0'):
            try:
                cnt = max(cnt, int(raw))
            except (TypeError, ValueError):
                cnt = max(cnt, 1)
        if cnt:
            unlocked[k] = cnt
    current = props.get('current_house_weather')
    if isinstance(current, bytes):
        current = current.decode('utf-8', errors='ignore')
    current = (str(current).strip() if current is not None else '') or 'None'
    force = props.get('force_next_weather', 0)
    return {
        'current': current,
        'force_next': force,
        'unlocked': unlocked,
        'catalog': catalog,
    }


def parse_house_unlocks(data):
    names = []
    p = 0
    while p + 8 <= len(data):
        slen = struct.unpack_from('<Q', data, p)[0]
        if 1 <= slen <= 48 and p + 8 + slen <= len(data):
            chunk = data[p + 8 : p + 8 + slen]
            if all(32 <= b <= 126 for b in chunk):
                names.append(chunk.decode('ascii'))
                p += 8 + slen
                continue
        p += 1
    return names


def storage_capacity(level):
    """Butch 仓库容量：基础 3x3，每次升级 +1 圈；7 级后每次重复 +1 格。
    游戏内实测确认：等级 4 = 49（= (3+4)²）。

    来源: game_assets/data/npc_favor_unlocks.gon 注释
    "start at 3x3 + 7 upgrades = 10x10"、"repeat 20 // 100 to 121 (11x11)"（后期每级+1）。
    注意：主线/支线任务道具存放在同一 blob 但不占用普通容量格子（游戏内实测）。
    """
    level = max(0, int(level))
    if level <= 7:
        return (3 + level) ** 2
    return 100 + (level - 7)


def get_shop_progress(properties, npc_records, house_unlocks_names):
    """汇总各商店/家园升级等级，供 UI 展示（只读）。"""
    rec = {}
    for name, val in npc_records:
        rec.setdefault(name, 0)
        rec[name] += max(val, 1)  # value=1 表示完成过；重复序列计数累加

    def count_prefix(prefix):
        return sum(v for k, v in rec.items() if k.startswith(prefix))

    storage_lv = properties.get('house_storage_upgrades', 0)
    tink_services = ['tink_prettybow', 'tink_basestats', 'tink_inbreeding', 'tink_sexuality',
                     'tink_tags', 'tink_aggression', 'tink_relationships']
    return {
        'storage_level': storage_lv,
        'storage_capacity': storage_capacity(storage_lv),
        'storage_records': count_prefix('upgrade_storage_'),   # npc_progress 侧记录（含 repeating）
        'jack_level': count_prefix('jack_shopupgrade'),        # Jack 家具店
        'tracy_foodstorage': count_prefix('tracy_foodstorage'),
        'tracy_blankcollar': count_prefix('tracy_blankcollar'),
        'tracy_idol': count_prefix('tracy_idol'),
        'organ_level': count_prefix('organ_upgrade'),
        'organ_unlocked': 'organ_unlock' in rec,
        'tink_unlocks': [k for k in tink_services if k in rec],
        'beanies_intro_done': rec.get('beanies_quests_intro', 0) > 0,
        'beanies_repeat_count': rec.get('beanies_quests_repeat', 0),
        'house_unlocks': list(house_unlocks_names),
    }


# ============================================================
# 职业通关角标 (class completion checkmarks) — 只读解析
# ============================================================

# 游戏内 9 个职业通关角标对应的章节（来自 chapter_id_enum.gon: major_class_checkmarks）
MAJOR_CHECKMARK_ZONES = ['caves', 'boneyard', 'moon', 'core', 'jurassic',
                         'theend', 'meatworld', 'dimensionx', 'endoftime']

_ZONE_IDS = ['debug', 'tutorial', 'alley', 'sewers', 'junkyard', 'caves', 'boneyard',
             'meatworld', 'desert', 'crater', 'bunker', 'moon', 'core', 'dimensionx',
             'lab', 'iceage', 'future', 'jurassic', 'theend', 'endoftime']
_CLASS_IDS = ['Colorless', 'Fighter', 'Hunter', 'Mage', 'Tank', 'Medic', 'Thief',
              'Necromancer', 'Tinkerer', 'Druid', 'Butcher', 'Psychic', 'Monk',
              'Jester', 'any']


def parse_class_zone_records(data):
    """扫描 npc_progress 中的 (章节, 职业) 记录。

    布局: [u64 章节名长][章节名][u64 职业名长][职业名][i32 a][i32 b][u32 visits][u32 0][u32 0]
    - a == -1 (0xFFFFFFFF) → 该职业已通关此章节（角标点亮）
    - b == -1 → 仅出现在前三大章（tutorial/alley/sewers/junkyard），疑似困难路径标记
    - visits → 进入该章节的次数
    返回 {(class, zone): (a, b, visits)}
    """
    records = {}
    p, n = 0, len(data)
    while p + 16 < n:
        zl = struct.unpack_from('<Q', data, p)[0]
        if 3 <= zl <= 12 and p + 8 + zl + 8 < n:
            zone = data[p + 8 : p + 8 + zl].decode('ascii', errors='ignore')
            if zone in _ZONE_IDS:
                q = p + 8 + zl
                cl = struct.unpack_from('<Q', data, q)[0]
                if 3 <= cl <= 12 and q + 8 + cl + 20 <= n:
                    cls = data[q + 8 : q + 8 + cl].decode('ascii', errors='ignore')
                    if cls in _CLASS_IDS:
                        t = q + 8 + cl
                        a, b, visits, _, _ = struct.unpack_from('<IIIII', data, t)
                        a = -1 if a == 0xFFFFFFFF else a
                        b = -1 if b == 0xFFFFFFFF else b
                        records[(cls, zone)] = (a, b, visits)
                        p = t
                        continue
        p += 1
    return records


class MewgenicsSaveManager:
    @classmethod
    def get_saves_dir(cls):
        base_dir = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics")
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir):
                if os.path.basename(root) == "saves":
                    return root
        return os.path.join(base_dir, "76561198096981781", "saves")

    @classmethod
    def find_default_save(cls):
        s_dir = cls.get_saves_dir()
        p1 = os.path.join(s_dir, "steamcampaign01.sav")
        if os.path.exists(p1):
            return p1
        if os.path.exists(s_dir):
            for f in os.listdir(s_dir):
                if f.endswith(".sav") and "campaign" in f:
                    return os.path.join(s_dir, f)
        return p1

    @classmethod
    def get_slot_info(cls, file_path, slot_num=1):
        if not file_path or not os.path.exists(file_path):
            return {
                'slot': slot_num,
                'exists': False,
                'path': file_path,
                'has_data': False,
                'title': '无数据',
                'location': '无数据',
                'percent': 0,
                'time_str': '00:00:00',
                'day': 0,
                'gold': 0,
                'food': 0,
                'cat_count': 0,
                'mtime_str': '--'
            }
        try:
            conn = sqlite3.connect(file_path)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='properties'")
            if not cur.fetchone():
                conn.close()
                return {
                    'slot': slot_num,
                    'exists': True,
                    'path': file_path,
                    'has_data': False,
                    'title': '无数据',
                    'location': '无数据',
                    'percent': 0,
                    'time_str': '00:00:00',
                    'day': 0,
                    'gold': 0,
                    'food': 0,
                    'cat_count': 0,
                    'mtime_str': '--'
                }

            cur.execute("SELECT key, data FROM properties")
            props = dict(cur.fetchall())

            cur.execute("SELECT COUNT(*) FROM cats")
            cat_count = cur.fetchone()[0]
            conn.close()

            loc_code = props.get('savescumlocation', 0)
            loc_map = {0: "家", 1: "小巷", 2: "下水道", 3: "沙漠", 4: "废料场", 5: "乱葬岗", 6: "地堡", 7: "洞穴", 8: "地心", 9: "陨石坑", 10: "血肉世界", 11: "月球"}
            location_str = loc_map.get(loc_code, f"区域 {loc_code}") if loc_code is not None else "家"

            percent = props.get('save_file_percent', 0)
            timer_frames = props.get('savefile_timer', 0)
            total_sec = int(timer_frames / 60)
            hh = total_sec // 3600
            mm = (total_sec % 3600) // 60
            ss = total_sec % 60
            time_str = f"{hh:02d}:{mm:02d}:{ss:02d}"

            day = props.get('current_day', 0)
            gold = props.get('house_gold', 0)
            food = props.get('house_food', 0)

            from datetime import datetime
            mtime = os.path.getmtime(file_path)
            mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

            has_data = (cat_count > 0 or timer_frames > 0 or day > 0)
            return {
                'slot': slot_num,
                'exists': True,
                'path': file_path,
                'has_data': has_data,
                'title': location_str if has_data else '无数据',
                'location': location_str if has_data else '无数据',
                'percent': percent if has_data else 0,
                'time_str': time_str if has_data else '00:00:00',
                'day': day,
                'gold': gold,
                'food': food,
                'cat_count': cat_count,
                'mtime_str': mtime_str
            }
        except Exception:
            return {
                'slot': slot_num,
                'exists': True,
                'path': file_path,
                'has_data': False,
                'title': '无数据',
                'location': '无数据',
                'percent': 0,
                'time_str': '00:00:00',
                'day': 0,
                'gold': 0,
                'food': 0,
                'cat_count': 0,
                'mtime_str': '--'
            }

    @classmethod
    def get_all_slots_info(cls):
        s_dir = cls.get_saves_dir()
        slots = []
        for i in range(1, 4):
            fn = f"steamcampaign0{i}.sav"
            fp = os.path.join(s_dir, fn)
            slots.append(cls.get_slot_info(fp, slot_num=i))
        return slots

    def __init__(self, file_path=None):
        self.file_path = file_path or self.find_default_save()
        self.cats = {}
        self.properties = {}
        self.inventories = {}      # {'storage': InventoryBlob, 'backpack': ..., 'trash': ...}
        self.furniture = {}        # {key: FurnitureRecord}
        self._furniture_orig_keys = set()
        self._properties_orig = {}
        self._house_state_dirty = False
        if self.file_path and os.path.exists(self.file_path):
            self.load()

    def load(self, path=None):
        if path:
            self.file_path = path
        conn = sqlite3.connect(self.file_path)
        cur = conn.cursor()
        
        cur.execute("SELECT key, data FROM properties")
        self.properties = {k: v for k, v in cur.fetchall()}
        self._properties_orig = dict(self.properties)
        self._house_state_dirty = False
        
        cur.execute("SELECT key, data FROM cats")
        self.cats = {}
        for k, blob in cur.fetchall():
            unc_sz = struct.unpack_from('<I', blob, 0)[0]
            raw = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
            try:
                c = CatRecord(k, raw)
                c.is_in_house = False
                c.house_room = ""
                self.cats[k] = c
            except Exception as e:
                pass

        # Parse living cats from house_state
        self.house_cat_ids = set()
        self.house_cat_rooms = {}
        self.house_state_raw = None
        try:
            cur.execute("SELECT data FROM files WHERE key='house_state'")
            row = cur.fetchone()
            if row and row[0]:
                self.house_state_raw = bytearray(row[0])
                data = self.house_state_raw
                p = 0
                while p < len(data) - 8:
                    slen = struct.unpack_from('<Q', data, p)[0]
                    if 1 <= slen <= 50 and p + 8 + slen <= len(data):
                        chunk = data[p+8 : p+8+slen]
                        if all(32 <= b <= 126 for b in chunk):
                            s = chunk.decode('ascii')
                            cat_id_pos = p - 8
                            if cat_id_pos >= 0:
                                cid = struct.unpack_from('<Q', data, cat_id_pos)[0]
                                if cid in self.cats:
                                    self.house_cat_ids.add(cid)
                                    self.house_cat_rooms[cid] = s
                                    self.cats[cid].is_in_house = True
                                    self.cats[cid].house_room = s
                            p += 8 + slen
                            continue
                    p += 1
        except Exception as e:
            pass

        # 库存道具 (inventory_storage/backpack/trash)
        self.inventories = {}
        for box in ('storage', 'backpack', 'trash'):
            try:
                row = cur.execute("SELECT data FROM files WHERE key=?", (f'inventory_{box}',)).fetchone()
                self.inventories[box] = InventoryBlob.parse(row[0]) if row and row[0] else InventoryBlob()
            except Exception:
                self.inventories[box] = InventoryBlob()

        # 家具
        self.furniture = {}
        try:
            for k, blob in cur.execute("SELECT key, data FROM furniture").fetchall():
                try:
                    self.furniture[k] = FurnitureRecord.parse(blob, table_key=k)
                except Exception:
                    pass
        except Exception:
            pass
        self._furniture_orig_keys = set(self.furniture.keys())

        # NPC/商店进度 + 房屋解锁（只读）
        self.npc_records = []
        self.house_unlocks = []
        self.class_zone_records = {}
        self.difficulty_progress = {}
        try:
            row = cur.execute("SELECT data FROM files WHERE key='npc_progress'").fetchone()
            if row and row[0]:
                self.npc_records = scan_string_value_records(row[0])
                self.class_zone_records = parse_class_zone_records(row[0])
                self.difficulty_progress = parse_difficulty_progress(row[0], self.properties)
            row = cur.execute("SELECT data FROM files WHERE key='house_unlocks'").fetchone()
            if row and row[0]:
                self.house_unlocks = parse_house_unlocks(row[0])
        except Exception:
            pass

        conn.close()
        return len(self.cats)

    def set_cat_room(self, cat_key, room_name):
        cat = self.cats.get(cat_key)
        if not cat:
            return False
            
        old_room = getattr(cat, 'house_room', '')
        if old_room == room_name:
            return True
            
        valid_rooms = ['Floor1_Large', 'Floor1_Small', 'Attic']
        
        # If moving out of house (or "移出家园")
        if not room_name or room_name not in valid_rooms or "移出" in room_name:
            self._remove_from_house_state(cat_key)
            cat.is_in_house = False
            cat.house_room = ""
            if cat_key in self.house_cat_ids:
                self.house_cat_ids.remove(cat_key)
            if cat_key in self.house_cat_rooms:
                del self.house_cat_rooms[cat_key]
            self._house_state_dirty = True
            return True

        # Moving to a valid house room
        cat.is_in_house = True
        cat.house_room = room_name
        self.house_cat_ids.add(cat_key)
        self.house_cat_rooms[cat_key] = room_name
        
        updated = self._update_room_in_house_state(cat_key, room_name)
        if not updated:
            self._append_to_house_state(cat_key, room_name)
        self._house_state_dirty = True
        return True

    def _update_room_in_house_state(self, cat_key, new_room):
        if not getattr(self, 'house_state_raw', None):
            return False
        raw = self.house_state_raw
        p = 0
        while p < len(raw) - 8:
            slen = struct.unpack_from('<Q', raw, p)[0]
            if slen in [5, 12] and p + 8 + slen <= len(raw):
                s = raw[p+8 : p+8+slen].decode('ascii', errors='ignore')
                if s in ['Floor1_Large', 'Floor1_Small', 'Attic']:
                    cid_pos = p - 8
                    cid = struct.unpack_from('<Q', raw, cid_pos)[0]
                    if cid == cat_key:
                        old_bytes = struct.pack('<Q', slen) + s.encode('ascii')
                        new_bytes = struct.pack('<Q', len(new_room)) + new_room.encode('ascii')
                        raw[p : p + len(old_bytes)] = new_bytes
                        return True
                    p += 8 + slen + 32
                    continue
            p += 1
        return False

    def _append_to_house_state(self, cat_key, room_name):
        if not getattr(self, 'house_state_raw', None):
            return False
        raw = self.house_state_raw
        val0, count = struct.unpack_from('<II', raw, 0)
        struct.pack_into('<I', raw, 4, count + 1)
        entry = bytearray()
        entry.extend(struct.pack('<Q', cat_key))
        entry.extend(struct.pack('<Q', len(room_name)))
        entry.extend(room_name.encode('ascii'))
        entry.extend(struct.pack('<4d', 15.0, 1.0, 0.0, 0.0))
        raw.extend(entry)
        return True

    def _remove_from_house_state(self, cat_key):
        if not getattr(self, 'house_state_raw', None):
            return False
        raw = self.house_state_raw
        p = 0
        while p < len(raw) - 8:
            slen = struct.unpack_from('<Q', raw, p)[0]
            if slen in [5, 12] and p + 8 + slen <= len(raw):
                s = raw[p+8 : p+8+slen].decode('ascii', errors='ignore')
                if s in ['Floor1_Large', 'Floor1_Small', 'Attic']:
                    cid_pos = p - 8
                    cid = struct.unpack_from('<Q', raw, cid_pos)[0]
                    if cid == cat_key:
                        entry_end = p + 8 + slen + 32
                        del raw[cid_pos : entry_end]
                        val0, count = struct.unpack_from('<II', raw, 0)
                        struct.pack_into('<I', raw, 4, max(0, count - 1))
                        return True
                    p += 8 + slen + 32
                    continue
            p += 1
        return False

    def add_furniture(self, name, room='', x=None, y=None):
        """添加一件家具。variant/flags 沿用同类型现有行；坐标缺省沿用同类型或 0。"""
        new_key = max(self.furniture.keys(), default=0) + 1
        rec = FurnitureRecord(new_key)
        rec.name = name
        rec.room = room or ''
        same = next((r for r in self.furniture.values() if r.name == name), None)
        if same:
            rec.variant, rec.flag1, rec.flag2 = same.variant, same.flag1, same.flag2
            rec.x = same.x if x is None else x
            rec.y = same.y if y is None else y
        else:
            rec.x = 0 if x is None else x
            rec.y = 0 if y is None else y
        rec.mark_dirty()
        self.furniture[new_key] = rec
        return rec

    def remove_furniture(self, key):
        return self.furniture.pop(key, None)

    def set_property(self, key, value):
        """只在值变化时写入 properties，避免无改动也标脏。"""
        if self.properties.get(key) == value:
            return False
        self.properties[key] = value
        return True

    def dirty_summary(self):
        furn = getattr(self, 'furniture', {})
        orig = getattr(self, '_furniture_orig_keys', set())
        return {
            'cats': [k for k, c in self.cats.items() if getattr(c, 'is_modified', False)],
            'inv': [b for b, blob in getattr(self, 'inventories', {}).items() if getattr(blob, 'dirty', False)],
            'furn': [k for k, r in furn.items() if getattr(r, 'dirty', False)],
            'furn_del': list(orig - set(furn.keys())),
            'props': [k for k, v in self.properties.items() if getattr(self, '_properties_orig', {}).get(k) != v],
            'house': bool(getattr(self, '_house_state_dirty', False)),
        }

    def has_dirty(self):
        s = self.dirty_summary()
        return bool(s['cats'] or s['inv'] or s['furn'] or s['furn_del'] or s['props'] or s['house'])

    def clear_dirty(self):
        for cat in self.cats.values():
            cat.is_modified = False
        for blob in getattr(self, 'inventories', {}).values():
            blob.dirty = False
        for rec in getattr(self, 'furniture', {}).values():
            rec.dirty = False
        self._furniture_orig_keys = set(self.furniture.keys())
        self._properties_orig = dict(self.properties)
        self._house_state_dirty = False

    def backup(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.file_path}.backup_{ts}"
        shutil.copy2(self.file_path, backup_path)
        return backup_path

    def save(self, target_path=None):
        dirty = self.dirty_summary()
        has_dirty = bool(dirty['cats'] or dirty['inv'] or dirty['furn'] or dirty['furn_del'] or dirty['props'] or dirty['house'])
        if not has_dirty and (not target_path or target_path == self.file_path):
            return None

        if target_path and target_path != self.file_path:
            shutil.copy2(self.file_path, target_path)
            dest = target_path
            backup_result = target_path
        else:
            backup_result = self.backup()
            dest = self.file_path
        
        conn = sqlite3.connect(dest)
        cur = conn.cursor()

        for k in dirty['props']:
            cur.execute("INSERT OR REPLACE INTO properties (key, data) VALUES (?, ?)", (k, self.properties[k]))

        # 只写改过的猫。未改字段保留原始间隔字节（装备栏空位 / 物品 / 等级）。
        for key in dirty['cats']:
            cat = self.cats[key]
            raw_cat = cat.build_bytes()
            comp = lz4.block.compress(raw_cat, store_size=False)
            blob = struct.pack('<I', len(raw_cat)) + comp
            cur.execute("INSERT OR REPLACE INTO cats (key, data) VALUES (?, ?)", (key, blob))

        if dirty['house'] and getattr(self, 'house_state_raw', None) is not None:
            cur.execute("INSERT OR REPLACE INTO files (key, data) VALUES (?, ?)",
                        ('house_state', bytes(self.house_state_raw)))

        for box in dirty['inv']:
            blob = self.inventories[box]
            cur.execute("INSERT OR REPLACE INTO files (key, data) VALUES (?, ?)",
                        (f'inventory_{box}', blob.build()))

        furn = getattr(self, 'furniture', {})
        for k in dirty['furn']:
            rec = furn[k]
            cur.execute("INSERT OR REPLACE INTO furniture (key, data) VALUES (?, ?)", (k, rec.build()))
        for k in dirty['furn_del']:
            cur.execute("DELETE FROM furniture WHERE key=?", (k,))

        conn.commit()
        conn.close()
        self.clear_dirty()
        return backup_result

    def create_new_cat(self, name="NewCat", gender="male", cat_class="Colorless", stats=None, template_id=835, room="Floor1_Large", sexuality="Straight (异性恋)"):
        if template_id not in self.cats:
            template_id = max(self.cats.keys()) if self.cats else 1
            
        template = self.cats[template_id]
        new_key = max(self.cats.keys()) + 1 if self.cats else 1
        
        # Clone template bytes
        raw_clone = bytearray(template.build_bytes())
        new_cat = CatRecord(new_key, raw_clone)
        new_cat.name = name
        new_cat.guid = random.getrandbits(64)
        new_cat.cat_class = cat_class
        new_cat.voice = "male55" if gender == "male" else "female50"
        new_cat.sexuality = sexuality
        
        if stats:
            for i, k in enumerate(CatRecord.STAT_NAMES):
                if k in stats:
                    new_cat.base_stats[i] = int(stats[k])
                    
        new_cat.is_modified = True
        self.cats[new_key] = new_cat
        if room and room != "移出家园 (谱系)":
            self.set_cat_room(new_key, room)
        return new_cat
