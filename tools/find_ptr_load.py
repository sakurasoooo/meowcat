import pefile

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw_data = f.read()

target_va = 0x141131d15
target_bytes = target_va.to_bytes(8, 'little')

for s in pe.sections:
    sec_data = raw_data[s.PointerToRawData : s.PointerToRawData + s.SizeOfRawData]
    sec_va = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
    pos = 0
    while True:
        pos = sec_data.find(target_bytes, pos)
        if pos == -1:
            break
        print(f"Direct pointer in {s.Name.decode().strip(chr(0))} at {hex(sec_va + pos)}")
        pos += 8
