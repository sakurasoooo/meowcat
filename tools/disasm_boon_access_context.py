"""Show contexts of the only two non-constructor accesses to the boon string (CatData+0x798)."""
import pefile, capstone, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw_data = open(exe_path, 'rb').read()
text_sec = next(s for s in pe.sections if b'.text' in s.Name)
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

for center in (0x140029947, 0x14002b402):
    print(f'=== context around {hex(center)} ===')
    s = center - 0x90
    code = text_data[s - text_base_va : center - text_base_va + 0xa0]
    for insn in md.disasm(code, s):
        mark = '>>>' if insn.address == center else '   '
        print(f'{mark} {hex(insn.address)}: {insn.mnemonic} {insn.op_str}')
    print()
