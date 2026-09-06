import struct
import json

gpak_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\resources.gpak'
with open(gpak_path, 'rb') as f:
    num_files = struct.unpack('<I', f.read(4))[0]
    
    files = []
    curr_offset = 0 # will adjust after header
    for i in range(num_files):
        fn_len = struct.unpack('<H', f.read(2))[0]
        fn = f.read(fn_len).decode('utf-8', errors='replace')
        f_size = struct.unpack('<I', f.read(4))[0]
        files.append((fn, f_size))
        
    data_start = f.tell()

# Calculate exact offsets
file_manifest = {}
offset = data_start
for fn, fsz in files:
    file_manifest[fn] = {'offset': offset, 'size': fsz}
    offset += fsz

# Search for interesting files
interesting = {}
for fn, info in file_manifest.items():
    fn_lower = fn.lower()
    if any(k in fn_lower for k in ['cat', 'class', 'breed', 'mutation', 'stat', 'dna', 'gene', 'body', 'item', 'ability', 'passive']):
        interesting[fn] = info

print(f"Total files in gpak: {len(file_manifest)}")
print(f"Interesting files found: {len(interesting)}")

# Print top 40 interesting files
for fn in sorted(interesting.keys())[:40]:
    print(f"  {fn} ({interesting[fn]['size']} bytes)")
