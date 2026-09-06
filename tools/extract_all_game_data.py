import struct
import json
import os
import re
import csv

gpak_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\resources.gpak'
csv_dir = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\_archived_csv'

game_data = {
    'classes': [
        'Colorless', 'Fighter', 'Mage', 'Hunter', 'Tank', 'Medic',
        'Thief', 'Necromancer', 'Butcher', 'Druid', 'Monk', 'Psychic',
        'Tinkerer', 'Jester'
    ],
    'abilities': [],
    'passives': [],
    'mutations': {},
    'items': [],
    'voices': [
        'male55', 'male109', 'male53', 'male59', 'male105', 'male22',
        'female50', 'female57', 'female102', 'female35',
        'spidercat', 'demoncat', 'robotcat'
    ]
}

# 1. Extract from archived CSVs
# Abilities
ab_path = os.path.join(csv_dir, 'abilities.csv')
if os.path.exists(ab_path):
    with open(ab_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].startswith('ABILITY_') and row[0].endswith('_NAME'):
                key = row[0][8:-5]
                name_en = row[1] if len(row) > 1 else key
                game_data['abilities'].append({'key': key, 'name': name_en})

# Passives
pass_path = os.path.join(csv_dir, 'passives.csv')
if os.path.exists(pass_path):
    with open(pass_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].startswith('PASSIVE_') and row[0].endswith('_NAME'):
                key = row[0][8:-5]
                name_en = row[1] if len(row) > 1 else key
                game_data['passives'].append({'key': key, 'name': name_en})

# Items
item_path = os.path.join(csv_dir, 'items.csv')
if os.path.exists(item_path):
    with open(item_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].startswith('ITEM_') and row[0].endswith('_NAME'):
                key = row[0][5:-5]
                name_en = row[1] if len(row) > 1 else key
                game_data['items'].append({'key': key, 'name': name_en})

# 2. Extract mutations from gpak
with open(gpak_path, 'rb') as f:
    num_files = struct.unpack('<I', f.read(4))[0]
    files = []
    for i in range(num_files):
        fn_len = struct.unpack('<H', f.read(2))[0]
        fn = f.read(fn_len).decode('utf-8', errors='replace')
        f_size = struct.unpack('<I', f.read(4))[0]
        files.append((fn, f_size))
    data_start = f.tell()

offset = data_start
gpak_manifest = {}
for fn, fsz in files:
    gpak_manifest[fn] = (offset, fsz)
    offset += fsz

parts = ['body', 'ears', 'eyebrows', 'eyes', 'head', 'legs', 'mouth', 'tail', 'texture']
with open(gpak_path, 'rb') as f:
    for p in parts:
        gpath = f'data/mutations/{p}.gon'
        if gpath in gpak_manifest:
            off, sz = gpak_manifest[gpath]
            f.seek(off)
            content = f.read(sz).decode('utf-8', errors='replace')
            # parse entries: number { ... }
            mut_list = []
            matches = re.finditer(r'^\s*([0-9]+)\s*\{(?:\s*//([^\n\r]+))?', content, re.MULTILINE)
            for m in matches:
                mut_id = int(m.group(1))
                comment = m.group(2).strip() if m.group(2) else f"{p.capitalize()} #{mut_id}"
                mut_list.append({'id': mut_id, 'name': comment})
            game_data['mutations'][p] = mut_list

output_json = 'mewgenics_game_data.json'
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(game_data, f, indent=2, ensure_ascii=False)

print(f"Extracted game data into {output_json}:")
print(f"  Abilities: {len(game_data['abilities'])}")
print(f"  Passives: {len(game_data['passives'])}")
print(f"  Items: {len(game_data['items'])}")
for p, ml in game_data['mutations'].items():
    print(f"  Mutations ({p}): {len(ml)}")
