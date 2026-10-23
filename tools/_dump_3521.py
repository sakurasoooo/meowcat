"""Dump ui.swf sprite 3521 frame labels + PlaceObject children, and nearby leftover IDs."""
import io, os, struct, sys, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

UI = r'game_assets\swfs\ui.swf'


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


def walk_tags(data, start=0):
    p = start
    while p + 2 <= len(data):
        code_len = struct.unpack_from('<H', data, p)[0]
        code, length = code_len >> 6, code_len & 0x3F
        p += 2
        if length == 0x3F:
            if p + 4 > len(data):
                break
            length = struct.unpack_from('<I', data, p)[0]
            p += 4
        payload = data[p:p + length]
        p += length
        yield code, payload
        if code == 0 and length == 0:
            break


def place_id(code, payload):
    """Return characterId from PlaceObject / PlaceObject2 / PlaceObject3 if present."""
    if code == 4 and len(payload) >= 2:  # PlaceObject
        return struct.unpack_from('<H', payload, 0)[0]
    if code in (26, 70) and len(payload) >= 3:  # PlaceObject2/3
        flags = payload[0]
        # PO2: flags bit 1 = HasCharacter; PO3 similar after extra flags
        off = 1
        if code == 70:
            extra = payload[1]
            off = 2
        depth = struct.unpack_from('<H', payload, off)[0]
        off += 2
        has_char = bool(flags & 0x02)
        if has_char and off + 2 <= len(payload):
            return struct.unpack_from('<H', payload, off)[0]
        return None
    return None


data = open(UI, 'rb').read()
body = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
p0 = read_rect(body, 0) + 4
sprites = {}
shapes = {}
for code, payload in walk_tags(body, p0):
    if code == 39 and len(payload) >= 4:
        sid = struct.unpack_from('<H', payload, 0)[0]
        sprites[sid] = payload
    elif code in (2, 22, 32, 83) and len(payload) >= 2:
        shapes[struct.unpack_from('<H', payload, 0)[0]] = code

print('=== sprite 3521 ===')
pl = sprites[3521]
print('framecount', struct.unpack_from('<H', pl, 2)[0])
frame = 1
placed = []
labels = {}
for code, payload in walk_tags(pl, 4):
    if code == 43:
        name = payload.rstrip(b'\x00').decode('utf-8', errors='replace')
        labels[frame] = name
        print(f'  LABEL f{frame}: {name}')
    elif code in (4, 26, 70):
        cid = place_id(code, payload)
        if cid is not None:
            placed.append((frame, cid, code))
            print(f'  PLACE f{frame}: cid={cid} tag={code}')
    elif code in (5, 28):  # RemoveObject / RemoveObject2
        print(f'  REMOVE f{frame} tag={code} {payload[:8].hex()}')
    elif code == 1:  # ShowFrame
        frame += 1

print('\n=== nearby sprites ===')
for sid in range(3490, 3540):
    if sid in sprites:
        fc = struct.unpack_from('<H', sprites[sid], 2)[0]
        labs = []
        fr = 1
        kids = []
        for code, payload in walk_tags(sprites[sid], 4):
            if code == 43:
                labs.append((fr, payload.rstrip(b'\x00').decode('utf-8', errors='replace')))
            elif code in (4, 26, 70):
                cid = place_id(code, payload)
                if cid is not None:
                    kids.append((fr, cid))
            elif code == 1:
                fr += 1
        print(f'  sprite {sid} frames={fc} labels={labs} kids={kids[:20]}')
    elif sid in shapes:
        print(f'  shape  {sid}')
