import re

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
with open(exe_path, 'rb') as f:
    data = f.read()

classes = re.findall(b'\x2e\x3f\x41\x56([a-zA-Z0-9_@]+)\x40\x40', data)
print(f"Total MSVC RTTI classes found: {len(classes)}")
cat_classes = [c.decode('latin1') for c in classes if b'cat' in c.lower() or b'game' in c.lower() or b'unit' in c.lower() or b'gene' in c.lower() or b'save' in c.lower()]
print(f"Interesting classes ({len(cat_classes)}):")
for c in cat_classes[:50]:
    print(" ", c)

cpp_files = set(re.findall(b'[a-zA-Z0-9_\\\\/]+\\.cpp', data))
print(f"\nSource files referenced ({len(cpp_files)}):")
for f in sorted([f.decode('latin1') for f in cpp_files if 'cat' in f.decode('latin1').lower() or 'game' in f.decode('latin1').lower() or 'save' in f.decode('latin1').lower()]):
    print(" ", f)
