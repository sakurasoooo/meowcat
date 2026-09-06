import re

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
with open(exe_path, 'rb') as f:
    data = f.read()

# Search for RTTI classes with Stream, Buffer, Serial, Pack, Binary
classes = re.findall(b'\x2e\x3f\x41\x56([a-zA-Z0-9_@]+)\x40\x40', data)
for c in classes:
    c_str = c.decode('latin1', errors='ignore').lower()
    if any(k in c_str for k in ['stream', 'serial', 'pack', 'binary', 'buffer', 'reader', 'writer']):
        print(c.decode('latin1'))

# Also search for GonObject or GON (Tyler Glaiel's object notation)
print("\n--- GON Object mentions ---")
for c in classes:
    if 'gon' in c.decode('latin1').lower():
        print(c.decode('latin1'))
