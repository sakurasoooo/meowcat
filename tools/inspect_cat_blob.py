import sqlite3
import os
import zlib

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

print("--- PROPERTIES SAMPLE ---")
cur.execute("SELECT key, data FROM properties LIMIT 25")
for k, v in cur.fetchall():
    print(f"{k}: {repr(v)[:100]}")

print("\n--- FILES ---")
cur.execute("SELECT key, length(data) FROM files")
for k, l in cur.fetchall():
    print(f"{k}: length={l}")

print("\n--- CATS SAMPLE ---")
cur.execute("SELECT key, length(data), hex(substr(data, 1, 32)) FROM cats LIMIT 5")
for k, l, h in cur.fetchall():
    print(f"Cat {k}: length={l}, hex={h}")

cur.execute("SELECT key, data FROM cats LIMIT 1")
row = cur.fetchone()
cat_id, cat_blob = row[0], row[1]
print(f"\nCat {cat_id} Raw Head 64 bytes:")
print(cat_blob[:64].hex(' '))
print("ASCII interpretation:")
print(''.join(chr(b) if 32 <= b <= 126 else '.' for b in cat_blob[:128]))

# Test zlib decompression
try:
    decomp = zlib.decompress(cat_blob)
    print("\nZlib decompressed successfully! Length:", len(decomp))
    print(decomp[:100])
except Exception as e:
    print("\nZlib decompression failed:", e)

# Test zlib with offset or raw inflate
for offset in range(16):
    try:
        decomp = zlib.decompress(cat_blob[offset:])
        print(f"\nZlib decompressed at offset {offset}! Length:", len(decomp))
        print(decomp[:100])
        break
    except:
        pass
