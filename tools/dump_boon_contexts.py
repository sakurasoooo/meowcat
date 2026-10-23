"""Context dumps for key candidate boon-related code sites."""
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

def dump(center, before=0x50, after=0x70):
    print(f'=== context around {hex(center)} ===')
    s = center - before
    for insn in md.disasm(text_data[s - text_base_va : center - text_base_va + after], s):
        extra = ''
        if insn.mnemonic == 'lea' and 'rip' in insn.op_str:
            try:
                disp = int(insn.op_str.split('rip + ')[1].rstrip(']'), 16)
                lit = cstr_at_va(insn.address + insn.size + disp)
                if lit and all(32 <= ord(c) < 127 for c in lit):
                    extra = f'   ; "{lit[:60]}"'
            except Exception:
                pass
        mark = '>>>' if insn.address == center else '   '
        print(f'{mark} {hex(insn.address)}: {insn.mnemonic} {insn.op_str}{extra}')
    print()

for c in [0x14002b506, 0x14002c6ef, 0x140144bb8, 0x14005d65d]:
    dump(c)
