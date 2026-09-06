import struct

def remove_cat_from_house(data, cat_id):
    p = 0
    while p < len(data) - 8:
        slen = struct.unpack_from('<Q', data, p)[0]
        if slen in [5, 12] and p + 8 + slen <= len(data):
            s = data[p+8 : p+8+slen].decode('ascii', errors='ignore')
            if s in ['Floor1_Large', 'Floor1_Small', 'Attic']:
                cid_pos = p - 8
                cid = struct.unpack_from('<Q', data, cid_pos)[0]
                if cid == cat_id:
                    entry_end = p + 8 + slen + 32
                    del data[cid_pos : entry_end]
                    # decrement count
                    val0, count = struct.unpack_from('<II', data, 0)
                    struct.pack_into('<I', data, 4, max(0, count - 1))
                    print(f"Removed cat {cat_id} from house_state! New count={count-1}")
                    return True
                p += 8 + slen + 32
                continue
        p += 1
    return False

data = bytearray(b'\x00\x00\x00\x00\x01\x00\x00\x00' + struct.pack('<Q', 100) + struct.pack('<Q', 5) + b'Attic' + struct.pack('<4d', 0, 0, 0, 0))
remove_cat_from_house(data, 100)
val0, count = struct.unpack_from('<II', data, 0)
assert count == 0
assert len(data) == 8
print("Remove test PASSED!")
