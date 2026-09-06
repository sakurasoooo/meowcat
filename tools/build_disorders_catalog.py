import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DATA_PATH = os.path.join(BASE_DIR, "mewgenics_game_data.json")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
PAS_DIR = os.path.join(ASSETS_DIR, "icons", "passives")

with open(GAME_DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

disorders = data.get('disorders', [])
disorders_catalog = []

for d in disorders:
    k = d['key']
    name = d.get('name', k)
    desc = d.get('desc', '').strip('"\r\n\t ')
    has_icon = os.path.exists(os.path.join(PAS_DIR, f"{k}.png"))
    disorders_catalog.append({
        'key': k,
        'name': name,
        'name_en': k,
        'desc': desc,
        'class': 'Disorder',
        'class_name': '疾病缺陷',
        'has_icon': has_icon
    })

dis_path = os.path.join(ASSETS_DIR, "disorders_catalog.json")
with open(dis_path, 'w', encoding='utf-8') as f:
    json.dump(disorders_catalog, f, indent=2, ensure_ascii=False)
print(f"Saved {len(disorders_catalog)} entries to {dis_path}")

# Update passives_catalog.json as well
pas_catalog_path = os.path.join(ASSETS_DIR, "passives_catalog.json")
if os.path.exists(pas_catalog_path):
    with open(pas_catalog_path, 'r', encoding='utf-8') as f:
        pas_cat = json.load(f)
    dis_map = {d['key']: d for d in disorders_catalog}
    updated = 0
    for item in pas_cat:
        if item['key'] in dis_map:
            d = dis_map[item['key']]
            item['name'] = d['name']
            item['desc'] = d['desc']
            item['class'] = 'Disorder'
            item['class_name'] = '疾病缺陷'
            updated += 1
    with open(pas_catalog_path, 'w', encoding='utf-8') as f:
        json.dump(pas_cat, f, indent=2, ensure_ascii=False)
    print(f"Updated {updated} disorder entries in {pas_catalog_path}")
