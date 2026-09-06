"""将 wiki_data CSV 的中文字段与游戏官方中文补丁 (data/text/combined.csv) 对齐。

映射规则（已验证）:
  items.csv      ITEM_<CODE大写>_NAME / _DESC
  furniture.csv  FURNITURE_NAME_<CODE大写> / FURNITURE_DESC_<CODE大写>
  abilities.csv  ABILITY_<CODE大写>_NAME / _DESC（升级版 <CODE>2_DESC 尝试填 desc_upgraded）
  passives.csv   PASSIVE_<CODE大写>_NAME / _DESC（升级版同理）
  characters.csv characters_db.json 的 name_key / tooltip_key（最可靠）
  mutations.csv  去掉 "Body 300: " 前缀后按官方英文唯一匹配
  weather.csv    行内 name_key / desc_key 列直查

无匹配时保留原值。输出各文件对齐覆盖率统计。
"""
import csv, json, os, re, sys, io
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFFICIAL = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\data\text\combined.csv'
if not os.path.exists(OFFICIAL):
    OFFICIAL = os.path.join(ROOT, 'game_assets', 'data', 'text', 'combined.csv')

# ---------- 载入官方文本 ----------
rows = list(csv.reader(open(OFFICIAL, encoding='utf-8-sig', newline='')))
header = [h.strip().lower() for h in rows[0]]
zh_i = header.index('zh')
en_i = header.index('en')
key2zh, key2en = {}, {}
en2zh = defaultdict(list)   # 英文 -> [(zh, key)]
for r in rows[1:]:
    if len(r) <= zh_i or not r[0] or r[0].startswith('//'):
        continue
    key2zh[r[0]] = r[zh_i].strip()
    key2en[r[0]] = r[en_i].strip()
    if r[en_i].strip() and r[zh_i].strip():
        en2zh[r[en_i].strip().lower()].append((r[zh_i].strip(), r[0]))
en2zh_uniq = {k: v[0][0] for k, v in en2zh.items() if len(v) == 1}
print(f'官方文本: {len(key2zh)} keys, 唯一英文匹配 {len(en2zh_uniq)} 条')

stats = {}

def align(path, name_fn, desc_fn, upgraded_fn=None, name_col='name_zh', desc_col='desc_zh'):
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig', newline='')))
    fields = list(rows[0].keys())
    n_name = n_desc = n_up = 0
    for r in rows:
        nk = name_fn(r)
        if nk and key2zh.get(nk) and name_col in fields:
            r[name_col] = key2zh[nk]
            n_name += 1
        dk = desc_fn(r)
        if dk and key2zh.get(dk) and desc_col in fields:
            r[desc_col] = key2zh[dk]
            n_desc += 1
        if upgraded_fn:
            uk = upgraded_fn(r)
            if uk and key2zh.get(uk):
                r['desc_upgraded_zh'] = key2zh[uk]
                n_up += 1
    total = len(rows)
    stats[os.path.basename(path)] = (total, n_name, n_desc, n_up)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

csvdir = os.path.join(ROOT, 'wiki_data', 'csv')

# items
align(os.path.join(csvdir, 'items.csv'),
      lambda r: f"ITEM_{r['item_code'].upper()}_NAME",
      lambda r: f"ITEM_{r['item_code'].upper()}_DESC")
# furniture
align(os.path.join(csvdir, 'furniture.csv'),
      lambda r: f"FURNITURE_NAME_{r['furniture_code'].upper()}",
      lambda r: f"FURNITURE_DESC_{r['furniture_code'].upper()}")
# abilities
align(os.path.join(csvdir, 'abilities.csv'),
      lambda r: f"ABILITY_{r['ability_code'].upper()}_NAME",
      lambda r: f"ABILITY_{r['ability_code'].upper()}_DESC")
# passives (+ upgraded)
align(os.path.join(csvdir, 'passives.csv'),
      lambda r: f"PASSIVE_{r['passive_code'].upper()}_NAME",
      lambda r: f"PASSIVE_{r['passive_code'].upper()}_DESC",
      upgraded_fn=lambda r: f"PASSIVE_{r['passive_code'].upper()}2_DESC" if r.get('has_upgrade') in ('1', 'true', 'True') else None)
# characters via db keys
db = json.load(open(os.path.join(ROOT, 'wiki_data', 'characters_db.json'), encoding='utf-8-sig'))
keymap = {c['character_key']: (c.get('name_key'), c.get('tooltip_key')) for c in db['characters']}
align(os.path.join(csvdir, 'characters.csv'),
      lambda r: keymap.get(r['character_key'], (None,))[0],
      lambda r: keymap.get(r['character_key'], (None, None))[1],
      name_col='name_zh', desc_col='tooltip_zh')
# mutations: 描述按 MUTATION_<部位大写>_<ID>_DESC 键直查（官方无逐部位名字文本）
align(os.path.join(csvdir, 'mutations.csv'),
      lambda r: None,
      lambda r: f"MUTATION_{r['part'].upper()}_{r['mutation_id']}_DESC",
      name_col='display_name', desc_col='desc_zh')
# weather: 行内 key 直查（列名为 name_texts_zh / desc_texts_zh）
align(os.path.join(csvdir, 'weather.csv'),
      lambda r: r.get('name_key') or None,
      lambda r: r.get('desc_key') or None,
      name_col='name_texts_zh', desc_col='desc_texts_zh')

print()
print(f"{'文件':<22}{'行数':>6}{'名字对齐':>10}{'描述对齐':>10}{'升级对齐':>10}")
for fn, (t, n, d, u) in stats.items():
    print(f'{fn:<24}{t:>6}{n:>10}{d:>10}{u:>10}')
