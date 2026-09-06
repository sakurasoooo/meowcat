import sqlite3
import os
import struct
import lz4.block

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, data FROM cats WHERE key=1")
blob = cur.fetchone()[1]
unc_sz = struct.unpack_from('<I', blob, 0)[0]
data = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)

print(f"Cat 1 Uncompressed Length: {len(data)}")

# Let's inspect every 4 bytes as int32 and float, and every 8 bytes as int64 and double
# Let's identify the sections by string locations:
# We know strings in Cat 1:
# Name: 'Taurus' at 0x14 (len=6)
# 'None' at 0x40 (len=4)
# 'male' at 0x01B4? Wait, let's find the exact offset of 'male' in Cat 1:
pos_male = data.find(b'male')
print(f"'male' found at offset 0x{pos_male:04X} ({pos_male})")
pos_color = data.find(b'Colorless')
print(f"'Colorless' found at offset 0x{pos_color:04X} ({pos_color})")
pos_move = data.find(b'DefaultMove')
print(f"'DefaultMove' found at offset 0x{pos_move:04X} ({pos_move})")

# Let's inspect bytes before 'male':
print("\n--- 64 bytes before 'male' ---")
chunk = data[pos_male - 64 : pos_male + 16]
for i in range(0, len(chunk), 16):
    sub = chunk[i:i+16]
    print(f"0x{pos_male - 64 + i:04X}: {' '.join(f'{b:02X}' for b in sub):<48} {''.join(chr(b) if 32<=b<=126 else '.' for b in sub)}")

# Let's inspect ints/doubles in that region
for off in range(pos_male - 64, pos_male, 4):
    val_i32 = struct.unpack_from('<i', data, off)[0]
    val_f32 = struct.unpack_from('<f', data, off)[0]
    if -100 <= val_i32 <= 1000:
        print(f"  0x{off:04X}: int32={val_i32} (float={val_f32:.2f})")
