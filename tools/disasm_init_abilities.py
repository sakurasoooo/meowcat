"""Confirm CatData string member offsets via InitializeAbilities, then find all code accessing the boon member."""
import pefile, capstone, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw_data = open(exe_path, 'rb').read()
text_sec = next(s for s in pe.sections if b'.text' in s.Name)
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

def disasm_range(start, end, title):
    print(f'=== {title} ===')
    code = text_data[start - text_base_va : end - text_base_va]
    for insn in md.disasm(code, start):
        print(f'{hex(insn.address)}: {insn.mnemonic} {insn.op_str}')

# 1) CatData::InitializeAbilities @ 0x1407a35df (per RE doc): confirm move/attack/boon offsets
disasm_range(0x1407a35df, 0x1407a3700, 'InitializeAbilities')
