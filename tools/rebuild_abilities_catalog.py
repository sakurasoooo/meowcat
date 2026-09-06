# -*- coding: utf-8 -*-
"""Rebuild assets/abilities_catalog.json from game-source ability_code.

Source of truth: wiki_data/abilities_combined.json (parsed from data2/abilities/*.gon).
Player-facing spells get a real class; enemy/item/debug entries are kept but marked
picker_hidden so 「通用」不再吞下整份内部表。
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from mewgenics_core import BASIC_ATTACK_ABILITIES, BASIC_MOVE_ABILITIES
from picker_dialog import resolve_icon_path, dedupe_catalog_items

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMB = os.path.join(ROOT, "wiki_data", "abilities_combined.json")
CSV = os.path.join(ROOT, "wiki_data", "csv", "abilities.csv")
OUT = os.path.join(ROOT, "assets", "abilities_catalog.json")
ICONS = os.path.join(ROOT, "assets", "icons", "abilities")
FB = os.path.join(ROOT, "assets", "icons", "fallback.png")

REAL_CLASSES = {
    "Colorless", "Fighter", "Mage", "Hunter", "Tank", "Medic", "Thief",
    "Necromancer", "Butcher", "Druid", "Monk", "Psychic", "Tinkerer", "Jester",
}
PLAYER_BASICS = set(BASIC_ATTACK_ABILITIES) | set(BASIC_MOVE_ABILITIES)

FILE_TO_CLASS = {
    "colorless_abilities.gon": "Colorless",
    "fighter_abilities.gon": "Fighter",
    "mage_abilities.gon": "Mage",
    "hunter_abilities.gon": "Hunter",
    "tank_abilities.gon": "Tank",
    "medic_abilities.gon": "Medic",
    "thief_abilities.gon": "Thief",
    "necromancer_abilities.gon": "Necromancer",
    "butcher_abilities.gon": "Butcher",
    "druid_abilities.gon": "Druid",
    "monk_abilities.gon": "Monk",
    "psychic_abilities.gon": "Psychic",
    "tinkerer_abilities.gon": "Tinkerer",
    "jester_abilities.gon": "Jester",
}


def _pool_class(token):
    t = str(token).replace("file:", "").replace("\\", "/").split("/")[-1]
    if t in FILE_TO_CLASS:
        return FILE_TO_CLASS[t]
    low = t.lower()
    for cls in REAL_CLASSES:
        cl = cls.lower()
        if low.startswith(cl + ".") or low.startswith(cl + "_") or low == cl + "abilities":
            return cls
    return None


def infer_class(w):
    ac = w.get("ability_class")
    if ac in REAL_CLASSES:
        return ac
    for p in w.get("ability_pools") or []:
        c = _pool_class(p)
        if c:
            return c
    src = (w.get("source_file") or "").replace("\\", "/").split("/")[-1]
    return FILE_TO_CLASS.get(src)


def infer_kind(w):
    src = " ".join([w.get("source_file") or "", *(w.get("ability_pools") or [])]).lower()
    if "special_enemy" in src or "enemy_abilities" in src:
        return "enemy"
    if "item_abilities" in src or "armor_abilities" in src or "consumable" in src:
        return "item"
    if (w.get("source_file") or "").endswith("basic_attacks.gon"):
        return "basic_attack"
    if (w.get("source_file") or "").endswith("basic_movement.gon"):
        return "basic_move"
    return "spell"


def is_debug_key(key):
    if not key:
        return True
    if key.startswith("AZ_") or "PLACEHOLDER" in key.upper():
        return True
    if key.endswith("_AI"):
        return True
    return False


def clean_desc(s):
    if not s:
        return ""
    return (
        str(s)
        .replace("{he}", "它")
        .replace("{He}", "它")
        .replace("\r", " ")
        .strip()
    )


def load_csv_zh():
    out = {}
    if not os.path.exists(CSV):
        return out
    with open(CSV, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            code = row.get("ability_code")
            if not code:
                continue
            out[code] = {
                "name": (row.get("name_zh") or "").strip(),
                "name_en": (row.get("name_en") or "").strip(),
                "desc": (row.get("desc_zh") or "").strip(),
            }
    return out


def main():
    wiki = json.load(open(COMB, encoding="utf-8-sig"))
    csv_zh = load_csv_zh()
    catalog = []
    seen = set()
    stats = {"player": 0, "hidden": 0, "icon": 0, "zh": 0, "colorless": 0}

    for w in wiki.get("abilities") or []:
        key = w.get("ability_code")
        if not key or key in seen or key == "None":
            continue
        seen.add(key)

        cls = infer_class(w)
        kind = infer_kind(w)
        debug = is_debug_key(key)
        player = (not debug) and not key.startswith("Basic") and (
            cls in REAL_CLASSES
            or key in PLAYER_BASICS
            or kind in ("basic_attack", "basic_move")
        )
        if not cls:
            if kind == "enemy":
                cls = "Enemy"
            elif kind == "item":
                cls = "Item"
            elif kind in ("basic_attack", "basic_move"):
                cls = "Colorless"
            else:
                cls = "Internal"

        texts = w.get("ability_name_texts") or {}
        dtexts = w.get("description_texts") or {}
        csv_hit = csv_zh.get(key, {})
        name = texts.get("zh") or csv_hit.get("name") or w.get("ability_name") or key
        name_en = texts.get("en") or csv_hit.get("name_en") or w.get("ability_name") or key
        desc = clean_desc(dtexts.get("zh") or csv_hit.get("desc") or w.get("description") or "")

        icon_key = w.get("ability_icon") or ""
        if icon_key in ("None", key):
            icon_key = ""
        png = resolve_icon_path(ICONS, key, None, extra_keys=[icon_key])
        if not png:
            png = resolve_icon_path(os.path.join(ROOT, "assets", "icons", "passives"), key, None, extra_keys=[icon_key])
        has_icon = bool(png)

        cost = w.get("cost") or {}
        mana = cost.get("mana") or 0
        dmg = ""
        if w.get("damage") and w["damage"].get("value"):
            dmg = str(w["damage"]["value"])
        elif w.get("icon_damage_display"):
            dmg = str(w["icon_damage_display"])

        item = {
            "key": key,
            "name": name,
            "name_en": name_en,
            "desc": desc,
            "class": cls,
            "mana": mana if isinstance(mana, int) else 0,
            "damage": dmg,
            "range": 0,
            "variant_of": w.get("ability_code_upgraded") or "",
            "has_icon": has_icon,
            "icon_key": icon_key,
            "type_icon": w.get("type_icon") or "",
            "elements": [str(e).lower() for e in (w.get("elements") or [])],
            "picker_hidden": not player,
            "source": (w.get("source_file") or "").replace("\\", "/").split("/")[-1],
        }
        catalog.append(item)
        if player:
            stats["player"] += 1
        else:
            stats["hidden"] += 1
        if has_icon:
            stats["icon"] += 1
        if name != key and any("\u4e00" <= c <= "\u9fff" for c in name):
            stats["zh"] += 1
        if cls == "Colorless" and player:
            stats["colorless"] += 1

    catalog = dedupe_catalog_items(catalog)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
        f.write("\n")

    by_cls = {}
    for it in catalog:
        if it.get("picker_hidden"):
            continue
        by_cls[it["class"]] = by_cls.get(it["class"], 0) + 1
    print(f"wrote {len(catalog)} abilities -> {OUT}")
    print(f"  player-facing {stats['player']}  hidden {stats['hidden']}")
    print(f"  translated zh {stats['zh']}  has_icon {stats['icon']}")
    print(f"  Colorless player pool {stats['colorless']}  pages {(stats['colorless'] + 31) // 32}")
    print("  player by class:", dict(sorted(by_cls.items(), key=lambda x: -x[1])))


if __name__ == "__main__":
    main()
