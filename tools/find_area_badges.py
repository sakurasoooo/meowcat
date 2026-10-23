"""Scan ui.swf sprites for area-name frame labels (completion checkmark badges) + defeat sprites."""
import io, sys, struct, zlib
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

ZONES = {'caves', 'boneyard', 'moon', 'core', 'jurassic', 'theend', 'meatworld', 'dimensionx', 'endoftime',
         'desert', 'sewers', 'lab', 'thecaves', 'themoon', 'thecore', 'boneyard'}

def walk_sprites(body):
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
        if code == 39:
            yield struct.unpack_from('<H', payload, 0)[0], payload
        if code == 0 and length == 0:
            break

def sprite_labels(payload):
    q = 4
    frame = 0
    labels = {}
    while q < len(payload):
        try:
            code_len = struct.unpack_from('<H', payload, q)[0]
        except struct.error:
            break
        c, l = code_len >> 6, code_len & 0x3F
        q += 2
        if l == 0x3F:
            if q + 4 > len(payload):
                break
            l = struct.unpack_from('<I', payload, q)[0]
            q += 4
        if c == 0 and l == 0:
            break
        if c == 1:
            frame += 1
        elif c == 43:
            labels[frame] = payload[q:q + l].rstrip(b'\x00').decode('utf-8', errors='replace')
        q += l
    return labels

for swf in ['ui.swf', 'map.swf', 'house.swf']:
    data = open(r'game_assets\swfs' + '\\' + swf, 'rb').read()
    body = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
    print(f'=== {swf} ===')
    for sid, payload in walk_sprites(body):
        labs = sprite_labels(payload)
        hit = {f: l for f, l in labs.items() if l.lower() in ZONES or l.lower().startswith(('the',)) and l[4:].lower() in ZONES}
        hit2 = {f: l for f, l in labs.items() if any(z in l.lower() for z in ZONES)}
        if hit2:
            print(f'  sprite {sid}: {len(labs)} labels; area hits: {dict(list(hit2.items())[:12])}')
