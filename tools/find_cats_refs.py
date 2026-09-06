import pefile

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw_data = f.read()

text_sec = [s for s in pe.sections if b'.text' in s.Name][0]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]

# Find "cats" in rdata
rdata_sec = [s for s in pe.sections if b'.rdata' in s.Name][0]
rdata_data = raw_data[rdata_sec.PointerToRawData : rdata_sec.PointerToRawData + rdata_sec.SizeOfRawData]
rdata_base_va = pe.OPTIONAL_HEADER.ImageBase + rdata_sec.VirtualAddress

pos = 0
while True:
    pos = rdata_data.find(b"cats\x00", pos)
    if pos == -1:
        break
    str_va = rdata_base_va + pos
    print(f'Found "cats\\0" at VA {hex(str_va)}')
    
    # Check RIP-rel references to this str_va in .text
    for i in range(len(text_data) - 7):
        if text_data[i] == 0x48 and text_data[i+1] == 0x8d: # lea rcx/rdx/r8, [rip + disp]
            disp = int.from_bytes(text_data[i+3:i+7], byteorder='little', signed=True)
            curr_va = text_base_va + i
            if curr_va + 7 + disp == str_va:
                reg_byte = text_data[i+2]
                reg_name = {0x0d: 'rcx', 0x15: 'rdx', 0x05: 'rax', 0x1d: 'rbx'}.get(reg_byte, hex(reg_byte))
                print(f'  LEA {reg_name} at VA {hex(curr_va)}')
    pos += 5
