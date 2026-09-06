import sqlite3
import os
import struct
import lz4.block

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, data FROM cats WHERE key=1")
row = cur.fetchone()
key, data = row[0], row[1]

uncompressed_size = struct.unpack_from('<I', data, 0)[0]
compressed_data = data[4:]
print(f"Cat 1: DB Size = {len(data)}, Uncompressed Size = {uncompressed_size}")

decompressed = lz4.block.decompress(compressed_data, uncompressed_size=uncompressed_size)
print(f"SUCCESSFULLY DECOMPRESSED! Length = {len(decompressed)}")

print("\n--- First 128 bytes hex ---")
for i in range(0, min(len(decompressed), 160), 16):
    chunk = decompressed[i:i+16]
    hex_str = ' '.join(f"{b:02X}" for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
    print(f"{i:04X}:  {hex_str:<48}  {ascii_str}")
