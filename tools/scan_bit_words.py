import re

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
with open(exe_path, 'rb') as f:
    data = f.read()

for k in [b"bit", b"Bit", b"Serial", b"serial", b"Pack", b"pack", b"save"]:
    matches = set(re.findall(rb'[a-zA-Z0-9_]{3,30}' + k + rb'[a-zA-Z0-9_]{3,30}', data))
    if matches:
        print(f"Matches for {k.decode()}:")
        for m in list(matches)[:20]:
            print(" ", m.decode('latin1', errors='ignore'))
