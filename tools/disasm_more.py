import pefile
import capstone

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw_data = f.read()

text_sec = None
for s in pe.sections:
    if b'.text' in s.Name:
        text_sec = s
        break

text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress

def disasm_func(va, length=200):
    offset = va - text_base_va
    dis_bytes = raw_data[text_sec.PointerToRawData + offset : text_sec.PointerToRawData + offset + length]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    print(f"\n--- Function at {hex(va)} ---")
    for insn in md.disasm(dis_bytes, va):
        print(f"  {hex(insn.address)}: {insn.mnemonic:<10} {insn.op_str}")

disasm_func(0x140774e10, 80)
disasm_func(0x140774ec0, 80)
