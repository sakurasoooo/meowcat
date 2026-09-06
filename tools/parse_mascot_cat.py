import sqlite3
import os
import struct

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT data FROM files WHERE key='save_file_cat'")
data = cur.fetchone()[0]

print(f"save_file_cat length: {len(data)}")

# Let's inspect string extraction across save_file_cat
pos = 0
while pos < len(data) - 8:
    # Check if there is a 64-bit length prefix for utf-16 string
    strlen = struct.unpack_from('<Q', data, pos)[0]
    if 1 <= strlen <= 64 and pos + 8 + strlen*2 <= len(data):
        raw_str = data[pos+8 : pos+8+strlen*2]
        try:
            s = raw_str.decode('utf-16le')
            if all(32 <= ord(c) <= 126 for c in s):
                print(f"Offset 0x{pos:04X} ({pos}): UTF-16LE string (len={strlen}): '{s}'")
                pos += 8 + strlen*2
                continue
        except:
            pass
    # Check if there is a 64-bit length prefix for ASCII string
    if 1 <= strlen <= 64 and pos + 8 + strlen <= len(data):
        raw_str = data[pos+8 : pos+8+strlen]
        try:
            s = raw_str.decode('ascii')
            if all(32 <= ord(c) <= 126 for c in s) and any(c.isalpha() for c in s):
                print(f"Offset 0x{pos:04X} ({pos}): ASCII string (len={strlen}): '{s}'")
                pos += 8 + strlen
                continue
        except:
            pass
    pos += 1
