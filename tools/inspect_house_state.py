import sqlite3
import os
import struct

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT data FROM files WHERE key='house_state'")
data = cur.fetchone()[0]
print(f"house_state length: {len(data)}")

# Let's inspect strings and ints in house_state
print("--- Hex head 128 bytes ---")
for i in range(0, min(len(data), 160), 16):
    chunk = data[i:i+16]
    print(f"{i:04X}: {' '.join(f'{b:02X}' for b in chunk):<48} {''.join(chr(b) if 32<=b<=126 else '.' for b in chunk)}")

# Search for cat IDs in house_state: e.g. int64 or int32 matching living cat keys
print("\n--- Potential Cat IDs (integers between 1 and 675) ---")
for off in range(0, len(data) - 8, 4):
    val_i32 = struct.unpack_from('<i', data, off)[0]
    val_i64 = struct.unpack_from('<q', data, off)[0]
    if 1 <= val_i32 <= 675:
        # Check if key exists in cats table
        cur.execute("SELECT key FROM cats WHERE key=?", (val_i32,))
        if cur.fetchone():
            print(f"  Offset 0x{off:04X}: int32 Cat ID = {val_i32}")
