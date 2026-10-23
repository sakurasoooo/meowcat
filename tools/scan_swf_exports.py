"""Scan arbitrary SWFs for FrameLabels matching move-ability keywords (per-sprite)."""
import io, sys, struct, zlib, re
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

def walk_sprites(body):
    p = read_rect(body, 0)
    p += 4
    sprites = {}
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
        if code == 39:
            sid = struct.unpack_from('<H', payload, 0)[0]
            sprites[sid] = payload
        elif code == 76:  # SymbolClass / export assets: name->tag ref (useful!)
            q = 0
            cnt = struct.unpack_from('<H', payload, q)[0]; q += 2
            for _ in range(cnt):
                tag_id = struct.unpack_from('<H', payload, q)[0]; q += 2
                nm = payload[q:payload.find(b'\x00', q)].decode('utf-8', errors='replace')
                q += len(nm) + 1
                yield ('export', tag_id, nm)
        if code == 0 and length == 0:
            break

def sprite_labels(payload):
    q = 4
    labels = {}
    while q < len(payload):
        try:
            code_len = struct.unpack_from('<H', payload, q)[0]
        except struct.error:
            break
        code = code_len >> 6
        length = code_len & 0x3F
        q += 2
        if length == 0x3F:
            if q + 4 > len(payload):
                break
            length = struct.unpack_from('<I', payload, q)[0]
            q += 4
        if code == 0 and length == 0:
            break
        if code == 43:
            s = payload[q:q + length].rstrip(b'\x00').decode('utf-8', errors='replace')
            labels[len(labels) + 1] = s
        q += length
    return labels

PAT = re.compile(r'(move|teleport|jump|dash|dig|swim|trample|shadow|float|swap)', re.I)

for path in sys.argv[1:]:
    data = open(path, 'rb').read()
    body = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
    hits_found = False
    exports = []
    for item in walk_sprites(body):
        if item[0] == 'export':
            exports.append(item[2])
    print(f'=== {path}: {len(exports)} exports')

    # ExportAssets 名字直接匹配
    for nm in exports:
        if PAT.search(nm):
            print('  EXPORT:', nm)
