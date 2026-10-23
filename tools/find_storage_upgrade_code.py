"""Find storage_expansion / house_storage_upgrades xrefs -> capacity computation code."""
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

def cstr_at_va(va):
    for s in pe.sections:
        base = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
        if base <= va < base + s.Misc_VirtualSize:
            off = s.PointerToRawData + (va - base)
            end = raw_data.find(b'\x00', off)
            return raw_data[off:end].decode('utf-8', errors='replace')
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
    return va, sorted(set(hits))

for s in [b'storage_expansion\x00', b'house_storage_upgrades\x00']:
    va, hits = xrefs(s)
    print(f'{s.decode().strip():26s} VA={hex(va) if va else None} xrefs={[hex(h) for h in hits]}')

# disassemble around each hit
for s in [b'house_storage_upgrades\x00', b'storage_expansion\x00']:
    va, hits = xrefs(s)
    if not hits:
        continue
    for h in hits[:3]:
        print(f'===== {s.decode().strip()} site {hex(h)} =====')
        START, END = h - 0x90, h + 0xB0
        code = text_data[START - text_base_va : END - text_base_va]
        for insn in md.disasm(code, START):
            extra = ''
            if 'rip' in insn.op_str and insn.mnemonic in ('lea', 'mov'):
                try:
                    disp = int(insn.op_str.split('rip + ')[1].rstrip(']'), 16)
                    lit = cstr_at_va(insn.address + insn.size + disp)
                    if lit and 1 <= len(lit) <= 60 and all(32 <= ord(c) < 127 for c in lit):
                        extra = f'   ; "{lit}"'
                except Exception:
                    pass
            mark = '>>>' if insn.address == h else '   '
            print(f'{mark}{hex(insn.address)}: {insn.mnemonic} {insn.op_str}{extra}')
        print()
