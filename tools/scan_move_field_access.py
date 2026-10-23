"""Resolve init literal for boon field, and map all accesses to move(0x7d0)/attack(0x7f0) to find the serializer access pattern."""
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

# literal assigned to [rsi+0x798] in reset fn
print('boon init literal:', repr(cstr_at_va(0x14002b410 + 0xea79e9)))
print('[rsi+0x7b8] init literal:', repr(cstr_at_va(0x14002b423 + 0x139990d)))

print('\nscanning for [reg+0x7d0] (move) accesses...')
hits = []
for insn in md.disasm(text_data, text_base_va):
    if '0x7d0]' in insn.op_str:
        hits.append((insn.address, insn.mnemonic, insn.op_str))
print(f'{len(hits)} hits:')
for addr, mn, ops in hits:
    print(f'  {hex(addr)}: {mn} {ops}')
