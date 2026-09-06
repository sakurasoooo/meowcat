import sqlite3
import os

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, data FROM files")
for key, data in cur.fetchall():
    print(f"\n================ File Key: {key} ({len(data)} bytes) ================")
    print("Hex head:", data[:48].hex(' '))
    ascii_sample = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[:80])
    print("ASCII head:", ascii_sample)
