import pefile
import capstone

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw = f.read()

text_sec = [s for s in pe.sections if b'.text' in s.Name][0]
text_base = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
text_data = raw[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]

target_str = b"App.cpp"
pos = raw.find(target_str)
print(f"Target '{target_str.decode()}' at {hex(pos)}")

rdata_sec = [s for s in pe.sections if b'.rdata' in s.Name][0]
str_va = pe.OPTIONAL_HEADER.ImageBase + rdata_sec.VirtualAddress + (pos - rdata_sec.PointerToRawData)
print(f"Str VA: {hex(str_va)}")

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
for i in range(len(text_data) - 7):
    if text_data[i] == 0x48 and text_data[i+1] == 0x8d:
        disp = int.from_bytes(text_data[i+3:i+7], byteorder='little', signed=True)
        curr_va = text_base + i
        if curr_va + 7 + disp == str_va:
            print(f"  XREF to App.cpp at VA {hex(curr_va)}")
            dis_bytes = text_data[i - 30 : i + 50]
            for insn in md.disasm(dis_bytes, curr_va - 30):
                print(f"    {hex(insn.address)}: {insn.mnemonic:<10} {insn.op_str}")
            break
