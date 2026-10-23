"""List ui.swf exports matching button/icon keywords (self-contained)."""
import io as _io
import sys as _sys
_orig = _sys.stdout.buffer
_sys.stdout = _io.TextIOWrapper(_orig, encoding='utf-8')
import struct, zlib

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

def walk_exports(body):
    p = read_rect(body, 0)
    p += 4
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
                yield nm
        if code == 0 and length == 0:
            break

data = open(r'game_assets\swfs\ui.swf', 'rb').read()
body = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
ex = list(walk_exports(body))
kw = ['btn', 'icon', 'button']
hits = [n for n in ex if any(k in n.lower() for k in kw)]
print(len(ex), 'exports,', len(hits), 'button/icon-like:')
for h in hits:
    print(' ', h)
