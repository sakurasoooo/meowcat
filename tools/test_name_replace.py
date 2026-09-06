import struct
import lz4.block
import sqlite3
import os

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()
cur.execute("SELECT data FROM cats WHERE key=835")
blob = cur.fetchone()[0]
unc_sz = struct.unpack_from('<I', blob, 0)[0]
data = bytearray(lz4.block.decompress(blob[4:], uncompressed_size=unc_sz))

old_name_len = struct.unpack_from('<Q', data, 0x0C)[0]
old_name = data[0x14 : 0x14 + old_name_len*2].decode('utf-16le')
print(f"Original Name: '{old_name}' (len={old_name_len})")

new_name = "SuperCat999"
new_name_encoded = new_name.encode('utf-16le')
new_name_len = len(new_name)

new_data = data[:0x0C] + struct.pack('<Q', new_name_len) + new_name_encoded + data[0x14 + old_name_len*2:]

# Check if new name reads back
chk_name_len = struct.unpack_from('<Q', new_data, 0x0C)[0]
chk_name = new_data[0x14 : 0x14 + chk_name_len*2].decode('utf-16le')
print(f"Checked New Name: '{chk_name}' (len={chk_name_len})")
assert chk_name == new_name
print("Name replacement SUCCESS!")
