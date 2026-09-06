import sqlite3
import os
import struct
import lz4.block
import re

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

for key in [1, 2, 835]:
    cur.execute("SELECT data FROM cats WHERE key=?", (key,))
    blob = cur.fetchone()[0]
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    raw = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    
    # Find class
    m = re.search(rb'(?:Colorless|Fighter|Tank|Mage|Hunter|Medic|Thief|Necromancer|Butcher|Druid|Monk|Psychic|Tinkerer|Jester)', raw)
    p_cls = m.start()
    cls_len = struct.unpack_from('<Q', raw, p_cls - 8)[0]
    tail_start = p_cls + cls_len
    
    tail = raw[tail_start:]
    print(f"\nCat {key} Tail after Class ({len(tail)} bytes):")
    for i in range(0, min(len(tail), 128), 16):
        c = tail[i:i+16]
        print(f"  +{i:03X}: {' '.join(f'{b:02X}' for b in c):<48} {''.join(chr(b) if 32<=b<=126 else '.' for b in c)}")
