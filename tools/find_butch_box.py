"""Find butch_box_unlocked / inventory_storage xrefs -> storage UI & capacity code."""
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

for s in [b'butch_box_unlocked\x00', b'inventory_storage\x00', b'StorageLocker\x00']:
    pos = raw.find(s)
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
    print(f'{s.decode().strip():22s} VA={hex(va)} xrefs={[hex(h) for h in hits[:6]]}')
    for h in hits[:2]:
        print(f'--- context around {hex(h)}')
        START, END = h - 0x40, h + 0xC0
        for insn in md.disasm(td[START - base: END - base], START):
            extra = ''
            if 'rip' in insn.op_str and insn.mnemonic in ('lea', 'mov'):
                try:
                    disp = int(insn.op_str.split('rip + ')[1].rstrip(']'), 16)
                    lit = cstr_at_va(insn.address + insn.size + disp)
                    if lit and 1 <= len(lit) <= 60 and all(32 <= ord(c) < 127 for c in lit):
                        extra = f'   ; "{lit}"'
                except Exception:
                    pass
            mark = '>>>' if insn.address == h else ' '
            print(f'{mark}{hex(insn.address)}: {insn.mnemonic} {insn.op_str}{extra}')
        print()
