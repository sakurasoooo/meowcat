import sqlite3
import os
import struct
import lz4.block
import re

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

def get_cat(cid):
    cur.execute("SELECT data FROM cats WHERE key=?", (cid,))
    blob = cur.fetchone()[0]
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    return lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)

d1 = get_cat(1)
d835 = get_cat(835)

# Find voice position
m1 = re.search(rb'(?:male|female)\d*', d1)
m835 = re.search(rb'(?:male|female)\d*', d835)

p_v1 = m1.start() - 8
p_v835 = m835.start() - 8

# Name end
nl1 = struct.unpack_from('<Q', d1, 0x0c)[0]
nl835 = struct.unpack_from('<Q', d835, 0x0c)[0]

start1 = 0x14 + nl1*2 + 0x24 # after title 'None' + uint32(1)
start835 = 0x14 + nl835*2 + 0x24

chunk1 = d1[start1 : p_v1]
chunk835 = d835[start835 : p_v835]

print(f"Cat 1 Parts chunk length: {len(chunk1)} bytes")
print(f"Cat 835 Parts chunk length: {len(chunk835)} bytes")

# Both chunks are 368 bytes!
# 368 bytes = fixed size struct for parts/genetics!
print(f"Are chunk lengths equal? {len(chunk1) == len(chunk835)} (Length: {len(chunk1)})")

# Let's inspect chunk1 as 368 bytes / 8 bytes = 46 qwords / doubles / pairs of ints!
for i in range(0, len(chunk1), 16):
    u32s_1 = struct.unpack_from('<4i', chunk1, i)
    u32s_835 = struct.unpack_from('<4i', chunk835, i)
    dbls_1 = struct.unpack_from('<2d', chunk1, i)
    dbls_835 = struct.unpack_from('<2d', chunk835, i)
    print(f"+0x{i:03X} ({i:3d}):")
    print(f"   Cat 1:   ints={u32s_1}  | dbls=({dbls_1[0]:.3f}, {dbls_1[1]:.3f})")
    print(f"   Cat 835: ints={u32s_835}  | dbls=({dbls_835[0]:.3f}, {dbls_835[1]:.3f})")
