"""Parse pedigree entries (stride 32: child, parentA, parentB, double) and test boon inheritance."""
import sqlite3, os, struct, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mewgenics_core import MewgenicsSaveManager

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
data = sqlite3.connect(save_path).execute("SELECT data FROM files WHERE key='pedigree'").fetchone()[0]
mgr = MewgenicsSaveManager(); mgr.load()
cats = mgr.cats if isinstance(mgr.cats, dict) else {c.key: c for c in mgr.cats}
valid = set(cats.keys())

# find stride-32 entries: (child:int64, parentA:int64, parentB:int64, double)
entries = []
for off in range(0, len(data) - 32, 4):
    a, b, c = struct.unpack_from('<3q', data, off)
    hi = struct.unpack_from('<I', data, off + 28)[0]  # double high word
    if a in valid and b in valid and c in valid and 0x3F000000 <= hi <= 0x41300000:
        entries.append((off, a, b, c))
print(f'candidate pedigree entries: {len(entries)}')

# boon inheritance test
STAT = ['str','dex','con','int','spd','cha','lck']
child_boon_from_parent = 0
child_boon_total = 0
mismatches = []
for off, child, pa, pb in entries:
    cc, ca, cb = cats[child], cats[pa], cats[pb]
    if cc.boon in STAT:
        child_boon_total += 1
        if cc.boon == ca.boon or cc.boon == cb.boon:
            child_boon_from_parent += 1
        else:
            mismatches.append((cc.name, cc.boon, ca.name, ca.boon, cb.name, cb.boon))
print(f'children with stat boon: {child_boon_total}')
print(f'  boon matches a parent: {child_boon_from_parent}')
for m in mismatches[:15]:
    print('  MISMATCH:', m)

# base-rate: probability a random cat has matching boon ~ (69/675)*(1/7)*2 ≈ 3%
print()
print('sample entries:')
for off, child, pa, pb in entries[:12]:
    print(f'  @{off}: {cats[child].name}(boon={cats[child].boon}) <- {cats[pa].name}(boon={cats[pa].boon}), {cats[pb].name}(boon={cats[pb].boon})')
