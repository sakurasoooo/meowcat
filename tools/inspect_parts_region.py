import sqlite3
import os
import struct
import lz4.block
import re

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, data FROM cats LIMIT 3")
for key, blob in cur.fetchall():
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    data = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    
    m = re.search(rb'(?:male|female)', data)
    pos_v = m.start() - 8 # start of voice string length
    
    name_len = struct.unpack_from('<Q', data, 0x0C)[0]
    name = data[0x14 : 0x14 + name_len * 2].decode('utf-16le')
    
    print(f"\n================ Cat {key} ('{name}') ================")
    # Print hex dump from 0x0020 to pos_v
    mid_chunk = data[0x0020 : pos_v]
    print(f"Middle section length: {len(mid_chunk)} bytes (0x0020 .. 0x{pos_v:04X})")
    for i in range(0, len(mid_chunk), 16):
        c = mid_chunk[i:i+16]
        hex_s = ' '.join(f"{b:02X}" for b in c)
        asc_s = ''.join(chr(b) if 32<=b<=126 else '.' for b in c)
        print(f"0x{0x0020 + i:04X}:  {hex_s:<48}  {asc_s}")
