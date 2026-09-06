import struct

gpak_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\resources.gpak'
with open(gpak_path, 'rb') as f:
    num_files = struct.unpack('<I', f.read(4))[0]
    
    files = []
    for i in range(num_files):
        fn_len = struct.unpack('<H', f.read(2))[0]
        fn = f.read(fn_len).decode('utf-8', errors='replace')
        f_size = struct.unpack('<I', f.read(4))[0]
        files.append((fn, f_size))
        
    data_start = f.tell()

target_files = [
    'data/tutorial_cats.gon',
    'data/special_strays.gon',
    'data/mutations/body.gon'
]

offset = data_start
found = {}
for fn, fsz in files:
    if fn in target_files:
        found[fn] = (offset, fsz)
    offset += fsz

with open(gpak_path, 'rb') as f:
    for fn in target_files:
        if fn in found:
            off, sz = found[fn]
            f.seek(off)
            content = f.read(sz).decode('utf-8', errors='replace')
            print(f"\n=================== {fn} ({sz} bytes) ===================")
            print(content[:1500])
