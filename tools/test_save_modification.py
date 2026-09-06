import sqlite3, os, struct, lz4.block, shutil

# Create a test save file copy in workspace
orig_save = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
test_save = r"c:\Users\10107\Documents\github\cheatenginemcp\test_campaign.sav"
shutil.copy2(orig_save, test_save)

conn = sqlite3.connect(test_save)
cur = conn.cursor()

# Test modifying Cat 835 (Champ)
cur.execute("SELECT data FROM cats WHERE key=835")
blob = cur.fetchone()[0]
unc_sz = struct.unpack_from('<I', blob, 0)[0]
raw = bytearray(lz4.block.decompress(blob[4:], uncompressed_size=unc_sz))

# 1. Modify name to 'OmegaChamp'
old_nl = struct.unpack_from('<Q', raw, 0x0c)[0]
new_name = "OmegaChamp"
new_name_bytes = new_name.encode('utf-16le')
raw = raw[:0x0c] + struct.pack('<Q', len(new_name)) + new_name_bytes + raw[0x14 + old_nl*2 :]

# 2. Modify stats to (99, 99, 99, 99, 99, 99, 99)
# Re-find voice & stats
import re
m = re.search(rb'(?:male\d+|female\d+|robotom|spidercat|demoncat|robotcat)', raw)
p_voice = m.start()
vl = struct.unpack_from('<Q', raw, p_voice - 8)[0]
p_stats = p_voice + vl + 8
struct.pack_into('<7i', raw, p_stats, 99, 99, 99, 99, 99, 99, 99)

# 3. Modify gold to 999999 in properties
cur.execute("UPDATE properties SET data=999999 WHERE key='house_gold'")
cur.execute("UPDATE properties SET data=888888 WHERE key='house_food'")

# 4. Recompress Cat 835
comp = lz4.block.compress(bytes(raw), store_size=False)
final_blob = struct.pack('<I', len(raw)) + comp
cur.execute("UPDATE cats SET data=? WHERE key=835", (final_blob,))
conn.commit()
conn.close()

# Verify test_save
conn2 = sqlite3.connect(test_save)
cur2 = conn2.cursor()
cur2.execute("SELECT data FROM cats WHERE key=835")
test_blob = cur2.fetchone()[0]
t_unc_sz = struct.unpack_from('<I', test_blob, 0)[0]
t_raw = lz4.block.decompress(test_blob[4:], uncompressed_size=t_unc_sz)

t_nl = struct.unpack_from('<Q', t_raw, 0x0c)[0]
t_name = t_raw[0x14 : 0x14 + t_nl*2].decode('utf-16le')

m2 = re.search(rb'(?:male\d+|female\d+|robotom|spidercat|demoncat|robotcat)', t_raw)
p2_v = m2.start()
vl2 = struct.unpack_from('<Q', t_raw, p2_v - 8)[0]
t_stats = struct.unpack_from('<7i', t_raw, p2_v + vl2 + 8)

cur2.execute("SELECT key, data FROM properties WHERE key IN ('house_gold', 'house_food')")
props = dict(cur2.fetchall())
conn2.close()

print("Verification Results on test_campaign.sav:")
print(f"  Name: '{t_name}' (expected: 'OmegaChamp')")
print(f"  Stats: {t_stats} (expected: (99, 99, 99, 99, 99, 99, 99))")
print(f"  Properties: {props}")
assert t_name == "OmegaChamp"
assert t_stats == (99, 99, 99, 99, 99, 99, 99)
assert props['house_gold'] == 999999
assert props['house_food'] == 888888
print("TEST COMPLETED WITH 100% SUCCESS!")
