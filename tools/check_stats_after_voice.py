import sqlite3
import os
import struct
import lz4.block

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, data FROM cats LIMIT 5")
for key, blob in cur.fetchall():
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    data = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    
    # Find voice string ('male' or 'female')
    pos_v = data.find(b'male')
    if pos_v == -1: pos_v = data.find(b'female')
    
    # Check after voice string
    # Length of voice string is at pos_v - 8
    v_len = struct.unpack_from('<Q', data, pos_v - 8)[0]
    pos_after_voice = pos_v + v_len
    
    print(f"\nCat {key} - after voice (0x{pos_after_voice:04X}):")
    # Read double at pos_after_voice
    dbl = struct.unpack_from('<d', data, pos_after_voice)[0]
    print(f"  Double: {dbl}")
    
    # Read ints after double
    ints = struct.unpack_from('<10i', data, pos_after_voice + 8)
    print(f"  Ints: {ints}")
