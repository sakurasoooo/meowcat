import os
import sys
import json
import shutil
import subprocess
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SWF_PATH = os.path.join(BASE_DIR, "catparts.swf")
EXTRACTOR_DIR = os.path.join(BASE_DIR, "_extractor")
JAVA_EXE = os.path.join(EXTRACTOR_DIR, "jre", "jdk-21.0.12.1+1-jre", "bin", "java.exe")
FFDEC_JAR = os.path.join(EXTRACTOR_DIR, "ffdec", "ffdec-cli.jar")
GAME_DATA_PATH = os.path.join(BASE_DIR, "mewgenics_game_data.json")
ASSETS_MUT_DIR = os.path.join(BASE_DIR, "assets", "icons", "mutations")
TEMP_DUMP_DIR = os.path.join(BASE_DIR, "_temp_mut_dump")

# 9 parts with character ID and class in catparts.swf
PART_CHIDS = {
    'head': 7132,       # CatHead
    'ears': 8051,       # CatEar
    'tail': 10982,      # CatTail
    'body': 8845,       # CatBody
    'legs': 9925,       # CatLeg
    'eyes': 5949,       # CatEye
    'mouth': 5947,      # CatMouth
    'eyebrows': 5519,   # CatEyebrow
    'texture': 2674,    # CatTexture
}

# Base / pure part frame IDs
BASE_PART_IDS = {
    'head': [100],
    'ears': [100],
    'tail': [100],
    'body': [100],
    'legs': [100],
    'eyes': [100],
    'mouth': [100],
    'eyebrows': [100],
    'texture': [246, 100],
}

def group_into_ranges(ids):
    if not ids:
        return ""
    sorted_ids = sorted(list(set(ids)))
    ranges = []
    start = end = sorted_ids[0]
    for n in sorted_ids[1:]:
        if n == end + 1:
            end = n
        else:
            ranges.append(f"{start}-{end}" if start != end else f"{start}")
            start = end = n
    ranges.append(f"{start}-{end}" if start != end else f"{start}")
    return ",".join(ranges)

def crop_and_save(src_png, dest_png, target_size=(72, 72)):
    try:
        with Image.open(src_png) as img:
            img = img.convert('RGBA')
            bbox = img.getbbox()
            if not bbox:
                return False
            cropped = img.crop(bbox)
            max_dim = max(cropped.width, cropped.height)
            if max_dim <= 0:
                return False
            # Leave 4px margin
            inner_w = target_size[0] - 8
            inner_h = target_size[1] - 8
            scale = min(inner_w / cropped.width, inner_h / cropped.height)
            new_w = max(1, int(cropped.width * scale))
            new_h = max(1, int(cropped.height * scale))
            resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            canvas = Image.new('RGBA', target_size, (0, 0, 0, 0))
            px = (target_size[0] - new_w) // 2
            py = (target_size[1] - new_h) // 2
            canvas.paste(resized, (px, py), resized)
            os.makedirs(os.path.dirname(dest_png), exist_ok=True)
            canvas.save(dest_png, 'PNG', optimize=True)
            return True
    except Exception as e:
        print(f"  [ERROR] cropping {src_png}: {e}")
        return False

def main():
    print("=== Mewgenics Cat Mutation Asset Exporter ===")
    if not os.path.exists(JAVA_EXE):
        print(f"Error: JRE not found at {JAVA_EXE}")
        return
    if not os.path.exists(FFDEC_JAR):
        print(f"Error: FFDec not found at {FFDEC_JAR}")
        return
    if not os.path.exists(SWF_PATH):
        print(f"Error: catparts.swf not found at {SWF_PATH}")
        return

    with open(GAME_DATA_PATH, 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    mutations = game_data.get('mutations', {})

    total_mutations_exported = 0

    for part, chid in PART_CHIDS.items():
        part_dir = os.path.join(ASSETS_MUT_DIR, part)
        os.makedirs(part_dir, exist_ok=True)

        mut_list = mutations.get(part, [])
        all_ids = [m['id'] for m in mut_list if 'id' in m and m['id'] >= 300]
        base_ids = BASE_PART_IDS.get(part, [])
        all_target_ids = sorted(list(set(all_ids + base_ids)))

        range_str = group_into_ranges(all_target_ids)
        print(f"\n--- Exporting [{part}] (chid: {chid}, count: {len(all_target_ids)} frames) ---")
        print(f"  Range: {range_str[:80]}...")

        # Temp directory for this part
        temp_part_dir = os.path.join(TEMP_DUMP_DIR, part)
        if os.path.exists(temp_part_dir):
            shutil.rmtree(temp_part_dir, ignore_errors=True)
        os.makedirs(temp_part_dir, exist_ok=True)

        # Run FFDec
        cmd = [
            JAVA_EXE,
            "-jar", FFDEC_JAR,
            "-format", "sprite:png",
            "-ignorebackground",
            "-zoom", "2",
            "-selectid", str(chid),
            "-select", f"{chid}:{range_str}",
            "-export", "sprite", temp_part_dir,
            SWF_PATH
        ]
        
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            print(f"  [ERROR] FFDec failed with code {proc.returncode}: {proc.stderr[:200]}")
            continue

        # Find exported sprite folder
        sprite_dirs = [d for d in os.listdir(temp_part_dir) if d.startswith(f"DefineSprite_{chid}")]
        if not sprite_dirs:
            print(f"  [WARN] No DefineSprite_{chid} directory found in {temp_part_dir}")
            continue

        sprite_folder = os.path.join(temp_part_dir, sprite_dirs[0])
        exported_files = [f for f in os.listdir(sprite_folder) if f.endswith('.png')]
        print(f"  FFDec exported {len(exported_files)} raw PNGs. Cropping & normalizing...")

        part_count = 0
        for fn in exported_files:
            try:
                frame_id = int(os.path.splitext(fn)[0])
            except ValueError:
                continue
            src_file = os.path.join(sprite_folder, fn)
            dest_file = os.path.join(part_dir, f"{frame_id}.png")
            if crop_and_save(src_file, dest_file, target_size=(72, 72)):
                part_count += 1

        print(f"  ✓ Successfully processed {part_count} icons for [{part}]")
        total_mutations_exported += part_count

        # Clean up temp part dir to free disk space
        shutil.rmtree(temp_part_dir, ignore_errors=True)

    if os.path.exists(TEMP_DUMP_DIR):
        shutil.rmtree(TEMP_DUMP_DIR, ignore_errors=True)

    print(f"\n🎉 ALL MUTATION ASSETS EXPORTED: {total_mutations_exported} total icons created in {ASSETS_MUT_DIR}! 🎉")

if __name__ == '__main__':
    main()
