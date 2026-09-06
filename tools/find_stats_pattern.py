import sqlite3
import os
import struct
import lz4.block

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT data FROM cats WHERE key=1")
blob = cur.fetchone()[0]
unc_sz = struct.unpack_from('<I', blob, 0)[0]
data = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)

print("Searching for stat-like patterns (int32 sequence 1..15) in Cat 1:")
for off in range(0, len(data) - 28, 4):
    vals = struct.unpack_from('<7i', data, off)
    if all(0 <= v <= 20 for v in vals) and any(v > 0 for v in vals):
        # Check if there is some variance
        if len(set(vals)) >= 3:
            print(f"Offset 0x{off:04X} ({off}): int32[7] = {vals}")

# Also check as int16
print("\nSearching as int16[7]:")
for off in range(0, len(data) - 14, 2):
    vals = struct.unpack_from('<7h', data, off)
    if all(0 <= v <= 20 for v in vals) and any(v > 0 for v in vals):
        if len(set(vals)) >= 3:
            print(f"Offset 0x{off:04X} ({off}): int16[7] = {vals}")

# Also check as uint8
print("\nSearching as uint8[7]:")
for off in range(0, len(data) - 7, 1):
    vals = tuple(data[off : off + 7])
    if all(1 <= v <= 20 for v in vals):
        if len(set(vals)) >= 3:
            print(f"Offset 0x{off:04X} ({off}): uint8[7] = {vals}")
