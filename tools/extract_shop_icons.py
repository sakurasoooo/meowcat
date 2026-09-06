"""Extract shop office icons (self-contained; no exec of other scripts)."""
import io as _io, sys as _sys, struct, zlib, os, subprocess, glob
_sys.stdout = _io.TextIOWrapper(_sys.stdout.buffer, encoding='utf-8')
from PIL import Image

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

def walk_exports(path):
    data = open(path, 'rb').read()
    body = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
    p = read_rect(body, 0) + 4
    while p < len(body):
        try:
            code_len = struct.unpack_from('<H', body, p)[0]
        except struct.error:
            break
        code, length = code_len >> 6, code_len & 0x3F
        p += 2
        if length == 0x3F:
            if p + 4 > len(body):
                break
            length = struct.unpack_from('<I', body, p)[0]
            p += 4
        payload = body[p:p + length]
        p += length
        if code == 76:
            q = 0
            cnt = struct.unpack_from('<H', payload, q)[0]; q += 2
            for _ in range(cnt):
                tid = struct.unpack_from('<H', payload, q)[0]; q += 2
                nm = payload[q:payload.find(b'\x00', q)].decode('utf-8', errors='replace')
                q += len(nm) + 1
                yield nm, tid
        if code == 0 and length == 0:
            break

tagmap = {}
for nm, tid in walk_exports(r'game_assets\swfs\npcs.swf'):
    tagmap[nm] = tid

SHOPS = {'Butch': 'ButchOffice', 'Jack': 'JackOffice', 'Tracy': 'TracyOffice',
         'Tink': 'TinkOffice', 'Organ': 'OrganOffice', 'Beanies': 'BeaniesOffice'}
print('shop symbol tag ids:')
for shop, sym in SHOPS.items():
    print(f'  {shop:8s} {sym}: {tagmap.get(sym)}')

JAVA = r'_extractor\jre\jdk-21.0.12.1+1-jre\bin\java.exe'
FFDEC = r'_extractor\ffdec\ffdec-cli.jar'
SWF = r'game_assets\swfs\npcs.swf'
OUT = r'tools\_swf_tmp\shops'
DEST = r'assets\icons\shops'
os.makedirs(OUT, exist_ok=True)
os.makedirs(DEST, exist_ok=True)

def norm(src, dest, target=64, pad=4):
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

for shop, sym in SHOPS.items():
    tid = tagmap.get(sym)
    if not tid:
        print(f'{shop}: NO TAG, skip')
        continue
    tmp = os.path.join(OUT, shop)
    os.makedirs(tmp, exist_ok=True)
    subprocess.run([JAVA, '-jar', FFDEC, '-format', 'sprite:png', '-ignorebackground', '-zoom', '1',
                    '-selectid', str(tid), '-select', f'{tid}:1', '-export', 'sprite', tmp, SWF],
                   capture_output=True, timeout=120)
    pngs = glob.glob(os.path.join(tmp, '**', '*.png'), recursive=True)
    if pngs:
        ok = norm(pngs[0], os.path.join(DEST, f'{shop}.png'))
        print(f'{shop}: {"OK" if ok else "EMPTY"} ({os.path.getsize(pngs[0])}b)')
    else:
        print(f'{shop}: NO PNG')
