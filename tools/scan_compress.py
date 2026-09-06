import re

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
with open(exe_path, 'rb') as f:
    data = f.read()

for k in [b"lz4", b"LZ4", b"miniz", b"tinfl", b"zstd", b"ZSTD", b"deflate", b"inflate", b"fastlz", b"snappy", b"compress", b"decompress"]:
    matches = set(re.findall(rb'[a-zA-Z0-9_]{0,20}' + k + rb'[a-zA-Z0-9_]{0,20}', data))
    if matches:
        print(f"Matches for {k.decode()}:")
        for m in list(matches)[:10]:
            print(" ", m.decode('latin1', errors='ignore'))
