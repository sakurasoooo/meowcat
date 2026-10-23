"""Find and disassemble mutation-related game functions via assert-string xrefs."""
import pefile, capstone, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw_data = open(exe_path, 'rb').read()
text_sec = next(s for s in pe.sections if b'.text' in s.Name)
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

def va_of(raw_off):
    for s in pe.sections:
        if s.PointerToRawData <= raw_off < s.PointerToRawData + s.SizeOfRawData:
            return pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress + (raw_off - s.PointerToRawData)
    return None

def xrefs_to_str(s):
    pos = raw_data.find(s)
    if pos < 0:
        return None, []
    va = va_of(pos)
    hits = []
    i = 0
    while True:
        i = text_data.find(b'\x48\x8d', i)  # lea r64, ...
        if i < 0 or i > len(text_data) - 7:
            break
        disp = int.from_bytes(text_data[i+3:i+7], byteorder='little', signed=True)
        if text_base_va + i + 7 + disp == va:
            hits.append(text_base_va + i)
        i += 1
    return va, hits

for s in [b'Could not mutate part: \x00', b'No mutatable part named: \x00', b'Unknown Mutate mode \x00', b'save_file_next_cat_mutation\x00', b'mutationcount\x00']:
    va, hits = xrefs_to_str(s)
    print(f'{s.decode().strip():40s} VA={hex(va) if va else None} xrefs={[hex(h) for h in hits]}')
