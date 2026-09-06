import sqlite3
import os
import struct
import lz4.block

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

for key in [1, 2, 3]:
    cur.execute("SELECT data FROM cats WHERE key=?", (key,))
    blob = cur.fetchone()[0]
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    raw = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    
    p = raw.find(b'DefaultMove') - 8
    print(f"\n=================== Cat {key} Abilities to End ===================")
    
    # Read string after string
    str_idx = 0
    while p < len(raw) - 8:
        slen = struct.unpack_from('<Q', raw, p)[0]
        if 1 <= slen <= 40 and p + 8 + slen <= len(raw):
            sub = raw[p+8 : p+8+slen]
            if all(32 <= b <= 126 for b in sub) and any(chr(b).isalpha() for b in sub):
                s = sub.decode('ascii')
                print(f"[{str_idx:2d}] At 0x{p:04X}: '{s}' (len={slen})")
                p += 8 + slen
                str_idx += 1
                continue
        p += 1
