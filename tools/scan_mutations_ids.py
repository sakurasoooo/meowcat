import struct
import re

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

target_mutations = [
    'data/mutations/body.gon',
    'data/mutations/ears.gon',
    'data/mutations/eyebrows.gon',
    'data/mutations/eyes.gon',
    'data/mutations/head.gon',
    'data/mutations/legs.gon',
    'data/mutations/mouth.gon',
    'data/mutations/tail.gon',
    'data/mutations/texture.gon',
]

offset = data_start
found = {}
for fn, fsz in files:
    if fn in target_mutations:
        found[fn] = (offset, fsz)
    offset += fsz

with open(gpak_path, 'rb') as f:
    for fn in target_mutations:
        if fn in found:
            off, sz = found[fn]
            f.seek(off)
            content = f.read(sz).decode('utf-8', errors='replace')
            # Extract top-level numbers
            ids = re.findall(r'^\s*([0-9]+)\s*\{', content, re.MULTILINE)
            print(f"{fn} ({len(ids)} mutations): sample IDs: {ids[:8]}")
