import re

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
with open(exe_path, 'rb') as f:
    data = f.read()

matches = set(re.findall(b'CatData::[a-zA-Z0-9_]+', data))
for m in sorted(matches):
    print(m.decode('latin1'))

print("\n--- MewSaveFile methods ---")
matches2 = set(re.findall(b'MewSaveFile::[a-zA-Z0-9_]+', data))
for m in sorted(matches2):
    print(m.decode('latin1'))

print("\n--- SQLSaveFile methods ---")
matches3 = set(re.findall(b'SQLSaveFile::[a-zA-Z0-9_]+', data))
for m in sorted(matches3):
    print(m.decode('latin1'))
