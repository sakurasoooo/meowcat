import pefile
import capstone

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw_data = f.read()

text_sec = [s for s in pe.sections if b'.text' in s.Name][0]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

target_va = 0x1403a6d88
offset = target_va - text_base_va
dis_bytes = raw_data[text_sec.PointerToRawData + offset : text_sec.PointerToRawData + offset + 200]
print(f"\nDisassembly starting from {hex(target_va)}:")
for insn in md.disasm(dis_bytes, target_va):
    print(f"  {hex(insn.address)}: {insn.mnemonic:<10} {insn.op_str}")
