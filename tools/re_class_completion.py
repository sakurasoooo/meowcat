"""Extract full class x zone completion matrix from npc_progress."""
import sqlite3, os, sys, io, struct
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = os.path.expandvars(r'%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav')
data = sqlite3.connect(p).execute("SELECT data FROM files WHERE key='npc_progress'").fetchone()[0]

ZONES = ['debug', 'tutorial', 'alley', 'sewers', 'junkyard', 'caves', 'boneyard', 'meatworld',
         'desert', 'crater', 'bunker', 'moon', 'core', 'dimensionx', 'lab', 'iceage',
         'future', 'jurassic', 'theend', 'endoftime']
CLASSES = ['Colorless', 'Fighter', 'Hunter', 'Mage', 'Tank', 'Medic', 'Thief',
           'Necromancer', 'Tinkerer', 'Druid', 'Butcher', 'Psychic', 'Monk', 'Jester', 'any']

records = {}
p = 0
n = len(data)
while p + 16 < n:
    zl = struct.unpack_from('<Q', data, p)[0]
    if 3 <= zl <= 12 and p + 8 + zl + 8 < n:
        zone = data[p+8:p+8+zl].decode('ascii', errors='ignore')
        if zone in ZONES:
            q = p + 8 + zl
            cl = struct.unpack_from('<Q', data, q)[0]
            if 3 <= cl <= 12 and q + 8 + cl + 20 <= n:
                cls = data[q+8:q+8+cl].decode('ascii', errors='ignore')
                if cls in CLASSES:
                    t = q + 8 + cl
                    a, b, visits, z1, z2 = struct.unpack_from('<IIIII', data, t)
                    a = a if a != 0xFFFFFFFF else -1
                    b = b if b != 0xFFFFFFFF else -1
                    records[(cls, zone)] = (a, b, visits)
                    p = t
                    continue
    p += 1

print(f'{len(records)} records')
combos = Counter((a, b) for a, b, v in records.values())
print('(a,b) combos:', dict(combos))

MAJOR = ['caves', 'boneyard', 'moon', 'core', 'jurassic', 'theend', 'meatworld', 'dimensionx', 'endoftime']
classes_present = sorted({c for c, z in records})
print()
hdr = 'class'.ljust(13) + ''.join(z[:8].ljust(10) for z in MAJOR)
print(hdr)
for c in classes_present:
    row = c.ljust(13)
    for z in MAJOR:
        r = records.get((c, z))
        row += (f'{r[0]},{r[1]},v{r[2]}'.ljust(10) if r else '-'.ljust(10))
    print(row)
print()
print('--- all zones per class (non-major too) ---')
for c in classes_present:
    zs = {z: (a, b, v) for (cc, z), (a, b, v) in records.items() if cc == c}
    print(c, zs)
