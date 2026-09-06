import struct

gpak_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\resources.gpak'
with open(gpak_path, 'rb') as f:
    raw = f.read(2048)

num_files = struct.unpack_from('<I', raw, 0)[0]
print(f"Num files: {num_files}")

pos = 4
for i in range(5):
    fname_len = struct.unpack_from('<H', raw, pos)[0]
    pos += 2
    fname = raw[pos : pos + fname_len].decode('latin1')
    pos += fname_len
    # Let's inspect the next 16 bytes
    next_bytes = raw[pos : pos + 16]
    print(f"[{i}] {fname}")
    print("   Hex:", next_bytes.hex(' '))
    # Let's see what uint32s or uint64s are here
    u32_0, u32_1, u32_2, u32_3 = struct.unpack_from('<IIII', next_bytes, 0)
    print(f"   u32: {u32_0}, {u32_1}, {u32_2}, {u32_3}")
    # advance pos to next entry
    # Is entry: offset(8) + size(8)? or offset(4) + size(4)? or offset(8) + size(4)?
    # Notice entry 1 has fname_len = 0x13 = 19 ('audio/house_sfx.gon')
    # Where does 'audio/house_sfx.gon' start?
    target_next = b'audio/house_sfx.gon'
    found_next = raw.find(target_next, pos)
    print(f"   Distance to next filename: {found_next - pos - 2} bytes")
    pos = found_next - 2
