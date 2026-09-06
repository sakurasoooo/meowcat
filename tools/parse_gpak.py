import struct

gpak_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\resources.gpak'
with open(gpak_path, 'rb') as f:
    header = f.read(512)

# Analyze the header entries
num_files = struct.unpack_from('<I', header, 0)[0]
print(f"Num files in gpak: {num_files}")

pos = 4
for i in range(15):
    fname_len = struct.unpack_from('<H', header, pos)[0]
    pos += 2
    fname = header[pos : pos + fname_len].decode('latin1')
    pos += fname_len
    # next fields
    f_offset, f_size = struct.unpack_from('<II', header, pos)
    pos += 8
    print(f"[{i:03d}] {fname} -> offset: 0x{f_offset:08X} ({f_offset}), size: {f_size}")
