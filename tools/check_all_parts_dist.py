import sqlite3, os, struct, lz4.block, re

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()
cur.execute("SELECT key, data FROM cats")
all_cats = cur.fetchall()

dists = set()
for key, blob in all_cats:
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    raw = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    
    nl = struct.unpack_from('<Q', raw, 0x0c)[0]
    p_after_name = 0x14 + nl * 2
    tl = struct.unpack_from('<Q', raw, p_after_name + 24)[0]
    p_after_title = p_after_name + 24 + 8 + tl
    
    m = re.search(rb'(?:male|female|spidercat|demoncat|robotcat)\d*', raw)
    if m:
        p_voice = m.start()
        p_voice_len = p_voice - 8
        dists.add(p_voice_len - p_after_title)
    else:
        print(f"Cat {key} did not match voice regex!")

print(f"Distinct distances across {len(all_cats)} cats: {dists}")
