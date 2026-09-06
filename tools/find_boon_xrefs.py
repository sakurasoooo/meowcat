"""Find xrefs to 'Levelup_Boon' UI string and dump surrounding code context."""
import pefile, capstone, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw_data = open(exe_path, 'rb').read()

def va_of(raw_off):
    for s in pe.sections:
        if s.PointerToRawData <= raw_off < s.PointerToRawData + s.SizeOfRawData:
            return pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress + (raw_off - s.PointerToRawData)
    return None

text_sec = next(s for s in pe.sections if b'.text' in s.Name)
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

for target_str in [b'Levelup_Boon\x00', b'boon1\x00', b'boon2\x00']:
    str_pos = raw_data.find(target_str)
    if str_pos < 0:
        print(f'{target_str} NOT FOUND'); continue
    str_va = va_of(str_pos)
    print(f'=== {target_str} VA={hex(str_va)}')
    xrefs = []
    for i in range(len(text_data) - 7):
        if text_data[i] == 0x48 and text_data[i+1] in (0x8d, 0x8b):
            disp = int.from_bytes(text_data[i+3:i+7], byteorder='little', signed=True)
            if text_base_va + i + 7 + disp == str_va:
                xrefs.append(text_base_va + i)
    print(f'   xrefs: {[hex(x) for x in xrefs]}')
    for xv in xrefs[:3]:
        i = xv - text_base_va
        dis_start = max(0, i - 60)
        dis_bytes = text_data[dis_start : i + 80]
        print(f'   --- context around {hex(xv)} ---')
        for insn in md.disasm(dis_bytes, text_base_va + dis_start):
            mark = '>>>' if insn.address == xv else '   '
            print(f'  {mark} {hex(insn.address)}: {insn.mnemonic} {insn.op_str}')
