import sqlite3
import os
import struct
import lz4.block

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, data FROM cats LIMIT 5")
for key, blob in cur.fetchall():
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    d = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    name_len = struct.unpack_from('<Q', d, 0x0C)[0]
    name = d[0x14 : 0x14 + name_len * 2].decode('utf-16le')
    after_name = 0x14 + name_len * 2
    print(f"Cat {key} ('{name}'):")
    print("  Bytes after name (0x{:04X}): {}".format(after_name, d[after_name : after_name + 48].hex(' ')))
