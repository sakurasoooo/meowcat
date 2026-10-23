"""Disassemble around the Inventory.cpp assert at 0x1402e14ca to find insert_item / capacity logic."""
import pefile, capstone, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw = open(exe_path, 'rb').read()
sec = next(s for s in pe.sections if b'.text' in s.Name)
td = raw[sec.PointerToRawData: sec.PointerToRawData + sec.SizeOfRawData]
base = pe.OPTIONAL_HEADER.ImageBase + sec.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

def cstr_at_va(va):
    for s in pe.sections:
        b = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
        if b <= va < b + s.Misc_VirtualSize:
            off = s.PointerToRawData + (va - b)
            end = raw.find(b'\x00', off)
            return raw[off:end].decode('utf-8', errors='replace')
    return None

START, END = 0x1402e1200, 0x1402e1520
for insn in md.disasm(td[START - base: END - base], START):
    extra = ''
    if 'rip' in insn.op_str and insn.mnemonic in ('lea', 'mov'):
        try:
            disp = int(insn.op_str.split('rip + ')[1].rstrip(']'), 16)
            lit = cstr_at_va(insn.address + insn.size + disp)
            if lit and 1 <= len(lit) <= 70 and all(32 <= ord(c) < 127 for c in lit):
                extra = f'   ; "{lit}"'
        except Exception:
            pass
    mark = '>>>' if insn.address == 0x1402e14ca else '  '
    print(f'{mark}{hex(insn.address)}: {insn.mnemonic} {insn.op_str}{extra}')
