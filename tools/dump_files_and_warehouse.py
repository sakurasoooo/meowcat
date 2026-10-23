"""List all files-table keys and dump favor/progress-related blobs; list room='' furniture names."""
import sqlite3, os, sys, io, struct, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mewgenics_core import FurnitureRecord

p = os.path.expandvars(r'%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav')
conn = sqlite3.connect(p)
print('=== files keys ===')
for k, l in conn.execute('SELECT key, length(data) FROM files'):
    print(f'  {k}: {l} bytes')

print()
print('=== room="" furniture (warehouse?) ===')
for k, blob in conn.execute('SELECT key, data FROM furniture'):
    r = FurnitureRecord.parse(blob, table_key=k)
    if r.room == '':
        print(f'  {k:3d}: {r.name} @({r.x},{r.y}) variant={r.variant}')

# dump unknown small blobs as strings
print()
for k, data in conn.execute('SELECT key, data FROM files'):
    if k in ('pedigree', 'name_gen_history_w', 'inventory_storage', 'inventory_backpack', 'inventory_trash', 'house_state', 'save_file_cat', 'house_unlocks', 'unlocks'):
        continue
    strs = [m.group().decode() for m in re.finditer(rb'[\x20-\x7e]{3,60}', data)]
    print(f'--- {k} ({len(data)}B) strings: {strs[:40]}')
