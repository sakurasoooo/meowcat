import sqlite3, os, struct, lz4.block

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

def test_cat(cid):
    cur.execute("SELECT data FROM cats WHERE key=?", (cid,))
    blob = cur.fetchone()[0]
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    raw = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    
    p = 0
    v0, guid = struct.unpack_from('<IQ', raw, p); p += 12
    nl = struct.unpack_from('<Q', raw, p)[0]; p += 8
    name = raw[p : p + nl*2].decode('utf-16le'); p += nl*2
    
    # Check title 1
    # Note: between name and title 1 there is an 8-byte or 16-byte header
    # Let's find title 2 'None'
    p_none = raw.find(b'None', p)
    # The length prefix of 'None' is 8 bytes before p_none
    p_title2_len = p_none - 8
    pre_parts = raw[p : p_title2_len]
    p = p_none + 4 # skip 'None'
    
    # After 'None' is post_title_u32 (4 bytes)
    post_title_u32 = struct.unpack_from('<I', raw, p)[0]; p += 4
    
    # 368 bytes parts
    parts = raw[p : p + 368]; p += 368
    
    # Voice
    vl = struct.unpack_from('<Q', raw, p)[0]; p += 8
    voice = raw[p : p + vl].decode('ascii'); p += vl
    
    # Pitch
    pitch = struct.unpack_from('<d', raw, p)[0]; p += 8
    
    # Stats
    base_stats = struct.unpack_from('<7i', raw, p); p += 28
    bonus_stats = struct.unpack_from('<7i', raw, p); p += 28
    
    # Mid flags (28 bytes)
    mid_flags = raw[p : p + 28]; p += 28
    
    # Boon
    bl = struct.unpack_from('<Q', raw, p)[0]; p += 8
    boon = raw[p : p + bl].decode('ascii'); p += bl
    
    # Post boon flags (14 bytes)
    post_boon = raw[p : p + 14]; p += 14
    
    # Move
    ml = struct.unpack_from('<Q', raw, p)[0]; p += 8
    move = raw[p : p + ml].decode('ascii'); p += ml
    
    # Attack
    al = struct.unpack_from('<Q', raw, p)[0]; p += 8
    atk = raw[p : p + al].decode('ascii'); p += al
    
    # 4 Actives
    actives = []
    for _ in range(4):
        sl = struct.unpack_from('<Q', raw, p)[0]; p += 8
        actives.append(raw[p : p + sl].decode('ascii')); p += sl
        
    # 8 Passives
    passives = []
    ranks = []
    for _ in range(8):
        sl = struct.unpack_from('<Q', raw, p)[0]; p += 8
        passives.append(raw[p : p + sl].decode('ascii')); p += sl
        rk = struct.unpack_from('<i', raw, p)[0]; p += 4
        ranks.append(rk)
        
    # Class
    cl = struct.unpack_from('<Q', raw, p)[0]; p += 8
    cat_class = raw[p : p + cl].decode('ascii'); p += cl
    
    tail = raw[p:]
    
    print(f"Cat {cid} ('{name}'):")
    print(f"  Voice: {voice}, Pitch: {pitch:.3f}")
    print(f"  Base Stats: {base_stats}")
    print(f"  Class: {cat_class}")
    print(f"  Move: {move}, Atk: {atk}")
    print(f"  Actives: {actives}")
    print(f"  Passives: {passives}")
    print(f"  Tail length: {len(tail)}")

test_cat(1)
test_cat(619)
test_cat(835)
