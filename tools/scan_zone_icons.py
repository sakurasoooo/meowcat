"""Scan map.swf + backgrounds-world for area/zone icon labels."""
import io as _io, sys as _sys, struct, zlib, os, re
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

ZONE_RE = re.compile(r'(caves|boneyard|moon|core|jurassic|theend|meatworld|dimensionx|endoftime|desert|lab|sewer)', re.I)

def scan(path):
    data = open(path, 'rb').read()
    body = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
    p = read_rect(body, 0) + 4
    found = []
    while p < len(body):
        try:
            code_len = struct.unpack_from('<H', body, p)[0]
        except struct.error:
            break
        code = code_len >> 6
        length = code_len & 0x3F
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
                q += 2
                nm = payload[q:payload.find(b'\x00', q)].decode('utf-8', errors='replace')
                q += len(nm) + 1
                if ZONE_RE.search(nm):
                    found.append(('export', nm))
        elif code == 39:
            sid = struct.unpack_from('<H', payload, 0)[0]
            q = 4
            frame = 0
            while q < len(payload):
                try:
                    cl2 = struct.unpack_from('<H', payload, q)[0]
                except struct.error:
                    break
                c2, l2 = cl2 >> 6, cl2 & 0x3F
                q += 2
                if l2 == 0x3F:
                    if q + 4 > len(payload):
                        break
                    l2 = struct.unpack_from('<I', payload, q)[0]
                    q += 4
                if c2 == 0 and l2 == 0:
                    break
                if c2 == 1:
                    frame += 1
                elif c2 == 43:
                    s = payload[q:q + l2].rstrip(b'\x00').decode('utf-8', errors='replace')
                    if ZONE_RE.search(s):
                        found.append((f'label[sprite{sid}]', s))
                q += l2
        elif code == 0 and length == 0:
            break
    return found

for name in ['map.swf', 'house.swf', 'backgrounds.swf']:
    p = os.path.join(r'game_assets\swfs', name)
    if not os.path.exists(p):
        continue
    print(f'=== {name} ===')
    found = scan(p)
    print(f'  {len(found)} zone hits')
    for kind, nm in found[:30]:
        print(f'    {kind}: {nm}')
