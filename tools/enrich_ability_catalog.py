"""把 wiki abilities_combined.json 的类型/元素标签/伤害字段合并进 assets/abilities_catalog.json。

新增字段（供 SkillCardWidget 显示）:
  type_icon  能力类型图标 (melee/ranged/magic/heal/...)
  elements  元素标签小写列表 (water/fire/...) -> 对应 assets/icons/tags/<e>.png
  damage  伤害公式文本（damage.value 优先，其次 icon_damage_display）
"""
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

wiki = json.load(open(os.path.join(ROOT, 'wiki_data', 'abilities_combined.json'), encoding='utf-8-sig'))
comb = {a['ability_code']: a for a in wiki['abilities'] if a.get('ability_code')}
cat_path = os.path.join(ROOT, 'assets', 'abilities_catalog.json')
cat = json.load(open(cat_path, encoding='utf-8'))

n_type = n_elem = n_dmg = 0
for item in cat:
    code = item['key']
    w = comb.get(code)
    if not w:
        continue
    t = w.get('type_icon')
    if t:
        item['type_icon'] = t
        n_type += 1
    elems = w.get('elements') or []
    if elems:
        item['elements'] = [str(e).lower() for e in elems]
        n_elem += 1
    dmg = None
    if w.get('damage') and w['damage'].get('value'):
        dmg = w['damage']['value']
    elif w.get('icon_damage_display'):
        dmg = w['icon_damage_display']
    if dmg:
        item['damage'] = dmg
        n_dmg += 1

with open(cat_path, 'w', encoding='utf-8') as f:
    json.dump(cat, f, ensure_ascii=False, indent=1)
print(f'abilities: {len(cat)} | 加类型 {n_type} | 加元素 {n_elem} | 加伤害 {n_dmg}')
