import pefile

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw_data = f.read()

rdata_sec = [s for s in pe.sections if b'.rdata' in s.Name][0]
rdata_base_va = pe.OPTIONAL_HEADER.ImageBase + rdata_sec.VirtualAddress

def get_str(va):
    off = va - pe.OPTIONAL_HEADER.ImageBase
    for s in pe.sections:
        if s.VirtualAddress <= off < s.VirtualAddress + s.Misc_VirtualSize:
            raw_off = s.PointerToRawData + (off - s.VirtualAddress)
            end = raw_data.find(b'\x00', raw_off)
            return raw_data[raw_off:end].decode('latin1', errors='ignore')
    return "UNKNOWN"

# Check string at 0x1400ef6ed + 7 + 0xdec45c
str2_va = 0x1400ef6ed + 7 + 0xdec45c
print(f"String at {hex(str2_va)}: '{get_str(str2_va)}'")

# Check other strings in 0x1403a6d19 function
str3_va = 0x1403a6d3c + 7 + 0xb33f8d
print(f"String at {hex(str3_va)}: '{get_str(str3_va)}'")
str4_va = 0x1403a6d6a + 7 + 0xb55a27
print(f"String at {hex(str4_va)}: '{get_str(str4_va)}'")
