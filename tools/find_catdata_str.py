import pefile
import capstone

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe"
pe = pefile.PE(exe_path)
image_base = pe.OPTIONAL_HEADER.ImageBase

with open(exe_path, "rb") as f:
    data = f.read()

# Find string "CatData"
matches = []
pos = 0
while True:
    pos = data.find(b"CatData", pos)
    if pos == -1: break
    matches.append(pos)
    pos += 7

print(f"Found {len(matches)} occurrences of 'CatData':")
for p in matches:
    rva = pe.get_rva_from_offset(p)
    print(f"  Offset {hex(p)}, RVA {hex(rva)}: {data[p:p+30]}")
