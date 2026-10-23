"""Compute ShowFrame-based frame numbers for zone labels (sprite 1828 map.swf)
and chosen move-art labels (sprite 1346 ability_icons.swf)."""
import io as _io, sys as _sys, struct, zlib
_sys.stdout = _io.TextIOWrapper(_sys.stdout.buffer, encoding='utf-8')

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
        if code == 0 and length == 0 or (target is not None and p >= len(body)):
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

# 地图区域 (sprite 1828 in map.swf)
zone = sprite_labels(r'game_assets\swfs\map.swf', 1828)
print('=== zone sprite 1828 (frame -> label) ===')
for f, l in sorted(zone.items()):
    print(f'  帧 {f}: {l}')

print()
# 技能 1346 的移动类标签帧号
ab = sprite_labels(r'game_assets\swfs\ability_icons.swf', 1346)
rev = {v: k for k, v in ab.items()}
MOVE_ART = ['Step', 'CatapultJump', 'MageTeleport', 'DigUpTheDead', 'Shadowshift', 'ThiefSwap',
            'TankTrample', 'ChaosTeleport', 'WindyStep', 'Dash', 'BlinkDodge', 'MageSwap', 'PrepareToJump', 'TankSwap']
print('=== move-art frames ===')
for m in MOVE_ART:
    print(f'  {m:16s} -> 帧 {rev.get(m)}')
