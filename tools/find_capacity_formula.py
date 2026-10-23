"""Find readers of global 0x1413aa9a0 (+0xbc expansion count) -> capacity formula."""
import pefile, capstone, sys, io, re, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw_data = open(exe_path, 'rb').read()
text_sec = next(s for s in pe.sections if b'.text' in s.Name)
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

TARGET = 0x1413aa9a0

def cstr_at_va(va):
    for s in pe.sections:
        base = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
        if base <= va < base + s.Misc_VirtualSize:
            off = s.PointerToRawData + (va - base)
            end = raw_data.find(b'\x00', off)
            return raw_data[off:end].decode('utf-8', errors='replace')
    return None

# find "mov r64, [rip+X]" loading TARGET
sites = []
i = 0
while True:
    i = text_data.find(b'\x48\x8b\x05', i)
    if i < 0 or i > len(text_data) - 7:
        break
    disp = int.from_bytes(text_data[i+3:i+7], byteorder='little', signed=True)
    if text_base_va + i + 7 + disp == TARGET:
        sites.append(text_base_va + i)
    i += 1
print(f'loads of global {hex(TARGET)}: {[hex(s) for s in sites]}')

for site in sites:
    print(f'===== site {hex(site)} =====')
    START, END = site - 0x50, site + 0x140
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
        mark = '>>>' if insn.address == site else '   '
        print(f'{mark}{hex(insn.address)}: {insn.mnemonic} {insn.op_str}{extra}')
    print()
