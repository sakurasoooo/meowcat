import struct

def append_cat_to_house(data, cat_id, room_name):
    # read count
    val0, count = struct.unpack_from('<II', data, 0)
    new_count = count + 1
    struct.pack_into('<I', data, 4, new_count)
    
    # default coordinates
    x, y, rot, flags = 15.0, 1.0, 0.0, 0.0
    entry = bytearray()
    entry.extend(struct.pack('<Q', cat_id))
    entry.extend(struct.pack('<Q', len(room_name)))
    entry.extend(room_name.encode('ascii'))
    entry.extend(struct.pack('<4d', x, y, rot, flags))
    
    data.extend(entry)
    print(f"Appended cat {cat_id} to room {room_name}! New count={new_count}, new len={len(data)}")
    return True

data = bytearray(b'\x00\x00\x00\x00\x01\x00\x00\x00' + struct.pack('<Q', 100) + struct.pack('<Q', 5) + b'Attic' + struct.pack('<4d', 0, 0, 0, 0))
append_cat_to_house(data, 999, 'Floor1_Large')
val0, count = struct.unpack_from('<II', data, 0)
assert count == 2
print("Append test PASSED!")