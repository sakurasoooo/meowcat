import sqlite3
import struct
import os
from mewgenics_core import MewgenicsSaveManager

save_path = MewgenicsSaveManager.find_default_save()
conn = sqlite3.connect(save_path)
cur = conn.cursor()
cur.execute("SELECT data FROM files WHERE key='house_state'")
raw_hs = bytearray(cur.fetchone()[0])
conn.close()

# Parse entries:
# Header: u32 val0, u32 count
val0, count = struct.unpack_from('<II', raw_hs, 0)
print(f"Header: val0={val0}, count={count}")

# Parse each entry by locating the room string
p = 0
entries = []
while p < len(raw_hs) - 8:
    slen = struct.unpack_from('<Q', raw_hs, p)[0]
    if slen in [5, 12] and p + 8 + slen <= len(raw_hs):
        s = raw_hs[p+8 : p+8+slen].decode('ascii', errors='ignore')
        if s in ['Floor1_Large', 'Floor1_Small', 'Attic']:
            cat_id = struct.unpack_from('<Q', raw_hs, p - 8)[0]
            entries.append({
                'cat_id_pos': p - 8,
                'cat_id': cat_id,
                'str_pos': p,
                'slen': slen,
                'room': s,
                'trailing_pos': p + 8 + slen
            })
            p += 8 + slen + 32 # jump past coordinates
            continue
    p += 1

print(f"Found {len(entries)} room entries in house_state:")
for e in entries[:5]:
    print(f"  cat_id={e['cat_id']} in room '{e['room']}' (offset {hex(e['str_pos'])})")

# Test moving cat 758 from Floor1_Large to Attic
def set_cat_room(data, cat_id, new_room):
    # Find existing
    for e in entries:
        if e['cat_id'] == cat_id:
            # Replace room string
            old_len = e['slen']
            new_len = len(new_room)
            old_str_block = struct.pack('<Q', old_len) + e['room'].encode('ascii')
            new_str_block = struct.pack('<Q', new_len) + new_room.encode('ascii')
            idx = data.find(old_str_block, e['str_pos'])
            if idx != -1:
                data[idx : idx + len(old_str_block)] = new_str_block
                print(f"Successfully moved cat {cat_id} from {e['room']} to {new_room}!")
                return True
    return False

test_data = bytearray(raw_hs)
set_cat_room(test_data, 758, 'Attic')
set_cat_room(test_data, 758, 'Floor1_Large')
