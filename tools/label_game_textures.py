"""Build a labeled CSV for textures extracted from resources.gpak.
Output: game_assets/game_textures.csv
"""
import csv, os, struct

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'game_assets')
TEX = os.path.join(ROOT, 'textures')

def png_size(path):
    try:
        with open(path, 'rb') as f:
            head = f.read(26)
        if head[:8] == b'\x89PNG\r\n\x1a\n' and head[12:16] == b'IHDR':
            w, h = struct.unpack('>II', head[16:24])
            return w, h
    except Exception:
        pass
    return '', ''

# heuristic tagging by filename
RULES = [
    ('cursor',   ['cursor/'],                        'UI 鼠标指针/交互光标'),
    ('ground',   ['dirt', 'road', 'ice', 'lava', 'water', 'freezingwater', 'oil', 'creep'], '地面/地形贴图'),
    ('effect',   ['blood', 'flowing', 'mutate', 'fx_', 'effect'],  '战斗特效贴图'),
    ('noise',    ['noise', 'grain', 'filmdust', 'perlin'], '噪点/滤镜叠加层'),
    ('palette',  ['palette'],                        '调色板'),
    ('ui',       ['btn', 'frame'],                   'UI 元素'),
]

def classify(name):
    low = name.lower()
    for cat, keys, desc in RULES:
        if any(k in low for k in keys):
            return cat, desc
    return 'misc', '其它贴图'

rows = []
for dirpath, _, files in os.walk(TEX):
    for fn in sorted(files):
        if not fn.lower().endswith('.png'):
            continue
        full = os.path.join(dirpath, fn)
        rel = os.path.relpath(full, ROOT).replace(os.sep, '/')
        cat, desc = classify(rel)
        w, h = png_size(full)
        rows.append({
            'file': rel,
            'category': cat,
            'usage_zh': desc,
            'width': w,
            'height': h,
            'size_kb': round(os.path.getsize(full) / 1024, 1),
        })

# also index the swfs (vector art containers — item/ability/cat icons live here)
swf_dir = os.path.join(ROOT, 'swfs')
for fn in sorted(os.listdir(swf_dir)):
    if not fn.lower().endswith('.swf'):
        continue
    full = os.path.join(swf_dir, fn)
    rows.append({
        'file': f'swfs/{fn}',
        'category': 'swf',
        'usage_zh': '矢量动画资源包（内含图标/角色部件，需 SWF 解析工具导出）',
        'width': '', 'height': '',
        'size_kb': round(os.path.getsize(full) / 1024, 1),
    })

out = os.path.join(ROOT, 'game_textures.csv')
with open(out, 'w', newline='', encoding='utf-8-sig') as f:
    wcsv = csv.DictWriter(f, fieldnames=['file', 'category', 'usage_zh', 'width', 'height', 'size_kb'])
    wcsv.writeheader()
    wcsv.writerows(rows)
print(f'wrote {out}: {len(rows)} rows')
