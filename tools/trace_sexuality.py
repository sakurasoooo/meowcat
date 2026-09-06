import re
import pefile
import capstone

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe"
pe = pefile.PE(exe_path)
image_base = pe.OPTIONAL_HEADER.ImageBase

with open(exe_path, "rb") as f:
    data = f.read()

words = [b"sexuality", b"libido", b"catinfo_unlock_sexuality"]
for w in words:
    pos = 0
    while True:
        pos = data.find(w, pos)
        if pos == -1: break
        rva = pe.get_rva_from_offset(pos)
        print(f"String '{w.decode('ascii')}' at offset {hex(pos)}, RVA {hex(rva)}, VA {hex(image_base + rva)}")
        pos += len(w)
