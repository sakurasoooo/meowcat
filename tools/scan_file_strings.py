import re

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
with open(exe_path, 'rb') as f:
    data = f.read()

# Look for strings around CatData.cpp or MewSaveFile.cpp
matches = re.finditer(b'([^\x00]{4,150}(?:CatData|MewSaveFile|SQLSaveFile)[^\x00]{0,150})', data)
for m in matches:
    print(m.group(0).decode('latin1', errors='ignore'))
