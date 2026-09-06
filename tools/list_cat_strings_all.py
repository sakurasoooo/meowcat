import sqlite3
import os
import struct
import lz4.block

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

def get_all_strings(data):
    p = 0
    strs = []
    while p < len(data) - 8:
        slen = struct.unpack_from('<Q', data, p)[0]
        if 1 <= slen <= 50 and p + 8 + slen <= len(data):
            chunk = data[p+8 : p+8+slen]
            if all(32 <= b <= 126 for b in chunk) and any(chr(b).isalpha() for b in chunk):
                s = chunk.decode('ascii')
                strs.append((p, slen, s))
                p += 8 + slen
                continue
        p += 1
    return strs

for cid in [1, 2, 6, 830, 835]:
    cur.execute("SELECT data FROM cats WHERE key=?", (cid,))
    blob = cur.fetchone()[0]
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    raw = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    
    nl = struct.unpack_from('<Q', raw, 0x0c)[0]
    name = raw[0x14 : 0x14 + nl*2].decode('utf-16le')
    s_list = get_all_strings(raw)
    print(f"\n--- Cat {cid} ('{name}', total length: {len(raw)}) ---")
    for i, (off, slen, st) in enumerate(s_list):
        print(f"  [{i:2d}] (0x{off:04X}): '{st}'")
