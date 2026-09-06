import pefile

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw_data = f.read()

target_str = b"Living cats table corrupted"
str_pos = raw_data.find(target_str)

str_va = None
for s in pe.sections:
    if s.PointerToRawData <= str_pos < s.PointerToRawData + s.SizeOfRawData:
        str_va = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress + (str_pos - s.PointerToRawData)
        break

print(f"Target VA: {hex(str_va)}")
str_rva = str_va - pe.OPTIONAL_HEADER.ImageBase

# Search across all sections for references
for s in pe.sections:
    sec_data = raw_data[s.PointerToRawData : s.PointerToRawData + s.SizeOfRawData]
    sec_va = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
    # Check RIP-relative (disp32)
    for i in range(len(sec_data) - 4):
        disp = int.from_bytes(sec_data[i:i+4], byteorder='little', signed=True)
        # instruction end can be i+4
        curr_end_va = sec_va + i + 4
        if curr_end_va + disp == str_va:
            print(f"RIP-rel reference in {s.Name.decode('latin1').strip(chr(0))} at VA {hex(sec_va + i)} (instr ends at {hex(curr_end_va)})")
    # Check 64-bit absolute
    packed_va = int.to_bytes(str_va, 8, 'little')
    pos = 0
    while True:
        pos = sec_data.find(packed_va, pos)
        if pos == -1:
            break
        print(f"Absolute pointer in {s.Name.decode('latin1').strip(chr(0))} at VA {hex(sec_va + pos)}")
        pos += 8
