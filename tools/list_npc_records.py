"""List ALL npc_progress record names (presence flags + valued) grouped by prefix."""
import io, sys, sqlite3, re, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from mewgenics_core import MewgenicsSaveManager
mgr = MewgenicsSaveManager()
blob = sqlite3.connect(mgr.file_path).execute("SELECT data FROM files WHERE key='npc_progress'").fetchone()[0]

# 提所有 [u64 len][name] 记录
names = []
p, n = 0, len(blob)
while p + 8 <= n:
    slen = struct.unpack_from('<Q', blob, p)[0]
    if 4 <= slen <= 60 and p + 8 + slen <= n:
        chunk = blob[p + 8 : p + 8 + slen]
        if all(32 <= b <= 126 for b in chunk):
            names.append(chunk.decode('ascii', errors='ignore'))
            p += 8 + slen
            continue
    p += 1
print(f'共 {len(names)} 条记录')
from collections import defaultdict
groups = defaultdict(list)
for nm in names:
    # 归组
    if 'difficulty_unlock' in nm:
        groups['difficulty_unlock'].append(nm)
    elif re.match(r'^(cleared|complete|finish)', nm, re.I):
        groups['cleared/complete'].append(nm)
    elif re.match(r'map_unlock', nm):
        groups['map_unlock'].append(nm)
    else:
        groups['other'].append(nm)
for g in ['difficulty_unlock', 'cleared/complete', 'map_unlock', 'other']:
    lst = groups.get(g, [])
    print(f'\n[{g}] {len(lst)}')
    for nm in sorted(set(lst))[:40]:
        print('   ', nm)
