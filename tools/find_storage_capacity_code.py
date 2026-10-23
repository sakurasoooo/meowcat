"""Find House.storage_capacity computation: scan for [r12+0x598] accesses and disassemble around them."""
import pefile, capstone, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw_data = open(exe_path, 'rb').read()
text_sec = next(s for s in pe.sections if b'.text' in s.Name)
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

def cstr_at_va(va):
    for s in pe.sections:
        base = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
        if base <= va < base + s.Misc_VirtualSize:
            off = s.PointerToRawData + (va - base)
            end = raw_data.find(b'\x00', off)
            return raw_data[off:end].decode('utf-8', errors='replace')
    return None

hits = []
for m in re.finditer(re.escape(b'\x98\x05\x00\x00'), text_data):
    off = m.start()
    # r12 base encodings: 41 8B 84 24 / 41 89 84 24 / 41 C7 84 24 (+ imm for C7)
    pre = text_data[off-4:off]
    if pre in (b'\x41\x8b\x84\x24'[1:], ) or True:
        pass
    if text_data[off-4:off] == bytes([0x41, 0x8b, 0x84]) or \
       text_data[off-4:off] == bytes([0x41, 0x89, 0x84]) or \
       text_data[off-4:off-1] == bytes([0x41, 0xc7, 0x84]):
        hits.append(off)

print(f'[r12+0x598] access sites: {len(hits)}')
for off in hits[:12]:
    va = text_base_va + off - 4
    print(f'--- site @ {hex(va)}')
    start = va - 0x60
    code = text_data[start - text_base_va : va + 0x40]
    for insn in md.disasm(code, start):
        extra = ''
        if 'rip' in insn.op_str and insn.mnemonic in ('lea', 'mov'):
            try:
                disp = int(insn.op_str.split('rip + ')[1].rstrip(']'), 16)
                lit = cstr_at_va(insn.address + insn.size + disp)
                if lit and 1 <= len(lit) <= 50 and all(32 <= ord(c) < 127 for c in lit):
                    extra = f'   ; "{lit}"'
            except Exception:
                pass
        print(f'  {hex(insn.address)}: {insn.mnemonic} {insn.op_str}{extra}')
    print()
