"""Dump the small getter functions near paired global loads."""
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

for site in [0x1401e57f7, 0x1401e5879, 0x1401e90e5, 0x1401e9127, 0x1401eea7b, 0x1401c5acb, 0x1401e6f16]:
    print(f'===== {hex(site)} =====')
    START, END = site - 0x10, site + 0x110
    for insn in md.disasm(td[START - base: END - base], START):
        extra = ''
        if 'rip' in insn.op_str and insn.mnemonic in ('lea', 'mov'):
            try:
                disp = int(insn.op_str.split('rip + ')[1].rstrip(']'), 16)
                lit = cstr_at_va(insn.address + insn.size + disp)
                if lit and 1 <= len(lit) <= 60 and all(32 <= ord(c) < 127 for c in lit):
                    extra = f'   ; "{lit}"'
            except Exception:
                pass
        print(f'  {hex(insn.address)}: {insn.mnemonic} {insn.op_str}{extra}')
        if insn.mnemonic == 'ret':
            break
    print()
