"""Fuzzy-map missing passives to SWF frames; extract+normalize icons."""
import io, sys, json, os, subprocess, glob, struct, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from PIL import Image

# ---- SWF label sets (515 passive, 1346 ability) ----
class BR:
    def __init__(s, b): s.b = b; s.pos = 0
    def ub(s, n):
        v = 0
        for _ in range(n):
            byte = s.b[s.pos >> 3]; bit = (byte >> (7 - (s.pos & 7))) & 1
            v = (v << 1) | bit; s.pos += 1
        return v
    def al(s): s.pos = (s.pos + 7) & ~7
def rr(b, o):
    n = (b[o] >> 3) & 0x1F; br = BR(b[o:]); br.ub(5); br.ub(n * 4); br.al()
    return o + (br.pos >> 3)
def slabels(path, want):
    data = open(path, 'rb').read()
    body = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
    p = rr(body, 0) + 4; target = None
    while p < len(body):
        try: cl = struct.unpack_from('<H', body, p)[0]
        except struct.error: break
        c, l = cl >> 6, cl & 0x3F; p += 2
        if l == 0x3F:
            if p + 4 > len(body): break
            l = struct.unpack_from('<I', body, p)[0]; p += 4
        pl = body[p:p + l]; p += l
        if c == 39:
            sd = struct.unpack_from('<H', pl, 0)[0]
            if sd == want: target = pl
        if c == 0 and l == 0: break
    if target is None: return {}
    q = 4; fr = 0; lab = {}
    while q < len(target):
        try: cl = struct.unpack_from('<H', target, q)[0]
        except struct.error: break
        c, l = cl >> 6, cl & 0x3F; q += 2
        if l == 0x3F:
            if q + 4 > len(target): break
            l = struct.unpack_from('<I', target, q)[0]; q += 4
        if c == 0 and l == 0: break
        if c == 1: fr += 1
        elif c == 43: lab[fr] = target[q:q + l].rstrip(b'\x00').decode('utf-8', 'replace')
        q += l
    return lab

p515 = slabels(r'game_assets\swfs\ability_icons.swf', 515)   # passive frames (1-based)
p1346 = slabels(r'game_assets\swfs\ability_icons.swf', 1346)
def norm(s): return ''.join(c for c in s.lower() if c.isalnum())

pas_cat = json.load(open('assets/passives_catalog.json', encoding='utf-8'))
missing = [e['key'] for e in pas_cat if not os.path.exists(os.path.join('assets/icons/passives', e['key'] + '.png'))]

def find_frame(key):
    nk = norm(key)
    # 1. exact norm
    for fr, lab in p515.items():
        if norm(lab) == nk: return 515, fr
    for fr, lab in p1346.items():
        if norm(lab) == nk: return 1346, fr
    # 2. one-s removal both directions
    for fr, lab in p515.items():
        nl = norm(lab)
        if nk[:-1] + '' + nk[-1:] == nl or nk == nl[:-1] + '' + nl[-1:]:
            continue
        if (nl[:-1] == nk[:-1] and len(nl) == len(nk)) or (nl == nk + 's') or (nl + 's' == nk) or (nl + 's' == nk):
            return 515, fr
    # 3. substring
    for fr, lab in p515.items():
        if nk in norm(lab) or norm(lab) in nk:
            return 515, fr
    for fr, lab in p1346.items():
        if nk in norm(lab) or norm(lab) in nk:
            return 1346, fr
    return None

JAVA = r'_extractor\jre\jdk-21.0.12.1+1-jre\bin\java.exe'
FFDEC = r'_extractor\ffdec\ffdec-cli.jar'
SWF = r'game_assets\swfs\ability_icons.swf'
OUT = r'tools\_swf_tmp\passive_fix'
DEST = 'assets/icons/passives'
os.makedirs(OUT, exist_ok=True)
os.makedirs(DEST, exist_ok=True)

def norm_png(src, dest, target=48, pad=3):
    img = Image.open(src).convert('RGBA')
    bbox = img.getbbox()
    if not bbox: return False
    img = img.crop(bbox)
    inner = target - pad * 2
    s = min(inner / img.width, inner / img.height)
    img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
    canvas = Image.new('RGBA', (target, target), (0, 0, 0, 0))
    canvas.paste(img, ((target - img.width) // 2, (target - img.height) // 2), img)
    canvas.save(dest, 'PNG', optimize=True)
    return True

done = 0
noframe = []
# group requests by (sprite, frame) for batch export
requests = {}   # (sprite, frame) -> [keys...]
for key in missing:
    m = find_frame(key)
    if m:
        spr, fr = m
        requests.setdefault((spr, fr), []).append(key)
    else:
        noframe.append(key)

print(f'找到帧的缺失被动: {len(requests)} 帧，未找到: {len(noframe)}')
print('未找到:', noframe)

# 逐帧 FFDec 导出并落盘
tmp_root = OUT
sprite_names = {515: 'passive', 1346: 'ability'}
for (spr, fr), keys in requests.items():
    tmp = os.path.join(tmp_root, f's{spr}_f{fr}')
    os.makedirs(tmp, exist_ok=True)
    subprocess.run([JAVA, '-jar', FFDEC, '-format', 'sprite:png', '-ignorebackground', '-zoom', '1',
                    '-selectid', str(spr), '-select', f'{spr}:{fr}', '-export', 'sprite', tmp, SWF],
                   capture_output=True, timeout=120)
    pngs = glob.glob(os.path.join(tmp, '**', '*.png'), recursive=True)
    src = pngs[0] if pngs else None
    if not src:
        print(f'sprite{spr} f{fr}: NO PNG')
        continue
    for key in keys:
        ok = norm_png(src, os.path.join(DEST, f'{key}.png'))
        print(f'  {key:24s} <- s{spr}#{fr}: {"OK" if ok else "EMPTY"}')
        if ok: done += 1
print(f'\n补全 {done} 个被动图标')
