"""Find Inventory.cpp assert xrefs -> insert_item and capacity check."""
import pefile, capstone, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw = open(exe_path, 'rb').read()
sec = next(s for s in pe.sections if b'.text' in s.Name)
td = raw[sec.PointerToRawData: sec.PointerToRawData + sec.SizeOfRawData]
base = pe.OPTIONAL_HEADER.ImageBase + sec.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

def va_of(raw_off):
    for s in pe.sections:
        if s.PointerToRawData <= raw_off < s.PointerToRawData + s.SizeOfRawData:
            return pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress + (raw_off - s.PointerToRawData)
    return None

def cstr_at_va(va):
    for s in pe.sections:
        b = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
        if b <= va < b + s.Misc_VirtualSize:
            off = s.PointerToRawData + (va - b)
            end = raw.find(b'\x00', off)
            return raw[off:end].decode('utf-8', errors='replace')
    return None

targets = [b'C:\\Users\\Tyler\\Desktop\\SVN\\Mewgenics\\game\\code\\Inventory.cpp\x00', b'More than one inventory\x00']
for s in targets:
    pos = raw.find(s)
    if pos < 0:
        print('NOT FOUND:', s); continue
    va = va_of(pos)
    hits = []
    i = 0
    while True:
        i = td.find(b'\x48\x8d', i)
        if i < 0 or i > len(td) - 7:
            break
        disp = int.from_bytes(td[i+3:i+7], byteorder='little', signed=True)
        if base + i + 7 + disp == va:
            hits.append(base + i)
        i += 1
    print(f'{s.decode()[:60]}: {len(hits)} xrefs: {[hex(h) for h in hits[:12]]}')
