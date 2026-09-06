import sqlite3
import os
import struct
import lz4.block
from mewgenics_core import MewgenicsSaveManager, CatRecord

save_path = MewgenicsSaveManager.find_default_save()
mgr = MewgenicsSaveManager(save_path)

c = mgr.cats[758]
raw = c.raw_data

print(f"Cat 758 '{c.name}' raw length: {len(raw)} bytes")

# Print all doubles in raw_data that look like values between -2.0 and +2.0
print("\nScanning all doubles in raw_data:")
for i in range(0, len(raw) - 8, 4):
    val = struct.unpack_from('<d', raw, i)[0]
    if -5.0 < val < 5.0 and abs(val) > 0.001 and val != 1.0:
        print(f"  offset {hex(i)}: double = {val:.4f}")

# Print ints/flags around voice/stats
print("\nOffsets around stats:")
# stats are at p
p_base = raw.find(struct.pack('<7i', *c.base_stats))
print(f"Base stats offset: {hex(p_base)}")
print(f"Bonus stats offset: {hex(p_base + 28)}")

# What is between bonus_stats and boon?
p_mid = p_base + 56
p_boon = c.str_records[0][0]
mid_chunk = raw[p_mid : p_boon]
print(f"Mid chunk ({hex(p_mid)} - {hex(p_boon)}, {len(mid_chunk)} bytes):")
print("  Hex:", mid_chunk.hex())

# Unpack mid_chunk as ints, floats, doubles
for i in range(0, len(mid_chunk) - 4, 4):
    i32 = struct.unpack_from('<i', mid_chunk, i)[0]
    f32 = struct.unpack_from('<f', mid_chunk, i)[0]
    print(f"  +0x{i:02x}: int={i32}, float={f32:.3f}")
