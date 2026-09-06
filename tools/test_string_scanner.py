import sqlite3, os, struct, lz4.block, re

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()
cur.execute("SELECT key, data FROM cats")
all_cats = cur.fetchall()

def parse_cat(raw):
    # Name
    nl = struct.unpack_from('<Q', raw, 0x0c)[0]
    name = raw[0x14 : 0x14 + nl*2].decode('utf-16le', errors='ignore')
    
    # Find voice & stats
    # Voice is followed by double pitch and 7 base stats
    m = re.search(rb'(?:male\d+|female\d+|robotom|spidercat|demoncat|robotcat)', raw)
    if not m:
        return None
    p_voice = m.start()
    p_voice_len = p_voice - 8
    vl = struct.unpack_from('<Q', raw, p_voice_len)[0]
    voice = raw[p_voice : p_voice + vl].decode('ascii', errors='ignore')
    
    p = p_voice + vl
    pitch = struct.unpack_from('<d', raw, p)[0]; p += 8
    base_stats = struct.unpack_from('<7i', raw, p); p += 28
    bonus_stats = struct.unpack_from('<7i', raw, p); p += 28
    
    # Find all strings after bonus stats
    p_search = p
    strings = []
    while p_search < len(raw) - 8:
        slen = struct.unpack_from('<Q', raw, p_search)[0]
        if 1 <= slen <= 40 and p_search + 8 + slen <= len(raw):
            sub = raw[p_search + 8 : p_search + 8 + slen]
            if all(32 <= b <= 126 for b in sub) and any(chr(b).isalpha() for b in sub):
                s = sub.decode('ascii')
                strings.append((p_search, slen, s))
                p_search += 8 + slen
                continue
        p_search += 1
        
    return {
        'name': name,
        'voice': voice,
        'pitch': pitch,
        'base_stats': base_stats,
        'bonus_stats': bonus_stats,
        'strings': [s[2] for s in strings]
    }

success = 0
failed = []
for key, blob in all_cats:
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    raw = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    res = parse_cat(raw)
    if res and len(res['strings']) >= 10:
        success += 1
    else:
        failed.append(key)

print(f"Tested {len(all_cats)} cats:")
print(f"  SUCCESS: {success}")
print(f"  FAILED: {len(failed)}")
if failed:
    print(f"  Failed: {failed[:10]}")
