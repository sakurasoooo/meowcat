"""Explore pedigree blob: find 银月 (key=790) and possible parent keys nearby."""
import sqlite3, os, struct, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
data = conn.execute("SELECT data FROM files WHERE key='pedigree'").fetchone()[0]
print(f"pedigree blob: {len(data)} bytes")

from mewgenics_core import MewgenicsSaveManager
mgr = MewgenicsSaveManager(); mgr.load()
cats = mgr.cats if isinstance(mgr.cats, dict) else {c.key: c for c in mgr.cats}
valid_keys = set(cats.keys())
print(f"cats in save: {len(valid_keys)}, max key: {max(valid_keys)}")

# scan all int32 positions where value == 790
hits = []
for off in range(0, len(data) - 4):
    v = struct.unpack_from('<i', data, off)[0]
    if v == 790:
        ctx = struct.unpack_from('<8i', data, max(0, off - 16))
        after = struct.unpack_from('<8i', data, off)
        hits.append(off)
print(f"occurrences of key 790 as int32: {len(hits)}")
for off in hits[:6]:
    lo = max(0, off - 32)
    vals = struct.unpack_from('<' + 'i' * ((64) // 4), data, lo)
    marks = []
    for j, v in enumerate(vals):
        tag = ''
        if lo + j * 4 == off:
            tag = ' <== 790'
        elif v in valid_keys and v != 0:
            nm = cats[v].name
            tag = f'  (cat {v}: {nm})'
        marks.append(f'{lo + j*4:6d}: {v:6d}{tag}')
    print('\n'.join(marks))
    print('---')
