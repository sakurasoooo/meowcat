import sqlite3
import os
import struct
import lz4.block

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, data FROM cats LIMIT 50")
rows = cur.fetchall()

cats = []
for key, blob in rows:
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    data = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    cats.append((key, data))

print(f"Loaded {len(cats)} decompressed cats.")
lens = [len(c[1]) for c in cats]
print(f"Min length: {min(lens)}, Max length: {max(lens)}, Average: {sum(lens)/len(lens):.1f}")

# Let's inspect the exact layout of Cat 1 (length 922)
cat_id, d = cats[0]
print(f"\nDissecting Cat {cat_id} (Length: {len(d)}):")

# 0x00: uint32
v0 = struct.unpack_from('<I', d, 0)[0]
print(f"  0x00: uint32 = {v0}")

# 0x04: uint64 (GUID?)
guid = struct.unpack_from('<Q', d, 4)[0]
print(f"  0x04: uint64 GUID = {hex(guid)}")

# 0x0C: uint64 name length
name_len = struct.unpack_from('<Q', d, 0x0C)[0]
name = d[0x14 : 0x14 + name_len * 2].decode('utf-16le')
print(f"  0x0C: Name len={name_len}, Name='{name}'")

cur_pos = 0x14 + name_len * 2
print(f"  Position after name: 0x{cur_pos:04X} ({cur_pos})")

# Let's check what is at cur_pos
print("  Next 32 bytes after name:", d[cur_pos : cur_pos + 32].hex(' '))
