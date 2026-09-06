import sqlite3, os, struct, lz4.block, re

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()
cur.execute("SELECT key, data FROM cats")
all_cats = cur.fetchall()

def parse_cat_data(raw):
    # Name
    nl = struct.unpack_from('<Q', raw, 0x0c)[0]
    name = raw[0x14 : 0x14 + nl*2].decode('utf-16le', errors='ignore')
    
    # Find voice
    m = re.search(rb'(?:male\d+|female\d+|robotom|spidercat|demoncat|robotcat)', raw)
    if not m:
        return None
    p_voice = m.start()
    p_voice_len = p_voice - 8
    vl = struct.unpack_from('<Q', raw, p_voice_len)[0]
    voice = raw[p_voice : p_voice + vl].decode('ascii', errors='ignore')
    
    # Check pitch & stats
    p = p_voice + vl
    pitch = struct.unpack_from('<d', raw, p)[0]; p += 8
    base_stats = struct.unpack_from('<7i', raw, p); p += 28
    bonus_stats = struct.unpack_from('<7i', raw, p); p += 28
    
    # 28 bytes mid flags
    mid_flags = raw[p : p + 28]; p += 28
    
    # Boon
    bl = struct.unpack_from('<Q', raw, p)[0]; p += 8
    boon = raw[p : p + bl].decode('ascii', errors='ignore'); p += bl
    
    # Post boon (14 bytes)
    post_boon = raw[p : p + 14]; p += 14
    
    # Move
    ml = struct.unpack_from('<Q', raw, p)[0]; p += 8
    move = raw[p : p + ml].decode('ascii', errors='ignore'); p += ml
    
    # Attack
    al = struct.unpack_from('<Q', raw, p)[0]; p += 8
    atk = raw[p : p + al].decode('ascii', errors='ignore'); p += al
    
    # 4 Actives
    actives = []
    for _ in range(4):
        sl = struct.unpack_from('<Q', raw, p)[0]; p += 8
        actives.append(raw[p : p + sl].decode('ascii', errors='ignore')); p += sl
        
    # 8 Passives
    passives = []
    ranks = []
    for _ in range(8):
        sl = struct.unpack_from('<Q', raw, p)[0]; p += 8
        passives.append(raw[p : p + sl].decode('ascii', errors='ignore')); p += sl
        rk = struct.unpack_from('<i', raw, p)[0]; p += 4
        ranks.append(rk)
        
    # Class
    cl = struct.unpack_from('<Q', raw, p)[0]; p += 8
    cat_class = raw[p : p + cl].decode('ascii', errors='ignore'); p += cl
    
    tail = raw[p:]
    
    return {
        'name': name,
        'voice': voice,
        'pitch': pitch,
        'base_stats': base_stats,
        'bonus_stats': bonus_stats,
        'boon': boon,
        'move': move,
        'attack': atk,
        'actives': actives,
        'passives': passives,
        'ranks': ranks,
        'class': cat_class,
        'tail_len': len(tail)
    }

success = 0
failed = []
for key, blob in all_cats:
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    raw = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    res = parse_cat_data(raw)
    if res and 20 <= sum(res['base_stats']) <= 50 and res['move'] == 'DefaultMove':
        success += 1
    else:
        failed.append(key)

print(f"Tested {len(all_cats)} cats:")
print(f"  SUCCESS (100% valid parsed cat): {success}")
print(f"  FAILED: {len(failed)}")
if failed:
    print(f"  Failed IDs: {failed}")
