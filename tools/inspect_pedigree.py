import sqlite3, os, struct

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()
cur.execute("SELECT data FROM files WHERE key='pedigree'")
data = cur.fetchone()[0]
print(f"pedigree length: {len(data)}")

# Let's inspect the first 128 bytes
print("First 128 bytes:")
for i in range(0, min(len(data), 128), 16):
    chunk = data[i:i+16]
    print(f"{i:04X}: {' '.join(f'{b:02X}' for b in chunk):<48} {''.join(chr(b) if 32<=b<=126 else '.' for b in chunk)}")

# In pedigree, how are entries structured?
# Head starts with: F5 FF FF FF FF FF FF FF 43 03 00 00 00 00 00 00 FF 03 00 00 00 00 00 00
# Notice 43 03 = 835! The max cat ID!
# FF 03 = 1023!
print("First 3 int64s:", struct.unpack_from('<3q', data, 0))
