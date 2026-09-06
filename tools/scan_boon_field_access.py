"""Scan .text for accesses to CatData+0x7b0 (boon std::string) and show contexts."""
import pefile, capstone, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw_data = open(exe_path, 'rb').read()
text_sec = next(s for s in pe.sections if b'.text' in s.Name)
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = False

# disassemble whole .text once, filter instructions with displacement 0x7b0
print('disassembling .text (this takes a moment)...')
hits = []
for insn in md.disasm(text_data, text_base_va):
    if '0x7b0]' in insn.op_str:
        hits.append((insn.address, insn.mnemonic, insn.op_str))
print(f'accesses to [reg+0x7b0]: {len(hits)}')
for addr, mn, ops in hits:
    print(f'  {hex(addr)}: {mn} {ops}')

# show small context for each hit
for addr, mn, ops in hits:
    print(f'\n=== context @ {hex(addr)} ===')
    s = max(text_base_va, addr - 0x60)
    code = text_data[s - text_base_va : addr - text_base_va + 0x60]
    for insn in md.disasm(code, s):
        mark = '>>>' if insn.address == addr else '   '
        print(f'{mark} {hex(insn.address)}: {insn.mnemonic} {insn.op_str}')
