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
    after = pos + len_prefix
    
    print(f"\nCat {key} (voice='{data[pos:after].decode()}'):")
    chunk = data[after : after + 64]
    print("  Hex:", chunk.hex(' '))
    # Let's see where the stats (numbers around 1..10) are!
    for off in range(after, after + 40):
        ints = struct.unpack_from('<7i', data, off)
        if all(1 <= x <= 15 for x in ints) and 25 <= sum(ints) <= 45:
            print(f"  FOUND STATS at offset 0x{off:04X} (+{off - after} from voice end): {ints} (Sum={sum(ints)})")
            break
