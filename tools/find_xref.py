import pefile
import capstone

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw_data = f.read()

target_str = b"Living cats table corrupted"
str_pos = raw_data.find(target_str)
print(f"Target string found at raw offset: {hex(str_pos)}")

# Find virtual address of string
str_va = None
for s in pe.sections:
    if s.PointerToRawData <= str_pos < s.PointerToRawData + s.SizeOfRawData:
        str_va = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress + (str_pos - s.PointerToRawData)
        print(f"String VA: {hex(str_va)} in section {s.Name.decode('latin1').strip(chr(0))}")
        break

# Find references to str_va in .text section
text_sec = None
for s in pe.sections:
    if b'.text' in s.Name:
        text_sec = s
        break

text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress

# In x64, LEA rdx, [rip + disp32] is common: 48 8d ?? disp32
# disp32 = target_va - (current_va + 7)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

print("\nSearching for XREFs...")
for i in range(len(text_data) - 7):
    # check for 48 8d (lea)
    if text_data[i] == 0x48 and text_data[i+1] in (0x8d, 0x8b):
        # 48 8d / 48 8b
        disp = int.from_bytes(text_data[i+3:i+7], byteorder='little', signed=True)
        curr_va = text_base_va + i
        target = curr_va + 7 + disp
        if target == str_va:
            print(f"XREF found at VA: {hex(curr_va)}")
            # Disassemble surrounding 30 instructions
            dis_start = max(0, i - 40)
            dis_bytes = text_data[dis_start : i + 100]
            dis_va = text_base_va + dis_start
            print("--- Disassembly ---")
            for insn in md.disasm(dis_bytes, dis_va):
                print(f"  {hex(insn.address)}: {insn.mnemonic} {insn.op_str}")
