import re

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
with open(exe_path, 'rb') as f:
    data = f.read()

# Search for strings near CatPartID
pos = 0
while True:
    pos = data.find(b"CatPartID", pos)
    if pos == -1:
        break
    # print context
    start = max(0, pos - 100)
    end = min(len(data), pos + 200)
    context = data[start:end]
    # filter readable ASCII
    readable = ''.join(chr(b) if 32 <= b <= 126 else ' ' for b in context)
    print(f"Match at {hex(pos)}: {readable.strip()}")
    pos += 9
