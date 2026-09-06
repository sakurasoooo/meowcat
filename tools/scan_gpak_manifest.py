import struct, collections, json

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

print(f"num_files={num_files} data_start={data_start}")

# extension histogram
hist = collections.Counter()
size_hist = collections.Counter()
for fn, fsz in files:
    ext = fn.rsplit('.', 1)[-1].lower() if '.' in fn else '(none)'
    hist[ext] += 1
    size_hist[ext] += fsz
for ext, cnt in hist.most_common(40):
    print(f"  .{ext:10s} x{cnt:6d}  {size_hist[ext]/1e6:10.1f} MB")

# top-level dir histogram
dirstat = collections.Counter()
for fn, fsz in files:
    dirstat[fn.split('/')[0]] += 1
print("\nTop-level dirs:")
for d, cnt in dirstat.most_common(30):
    print(f"  {d:30s} x{cnt}")

# save manifest
manifest = {}
offset = data_start
for fn, fsz in files:
    manifest[fn] = [offset, fsz]
    offset += fsz
with open('gpak_manifest.json', 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False)
print(f"\nmanifest saved: {len(manifest)} entries")
