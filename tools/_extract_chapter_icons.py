"""Export standalone chapter emblems + leftover mark sprites from ui.swf 3521 tree."""
import glob, io, os, struct, subprocess, sys, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from PIL import Image

JAVA = r'_extractor\jre\jdk-21.0.12.1+1-jre\bin\java.exe'
FFDEC = r'_extractor\ffdec\ffdec-cli.jar'
UI = r'game_assets\swfs\ui.swf'
TMP = r'tools\_swf_tmp\chaptermarks'
DEST = r'assets\icons\completion'
os.makedirs(TMP, exist_ok=True)
os.makedirs(DEST, exist_ok=True)


class BitReader:
    def __init__(self, b):
        self.b = b
        self.pos = 0
    def read_ub(self, n):
        v = 0
        for _ in range(n):
            byte = self.b[self.pos >> 3]
            bit = (byte >> (7 - (self.pos & 7))) & 1
            v = (v << 1) | bit
            self.pos += 1
        return v
    def align(self):
        self.pos = (self.pos + 7) & ~7


def read_rect(b, off):
    nbits = (b[off] >> 3) & 0x1F
    br = BitReader(b[off:])
    br.read_ub(5)
    br.read_ub(nbits * 4)
    br.align()
    return off + (br.pos >> 3)


def walk_tags(data, start=0):
    p = start
    while p + 2 <= len(data):
        code_len = struct.unpack_from('<H', data, p)[0]
        code, length = code_len >> 6, code_len & 0x3F
        p += 2
        if length == 0x3F:
            if p + 4 > len(data):
                break
            length = struct.unpack_from('<I', data, p)[0]
            p += 4
        payload = data[p:p + length]
        p += length
        yield code, payload
        if code == 0 and length == 0:
            break


data = open(UI, 'rb').read()
body = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
p0 = read_rect(body, 0) + 4
kinds = {}
for code, payload in walk_tags(body, p0):
    if code in (2, 22, 32, 83, 39, 20, 36) and len(payload) >= 2:
        cid = struct.unpack_from('<H', payload, 0)[0]
        if 3490 <= cid <= 3530 or cid in (1176, 3503, 3504, 3505, 3506, 3507):
            if code == 39:
                kinds[cid] = f'sprite frames={struct.unpack_from("<H", payload, 2)[0]}'
            elif code in (20, 36):
                kinds[cid] = 'bitmap'
            else:
                kinds[cid] = 'shape'
print('ids:', {k: kinds[k] for k in sorted(kinds)})


def ffdec(kind, chid, select, out, zoom='2'):
    os.makedirs(out, exist_ok=True)
    subprocess.run([JAVA, '-jar', FFDEC, '-format', f'{kind}:png', '-ignorebackground',
                    '-zoom', zoom, '-selectid', str(chid), '-select', select,
                    '-export', kind, out, UI], capture_output=True, timeout=180)
    return sorted(glob.glob(os.path.join(out, '**', '*.png'), recursive=True))


def norm(src, dest, target=64, pad=3):
    img = Image.open(src).convert('RGBA')
    bbox = img.getbbox()
    if not bbox:
        return False
    img = img.crop(bbox)
    inner = target - pad * 2
    s = min(inner / img.width, inner / img.height)
    img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
    canvas = Image.new('RGBA', (target, target), (0, 0, 0, 0))
    canvas.paste(img, ((target - img.width) // 2, (target - img.height) // 2), img)
    canvas.save(dest, 'PNG', optimize=True)
    return True


# 3521 frames 1-9 = chapter emblems (with child clips)
ZONES = ['caves', 'boneyard', 'core', 'moon', 'jurassic', 'theend', 'meatworld', 'dimensionx', 'endoftime']
print('\n=== sprite 3521 frames ===')
pngs = ffdec('sprite', 3521, '3521:1-9', os.path.join(TMP, 's3521'))
for p in pngs:
    base = os.path.splitext(os.path.basename(p))[0]
    n = int(base) if base.isdigit() else 0
    if 1 <= n <= 9:
        dest = os.path.join(DEST, f'emblem_{ZONES[n-1]}.png')
        print(f'  3521:{n} {ZONES[n-1]}', 'OK' if norm(p, dest, 64, 2) else 'EMPTY')

# child emblems 3513-3520 (zones 2-9) and 3506 frame1 (caves plain)
print('\n=== child emblems ===')
CH = {
    3506: ('caves', '3506:1'),
    3513: ('boneyard', '3513:1'),
    3514: ('core', '3514:1'),
    3515: ('moon', '3515:1'),
    3516: ('jurassic', '3516:1'),
    3517: ('theend', '3517:1'),
    3518: ('meatworld', '3518:1'),
    3519: ('dimensionx', '3519:1'),
    3520: ('endoftime', '3520:1'),
}
for chid, (name, sel) in CH.items():
    kind = 'sprite' if kinds.get(chid, '').startswith('sprite') else 'shape'
    pngs = ffdec(kind, chid, sel if kind == 'sprite' else str(chid), os.path.join(TMP, f'c{chid}'))
    dest = os.path.join(DEST, f'emblem_plain_{name}.png')
    if pngs:
        print(f'  {chid} {name}', 'OK' if norm(pngs[0], dest, 64, 2) else 'EMPTY', os.path.getsize(pngs[0]))
    else:
        print(f'  {chid} {name} NO PNG')

# 3507 leftover
print('\n=== 3507 ===')
kind = 'sprite' if kinds.get(3507, '').startswith('sprite') else 'shape'
pngs = ffdec(kind, 3507, '3507:1' if kind == 'sprite' else '3507', os.path.join(TMP, 'c3507'))
if pngs:
    print('3507', kinds.get(3507), os.path.getsize(pngs[0]), 'OK' if norm(pngs[0], os.path.join(DEST, 'mark_3507.png'), 48, 2) else 'EMPTY')
else:
    print('3507 none', kinds.get(3507))

# tooltip checkmarks
for chid, name in [(3522, 'tooltip_small_check'), (3628, 'tooltip_check')]:
    pngs = ffdec('sprite', chid, f'{chid}:1', os.path.join(TMP, f't{chid}'))
    dest = os.path.join(DEST, f'{name}.png')
    if pngs:
        print(chid, name, 'OK' if norm(pngs[0], dest, 48, 2) else 'EMPTY')
    else:
        print(chid, name, 'NO PNG')
