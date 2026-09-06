import pefile
import capstone

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw = f.read()

text_sec = [s for s in pe.sections if b'.text' in s.Name][0]
text_base = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
text_data = raw[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]

def get_str_at_va(va):
    off = va - pe.OPTIONAL_HEADER.ImageBase
    for s in pe.sections:
        if s.VirtualAddress <= off < s.VirtualAddress + s.Misc_VirtualSize:
            raw_off = s.PointerToRawData + (off - s.VirtualAddress)
            end = raw.find(b'\x00', raw_off)
            return raw[raw_off:end].decode('latin1', errors='ignore')
    return "UNKNOWN"

start_va = 0x140736800
dis_bytes = text_data[start_va - text_base : 0x140736cf0 - text_base]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

last_str = None
enum_map = {}
for insn in md.disasm(dis_bytes, start_va):
    if insn.mnemonic == 'lea' and insn.op_str.startswith('rdx, [rip + '):
        disp = int(insn.op_str.split('+ ')[1].rstrip(']'), 16)
        target_va = insn.address + insn.size + disp
        s = get_str_at_va(target_va)
        if len(s) < 30 and not s.startswith('C:\\'):
            last_str = s
    elif insn.mnemonic == 'mov' and insn.op_str.startswith('eax, 0x'):
        val = int(insn.op_str.split(', 0x')[1], 16)
        enum_map[val] = last_str
    elif insn.mnemonic == 'mov' and insn.op_str.startswith('eax, ') and insn.op_str.split(', ')[1].isdigit():
        val = int(insn.op_str.split(', ')[1])
        enum_map[val] = last_str

print(f"Total CatPartID entries found: {len(enum_map)}")
for k in sorted(enum_map.keys()):
    print(f"  {k:2d} (0x{k:02X}): {enum_map[k]}")
