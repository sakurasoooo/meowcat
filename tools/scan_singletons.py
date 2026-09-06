import pefile
import capstone
import re

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw = f.read()

text_sec = [s for s in pe.sections if b'.text' in s.Name][0]
text_base = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
text_data = raw[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Look for CatDatabase or Director strings in rdata
for s_target in [b"CatDatabase", b"MewDirector", b"HouseCat", b"MewSaveFile"]:
    pos = 0
    while True:
        pos = raw.find(s_target, pos)
        if pos == -1: break
        # check VA
        for s in pe.sections:
            if s.PointerToRawData <= pos < s.PointerToRawData + s.SizeOfRawData:
                str_va = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress + (pos - s.PointerToRawData)
                # Check XREF
                for i in range(len(text_data) - 7):
                    if text_data[i] == 0x48 and text_data[i+1] == 0x8d:
                        disp = int.from_bytes(text_data[i+3:i+7], byteorder='little', signed=True)
                        curr_va = text_base + i
                        if curr_va + 7 + disp == str_va:
                            print(f"XREF to '{s_target.decode()}' at {hex(curr_va)}")
        pos += len(s_target)
