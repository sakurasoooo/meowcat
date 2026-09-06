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

offset = data_start
data_files = []
for fn, fsz in files:
    if not fn.endswith(('.wav', '.ogg', '.mp3')):
        data_files.append((fn, offset, fsz))
    offset += fsz

print(f"Total non-audio files in gpak: {len(data_files)}")
for fn, off, sz in sorted(data_files, key=lambda x: x[0]):
    if any(k in fn.lower() for k in ['cat', 'class', 'breed', 'mutation', 'stat', 'dna', 'gene', 'data', 'gon']):
        print(f"  {fn} (size: {sz} bytes)")
