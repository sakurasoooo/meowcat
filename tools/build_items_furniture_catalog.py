import os
import sys
import csv
import json

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI_CSV_DIR = os.path.join(BASE_DIR, "wiki_data", "csv")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

ITEMS_CSV = os.path.join(WIKI_CSV_DIR, "items.csv")
FURNITURE_CSV = os.path.join(WIKI_CSV_DIR, "furniture.csv")

def build_items():
    if not os.path.exists(ITEMS_CSV):
        print(f"Error: {ITEMS_CSV} not found")
        return []
    
    with open(ITEMS_CSV, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    items_catalog = []
    for r in rows:
        # Handle BOM
        code = r.get('\ufeffitem_code') or r.get('item_code') or ''
        if not code:
            continue
        kind = (r.get('kind') or '').strip().lower()
        rarity = (r.get('rarity') or '').strip().lower()
        name_zh = (r.get('name_zh') or '').strip()
        name_en = (r.get('name_en') or '').strip()
        desc_zh = (r.get('desc_zh') or '').strip()
        desc_en = (r.get('desc_en') or '').strip()
        sets = (r.get('sets') or '').strip()
        stats = (r.get('stats') or '').strip()
        dur = (r.get('durability') or '').strip()
        cursed = (r.get('cursed') or '').strip().lower() == 'true'
        icon_local = (r.get('icon_local') or '').replace('\\', '/')

        items_catalog.append({
            'key': code,
            'name': name_zh or name_en or code,
            'name_en': name_en or code,
            'kind': kind,
            'rarity': rarity,
            'desc': desc_zh or desc_en or '',
            'sets': sets,
            'stats': stats,
            'durability': dur,
            'cursed': cursed,
            'icon_rel': icon_local,
            'has_icon': bool(icon_local and os.path.exists(os.path.join(BASE_DIR, "wiki_data", icon_local)))
        })

    out_path = os.path.join(ASSETS_DIR, "items_catalog.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(items_catalog, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {len(items_catalog)} items to {out_path}")
    return items_catalog

def build_furniture():
    if not os.path.exists(FURNITURE_CSV):
        print(f"Error: {FURNITURE_CSV} not found")
        return []
    
    with open(FURNITURE_CSV, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    furn_catalog = []
    for r in rows:
        code = r.get('\ufefffurniture_code') or r.get('furniture_code') or ''
        if not code:
            continue
        name_zh = (r.get('name_zh') or '').strip()
        name_en = (r.get('name_en') or '').strip()
        desc_zh = (r.get('desc_zh') or '').strip()
        desc_en = (r.get('desc_en') or '').strip()
        f_set = (r.get('set') or '').strip().lower()
        stats = (r.get('stats') or '').strip()
        special = (r.get('special') or '').strip().lower() == 'true'
        icon_local = (r.get('icon_local') or '').replace('\\', '/')

        furn_catalog.append({
            'key': code,
            'name': name_zh or name_en or code,
            'name_en': name_en or code,
            'set': f_set or 'none',
            'desc': desc_zh or desc_en or '',
            'stats': stats,
            'special': special,
            'icon_rel': icon_local,
            'has_icon': bool(icon_local and os.path.exists(os.path.join(BASE_DIR, "wiki_data", icon_local)))
        })

    out_path = os.path.join(ASSETS_DIR, "furniture_catalog.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(furn_catalog, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {len(furn_catalog)} furniture items to {out_path}")
    return furn_catalog

if __name__ == '__main__':
    print("=== Building Items & Furniture Catalogs ===")
    os.makedirs(ASSETS_DIR, exist_ok=True)
    build_items()
    build_furniture()
    print("🎉 Done! 🎉")
