import os
import sys
import json
import struct
import re
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\10107\Documents\github\meowcat"
SWF_PATH = os.path.join(BASE_DIR, "ability_icons.swf")
SPRITES_DIR = os.path.join(BASE_DIR, "extracted_sprites")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICONS_AB_DIR = os.path.join(ASSETS_DIR, "icons", "abilities")
ICONS_PAS_DIR = os.path.join(ASSETS_DIR, "icons", "passives")
TERMS_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\terms.json"
GON_ABILITIES_DIR = os.path.join(BASE_DIR, "game_assets", "data", "abilities")

os.makedirs(ICONS_AB_DIR, exist_ok=True)
os.makedirs(ICONS_PAS_DIR, exist_ok=True)

# 1. Extract SWF frame labels
def get_swf_labels():
    with open(SWF_PATH, 'rb') as f:
        data = f.read()

    pos = 8
    first_byte = data[pos]
    nbits = first_byte >> 3
    pos += (5 + nbits * 4 + 7) // 8 + 4

    sprites = {}
    while pos < len(data):
        tag_h = struct.unpack('<H', data[pos:pos+2])[0]
        pos += 2
        t_type = tag_h >> 6
        t_len = tag_h & 0x3F
        if t_len == 0x3F:
            t_len = struct.unpack('<I', data[pos:pos+4])[0]
            pos += 4
        tag_data = data[pos:pos+t_len]
        if t_type == 39: # DefineSprite
            sid, fc = struct.unpack('<HH', tag_data[:4])
            sub_p = 4
            f_idx = 1
            frame_labels = {}
            while sub_p < len(tag_data):
                st_h = struct.unpack('<H', tag_data[sub_p:sub_p+2])[0]
                sub_p += 2
                st_type = st_h >> 6
                st_len = st_h & 0x3F
                if st_len == 0x3F:
                    st_len = struct.unpack('<I', tag_data[sub_p:sub_p+4])[0]
                    sub_p += 4
                sdata = tag_data[sub_p:sub_p+st_len]
                if st_type == 43: # FrameLabel
                    np = sdata.find(b'\x00')
                    lbl = sdata[:np].decode('utf-8', errors='replace')
                    frame_labels[f_idx] = lbl
                elif st_type == 1: # ShowFrame
                    f_idx += 1
                sub_p += st_len
            sprites[sid] = frame_labels
        pos += t_len
    return sprites.get(1346, {}), sprites.get(515, {})

# 2. Resize and save icon to 48x48
def process_and_save_icon(src_png, dest_png, target_size=(48, 48)):
    if not os.path.exists(src_png):
        return False
    try:
        with Image.open(src_png) as img:
            img = img.convert('RGBA')
            bbox = img.getbbox()
            if bbox:
                img = img.crop(bbox)
            
            # Scale maintaining aspect ratio, fitting within (target_size - 6px padding)
            max_dim = max(img.width, img.height)
            if max_dim > 0:
                inner_size = target_size[0] - 6 # 3px padding
                scale = inner_size / max_dim
                new_w = max(1, int(img.width * scale))
                new_h = max(1, int(img.height * scale))
                resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Canvas
                canvas = Image.new('RGBA', target_size, (0, 0, 0, 0))
                paste_x = (target_size[0] - new_w) // 2
                paste_y = (target_size[1] - new_h) // 2
                canvas.paste(resized, (paste_x, paste_y), resized)
                canvas.save(dest_png, 'PNG', optimize=True)
                return True
    except Exception as e:
        print(f"Error processing {src_png}: {e}")
    return False

COMBINED_CSV = os.path.join(BASE_DIR, "game_assets", "data", "text", "combined.csv")

def clean_game_text(text):
    if not text:
        return ""
    text = text.replace('\u200b', '')
    img_map = {
        '[img:shield]': '【护盾】',
        '[img:str]': '【力量】',
        '[img:dex]': '【敏捷】',
        '[img:con]': '【体质】',
        '[img:int]': '【智力】',
        '[img:spd]': '【速度】',
        '[img:cha]': '【魅力】',
        '[img:lck]': '【幸运】',
        '[img:mana]': '【魔能】',
        '[img:damage]': '【伤害】',
        '[img:health]': '【生命】',
        '[img:hp]': '【生命】',
        '[img:coin]': '【金币】',
        '[img:gold]': '【金币】',
    }
    for tag, rep in img_map.items():
        text = text.replace(tag, rep)
    # Remove BBCode tags like [s:.7], [/s], &nbsp;
    text = re.sub(r'\[/?[a-zA-Z0-9_\:\.]+\]', '', text)
    text = text.replace('&nbsp;', ' ')
    return text.strip()

# 3. Load combined.csv localization
def load_localization():
    terms_dict = {}
    if os.path.exists(COMBINED_CSV):
        import csv
        with open(COMBINED_CSV, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row or len(row) < 2:
                    continue
                k = row[0].strip().lstrip('\ufeff')
                en = row[1].strip() if len(row) > 1 else ""
                zh = row[11].strip() if len(row) > 11 and row[11].strip() else en
                terms_dict[k] = clean_game_text(zh) if zh else clean_game_text(en)
                
    # Fallback to terms.json
    if os.path.exists(TERMS_PATH):
        with open(TERMS_PATH, 'r', encoding='utf-8') as f:
            terms_list = json.load(f)
            for item in terms_list:
                skey = item.get('source_key', '')
                trans = item.get('translation', '')
                orig = item.get('original', '')
                if skey and skey not in terms_dict:
                    terms_dict[skey] = clean_game_text(trans or orig)
    return terms_dict

# 4. Parse GON ability files for metadata (class, mana, damage, range)
def parse_gon_abilities():
    catalog = {}
    if not os.path.exists(GON_ABILITIES_DIR):
        return catalog

    for fname in os.listdir(GON_ABILITIES_DIR):
        if not fname.endswith('.gon'):
            continue
        default_class = 'Colorless'
        if '_' in fname:
            c_prefix = fname.split('_')[0].capitalize()
            if c_prefix in ['Fighter', 'Mage', 'Hunter', 'Tank', 'Medic', 'Thief', 'Necromancer', 'Butcher', 'Druid', 'Monk', 'Psychic', 'Tinkerer', 'Jester']:
                default_class = c_prefix
        
        fpath = os.path.join(GON_ABILITIES_DIR, fname)
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        blocks = re.findall(r'(\b[a-zA-Z0-9_]+)\s*\{([^\{\}]*(?:\{[^\{\}]*\}[^\{\}]*)*)\}', content)
        for key, body in blocks:
            if key in ['meta', 'cost', 'target', 'damage_instance', 'sounds', 'graphics', 'tags']:
                continue
            
            meta_m = re.search(r'name\s+["\']?([^"\'\s\r\n]+)["\']?', body)
            desc_m = re.search(r'desc\s+["\']?([^"\'\s\r\n]+)["\']?', body)
            class_m = re.search(r'class\s+([a-zA-Z0-9_]+)', body)
            mana_m = re.search(r'mana\s+([0-9]+)', body)
            dmg_m = re.search(r'damage\s+([0-9\+\-a-zA-Z_]+)', body)
            range_m = re.search(r'range\s+([0-9]+)', body)
            var_of_m = re.search(r'variant_of\s+([a-zA-Z0-9_]+)', body)

            cls_name = class_m.group(1) if class_m else default_class
            if cls_name == 'MultiHitMeleeAttackAbility' or 'Ability' in cls_name:
                cls_name = default_class

            catalog[key] = {
                'key': key,
                'name_key': meta_m.group(1) if meta_m else f"ABILITY_{key.upper()}_NAME",
                'desc_key': desc_m.group(1) if desc_m else f"ABILITY_{key.upper()}_DESC",
                'class': cls_name,
                'mana': int(mana_m.group(1)) if mana_m else 0,
                'damage': dmg_m.group(1) if dmg_m else "",
                'range': int(range_m.group(1)) if range_m else 0,
                'variant_of': var_of_m.group(1) if var_of_m else ""
            }
    return catalog

def main():
    print("=== Step 1: Parsing SWF Frame Labels ===")
    ab_labels, pas_labels = get_swf_labels()
    print(f"Found {len(ab_labels)} ability labels, {len(pas_labels)} passive labels.")

    print("\n=== Step 2: Extracting & Normalizing Icons to 48x48 ===")
    # Abilities
    ab_src_dir = os.path.join(SPRITES_DIR, "DefineSprite_1346_AbilityIcon")
    ab_saved = 0
    for f_idx, lbl in ab_labels.items():
        if lbl == 'unknown':
            continue
        src = os.path.join(ab_src_dir, f"{f_idx}.png")
        dst = os.path.join(ICONS_AB_DIR, f"{lbl}.png")
        if process_and_save_icon(src, dst):
            ab_saved += 1
    print(f"✓ Saved {ab_saved} ability icons to {ICONS_AB_DIR}")

    # Passives
    pas_src_dir = os.path.join(SPRITES_DIR, "DefineSprite_515_PassiveIcon")
    pas_saved = 0
    for f_idx, lbl in pas_labels.items():
        if lbl == 'unknown':
            continue
        src = os.path.join(pas_src_dir, f"{f_idx}.png")
        dst = os.path.join(ICONS_PAS_DIR, f"{lbl}.png")
        if process_and_save_icon(src, dst):
            pas_saved += 1
    print(f"✓ Saved {pas_saved} passive icons to {ICONS_PAS_DIR}")

    # Create a default fallback icon
    fallback_img = Image.new('RGBA', (48, 48), (30, 41, 59, 255))
    fallback_path = os.path.join(ASSETS_DIR, "icons", "fallback.png")
    fallback_img.save(fallback_path, 'PNG')

    print("\n=== Step 3: Loading Localization and GON Data ===")
    loc_dict = load_localization()
    print(f"Loaded {len(loc_dict)} localization strings from terms.json.")
    gon_meta = parse_gon_abilities()
    print(f"Loaded {len(gon_meta)} ability metadata records from GON files.")

    # 4. Build rich catalog for all abilities in game_data
    with open(os.path.join(BASE_DIR, "mewgenics_game_data.json"), 'r', encoding='utf-8') as f:
        game_data = json.load(f)

    abilities_catalog = []
    seen_ab_keys = set()
    
    # Process game_data abilities
    for ab in game_data.get('abilities', []):
        k = ab['key']
        if k in seen_ab_keys:
            continue
        seen_ab_keys.add(k)

        meta = gon_meta.get(k, {})
        n_key = meta.get('name_key', f"ABILITY_{k.upper()}_NAME")
        d_key = meta.get('desc_key', f"ABILITY_{k.upper()}_DESC")
        
        cn_name = loc_dict.get(n_key, ab.get('name', k))
        cn_desc = loc_dict.get(d_key, "")

        has_icon = os.path.exists(os.path.join(ICONS_AB_DIR, f"{k}.png"))

        abilities_catalog.append({
            'key': k,
            'name': cn_name,
            'name_en': ab.get('name', k),
            'desc': cn_desc,
            'class': meta.get('class', 'Colorless'),
            'mana': meta.get('mana', 0),
            'damage': str(meta.get('damage', '')),
            'range': meta.get('range', 0),
            'variant_of': meta.get('variant_of', ''),
            'has_icon': has_icon
        })

    for lbl in set(ab_labels.values()):
        if lbl and lbl != 'unknown' and lbl not in seen_ab_keys:
            seen_ab_keys.add(lbl)
            meta = gon_meta.get(lbl, {})
            n_key = meta.get('name_key', f"ABILITY_{lbl.upper()}_NAME")
            d_key = meta.get('desc_key', f"ABILITY_{lbl.upper()}_DESC")
            abilities_catalog.append({
                'key': lbl,
                'name': loc_dict.get(n_key, lbl),
                'name_en': lbl,
                'desc': loc_dict.get(d_key, ""),
                'class': meta.get('class', 'Colorless'),
                'mana': meta.get('mana', 0),
                'damage': str(meta.get('damage', '')),
                'range': meta.get('range', 0),
                'variant_of': meta.get('variant_of', ''),
                'has_icon': True
            })

    catalog_path = os.path.join(ASSETS_DIR, "abilities_catalog.json")
    with open(catalog_path, 'w', encoding='utf-8') as f:
        json.dump(abilities_catalog, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {len(abilities_catalog)} rich ability catalog entries to {catalog_path}")

    # Build passives catalog
    passives_catalog = []
    seen_pas_keys = set()
    for pas in game_data.get('passives', []):
        k = pas['key']
        if k in seen_pas_keys:
            continue
        seen_pas_keys.add(k)
        n_key = f"PASSIVE_{k.upper()}_NAME"
        d_key = f"PASSIVE_{k.upper()}_DESC"
        cn_name = loc_dict.get(n_key, pas.get('name', k))
        cn_desc = loc_dict.get(d_key, "")
        has_icon = os.path.exists(os.path.join(ICONS_PAS_DIR, f"{k}.png"))
        passives_catalog.append({
            'key': k,
            'name': cn_name,
            'name_en': pas.get('name', k),
            'desc': cn_desc,
            'has_icon': has_icon
        })

    for lbl in set(pas_labels.values()):
        if lbl and lbl != 'unknown' and lbl not in seen_pas_keys:
            seen_pas_keys.add(lbl)
            n_key = f"PASSIVE_{lbl.upper()}_NAME"
            d_key = f"PASSIVE_{lbl.upper()}_DESC"
            passives_catalog.append({
                'key': lbl,
                'name': loc_dict.get(n_key, lbl),
                'name_en': lbl,
                'desc': loc_dict.get(d_key, ""),
                'has_icon': True
            })

    pas_catalog_path = os.path.join(ASSETS_DIR, "passives_catalog.json")
    with open(pas_catalog_path, 'w', encoding='utf-8') as f:
        json.dump(passives_catalog, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {len(passives_catalog)} rich passive catalog entries to {pas_catalog_path}")

    print("\n🎉 ALL ASSETS EXPORTED AND CATALOGED SUCCESSFULLY! 🎉")

if __name__ == '__main__':
    main()
