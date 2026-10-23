"""Scan all SWFs' sprites for FrameLabels matching move keys (icons strip pattern)."""
import io as _io
import sys as _sys
_sys.stdout = _io.TextIOWrapper(_sys.stdout.buffer, encoding='utf-8')
import struct, zlib, os

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

MOVE_KEYS = ['DefaultMove', 'BasicJump', 'Teleport', 'BasicDig', 'Shadowstep', 'SwapPositions',
             'SwimmerMove', 'TrampleMove', 'TrampleMoveOne', 'MaxTeleport', 'FloatMove']

def scan(path):
    data = open(path, 'rb').read()
    body = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
    p = read_rect(body, 0) + 4
    n_sprites = 0
    found = {}
    exports = {}
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
            n_sprites += 1
            sid = struct.unpack_from('<H', payload, 0)[0]
            q = 4
            frame = 0
            labs = {}
            while q < len(payload):
                try:
                    cl2 = struct.unpack_from('<H', payload, q)[0]
                except struct.error:
                    break
                c2 = cl2 >> 6
                l2 = cl2 & 0x3F
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
                    labs.setdefault(frame, s)
                q += l2
            for fr, lb in labs.items():
                if lb in MOVE_KEYS:
                    found[lb] = (sid, fr)
        elif code == 76:
            q = 0
            cnt = struct.unpack_from('<H', payload, q)[0]; q += 2
            for _ in range(cnt):
                tag_id = struct.unpack_from('<H', payload, q)[0]; q += 2
                nm = payload[q:payload.find(b'\x00', q)].decode('utf-8', errors='replace')
                q += len(nm) + 1
                exports[nm] = tag_id
        elif code == 0 and length == 0:
            break
    print(f'{os.path.basename(path)}: {n_sprites} sprites, {len(exports)} exports')
    for lb in MOVE_KEYS:
        if lb in found:
            sid, fr = found[lb]
            print(f'  HIT {lb}: sprite {sid} frame {fr}')
        elif lb in exports:
            print(f'  EXPORT-HIT {lb}: tag {exports[lb]}')
    return found, exports

for name in ['ui.swf', 'effects.swf', 'map.swf', 'house.swf', 'portraits.swf']:
    scan(os.path.join(r'game_assets\swfs', name))
