import pefile

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw = f.read()

target_va = 0x140f00a15
# Search for target_va in .rdata or .data or .text
for s in pe.sections:
    sec_data = raw[s.PointerToRawData : s.PointerToRawData + s.SizeOfRawData]
    sec_base = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
    pos = 0
    while True:
        pos = sec_data.find(target_va.to_bytes(8, 'little'), pos)
        if pos == -1: break
        print(f"Direct pointer in {s.Name.decode().strip(chr(0))} at {hex(sec_base + pos)}")
        pos += 8
