import sqlite3
import os
import struct
import lz4.block
import re

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

for key in [1, 2, 3, 4, 5]:
    cur.execute("SELECT data FROM cats WHERE key=?", (key,))
    blob = cur.fetchone()[0]
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    raw = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    
    p_move = raw.find(b'DefaultMove')
    p_move_len = p_move - 8
    
    # Boon string ends before p_move_len
    # Let's inspect the 20 bytes before p_move_len
    chunk = raw[p_move_len - 24 : p_move_len]
    print(f"Cat {key} before move_len (24 bytes):")
    print("  Hex:", chunk.hex(' '))
    print("  ASCII:", ''.join(chr(b) if 32<=b<=126 else '.' for b in chunk))
