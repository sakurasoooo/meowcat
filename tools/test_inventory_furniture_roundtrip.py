"""Round-trip fidelity test: parse -> build must be byte-identical for inventories and furniture."""
import sqlite3, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mewgenics_core import InventoryBlob, FurnitureRecord

p = os.path.expandvars(r'%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav')
conn = sqlite3.connect(p)

ok = True
for box in ('storage', 'backpack', 'trash'):
    raw = conn.execute("SELECT data FROM files WHERE key=?", (f'inventory_{box}',)).fetchone()[0]
    rebuilt = InventoryBlob.parse(raw).build()
    match = rebuilt == raw
    print(f'inventory_{box}: {len(raw)} bytes, round-trip {"OK" if match else "MISMATCH"}')
    ok &= match

n_bad = 0
rows = conn.execute("SELECT key, data FROM furniture").fetchall()
for k, blob in rows:
    rebuilt = FurnitureRecord.parse(blob, table_key=k).build()
    if rebuilt != blob:
        n_bad += 1
        print(f'furniture key={k}: MISMATCH ({len(blob)} vs {len(rebuilt)})')
print(f'furniture: {len(rows)} rows, mismatches: {n_bad}')
ok &= (n_bad == 0)

print('\nRESULT:', 'ALL OK' if ok else 'FAILURES PRESENT')
sys.exit(0 if ok else 1)
