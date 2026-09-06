"""Crawl mewcodex.github.io wiki images + build labeled CSVs for editor integration.

Inputs : wiki_data/*.json  (already downloaded)
Outputs: wiki_data/images/<relpath>.png
         wiki_data/csv/<category>.csv  + all_images.csv (master index)
"""
import csv, json, os, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = 'https://mewcodex.github.io/'
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'wiki_data')
IMG_DIR = os.path.join(ROOT, 'images')
CSV_DIR = os.path.join(ROOT, 'csv')
os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)

def load(name):
    with open(os.path.join(ROOT, name + '.json'), encoding='utf-8') as f:
        return json.load(f)

def texts(entry, key):
    """Return (en, zh) from a *_texts dict field."""
    t = entry.get(key) or {}
    if isinstance(t, dict):
        return t.get('en', ''), t.get('zh', '')
    return (entry.get(key.replace('_texts', ''), '') or ''), ''

def j(o):
    return json.dumps(o, ensure_ascii=False) if o not in (None, '', [], {}) else ''

# ---------------- collect download tasks ----------------
# rel -> local abs path
downloads = {}

def add(rel):
    if rel:
        downloads[rel.replace('\\', '/').lstrip('/')] = True

rows = {}  # category -> list of dict rows

# ---- characters ----
chars = load('characters_db')['characters']
rows['characters'] = []
for c in chars:
    en, zh = texts(c, 'name_texts')
    ten, tzh = texts(c, 'tooltip_texts')
    rel = c.get('image_path')
    add(rel)
    rows['characters'].append({
        'character_key': c.get('character_key', ''),
        'variant_of': c.get('variant_of') or '',
        'name_en': en, 'name_zh': zh,
        'tooltip_en': ten, 'tooltip_zh': tzh,
        'movieclip': c.get('movieclip', ''),
        'sprite_id': c.get('image_sprite_id', ''),
        'icon_url': rel or '',
        'icon_local': os.path.join('images', rel).replace('/', os.sep) if rel else '',
    })

# ---- furniture ----
furn = load('furniture_db')
rows['furniture'] = []
for f_ in furn:
    en, zh = texts(f_, 'name_texts')
    den, dzh = texts(f_, 'desc_texts')
    sid = f_.get('sprite_id')
    frames = f_.get('image_frames') or [1]
    rels = []
    for fr in frames:
        rel = f'FurnitureIcon/{sid}/{fr}.png'
        add(rel)
        rels.append(rel)
    rows['furniture'].append({
        'furniture_code': f_.get('furniture_code', ''),
        'name_en': en, 'name_zh': zh,
        'desc_en': den, 'desc_zh': dzh,
        'set': f_.get('set') or '',
        'special': f_.get('special') or '',
        'can_be_rare': f_.get('can_be_rare', ''),
        'removed': f_.get('removed', ''),
        'stats': j(f_.get('stats')),
        'sprite_id': sid,
        'icon_url': rels[0] if rels else '',
        'icon_frames': ';'.join(rels),
        'icon_local': os.path.join('images', rels[0]).replace('/', os.sep) if rels else '',
    })

# ---- passives ----
pas = load('passives_combined')['passives']
if isinstance(pas, dict):
    pas = list(pas.values())
rows['passives'] = []
for p in pas:
    en, zh = texts(p, 'passive_name_texts')
    den, dzh = texts(p, 'description_texts')
    d2en, d2zh = texts(p, 'description2_texts')
    fr = p.get('frame_number')
    rel = f'PassiveIcon/{fr}.png' if isinstance(fr, int) else ''
    add(rel)
    rows['passives'].append({
        'passive_code': p.get('passive_code', ''),
        'passive_class': p.get('passive_class') or '',
        'name_en': en, 'name_zh': zh,
        'desc_en': den, 'desc_zh': dzh,
        'desc_upgraded_en': d2en, 'desc_upgraded_zh': d2zh,
        'has_upgrade': p.get('has_upgrade', ''),
        'frame_number': fr if isinstance(fr, int) else '',
        'icon_url': rel,
        'icon_local': os.path.join('images', rel).replace('/', os.sep) if rel else '',
    })

# ---- abilities ----
abs_ = load('abilities_combined')['abilities']
if isinstance(abs_, dict):
    abs_ = list(abs_.values())
rows['abilities'] = []
for a in abs_:
    en, zh = texts(a, 'ability_name_texts')
    den, dzh = texts(a, 'description_texts')
    fr = a.get('frame_number')
    rel = f'AbilityIcon/{fr}.png' if isinstance(fr, int) else ''
    add(rel)
    rows['abilities'].append({
        'ability_code': a.get('ability_code') or '',
        'name_en': en or (a.get('ability_name') if a.get('ability_name') != 'None' else ''),
        'name_zh': zh,
        'desc_en': den, 'desc_zh': dzh,
        'type_icon': a.get('type_icon') or '',
        'frame_number': fr if isinstance(fr, int) else '',
        'icon_url': rel,
        'icon_local': os.path.join('images', rel).replace('/', os.sep) if rel else '',
    })

# ---- items ----
KIND_FOLDER = {'trinket': 'TrinketIcon', 'weapon': 'WeaponIcon', 'neck': 'NeckItemIcon',
               'face': 'FaceItemIcon', 'head': 'HeadItemIcon'}
items = load('items_db')
rows['items'] = []
for it in items:
    en, zh = texts(it, 'item_name_texts')
    den, dzh = texts(it, 'description_texts')
    fr = it.get('frame')
    folder = KIND_FOLDER.get(it.get('kind'), 'TrinketIcon')
    rel = f'{folder}/{fr}.png' if isinstance(fr, int) else ''
    add(rel)
    rows['items'].append({
        'item_code': it.get('item_code', ''),
        'kind': it.get('kind', ''),
        'rarity': it.get('rarity', ''),
        'name_en': en, 'name_zh': zh,
        'desc_en': den, 'desc_zh': dzh,
        'sets': ';'.join(it.get('sets') or []),
        'stats': j(it.get('stats')),
        'durability': it.get('durability') if it.get('durability') is not None else '',
        'cursed': it.get('cursed', ''),
        'frame': fr if isinstance(fr, int) else '',
        'icon_url': rel,
        'icon_local': os.path.join('images', rel).replace('/', os.sep) if rel else '',
    })

# ---- mutations (no icons on wiki; cat-part appearance lives in swfs/catparts.swf) ----
muts = load('mutations_combined')['mutations']
if isinstance(muts, dict):
    muts = list(muts.values())
rows['mutations'] = []
for m in muts:
    plen, plzh = texts(m, 'part_label_texts')
    den, dzh = texts(m, 'description_texts')
    rows['mutations'].append({
        'mutation_id': m.get('mutation_id', ''),
        'part': m.get('part', ''),
        'display_name': m.get('display_name', ''),
        'part_label_en': plen, 'part_label_zh': plzh,
        'desc_en': den, 'desc_zh': dzh,
        'stats': j(m.get('stats')),
        'is_birth_defect': m.get('is_birth_defect', ''),
        'source_file': m.get('source_file', ''),
    })

# ---- events ----
evs = load('events_combined')
evs = evs.get('events', evs)
if isinstance(evs, dict):
    evs = list(evs.values())
rows['events'] = []
for e in evs:
    ten, tzh = texts(e, 'title_texts')
    pen, pzh = texts(e, 'main_prompt_texts')
    rows['events'].append({
        'event_key': e.get('event_key', ''),
        'title_en': ten, 'title_zh': tzh,
        'prompt_en': pen, 'prompt_zh': pzh,
        'options': j(e.get('options')),
        'source_file': e.get('source_file', ''),
    })

# ---- weather ----
wea = load('weather_db')
if isinstance(wea, dict):
    wea = wea.get('weather', wea.get('weathers', list(wea.values())))
rows['weather'] = []
for w in wea:
    if not isinstance(w, dict):
        continue
    row = {'weather_key': w.get('weather_key', w.get('key', w.get('name', '')))}
    for k, v in w.items():
        if isinstance(v, dict) and 'en' in v:
            row[k + '_en'], row[k + '_zh'] = v.get('en', ''), v.get('zh', '')
        elif not isinstance(v, (dict, list)):
            row[k] = v
        else:
            row[k] = j(v)
    rows['weather'].append(row)

# ---- achievements (quest -> unlock refs; codes join with items/passives CSVs) ----
ach = load('achievements_tables')['tables']
rows['achievements'] = []

def emit_ach(table, quest_key, purpose, refs, extra=None):
    refs = refs or []
    if not refs:
        refs = [{'type': '', 'code': ''}]
    for r in refs:
        rows['achievements'].append({
            'table': table,
            'quest_key': quest_key,
            'purpose': purpose or '',
            'ref_type': r.get('type', '') if isinstance(r, dict) else '',
            'ref_code': r.get('code', '') if isinstance(r, dict) else str(r),
            'extra': j(extra) if extra else '',
        })

for table_name, tbl in ach.items():
    if not isinstance(tbl, dict):
        continue
    purpose = tbl.get('purpose', '')
    if isinstance(tbl.get('rows'), list):                      # box_unlocks
        for i, r in enumerate(tbl['rows']):
            emit_ach(table_name, f'difficulty_{r.get("difficulty", i)}', purpose, r.get('refs'), r)
    if isinstance(tbl.get('quest_unlocks'), dict):             # boss_unlocks
        for qk, qv in tbl['quest_unlocks'].items():
            emit_ach(table_name, qk, purpose, qv.get('refs'), qv)
    if isinstance(tbl.get('refs'), list):                      # other_main_quests
        emit_ach(table_name, table_name, purpose, tbl['refs'])
    for pool_key in ('main_pool', 'reward_overrides'):         # beanies_quests
        pool = tbl.get(pool_key)
        if isinstance(pool, dict):
            for qk, qv in pool.items():
                emit_ach(table_name, qk, pool_key, qv.get('refs') if isinstance(qv, dict) else None, qv)
        elif isinstance(pool, list):
            for i, qv in enumerate(pool):
                emit_ach(table_name, f'{pool_key}_{i}', pool_key, qv.get('refs') if isinstance(qv, dict) else None, qv)
    if tbl.get('extra_quest_icons'):                           # icon refs (frame numbers)
        emit_ach(table_name, 'extra_quest_icons', 'icons', tbl['extra_quest_icons'])

# ---------------- download images ----------------
def fetch(rel):
    dest = os.path.join(IMG_DIR, rel.replace('/', os.sep))
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return rel, True, 'cached'
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    url = BASE + urllib.parse.quote(rel)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'meowcat-wiki-crawler/1.0'})
        with urllib.request.urlopen(req, timeout=30) as r, open(dest, 'wb') as out:
            out.write(r.read())
        return rel, True, 'ok'
    except Exception as ex:
        return rel, False, str(ex)

import urllib.parse
rels = sorted(downloads)
print(f'downloading {len(rels)} images ...')
ok, fail = 0, []
with ThreadPoolExecutor(max_workers=16) as ex:
    futs = [ex.submit(fetch, r) for r in rels]
    for i, fut in enumerate(as_completed(futs), 1):
        rel, success, msg = fut.result()
        if success:
            ok += 1
        else:
            fail.append((rel, msg))
        if i % 200 == 0:
            print(f'  {i}/{len(rels)} ...')
print(f'downloaded: {ok}, failed: {len(fail)}')
for rel, msg in fail[:20]:
    print('  FAIL', rel, msg)

# ---------------- write CSVs ----------------
total_rows = 0
for cat, cat_rows in rows.items():
    if not cat_rows:
        continue
    # union of keys, stable order
    keys = []
    for r in cat_rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    path = os.path.join(CSV_DIR, f'{cat}.csv')
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        wcsv = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
        wcsv.writeheader()
        wcsv.writerows(cat_rows)
    total_rows += len(cat_rows)
    print(f'csv: {cat}.csv ({len(cat_rows)} rows)')

# master image index
with open(os.path.join(CSV_DIR, 'all_images.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    wcsv = csv.writer(f)
    wcsv.writerow(['image_relpath', 'local_path', 'downloaded'])
    for rel in rels:
        dest = os.path.join(IMG_DIR, rel.replace('/', os.sep))
        wcsv.writerow([rel, os.path.join('images', rel).replace('/', os.sep),
                       '1' if os.path.exists(dest) else '0'])
print(f'master index: all_images.csv ({len(rels)} images); total csv rows: {total_rows}')
