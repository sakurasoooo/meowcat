"""Resolve string literals and find all accesses to candidate boon string offsets 0x798 / 0x7b8."""
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

# literals in InitializeAbilities & constructor
for label, va in [
    ('InitAbilities: set [r13+0x7f0] = ', 0x1407a35ed + 0x736be3),
    ('InitAbilities: set [r13+0x7d0] = ', 0x1407a3600 + 0x735517),
    ('ctor A: init [rdi+0x7b8] = ', 0x140027011 + 0x139dd1f),
    ('ctor B: init [rdi+0x7b8] = ', 0x140028bbd + 0x139c173),
    ('InitAbilities local str @ 0x1407a360c = ', 0x1407a3610 + 0x977a6c),
]:
    print(f'{label} {cstr_at_va(va)!r}  (VA {hex(va)})')

print('\nscanning .text for [reg+0x798] and [reg+0x7b8] accesses...')
hits = {'0x798': [], '0x7b8': []}
for insn in md.disasm(text_data, text_base_va):
    for off in hits:
        if f'{off}]' in insn.op_str:
            hits[off].append((insn.address, insn.mnemonic, insn.op_str))
for off, lst in hits.items():
    print(f'\n=== [reg+{off}]: {len(lst)} hits ===')
    for addr, mn, ops in lst[:30]:
        print(f'  {hex(addr)}: {mn} {ops}')
