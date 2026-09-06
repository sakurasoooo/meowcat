import sqlite3
import os
import struct

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, data FROM cats WHERE key=1")
row = cur.fetchone()
key, data = row[0], row[1]

print(f"Cat 1 Total Length: {len(data)}")

# Let's inspect string extraction across the entire blob
print("\n--- All ASCII / UTF-16 strings in Cat 1 ---")
# Check UTF-16LE strings (min length 2 chars)
i = 0
while i < len(data) - 4:
    # Try reading as utf-16
    j = i
    chars = []
    while j < len(data) - 1:
        w = data[j:j+2]
        if w[1] == 0 and 32 <= w[0] <= 126:
            chars.append(chr(w[0]))
            j += 2
        else:
            break
    if len(chars) >= 3:
        print(f"Offset 0x{i:04X} ({i}): UTF-16LE: {''.join(chars)}")
        i = j
    else:
        i += 1

# Check ASCII strings
i = 0
while i < len(data) - 3:
    j = i
    chars = []
    while j < len(data):
        b = data[j]
        if 32 <= b <= 126:
            chars.append(chr(b))
            j += 1
        else:
            break
    if len(chars) >= 3:
        print(f"Offset 0x{i:04X} ({i}): ASCII: {''.join(chars)}")
        i = j
    else:
        i += 1
