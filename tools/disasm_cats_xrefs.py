import pefile
import capstone

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw_data = f.read()

text_sec = [s for s in pe.sections if b'.text' in s.Name][0]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

for target_va in [0x1400ef6c3, 0x1403a6d19, 0x140929383]:
    print(f"\n==================== VA {hex(target_va)} ====================")
    offset = target_va - text_base_va
    start_off = max(0, offset - 40)
    end_off = offset + 120
    dis_bytes = raw_data[text_sec.PointerToRawData + start_off : text_sec.PointerToRawData + end_off]
    for insn in md.disasm(dis_bytes, text_base_va + start_off):
        prefix = "==> " if insn.address == target_va else "    "
        print(f"{prefix}{hex(insn.address)}: {insn.mnemonic:<10} {insn.op_str}")
