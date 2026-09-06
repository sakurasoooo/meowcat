"""Extract selected resource trees from resources.gpak into game_assets/.
Usage: python tools/extract_gpak_assets.py
"""
import os, json, struct

GPAK = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\resources.gpak'
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'game_assets')
PREFIXES = ('textures/', 'data/', 'swfs/')

with open(GPAK, 'rb') as f:
    num_files = struct.unpack('<I', f.read(4))[0]
    entries = []
    for _ in range(num_files):
        fn_len = struct.unpack('<H', f.read(2))[0]
        fn = f.read(fn_len).decode('utf-8', errors='replace')
        f_size = struct.unpack('<I', f.read(4))[0]
        entries.append((fn, f_size))
    data_start = f.tell()

    offset = data_start
    extracted = 0
    total_bytes = 0
    for fn, fsz in entries:
        cur = offset
        offset += fsz
        if not fn.startswith(PREFIXES):
            continue
        dest = os.path.join(OUT, fn.replace('/', os.sep))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        f.seek(cur)
        with open(dest, 'wb') as out:
            remaining = fsz
            while remaining > 0:
                chunk = f.read(min(8 * 1024 * 1024, remaining))
                if not chunk:
                    break
                out.write(chunk)
                remaining -= len(chunk)
        extracted += 1
        total_bytes += fsz

print(f"extracted {extracted} files, {total_bytes/1e6:.1f} MB -> {OUT}")
