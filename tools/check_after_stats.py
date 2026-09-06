import sqlite3
import os
import struct
import lz4.block
import re

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, data FROM cats LIMIT 5")
for key, blob in cur.fetchall():
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    data = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    
    m = re.search(rb'(?:male|female)', data)
    pos = m.start()
    len_prefix = struct.unpack_from('<Q', data, pos - 8)[0]
    stats_pos = pos + len_prefix + 8
    
    base_stats = struct.unpack_from('<7i', data, stats_pos)
    bonus_stats = struct.unpack_from('<7i', data, stats_pos + 28)
    
    after_bonus = stats_pos + 56
    print(f"\nCat {key}:")
    print(f"  Base Stats:  {base_stats}")
    print(f"  Bonus Stats: {bonus_stats}")
    print(f"  After bonus (0x{after_bonus:04X}):")
    # Read next 64 bytes
    chunk = data[after_bonus : after_bonus + 64]
    print("    Hex:", chunk.hex(' '))
    # Check if there are strings
    found_strs = []
    p = after_bonus
    while p < min(len(data) - 8, after_bonus + 128):
        slen = struct.unpack_from('<Q', data, p)[0]
        if 1 <= slen <= 32 and p + 8 + slen <= len(data):
            try:
                st = data[p+8 : p+8+slen].decode('ascii')
                if any(c.isalpha() for c in st):
                    found_strs.append((p, slen, st))
            except:
                pass
        p += 1
    for p, slen, st in found_strs[:6]:
        print(f"    String at 0x{p:04X} (len={slen}): '{st}'")
