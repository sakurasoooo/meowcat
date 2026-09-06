# -*- coding: utf-8 -*-
"""Rewrite passives_catalog.json: drop exact duplicates and leftover alias keys."""
import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from mewgenics_core import get_canonical_passive_code, dedupe_catalog_items
from picker_dialog import resolve_icon_path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "assets", "passives_catalog.json")
ICONS = os.path.join(ROOT, "assets", "icons", "passives")
FB = os.path.join(ROOT, "assets", "icons", "fallback.png")


def main():
    items = json.load(open(CAT, encoding="utf-8"))
    before = len(items)
    keys_before = [it.get("key") for it in items]
    thou_before = sum(1 for k in keys_before if k == "ThouShaltNotKill")
    soul_before = sum(1 for k in keys_before if k and "soul" in k.lower() and "void" not in k.lower())

    deduped = dedupe_catalog_items(items, canonicalize=get_canonical_passive_code)
    for it in deduped:
        p = resolve_icon_path(ICONS, it["key"], FB)
        it["has_icon"] = bool(p and os.path.basename(p) != "fallback.png")

    with open(CAT, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2, ensure_ascii=False)
        f.write("\n")

    keys_after = [it.get("key") for it in deduped]
    thou_after = sum(1 for k in keys_after if k == "ThouShaltNotKill")
    leftover = [k for k in ("FighterSoul", "HunterSoul", "Frenzy", "JaggedEdge") if k in keys_after]
    print(f"entries {before} -> {len(deduped)}")
    print(f"unique keys {len(set(keys_before))} -> {len(set(keys_after))}")
    print(f"ThouShaltNotKill count {thou_before} -> {thou_after}")
    print(f"soul-like keys before {soul_before} after {sum(1 for k in keys_after if k and 'soul' in k.lower() and 'void' not in k.lower())}")
    print(f"leftover alias keys remaining: {leftover}")
    thou = next(it for it in deduped if it["key"] == "ThouShaltNotKill")
    print("不可杀生:", thou.get("name"), "has_icon", thou.get("has_icon"))
    fs = next((it for it in deduped if it["key"] == "FightersSoul"), None)
    print("战士之魂:", None if not fs else (fs.get("name"), fs.get("has_icon")))


if __name__ == "__main__":
    main()
