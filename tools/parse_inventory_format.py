"""Nail the inventory_storage entry format by alignment-based parsing (read-only)."""
import sqlite3, os, struct, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

p = os.path.expandvars(r'%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav')
data = sqlite3.connect(p).execute("SELECT data FROM files WHERE key='inventory_storage'").fetchone()[0]

count = struct.unpack_from('<I', data, 0)[0]
print(f'count={count}, total={len(data)} bytes')

# hypothesis: entry = [u32 a][u8 b][u64 len][name][8 bytes][i32 c][u32 d][u32 e][u16/u32 f][u8 FF?][u8 01?]
# parse greedily: after fixed head, consume tail until next valid entry header
def try_header(off):
    if off + 13 > len(data):
        return None
    a, b = struct.unpack_from('<IB', data, off)
    ln = struct.unpack_from('<Q', data, off + 5)[0]
    if a != 5 or b != 1 or not (1 <= ln <= 40):
        return None
    end = off + 13 + ln
    if end > len(data):
        return None
    name = data[off+13:end]
    if all(32 <= c <= 126 for c in name):
        return end, name.decode()
    return None

off = 4
items = []
for i in range(count):
    h = try_header(off)
    if not h:
        print(f'HEADER FAIL at item {i}, off={hex(off)}')
        break
    name_end, name = h
    # find next header by scanning forward from name_end
    nxt = None
    for probe in range(name_end, min(name_end + 64, len(data))):
        if try_header(probe):
            nxt = probe
            break
    tail = data[name_end:nxt] if nxt else data[name_end:]
    items.append((name, off, name_end, nxt, tail))
    if nxt is None:
        print(f'item {i} {name}: last item, tail={tail.hex()} ({len(tail)} bytes)')
        break
    off = nxt

print(f'parsed {len(items)} items\n')
# group tails by pattern
from collections import Counter
patterns = Counter(len(t[4]) for t in items)
print('tail lengths distribution:', dict(patterns))
for name, so, ne, nxt, tail in items[:12]:
    t = tail.hex()
    print(f'{name:24s} tail[{len(tail):2d}]={t}')
# analyze tail structure: 8z, FFFFFFFF(-1), then?
print()
for name, so, ne, nxt, tail in items:
    if len(tail) >= 14:
        z8 = tail[:8]
        m1 = struct.unpack_from('<i', tail, 8)[0]
        rest = tail[12:]
        print(f'{name:24s} zeros={z8.hex()} m1={m1} rest={rest.hex()}')
