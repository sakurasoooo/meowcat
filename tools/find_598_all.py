"""Broaden: find all disp32=0x598 instruction sites in .text and classify registers."""
import pefile, capstone, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw_data = open(exe_path, 'rb').read()
text_sec = next(s for s in pe.sections if b'.text' in s.Name)
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

sites = [m.start() for m in re.finditer(re.escape(b'\x98\x05\x00\x00'), text_data)]
print(f'raw 0x598 disp occurrences: {len(sites)}')
seen_funcs = set()
for off in sites:
    # back-disassemble from up to 24 bytes before
    va = text_base_va + off
    found = None
    for back in range(8, 25):
        s = va - back
        try:
            insns = list(md.disasm(text_data[s - text_base_va : s - text_base_va + back + 8], s))
        except Exception:
            continue
        if insns and insns[-1].address <= va and insns[-1].address + insns[-1].size >= va:
            last = insns[-1]
            if '0x598' in last.op_str:
                found = (last, insns[:-1])
                break
    if not found:
        continue
    insn, pre = found
    key = insn.mnemonic + '|' + insn.op_str.split(',')[0]
    if key in seen_funcs:
        continue
    seen_funcs.add(key)
    print(f'{hex(insn.address)}: {insn.mnemonic} {insn.op_str}')
    for p in pre[-3:]:
        print(f'    pre: {p.mnemonic} {p.op_str}')
