"""Correct label->frame mapping via ShowFrame counting; list unlabeled frames."""
import io as _io
import sys as _sys
_sys.stdout = _io.TextIOWrapper(_sys.stdout.buffer, encoding='utf-8')
import struct, zlib, json

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

data = open(r'game_assets\swfs\ability_icons.swf', 'rb').read()
body = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
p = read_rect(body, 0) + 4

target = None
while p < len(body):
    code_len = struct.unpack_from('<H', body, p)[0]
    code = code_len >> 6
    length = code_len & 0x3F
    p += 2
    if length == 0x3F:
        length = struct.unpack_from('<I', body, p)[0]
        p += 4
    payload = body[p:p + length]
    p += length
    if code == 39:
        sid = struct.unpack_from('<H', payload, 0)[0]
        if sid == 1346:
            target = payload
        if code == 0 and length == 0:
            break

q = 4
frame = 0
labels = {}      # frame -> label
order = 0
while q < len(target):
    code_len = struct.unpack_from('<H', target, q)[0]
    code = code_len >> 6
    length = code_len & 0x3F
    q += 2
    if length == 0x3F:
        length = struct.unpack_from('<I', target, q)[0]
        q += 4
    if code == 0 and length == 0:
        break
    if code == 1:      # ShowFrame
        frame += 1
    elif code == 43:   # FrameLabel
        s = target[q:q + length].rstrip(b'\x00').decode('utf-8', errors='replace')
        labels[frame] = s
    q += length

all_frames = set(range(1, 901))
labeled = set(labels)
unlabeled = sorted(all_frames - labeled)
print('total frames: 900/901, labeled:', len(labels), 'unlabeled:', len(unlabeled))
print('unlabeled frames:', unlabeled)
print()
# 已知移动键仍未标注？
MOVE_KEYS = ['DefaultMove', 'BasicJump', 'Teleport', 'BasicDig', 'Shadowstep', 'SwapPositions',
             'SwimmerMove', 'TrampleMove', 'TrampleMoveOne', 'MaxTeleport', 'FloatMove']
rev = {v: k for k, v in labels.items()}
for k in MOVE_KEYS:
    print(f'{k:18s} -> frame {rev.get(k)}')
print()
print('帧号 1..20 的标签:', [(f, labels.get(f)) for f in range(1, 21)])
json.dump(labels, open('tools/_ability_frame_labels.json', 'w'))
