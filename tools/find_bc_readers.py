"""Among House-global load sites, find those reading +0xbc (expansion count) and dump the function math."""
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

sites = [0x1401a09f3, 0x1401a19ed, 0x1401a5eae, 0x1401ab3f0, 0x1401c5acb, 0x1401d2821, 0x1401d426a,
         0x1401e0800, 0x1401e57f7, 0x1401e5879, 0x1401e6f16, 0x1401e90e5, 0x1401e9127, 0x1401eea7b,
         0x140209db1, 0x14021187c, 0x140214033, 0x1402ec82a, 0x140336004]

for site in sites:
    # look ahead 120 bytes for access to +0xbc on the loaded register
    code = td[site - base: site - base + 130]
    insns = list(md.disasm(code, site))
    bc_hit = None
    reg = None
    for k, insn in enumerate(insns):
        if insn.mnemonic.startswith('mov') and 'rip' in insn.op_str and '0xbc]' in insn.op_str:
            pass
        # first insn is the global load -> reg
        if k == 0:
            reg = insn.op_str.split(',')[0]
        if f'[{reg} + 0xbc]' in insn.op_str:
            bc_hit = insn
            break
    if bc_hit:
        print(f'===== site {hex(site)} uses [house+0xbc] @ {hex(bc_hit.address)}: {bc_hit.mnemonic} {bc_hit.op_str}')
        START = site - 0x20
        endva = min(site + 0x180, bc_hit.address + 0x120)
        for insn in md.disasm(td[START - base: endva - base], START):
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
        print()
