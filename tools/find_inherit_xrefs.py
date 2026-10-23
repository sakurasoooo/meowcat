"""Find xrefs to inheritance config key strings to locate the breeding/kitten-generation code."""
import pefile, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw_data = open(exe_path, 'rb').read()
text_sec = next(s for s in pe.sections if b'.text' in s.Name)
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress

def va_of(raw_off):
    for s in pe.sections:
        if s.PointerToRawData <= raw_off < s.PointerToRawData + s.SizeOfRawData:
            return pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress + (raw_off - s.PointerToRawData)
    return None

def xrefs(s):
    pos = raw_data.find(s)
    if pos < 0:
        return None, []
    va = va_of(pos)
    hits = []
    i = 0
    while True:
        i = text_data.find(b'\x48\x8d', i)
        if i < 0 or i > len(text_data) - 7:
            break
        disp = int.from_bytes(text_data[i+3:i+7], byteorder='little', signed=True)
        if text_base_va + i + 7 + disp == va:
            hits.append(text_base_va + i)
        i += 1
    return va, hits

for s in [b'InheritPieceFavorMutation\x00', b'InheritAbilityChance\x00', b'KittenChanceOfExtraRandomStat\x00',
          b'HOUSE_CAT_INFO_HAS_MUTATIONS\x00', b'CatParts\x00']:
    va, hits = xrefs(s)
    print(f'{s.decode().strip():35s} VA={hex(va) if va else None} xrefs={[hex(h) for h in hits[:8]]}')
