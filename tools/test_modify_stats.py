import sqlite3
import os
import struct
import lz4.block
import re

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")

# We will work on an in-memory SQLite DB or test DB first
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT data FROM cats WHERE key=835")
blob = cur.fetchone()[0]
unc_sz = struct.unpack_from('<I', blob, 0)[0]
data = bytearray(lz4.block.decompress(blob[4:], uncompressed_size=unc_sz))

print("Original uncompressed length:", len(data))

# Let's inspect modifying stats:
m = re.search(rb'(?:male|female)\d*', data)
pos_v = m.start()
v_len = struct.unpack_from('<Q', data, pos_v - 8)[0]
stats_pos = pos_v + v_len + 8

old_stats = struct.unpack_from('<7i', data, stats_pos)
print("Old Base Stats:", old_stats)

# Modify stats to (20, 20, 20, 20, 20, 20, 20)
new_stats = (20, 20, 20, 20, 20, 20, 20)
struct.pack_into('<7i', data, stats_pos, *new_stats)

# Verify stats updated in buffer
updated_stats = struct.unpack_from('<7i', data, stats_pos)
print("Updated Base Stats in buffer:", updated_stats)

# Recompress
comp = lz4.block.compress(bytes(data), store_size=False)
final_blob = struct.pack('<I', len(data)) + comp
print(f"Recompressed blob size: {len(final_blob)} (Original: {len(blob)})")

# Decompress and verify
test_unc_sz = struct.unpack_from('<I', final_blob, 0)[0]
decomp = lz4.block.decompress(final_blob[4:], uncompressed_size=test_unc_sz)
assert struct.unpack_from('<7i', decomp, stats_pos) == new_stats
print("Roundtrip modification SUCCESS!")
