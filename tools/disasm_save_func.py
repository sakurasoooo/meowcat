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
target_va = 0x1407749cc
offset = target_va - text_base_va

dis_start = max(0, offset - 100)
dis_bytes = raw_data[text_sec.PointerToRawData + dis_start : text_sec.PointerToRawData + offset + 300]
dis_va = text_base_va + dis_start

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
for insn in md.disasm(dis_bytes, dis_va):
    prefix = "==> " if insn.address == target_va else "    "
    print(f"{prefix}{hex(insn.address)}: {insn.mnemonic:<10} {insn.op_str}")
