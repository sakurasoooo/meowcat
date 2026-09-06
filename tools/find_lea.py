import pefile

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw_data = f.read()

text_sec = [s for s in pe.sections if b'.text' in s.Name][0]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]

target_va = 0x141131d15

# In x64:
# 48 8d 0d [disp32] (rcx) -> 7 bytes
# 48 8d 15 [disp32] (rdx) -> 7 bytes
# 4c 8d 05 [disp32] (r8)  -> 7 bytes
# 4c 8d 0d [disp32] (r9)  -> 7 bytes
# 48 8d 05 [disp32] (rax) -> 7 bytes

found = False
for i in range(len(text_data) - 7):
    # check 7-byte LEA with REX.W
    b0, b1, b2 = text_data[i], text_data[i+1], text_data[i+2]
    if (b0 == 0x48 or b0 == 0x4c) and b1 == 0x8d and (b2 & 0xc7 == 0x05):
        disp = int.from_bytes(text_data[i+3:i+7], byteorder='little', signed=True)
        curr_end_va = text_base_va + i + 7
        if curr_end_va + disp == target_va:
            print(f"Match at VA {hex(text_base_va + i)}!")
            found = True

if not found:
    print("No direct LEA found, checking disp32 anywhere...")
    # Check if target_va is reached by any 4-byte displacement
    for i in range(len(text_data) - 4):
        disp = int.from_bytes(text_data[i:i+4], byteorder='little', signed=True)
        for offset_after in range(4, 9):
            if text_base_va + i + offset_after + disp == target_va:
                print(f"Possible instr ending at +{offset_after} from {hex(text_base_va + i)}")
