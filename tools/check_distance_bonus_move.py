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
    
    # Find voice
    m = re.search(rb'(?:male|female)\d*', raw)
    pos_v = m.start()
    v_len = struct.unpack_from('<Q', raw, pos_v - 8)[0]
    pos_after_voice = pos_v + v_len
    
    p_stats = pos_after_voice + 8
    p_after_bonus = p_stats + 56
    
    # Find 'DefaultMove'
    p_move = raw.find(b'DefaultMove')
    
    # Between p_after_bonus and p_move
    between = raw[p_after_bonus : p_move]
    print(f"Cat {key}: Distance between bonus stats and DefaultMove: {len(between)} bytes")
    print("  Hex:", between.hex(' '))
