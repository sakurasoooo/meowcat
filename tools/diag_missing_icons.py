"""Diagnose missing ability/passive icons: cross-ref catalog has_icon vs SWF labels."""
import io, sys, json, os, struct, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')

# 复用 scan_swf_frames2.py 的 sprite_labels
import importlib.util
spec = importlib.util.spec_from_file_location('fx', r'tools\scan_swf_frames2.py')
# 直接内联更稳
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
def sprite_labels(path, want_sid):
    data = open(path, 'rb').read()
    body = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
    p = read_rect(body, 0) + 4
    target = None
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
        if code == 39:
            sid = struct.unpack_from('<H', payload, 0)[0]
            if sid == want_sid:
                target = payload
        if code == 0 and length == 0:
            break
    if target is None:
        return {}
    q = 4
    frame = 0
    labels = {}
    while q < len(target):
        try:
            code_len = struct.unpack_from('<H', target, q)[0]
        except struct.error:
            break
        c2, l2 = code_len >> 6, code_len & 0x3F
        q += 2
        if l2 == 0x3F:
            if q + 4 > len(target):
                break
            l2 = struct.unpack_from('<I', target, q)[0]
            q += 4
        if c2 == 0 and l2 == 0:
            break
        if c2 == 1:
            frame += 1
        elif c2 == 43:
            labels[frame] = target[q:q + l2].rstrip(b'\x00').decode('utf-8', errors='replace')
        q += l2
    return labels

ab_labels = set(sprite_labels(r'game_assets\swfs\ability_icons.swf', 1346).values())
pas_labels = set(sprite_labels(r'game_assets\swfs\ability_icons.swf', 515).values())

ab_cat = json.load(open('assets/abilities_catalog.json', encoding='utf-8'))
pas_cat = json.load(open('assets/passives_catalog.json', encoding='utf-8'))

def missing(cat, labels, icon_dir, title):
    miss = []
    for e in cat:
        k = e['key']
        if e.get('has_icon'):
            continue
        if not os.path.exists(os.path.join(icon_dir, k + '.png')):
            miss.append((k, k in labels))
    print(f'=== {title}: {len(miss)} 缺图标 (其中在SWF标签中可提取: {sum(1 for _,y in miss if y)}) ===')
    in_swf = [k for k, y in miss if y]
    not_swf = [k for k, y in miss if not y]
    print(f'  可提取({len(in_swf)}):', sorted(in_swf)[:40])
    print(f'  SWF无标签({len(not_swf)}):', sorted(not_swf)[:40])
    return miss

missing(ab_cat, ab_labels, 'assets/icons/abilities', '主动技能')
missing(pas_cat, pas_labels, 'assets/icons/passives', '被动')
