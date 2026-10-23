"""Dump inventory_storage and furniture blobs to understand their formats (read-only)."""
import sqlite3, os, struct, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

p = os.path.expandvars(r'%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav')
conn = sqlite3.connect(p)

def hexdump(data, max_len=256):
    for i in range(0, min(len(data), max_len), 16):
        chunk = data[i:i+16]
        print(f'  {i:04X}: {" ".join(f"{b:02X}" for b in chunk):<48} {"".join(chr(b) if 32<=b<=126 else "." for b in chunk)}')

for key in ['inventory_storage', 'inventory_backpack', 'inventory_trash']:
    data = conn.execute("SELECT data FROM files WHERE key=?", (key,)).fetchone()[0]
    print(f'=== files/{key}: {len(data)} bytes ===')
    hexdump(data, 400 if 'storage' in key else 64)
    # scan for strings
    strs = [m.group().decode() for m in re.finditer(rb'[\x20-\x7e]{4,60}', data)]
    print('  strings:', strs[:20])
    print()

print('=== furniture table samples ===')
for key, data in conn.execute('SELECT key, data FROM furniture ORDER BY key LIMIT 6'):
    print(f'--- furniture key={key}: {len(data)} bytes')
    hexdump(data, 96)
    strs = [m.group().decode() for m in re.finditer(rb'[\x20-\x7e]{3,50}', data)]
    print('  strings:', strs[:10])
