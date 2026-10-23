"""Disassemble House storage capacity computation sites: 0x1403cb7fe area and 0x1403cbbd5."""
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

for START, END, tag in [(0x1403cb760, 0x1403cb860, 'write 0x598 #1'), (0x1403cbb40, 0x1403cbc40, 'write/lea 0x598 #2'), (0x1401c2720, 0x1401c2820, 'read r12+0x598')]:
    print(f'===== {tag} =====')
    code = text_data[START - text_base_va : END - text_base_va]
    for insn in md.disasm(code, START):
        extra = ''
        if 'rip' in insn.op_str and insn.mnemonic in ('lea', 'mov'):
            try:
                disp = int(insn.op_str.split('rip + ')[1].rstrip(']'), 16)
                lit = cstr_at_va(insn.address + insn.size + disp)
                if lit and 1 <= len(lit) <= 60 and all(32 <= ord(c) < 127 for c in lit):
                    extra = f'   ; "{lit}"'
            except Exception:
                pass
        mark = '>>>' if '0x598' in insn.op_str else '   '
        print(f'{mark}{hex(insn.address)}: {insn.mnemonic} {insn.op_str}{extra}')
    print()
