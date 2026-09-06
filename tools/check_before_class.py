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
    
    p_color = raw.find(b'Colorless') - 8
    # Inspect 32 bytes before p_color
    chunk = raw[p_color - 32 : p_color]
    print(f"Cat {key} 32 bytes before Class (0x{p_color:04X}):")
    print("  Hex:", chunk.hex(' '))
    # Check ints
    u32s = struct.unpack_from('<8i', chunk, 0)
    print("  Ints:", u32s)
