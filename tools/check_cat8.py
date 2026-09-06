import sqlite3, os, struct, lz4.block

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

def dump_strings(cid):
    cur.execute("SELECT data FROM cats WHERE key=?", (cid,))
    blob = cur.fetchone()[0]
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    raw = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    nl = struct.unpack_from('<Q', raw, 0x0c)[0]
    name = raw[0x14 : 0x14 + nl*2].decode('utf-16le', errors='ignore')
    print(f"\n--- Cat {cid} ('{name}', total {len(raw)} bytes) ---")
    p = 0
    while p < len(raw) - 8:
        slen = struct.unpack_from('<Q', raw, p)[0]
        if 1 <= slen <= 40 and p + 8 + slen <= len(raw):
            chunk = raw[p+8 : p+8+slen]
            if all(32 <= b <= 126 for b in chunk) and any(chr(b).isalpha() for b in chunk):
                print(f"  0x{p:04X}: '{chunk.decode('ascii')}' (len={slen})")
                p += 8 + slen
                continue
        p += 1

dump_strings(8)
dump_strings(15)
