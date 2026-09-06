import sqlite3, os, struct, lz4.block, re

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

for key in [1, 2, 835]:
    cur.execute("SELECT data FROM cats WHERE key=?", (key,))
    blob = cur.fetchone()[0]
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    raw = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    
    # Name
    nl = struct.unpack_from('<Q', raw, 0x0c)[0]
    p_after_name = 0x14 + nl * 2
    
    # Title
    tl = struct.unpack_from('<Q', raw, p_after_name + 24)[0]
    p_after_title = p_after_name + 24 + 8 + tl
    
    # Search for voice
    m = re.search(rb'(?:male|female)\d*', raw)
    p_voice = m.start()
    p_voice_len = p_voice - 8
    
    dist = p_voice_len - p_after_title
    print(f"Cat {key}: dist from title end to voice_len = {dist} bytes")
    # Check what is in the first 16 bytes after title
    print(f"   First 16 bytes after title: {raw[p_after_title : p_after_title + 16].hex(' ')}")
