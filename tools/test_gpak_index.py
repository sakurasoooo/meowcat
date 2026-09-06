import struct

gpak_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\resources.gpak'
with open(gpak_path, 'rb') as f:
    num_files = struct.unpack('<I', f.read(4))[0]
    print(f"Num files in index: {num_files}")
    
    files = []
    for i in range(num_files):
        sz_bytes = f.read(2)
        if len(sz_bytes) < 2:
            break
        fn_len = struct.unpack('<H', sz_bytes)[0]
        fn = f.read(fn_len).decode('utf-8', errors='replace')
        f_size = struct.unpack('<I', f.read(4))[0]
        files.append((fn, f_size))
        
    data_start_offset = f.tell()
    print(f"Index parsed successfully! Total entries: {len(files)}")
    print(f"Data starts at offset: 0x{data_start_offset:08X} ({data_start_offset})")

# Let's inspect first file data
with open(gpak_path, 'rb') as f:
    fn0, sz0 = files[0]
    f.seek(data_start_offset)
    data0 = f.read(min(sz0, 200))
    print(f"\nFile 0: '{fn0}' (size: {sz0})")
    print("Content head:")
    print(data0.decode('utf-8', errors='replace'))
