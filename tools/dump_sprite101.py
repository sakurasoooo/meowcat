"""Dump ui.swf sprite 101 labels (UnlockArea badges); extract the 9 major-zone unlock badges."""
import io, sys, os, struct, zlib, subprocess, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from PIL import Image

class BR:
    def __init__(s, b): s.b = b; s.pos = 0
    def ub(s, n):
        v = 0
        for _ in range(n):
            byte = s.b[s.pos >> 3]; bit = (byte >> (7 - (s.pos & 7))) & 1
            v = (v << 1) | bit; s.pos += 1
        return v
    def al(s): s.pos = (s.pos + 7) & ~7
def rr(b, o):
    n = (b[o] >> 3) & 0x1F; br = BR(b[o:]); br.ub(5); br.ub(n * 4); br.al()
    return o + (br.pos >> 3)

def slabels(path, want):
    data = open(path, 'rb').read()
    body = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
    p = rr(body, 0) + 4; target = None
    while p < len(body):
        try: cl = struct.unpack_from('<H', body, p)[0]
        except struct.error: break
        c, l = cl >> 6, cl & 0x3F; p += 2
        if l == 0x3F:
            if p + 4 > len(body): break
            l = struct.unpack_from('<I', body, p)[0]; p += 4
        pl = body[p:p + l]; p += l
        if c == 39:
            sd = struct.unpack_from('<H', pl, 0)[0]
            if sd == want: target = pl
        if c == 0 and l == 0: break
    if target is None: return {}
    q = 4; fr = 0; lab = {}
    while q < len(target):
        try: cl = struct.unpack_from('<H', target, q)[0]
        except struct.error: break
        c, l = cl >> 6, cl & 0x3F; q += 2
        if l == 0x3F:
            if q + 4 > len(target): break
            l = struct.unpack_from('<I', target, q)[0]; q += 4
        if c == 0 and l == 0: break
        if c == 1: fr += 1
        elif c == 43: lab[fr] = target[q:q + l].rstrip(b'\x00').decode('utf-8', 'replace')
        q += l
    return lab

labs = slabels(r'game_assets\swfs\ui.swf', 101)
print('sprite 101 labels:', {f: l for f, l in labs.items()})
