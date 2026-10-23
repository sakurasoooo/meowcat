# -*- coding: utf-8 -*-
"""Verify skill-card code extraction + passive icon path resolution."""
import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from skill_card_widget import extract_skill_code
from mewgenics_core import get_canonical_passive_code, dedupe_catalog_items
from picker_dialog import resolve_icon_path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS = os.path.join(ROOT, "assets", "icons", "passives")
FB = os.path.join(ROOT, "assets", "icons", "fallback.png")


def _bn(path):
    return os.path.basename(path).lower() if path else None


def main():
    cases = [
        (None, "None"),
        ("None (无被动)", "None"),
        ("ThouShaltNotKill", "ThouShaltNotKill"),
        (
            "★ [牧师] 不可杀生 (ThouShaltNotKill) - 敌人击倒其他单位时，它会受到10点神圣伤害。",
            "ThouShaltNotKill",
        ),
        ("[Medic] 不可杀生 (ThouShaltNotKill) - 敌人击倒...", "ThouShaltNotKill"),
        ("战士之魂 (FighterSoul) - 升级时还会出现战士能力。", "FighterSoul"),
        ("★ [战士] 战士之魂 (FightersSoul) - desc", "FightersSoul"),
    ]
    failed = 0
    for raw, expect in cases:
        got = extract_skill_code(raw)
        ok = got == expect
        failed += not ok
        print(("OK " if ok else "FAIL"), repr(raw)[:70], "=>", got, "expected", expect)

    canon_cases = [
        ("ThouShaltNotKill", "ThouShaltNotKill"),
        ("THOUSHALTNOTKILL", "ThouShaltNotKill"),
        ("FighterSoul", "FightersSoul"),
        ("FIGHTERSOUL", "FightersSoul"),
        ("Frenzy", "BloodFrenzy"),
        ("FRENZY", "BloodFrenzy"),
    ]
    for raw, expect in canon_cases:
        got = get_canonical_passive_code(raw)
        ok = got == expect
        failed += not ok
        print(("OK " if ok else "FAIL"), "canon", raw, "=>", got, "expected", expect)

    resolve_cases = [
        ("ThouShaltNotKill", "thoushaltnotkill.png"),
        ("THOUSHALTNOTKILL", "thoushaltnotkill.png"),
        ("FighterSoul", "fighterssoul.png"),
        ("FIGHTERSOUL", "fighterssoul.png"),
        ("FightersSoul", "fighterssoul.png"),
        ("Frenzy", "bloodfrenzy.png"),
        ("JaggedEdge", "jaggededges.png"),
    ]
    for raw, expect in resolve_cases:
        got = _bn(resolve_icon_path(ICONS, raw, FB))
        ok = got == expect
        failed += not ok
        print(("OK " if ok else "FAIL"), "icon", raw, "=>", got, "expected", expect)

    # end-to-end: display string → extract → canon → file
    disp = "★ [牧师] 不可杀生 (ThouShaltNotKill) - 敌人击倒其他单位时，它会受到10点神圣伤害。"
    code = get_canonical_passive_code(extract_skill_code(disp))
    icon = _bn(resolve_icon_path(ICONS, code, FB))
    ok = code == "ThouShaltNotKill" and icon == "thoushaltnotkill.png"
    failed += not ok
    print(("OK " if ok else "FAIL"), "e2e 不可杀生", code, icon)

    # catalog dedupe: exact key + leftover alias
    raw = [
        {"key": "ThouShaltNotKill", "name": "不可杀生", "name_en": "Thou Shalt Not Kill", "desc": "A", "has_icon": True},
        {"key": "ThouShaltNotKill", "name": "ThouShaltNotKill", "name_en": "ThouShaltNotKill", "desc": "", "has_icon": True},
        {"key": "FighterSoul", "name": "战士之魂", "name_en": "Fighter's Soul", "desc": "升级时还会出现战士能力。", "has_icon": False},
        {"key": "FightersSoul", "name": "FightersSoul", "name_en": "FightersSoul", "desc": "", "has_icon": True},
    ]
    out = dedupe_catalog_items(raw, canonicalize=get_canonical_passive_code)
    keys = [it["key"] for it in out]
    thou = next(it for it in out if it["key"] == "ThouShaltNotKill")
    soul = next(it for it in out if it["key"] == "FightersSoul")
    ok = (
        keys.count("ThouShaltNotKill") == 1
        and "FighterSoul" not in keys
        and keys.count("FightersSoul") == 1
        and thou["name"] == "不可杀生"
        and soul["name"] == "战士之魂"
        and soul.get("has_icon") is True
    )
    failed += not ok
    print(("OK " if ok else "FAIL"), "dedupe", keys, thou["name"], soul["name"])

    cat = json.load(open(os.path.join(ROOT, "assets", "passives_catalog.json"), encoding="utf-8"))
    cat_keys = [it["key"] for it in cat]
    ok = cat_keys.count("ThouShaltNotKill") == 1 and "FighterSoul" not in cat_keys
    failed += not ok
    print(("OK " if ok else "FAIL"), "catalog file 不可杀生", cat_keys.count("ThouShaltNotKill"), "FighterSoul" in cat_keys)

    if failed:
        print(f"\n{failed} FAILED")
        sys.exit(1)
    print("\nall passed")


if __name__ == "__main__":
    main()
