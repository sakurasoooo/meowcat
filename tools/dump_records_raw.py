"""Dump raw class_zone record bytes (all 5 ints) to find the per-(class,zone) difficulty field."""
import io, sys, sqlite3, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from mewgenics_core import _ZONE_IDS, _CLASS_IDS, MewgenicsSaveManager

mgr = MewgenicsSaveManager()
blob = sqlite3.connect(mgr.file_path).execute("SELECT data FROM files WHERE key='npc_progress'").fetchone()[0]

p, n = 0, len(blob)
cnt = 0
seen_b = {}
while p + 16 < n:
    zl = struct.unpack_from('<Q', blob, p)[0]
    if 3 <= zl <= 12 and p + 8 + zl + 8 < n:
        zone = blob[p + 8 : p + 8 + zl].decode('ascii', errors='ignore')
        if zone in _ZONE_IDS:
            q = p + 8 + zl
            cl = struct.unpack_from('<Q', blob, q)[0]
            if 3 <= cl <= 12 and q + 8 + cl + 20 <= n:
                cls = blob[q + 8 : q + 8 + cl].decode('ascii', errors='ignore')
                if cls in _CLASS_IDS:
                    t = q + 8 + cl
                    a, b, visits, c4, c5 = struct.unpack_from('<IIIII', blob, t)
                    a = -1 if a == 0xFFFFFFFF else a
                    b = -1 if b == 0xFFFFFFFF else b
                    seen_b.setdefault(b, []).append((cls, zone, a, visits))
                    cnt += 1
                    if cnt <= 14:
                        print(f'{cls:12s} {zone:12s} a={a} b={b} visits={visits} c4={c4} c5={c5}')
                    p = t + 20
                    continue
    p += 1

print()
print('b 值出现次数统计:')
for b, lst in seen_b.items():
    print(f'  b={b}: {len(lst)} 条 (样例 {lst[:3]})')
