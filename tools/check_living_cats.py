import sqlite3
import os
import struct
import lz4.block

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, length(data) FROM cats")
cats = cur.fetchall()
print(f"Total cats in save: {len(cats)}")

# Let's inspect the last 20 cats in the table (these are likely the latest generated/living cats)
last_cats = cats[-15:]
for key, l in last_cats:
    cur.execute("SELECT data FROM cats WHERE key=?", (key,))
    blob = cur.fetchone()[0]
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    data = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    
    name_len = struct.unpack_from('<Q', data, 0x0C)[0]
    name = data[0x14 : 0x14 + name_len * 2].decode('utf-16le', errors='ignore')
    
    # Check end of cat blob
    tail = data[-32:]
    print(f"Cat {key:3d} ('{name}'): Len={len(data)}, Tail Hex={tail[-16:].hex(' ')}")
