# -*- coding: utf-8 -*-
"""用 mewcodex beta 中文补丁 combined.csv 回填疾病目录的中文名和完整描述。
来源：https://github.com/mewcodex/Mewgenics-Chinese-Translation （尚未合入主游戏）
"""
import csv
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CANDIDATES = [
    os.environ.get("MEW_ZH_CSV") or "",
    os.path.join(ROOT, "tools", "_zh_mewcodex", "Mewgenics_CN_patch", "data", "text", "combined.csv"),
    os.path.join(ROOT, "game_assets", "data", "text", "combined.csv"),
]
OFFICIAL = next((p for p in _CANDIDATES if p and os.path.exists(p)), "")
if not OFFICIAL:
    raise SystemExit("找不到 mewcodex combined.csv，请设置 MEW_ZH_CSV")

rows = list(csv.reader(open(OFFICIAL, encoding="utf-8-sig", newline="")))
header = [h.strip().lower() for h in rows[0]]
zi = next(header.index(c) for c in ("zh", "zh-cn", "schinese") if c in header)
ei = header.index("en")
official = {}
for r in rows[1:]:
    if not r or not r[0] or r[0].startswith("//"):
        continue
    official[r[0]] = {
        "en": (r[ei] if ei < len(r) else "").strip(),
        "zh": (r[zi] if zi < len(r) else "").strip(),
    }

wiki_path = os.path.join(ROOT, "wiki_data", "passives_combined.json")
wiki = {}
if os.path.exists(wiki_path):
    for p in json.load(open(wiki_path, encoding="utf-8")).get("passives", []):
        if p.get("passive_class") != "Disorder":
            continue
        wiki[p.get("passive_code")] = p


def pick_text(key, wiki_zh="", wiki_en=""):
    pair = official.get(key) or {}
    zh = (pair.get("zh") or "").strip()
    en = (pair.get("en") or "").strip()
    if zh:
        return zh
    if wiki_zh:
        return wiki_zh
    return en or wiki_en


def name_keys(code, desc_key):
    keys = []
    if desc_key:
        keys.append(desc_key.replace("_DESC", "_NAME").replace("_DESCRIPTION", "_NAME"))
    up = (code or "").upper()
    keys.append(f"DISORDER_{up}_NAME")
    keys.append(f"DISORDER_{up}_DESC")  # last resort not used for name
    return keys


dis_path = os.path.join(ROOT, "assets", "disorders_catalog.json")
catalog = json.load(open(dis_path, encoding="utf-8"))
updated = 0
still_en = []
for item in catalog:
    code = item.get("key")
    w = wiki.get(code) or {}
    desc_key = w.get("desc_key") or f"DISORDER_{code.upper()}_DESC"
    name_key = None
    for cand in name_keys(code, desc_key):
        if cand.endswith("_NAME") and official.get(cand, {}).get("zh"):
            name_key = cand
            break
    if not name_key:
        name_key = (desc_key or "").replace("_DESC", "_NAME").replace("_DESCRIPTION", "_NAME")

    wiki_name = (w.get("passive_name_texts") or {}).get("zh") or ""
    wiki_desc = (w.get("description_texts") or {}).get("zh") or ""
    wiki_en_desc = (w.get("description_texts") or {}).get("en") or w.get("description") or ""

    new_name = pick_text(name_key, wiki_name, item.get("name_en") or code)
    new_desc = pick_text(desc_key, wiki_desc, wiki_en_desc or item.get("desc") or "")
    pair_name = official.get(name_key) or {}
    pair_desc = official.get(desc_key) or {}
    new_name_en = (pair_name.get("en") or (w.get("passive_name_texts") or {}).get("en") or item.get("name_en") or code).strip()
    new_desc_en = (pair_desc.get("en") or wiki_en_desc or "").strip()
    if new_name and new_name != item.get("name"):
        item["name"] = new_name
        updated += 1
    if new_desc and new_desc != item.get("desc"):
        item["desc"] = new_desc
        updated += 1
    item["name_en"] = new_name_en
    item["desc_en"] = new_desc_en
    if new_desc and re.match(r"^[A-Za-z]", new_desc):
        still_en.append(code)

json.dump(catalog, open(dis_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"disorders_catalog: {len(catalog)} entries, {updated} field updates, still-english {still_en}")

pas_path = os.path.join(ROOT, "assets", "passives_catalog.json")
pas = json.load(open(pas_path, encoding="utf-8"))
dmap = {d["key"]: d for d in catalog}
n = 0
for item in pas:
    d = dmap.get(item.get("key"))
    if not d:
        continue
    item["name"] = d["name"]
    item["name_en"] = d.get("name_en") or item.get("name_en")
    item["desc"] = d["desc"]
    item["desc_en"] = d.get("desc_en") or ""
    item["class"] = "Disorder"
    item["class_name"] = "疾病缺陷"
    n += 1
json.dump(pas, open(pas_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"passives_catalog: synced {n} disorder rows")

inv = dmap.get("Invincible") or {}
print("--- Invincible ---")
print("name:", inv.get("name"), "/", inv.get("name_en"))
print("desc_zh:", inv.get("desc"))
print("desc_en:", inv.get("desc_en"))
