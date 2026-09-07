"""Extract house-boss head stamps + completion overlays from game SWFs.

house.swf sprite 554  — 9 家园 Boss 头 + unknown/none
ui.swf shapes 3503/3504/3505 — 困难斜线 / 疯狂交叉 / 不可能圆圈
ui.swf shape  3508          — 右下红星（3512 none）
ui.swf shapes 3510/3511     — 右下单职业叉 / 单人对勾
ui.swf shapes 3507,3513-3520 — 9 章节中心图（不含底卡/叠线）
ui.swf sprite 3506          — 白底卡 × 4 难度合成（对照）
ui.swf sprite 3512          — none / monoclass / solocat
"""
import glob, io, os, shutil, subprocess, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from PIL import Image

JAVA = r'_extractor\jre\jdk-21.0.12.1+1-jre\bin\java.exe'
FFDEC = r'_extractor\ffdec\ffdec-cli.jar'
UI = r'game_assets\swfs\ui.swf'
HOUSE = r'game_assets\swfs\house.swf'
TMP = r'tools\_swf_tmp\stamps'
DEST_MARK = r'assets\icons\completion'
DEST_HEAD = r'assets\icons\houseboss'
os.makedirs(TMP, exist_ok=True)
os.makedirs(DEST_MARK, exist_ok=True)
os.makedirs(DEST_HEAD, exist_ok=True)


def ffdec(swf, kind, chid, select, out_dir, zoom='2'):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [JAVA, '-jar', FFDEC, '-format', f'{kind}:png', '-ignorebackground',
           '-zoom', zoom, '-selectid', str(chid), '-select', select,
           '-export', kind, out_dir, swf]
    r = subprocess.run(cmd, capture_output=True, timeout=180)
    pngs = sorted(glob.glob(os.path.join(out_dir, '**', '*.png'), recursive=True))
    err = (r.stderr or b'').decode('utf-8', errors='replace')[-400:]
    return pngs, err


def invert_dark(img):
    """黑线叠图翻成浅色，方便深色编辑器底。"""
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 8 and r + g + b < 240:
                px[x, y] = (255 - r, 255 - g, 255 - b, a)
    return img


def norm(src, dest, target=64, pad=4, invert=False):
    img = Image.open(src).convert('RGBA')
    bbox = img.getbbox()
    if not bbox:
        return False
    img = img.crop(bbox)
    inner = target - pad * 2
    s = min(inner / img.width, inner / img.height)
    img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
    if invert:
        img = invert_dark(img)
    canvas = Image.new('RGBA', (target, target), (0, 0, 0, 0))
    canvas.paste(img, ((target - img.width) // 2, (target - img.height) // 2), img)
    canvas.save(dest, 'PNG', optimize=True)
    return True


# --- standalone marks (shapes) ---
SHAPES = {
    3503: ('slash_hard', False),
    3504: ('slash_crazy', False),
    3505: ('circle_impossible', False),
    3508: ('mark_star', False),
    3510: ('mark_x', False),
    3511: ('mark_check', False),
}
print('=== standalone marks ===')
for chid, (name, inv) in SHAPES.items():
    tmp = os.path.join(TMP, f'shape_{chid}')
    pngs, err = ffdec(UI, 'shape', chid, str(chid), tmp)
    dest = os.path.join(DEST_MARK, f'{name}.png')
    if pngs:
        ok = norm(pngs[0], dest, target=48, pad=2, invert=inv)
        print(f'  {chid} {name}: {"OK" if ok else "EMPTY"} {os.path.getsize(pngs[0])}b -> {dest}')
    else:
        print(f'  {chid} {name}: NO PNG {err}')
# 深色底图例用的浅色叉/勾（原图是黑线）
for src, dst in (('mark_x', 'check_monoclass'), ('mark_check', 'check_solo')):
    p = os.path.join(DEST_MARK, f'{src}.png')
    if os.path.isfile(p):
        ok = norm(p, os.path.join(DEST_MARK, f'{dst}.png'), target=48, pad=2, invert=True)
        print(f'  invert {src} -> {dst}: {"OK" if ok else "EMPTY"}')

# --- chapter emblems (center art only) ---
EMBLEMS = {
    3507: 'caves',
    3513: 'boneyard',
    3514: 'core',
    3515: 'moon',
    3516: 'jurassic',
    3517: 'theend',
    3518: 'meatworld',
    3519: 'dimensionx',
    3520: 'endoftime',
}
print('=== chapter emblems ===')
for chid, name in EMBLEMS.items():
    tmp = os.path.join(TMP, f'emblem_{chid}')
    pngs, err = ffdec(UI, 'shape', chid, str(chid), tmp)
    dest = os.path.join(DEST_MARK, f'emblem_{name}.png')
    dest_plain = os.path.join(DEST_MARK, f'emblem_plain_{name}.png')
    if pngs:
        ok = norm(pngs[0], dest, target=64, pad=2)
        if ok:
            shutil.copyfile(dest, dest_plain)
        print(f'  {chid} {name}: {"OK" if ok else "EMPTY"} {os.path.getsize(pngs[0])}b')
    else:
        print(f'  {chid} {name}: NO PNG {err}')

# --- composed difficulty (sprite 3506, 4 frames) ---
print('=== sprite 3506 difficulty compose ===')
tmp = os.path.join(TMP, 's3506')
pngs, err = ffdec(UI, 'sprite', 3506, '3506:1-4', tmp)
for i, p in enumerate(pngs[:4], start=1):
    dest = os.path.join(DEST_MARK, f'compose_diff_{i-1}.png')
    ok = norm(p, dest, target=72, pad=2)
    print(f'  3506:{i} {"OK" if ok else "EMPTY"} {os.path.getsize(p)}b')
if not pngs:
    print('  NO PNG', err)

# --- solo clip 3512 ---
print('=== sprite 3512 solo ===')
tmp = os.path.join(TMP, 's3512')
pngs, err = ffdec(UI, 'sprite', 3512, '3512:1-3', tmp)
labels = ['none', 'monoclass', 'solocat']
for i, p in enumerate(pngs[:3]):
    dest = os.path.join(DEST_MARK, f'solo_{labels[i]}.png')
    ok = norm(p, dest, target=48, pad=2)
    print(f'  3512:{i+1} {labels[i]} {"OK" if ok else "EMPTY"}')
if not pngs:
    print('  NO PNG', err)

# --- house boss card frames (sort by frame number, not lex) ---
print('=== house.swf 554 cards ===')
HEADS = [
    'guillotina_1', 'guillotina_2', 'guillotina_3',
    'pyrophina', 'zaratana', 'pyrophina_vs_zaratana',
    'terminator_1', 'terminator_2', 'terminator_3',
    'unknown', 'none',
]
tmp = os.path.join(TMP, 's554')
pngs, err = ffdec(HOUSE, 'sprite', 554, '554:1-11', tmp, zoom='2')
if not pngs:
    print('  NO PNG', err)
else:
    def frame_no(p):
        base = os.path.splitext(os.path.basename(p))[0]
        return int(base) if base.isdigit() else 0
    pngs = sorted(pngs, key=frame_no)
    print(f'  got {len(pngs)} pngs')
    for p in pngs:
        n = frame_no(p)
        name = HEADS[n - 1] if 1 <= n <= len(HEADS) else f'f{n}'
        dest = os.path.join(DEST_HEAD, f'card_{name}.png')
        ok = norm(p, dest, target=96, pad=2)
        print(f'  554:{n} {name} {"OK" if ok else "EMPTY"} {os.path.getsize(p)}b')

# isolated red head stamps (PlaceObject children of 554)
print('=== house.swf head children ===')
HEAD_CHIDS = {
    526: 'guillotina_1',
    529: 'guillotina_2',
    532: 'guillotina_3',
    535: 'pyrophina',
    538: 'zaratana',
    541: 'pyrophina_vs_zaratana',
    544: 'terminator_1',
    547: 'terminator_2',
    550: 'terminator_3',
    553: 'unknown',
    31: 'housebossicon',
}
for chid, name in HEAD_CHIDS.items():
    tmp = os.path.join(TMP, f'head_{chid}')
    pngs, err = ffdec(HOUSE, 'sprite', chid, f'{chid}:1', tmp, zoom='4')
    dest = os.path.join(DEST_HEAD, f'{name}.png')
    if pngs:
        ok = norm(pngs[0], dest, target=48, pad=2)
        print(f'  {chid} {name}: {"OK" if ok else "EMPTY"} {os.path.getsize(pngs[0])}b')
    else:
        print(f'  {chid} {name}: NO PNG {err}')

# --- ui.swf 黑色带血猫头（职业页戳，9 个 defeated clip）---
print('=== ui.swf black defeated heads ===')
DEAD = [
    (634, 'guillotina_1'),
    (639, 'guillotina_2'),
    (644, 'guillotina_3'),
    (649, 'pyrophina'),
    (654, 'zaratana'),
    (659, 'pyrophina_vs_zaratana'),
    (664, 'terminator_1'),
    (669, 'terminator_2'),
    (674, 'terminator_3'),
]
for chid, name in DEAD:
    tmp = os.path.join(TMP, f'dead_{chid}')
    # frame 2 = defeated0（黑猫头+血泊）
    pngs, err = ffdec(UI, 'sprite', chid, f'{chid}:2', tmp, zoom='3')
    dest = os.path.join(DEST_HEAD, f'dead_{name}.png')
    if pngs:
        ok = norm(pngs[0], dest, target=56, pad=2)
        print(f'  {chid} dead_{name}: {"OK" if ok else "EMPTY"} {os.path.getsize(pngs[0])}b')
    else:
        print(f'  {chid} dead_{name}: NO PNG {err}')

print('\nDONE')
