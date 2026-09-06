"""Disassemble a wide window around the Levelup_Boon UI reference to see how boon is read."""
import pefile, capstone, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw_data = open(exe_path, 'rb').read()
text_sec = next(s for s in pe.sections if b'.text' in s.Name)
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

START, END = 0x14037acc0, 0x14037b060
off_s, off_e = START - text_base_va, END - text_base_va
code = text_data[off_s:off_e]
for insn in md.disasm(code, START):
    print(f'{hex(insn.address)}: {insn.mnemonic} {insn.op_str}')
