import sqlite3
import os
import struct
import lz4.block

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, data FROM cats LIMIT 5")
rows = cur.fetchall()

def read_str_u16(d, pos):
    sz = struct.unpack_from('<Q', d, pos)[0]
    pos += 8
    raw = d[pos : pos + sz * 2]
    pos += sz * 2
    return raw.decode('utf-16le', errors='ignore'), pos

def read_str_ascii(d, pos):
    sz = struct.unpack_from('<Q', d, pos)[0]
    pos += 8
    raw = d[pos : pos + sz]
    pos += sz
    return raw.decode('ascii', errors='ignore'), pos

for key, blob in rows:
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    d = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    pos = 0
    v0 = struct.unpack_from('<I', d, pos)[0]; pos += 4
    guid = struct.unpack_from('<Q', d, pos)[0]; pos += 8
    name, pos = read_str_u16(d, pos)
    s1, pos = read_str_u16(d, pos)
    s2, pos = read_str_u16(d, pos)
    s3, pos = read_str_u16(d, pos)
    s4, pos = read_str_ascii(d, pos)
    print(f"Cat {key}: v0={v0}, GUID={hex(guid)}, Name='{name}', s1='{s1}', s2='{s2}', s3='{s3}', s4='{s4}', pos=0x{pos:04X} ({pos})")
