"""Get exact SWF labels for the 12 frames used in passive extraction."""
import io, sys, struct, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
exec(open(r'tools\scan_swf_frames2.py', encoding='utf-8').read().split('total frames')[0].split('def read_rect')[0]) if False else None
# 内联
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

p515 = slabels(r'game_assets\swfs\ability_icons.swf', 515)
p1346 = slabels(r'game_assets\swfs\ability_icons.swf', 1346)
# 我提取时 0-based frame +1 = FFDec 帧。slabels 返回的 frame 是 ShowFrame 1-based 计数（与 FFDec 帧一致）
MISSING = {
    'HUNTERSOUL': (515, 755), 'BUTCHERSOUL': (515, 487), 'JAGGEDEDGE': (515, 247),
    'IRONSKINTECHNIQUE': (515, 254), 'FRENZY': (515, 810), 'MATHQ': (515, 696),
    'PATELLARREFLEX': (515, 756), 'EMPTYVESSEL': (515, 220), 'PROTECTIVE': (515, 42),
    'SWIFTLOOTER': (515, 64), 'SYNTHESIZE': (515, 537), 'STARTER_PLACEHOLDER': (515, 405),
}
# 注意我实际用 515 还是 1346？fix_passive_icons 里 find_frame 可能返回 515 或 1346。按输出：
ACTUAL = {
    'HUNTERSOUL': (1346, 755), 'BUTCHERSOUL': (1346, 487), 'JAGGEDEDGE': (515, 247),
    'IRONSKINTECHNIQUE': (515, 254), 'FRENZY': (515, 810), 'MATHQ': (1346, 696),
    'PATELLARREFLEX': (1346, 756), 'EMPTYVESSEL': (515, 220), 'PROTECTIVE': (515, 42),
    'SWIFTLOOTER': (515, 64), 'SYNTHESIZE': (1346, 537), 'STARTER_PLACEHOLDER': (515, 405),
}
for key, (spr, fr) in ACTUAL.items():
    lab = (p515 if spr == 515 else p1346).get(fr)
    print(f'{key:22s} -> s{spr}#{fr} label={lab!r}')
