"""Probe npcs.swf exports for shop NPC names."""
import io as _io, sys as _sys, struct, zlib, re
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

def exports(path):
    data = open(path, 'rb').read()
    body = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
    p = read_rect(body, 0) + 4
    out = []
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
                q += 2
                nm = payload[q:payload.find(b'\x00', q)].decode('utf-8', errors='replace')
                q += len(nm) + 1
                out.append(nm)
        if code == 0 and length == 0:
            break
    return out

PAT = re.compile(r'(butch|jack|tracy|tink|organ|shop|npc_|seller|beanies)', re.I)
ex = exports(r'game_assets\swfs\npcs.swf')
print(len(ex), 'exports')
hits = [n for n in ex if PAT.search(n)]
for h in hits[:60]:
    print(' ', h)
