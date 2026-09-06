import sqlite3, os, struct, lz4.block

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()
cur.execute("SELECT key, data FROM cats")
all_cats = cur.fetchall()

def locate_cat_sections(raw):
    # 1. Name
    nl = struct.unpack_from('<Q', raw, 0x0c)[0]
    p_name_str = 0x14
    p_name_end = p_name_str + nl * 2
    name = raw[p_name_str : p_name_end].decode('utf-16le', errors='ignore')
    
    # 2. Title
    p_title_len = p_name_end + 24
    tl = struct.unpack_from('<Q', raw, p_title_len)[0]
    p_title_str = p_title_len + 8
    title = raw[p_title_str : p_title_str + tl].decode('ascii', errors='ignore')
    p_parts_start = p_title_str + tl
    
    # 3. Find stats & voice
    # Look for 7 ints with sum between 20 and 50
    # Voice string length is 8 bytes before voice string, which is 8 bytes before pitch
    found_stats = False
    for p in range(p_parts_start + 100, len(raw) - 100):
        # check 7 ints
        ints = struct.unpack_from('<7i', raw, p)
        if all(0 <= x <= 25 for x in ints) and 20 <= sum(ints) <= 50:
            # Check if p-8 is double pitch (between 0.1 and 3.0)
            pitch = struct.unpack_from('<d', raw, p - 8)[0]
            if 0.2 <= pitch <= 3.0 or pitch == 0.0:
                # Check if before pitch is an ASCII string
                # Find length prefix
                for vlen in range(3, 20):
                    if p - 8 - vlen - 8 >= p_parts_start:
                        chk_len = struct.unpack_from('<Q', raw, p - 8 - vlen - 8)[0]
                        if chk_len == vlen:
                            v_str = raw[p - 8 - vlen : p - 8].decode('ascii', errors='ignore')
                            if all(32 <= ord(c) <= 126 for c in v_str) and any(c.isalpha() for c in v_str):
                                p_voice_len = p - 8 - vlen - 8
                                p_stats = p
                                found_stats = True
                                return {
                                    'name': name,
                                    'title': title,
                                    'parts_len': p_voice_len - p_parts_start,
                                    'voice': v_str,
                                    'pitch': pitch,
                                    'stats': ints,
                                    'p_stats': p_stats
                                }
    return None

success = 0
failed = []
for key, blob in all_cats:
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    raw = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    res = locate_cat_sections(raw)
    if res:
        success += 1
    else:
        failed.append(key)

print(f"Tested {len(all_cats)} cats:")
print(f"  SUCCESS: {success}")
print(f"  FAILED: {len(failed)}")
if failed:
    print(f"  Failed keys: {failed[:10]}")
