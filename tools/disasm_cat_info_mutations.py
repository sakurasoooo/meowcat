"""Disassemble house cat info card around HOUSE_CAT_INFO_HAS_MUTATIONS / MutationTooltip."""
import pefile, capstone, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw_data = open(exe_path, 'rb').read()
text_sec = next(s for s in pe.sections if b'.text' in s.Name)
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

def cstr_at_va(va):
    for s in pe.sections:
        base = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
        if base <= va < base + s.Misc_VirtualSize:
            off = s.PointerToRawData + (va - base)
            end = raw_data.find(b'\x00', off)
            return raw_data[off:end].decode('utf-8', errors='replace')
    return None

START, END = 0x1400e5500, 0x1400e5b00
code = text_data[START - text_base_va : END - text_base_va]
for insn in md.disasm(code, START):
    extra = ''
    if insn.mnemonic in ('lea', 'mov') and 'rip' in insn.op_str:
        try:
            disp = int(insn.op_str.split('rip + ')[1].rstrip(']'), 16)
            lit = cstr_at_va(insn.address + insn.size + disp)
            if lit and 1 <= len(lit) <= 70 and all(32 <= ord(c) < 127 for c in lit):
                extra = f'   ; "{lit}"'
        except Exception:
            pass
    mark = '>>>' if insn.address in (0x1400e5618, 0x1400e5765) else '   '
    print(f'{mark} {hex(insn.address)}: {insn.mnemonic} {insn.op_str}{extra}')
