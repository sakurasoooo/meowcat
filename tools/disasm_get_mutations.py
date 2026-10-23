"""Disassemble the mutation-list builder (called at 0x14081b9e2 -> fn 0x140830930).
Question: does it iterate 15 physical parts or 10 part types? Also check HOUSE_CAT_INFO text."""
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

START = 0x140830930
END = START + 0x700
code = text_data[START - text_base_va : END - text_base_va]
for insn in md.disasm(code, START):
    extra = ''
    if insn.mnemonic in ('lea', 'mov') and 'rip' in insn.op_str:
        try:
            disp = int(insn.op_str.split('rip + ')[1].rstrip(']'), 16)
            lit = cstr_at_va(insn.address + insn.size + disp)
            if lit and 1 <= len(lit) <= 60 and all(32 <= ord(c) < 127 for c in lit):
                extra = f'   ; "{lit}"'
        except Exception:
            pass
    # highlight compares against 10/15 and calls
    interesting = insn.mnemonic in ('cmp', 'call', 'jmp') or '0xf' in insn.op_str or '0xa' in insn.op_str
    mark = '*' if interesting else ' '
    print(f'{mark}{hex(insn.address)}: {insn.mnemonic} {insn.op_str}{extra}')
    if insn.mnemonic == 'ret':
        break
