import sqlite3
import os
import struct
import lz4.block
import re

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, data FROM cats WHERE key IN (1, 2, 5, 11)")
for key, blob in cur.fetchall():
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    data = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    
    m = re.search(rb'(?:male|female)', data)
    pos = m.start()
    len_prefix = struct.unpack_from('<Q', data, pos - 8)[0]
    print(f"Cat {key}: pos={hex(pos)}, len_prefix={len_prefix}, string={data[pos:pos+len_prefix]}")
