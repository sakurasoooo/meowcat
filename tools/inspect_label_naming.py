"""Inspect SWF label naming vs catalog keys (case/normalize analysis)."""
import io, sys, json, struct, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

ab = sprite_labels(r'game_assets\swfs\ability_icons.swf', 1346)
pa = sprite_labels(r'game_assets\swfs\ability_icons.swf', 515)

# 找含 thou/kill/bullseye 的标签（不区分大小写）
def find(labels, words):
    for f, l in labels.items():
        low = l.lower()
        if any(w in low for w in words):
            print(f'  frame {f}: {l}')
    return

print('=== AbilityIcon(1346) 含 thou/kill/bull/aim ===')
find(ab, ['thou', 'kill', 'bull', 'aim', 'soul'])
print('=== PassiveIcon(515) 含 thou/kill/bull/soul/eye ===')
find(pa, ['thou', 'kill', 'bull', 'soul', 'eye', 'aspect', 'frenzy'])

ab_cat = json.load(open('assets/abilities_catalog.json', encoding='utf-8'))
pas_cat = json.load(open('assets/passives_catalog.json', encoding='utf-8'))
print()
print('catalog 中含 thou 的主动:', [e['key'] for e in ab_cat if 'thou' in e['key'].lower()][:5])
print('catalog 中含 bull 的主动:', [e['key'] for e in ab_cat if 'bull' in e['key'].lower()][:5])
print('catalog 中含 soul 的主动:', [e['key'] for e in ab_cat if 'soul' in e['key'].lower()][:5])
# 归一化（去大小写/下划线）匹配率
def norm(s):
    return ''.join(c for c in s.lower() if c.isalnum())
ablab_n = set(norm(x) for x in ab.values())
paslab_n = set(norm(x) for x in pa.values())
ab_nohit_n = sum(1 for e in ab_cat if not e.get('has_icon') and norm(e['key']) not in ablab_n)
pa_nohit_n = sum(1 for e in pas_cat if not e.get('has_icon') and norm(e['key']) not in paslab_n)
print()
print(f'归一化后仍不在AbilityIcon中的主动: {ab_nohit_n} / 缺图 {sum(1 for e in ab_cat if not e.get("has_icon"))}')
print(f'归一化后仍在PassiveIcon中的被动(可提取候选): {sum(1 for e in pas_cat if not e.get("has_icon") and norm(e["key"]) in paslab_n)} / 缺图 {sum(1 for e in pas_cat if not e.get("has_icon"))}')
