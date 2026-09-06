"""Dump the string-table neighborhood around Levelup_Boon and identify UI name clusters."""
import pefile, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw_data = open(exe_path, 'rb').read()

def raw_of_va(va):
    for s in pe.sections:
        base = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
        if base <= va < base + s.Misc_VirtualSize:
            return s.PointerToRawData + (va - base)
    return None

# strings around Levelup_Boon VA 0x140f134e0
center = raw_of_va(0x140f134e0)
region = raw_data[center - 600 : center + 900]
strings = []
for m in re.finditer(rb'[\x20-\x7e]{4,80}', region):
    strings.append(m.group().decode())
print('=== string neighborhood of Levelup_Boon ===')
for s in strings:
    print('  ', s)

# also around boon2 VA 0x140f13968
center2 = raw_of_va(0x140f13968)
region2 = raw_data[center2 - 500 : center2 + 500]
print('\n=== string neighborhood of boon2 ===')
for m in re.finditer(rb'[\x20-\x7e]{4,80}', region2):
    print('  ', m.group().decode())
