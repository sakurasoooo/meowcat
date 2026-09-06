import sqlite3
import os
import struct
import lz4.block
import re

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, data FROM cats LIMIT 10")
for key, blob in cur.fetchall():
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    data = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    
    # Search for voice string: 8-byte length followed by (male\d+|female\d+)
    m = re.search(rb'(?:male|female)\d+', data)
    if m:
        pos_v = m.start()
        v_len = m.end() - m.start()
        voice_str = data[pos_v : pos_v + v_len].decode('ascii')
        
        pos_after_voice = pos_v + v_len
        voice_pitch = struct.unpack_from('<d', data, pos_after_voice)[0]
        
        # 7 base stats
        stats = struct.unpack_from('<7i', data, pos_after_voice + 8)
        # extra fields
        extra_ints = struct.unpack_from('<7i', data, pos_after_voice + 8 + 28)
        
        name_len = struct.unpack_from('<Q', data, 0x0C)[0]
        name = data[0x14 : 0x14 + name_len * 2].decode('utf-16le', errors='ignore')
        
        print(f"Cat {key:3d} ('{name}'): Voice='{voice_str}', Pitch={voice_pitch:.3f}")
        print(f"    Base Stats -> STR:{stats[0]:2d}, DEX:{stats[1]:2d}, CON:{stats[2]:2d}, INT:{stats[3]:2d}, SPD:{stats[4]:2d}, CHA:{stats[5]:2d}, LCK:{stats[6]:2d} (Sum={sum(stats)})")
        print(f"    Extra Ints -> {extra_ints}")
