import sqlite3
import os
import struct

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, data FROM cats LIMIT 10")
rows = cur.fetchall()

print(f"Analyzing {len(rows)} cats:")
for key, blob in rows:
    print(f"\n================ Cat ID: {key} (Length: {len(blob)} bytes) ================")
    # Print hex dump in 16-byte lines
    for i in range(0, min(len(blob), 160), 16):
        chunk = blob[i:i+16]
        hex_str = ' '.join(f"{b:02X}" for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        print(f"{i:04X}:  {hex_str:<48}  {ascii_str}")
