"""Find xrefs to lowercase 'none' string literal - the boon default value."""
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

# all occurrences of standalone lowercase 'none\0' (not preceded by letter, to avoid 'xnone' etc.)
positions = []
pos = 0
while True:
    i = raw_data.find(b'none\x00', pos)
    if i < 0:
        break
    pos = i + 1
    prev = raw_data[i-1] if i > 0 else 0
    if prev != 0 and not (65 <= prev <= 90 or 97 <= prev <= 122):
        pass  # preceded by letter -> part of longer string, skip? keep only standalone
    if prev == 0 or prev in (0x20,):
        positions.append(i)
print(f'standalone none\\0 occurrences: {len(positions)}')

# find xrefs for each
for str_pos in positions:
    str_va = va_of(str_pos)
    if str_va is None:
        continue
    needle_hits = []
    for i in range(len(text_data) - 7):
        if text_data[i] == 0x48 and text_data[i+1] in (0x8d, 0x8b):
            disp = int.from_bytes(text_data[i+3:i+7], byteorder='little', signed=True)
            if text_base_va + i + 7 + disp == str_va:
                needle_hits.append(text_base_va + i)
    if needle_hits:
        print(f'VA {hex(str_va)} (off {hex(str_pos)}): {len(needle_hits)} xrefs: {[hex(h) for h in needle_hits[:12]]}')
