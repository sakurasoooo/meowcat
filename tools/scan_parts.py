import re

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
with open(exe_path, 'rb') as f:
    data = f.read()

# Search for part names in rdata
parts = ['head', 'body', 'tail', 'ears', 'eyes', 'mouth', 'legs', 'feet', 'color', 'pattern', 'coat', 'whiskers', 'gender', 'stats', 'health', 'strength', 'dexterity', 'intelligence', 'constitution', 'speed', 'charisma', 'luck']

for p in parts:
    matches = set(re.findall(rb'[a-zA-Z0-9_]{0,10}' + p.encode() + rb'[a-zA-Z0-9_]{0,10}', data, re.IGNORECASE))
    filtered = [m.decode('latin1') for m in matches if len(m) < 25]
    if filtered:
        print(f"Keywords for '{p}': {', '.join(filtered[:10])}")
