"""Find who calls get_mutation / iterates mutation stat bonuses (stat aggregation)."""
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
    for prefix in (b'\x48\x8d', b'\x4c\x8d'):
        i = 0
        while True:
            i = text_data.find(prefix, i)
            if i < 0 or i > len(text_data) - 7:
                break
            disp = int.from_bytes(text_data[i+3:i+7], byteorder='little', signed=True)
            if text_base_va + i + 7 + disp == va:
                hits.append(text_base_va + i)
            i += 1
    return va, sorted(set(hits))

for s in [b'get_mutation\x00', b'data/mutations\x00']:
    va, hits = xrefs(s)
    print(f'{s.decode().strip():20s} VA={hex(va) if va else None} xrefs={[hex(h) for h in hits[:12]]}')

# also locate the demangled CatStats::mutate and any function strings with 'GetMutation'
import re
for m in re.finditer(rb'[\x20-\x7e]{8,90}', raw_data):
    s2 = m.group().decode()
    if ('GetMutation' in s2 or 'MutationStat' in s2 or 'mutation_stat' in s2) and not s2.startswith('.?'):
        print('STR:', s2)
