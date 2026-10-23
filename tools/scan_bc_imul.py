"""Scan all [reg+0xbc] reads; keep those with imul/add-chain nearby (capacity formula candidates)."""
import pefile, capstone, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw = open(exe_path, 'rb').read()
sec = next(s for s in pe.sections if b'.text' in s.Name)
td = raw[sec.PointerToRawData: sec.PointerToRawData + sec.SizeOfRawData]
base = pe.OPTIONAL_HEADER.ImageBase + sec.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# find ", 0xbc]" text pattern in disassembly is slow; instead find disp bytes 0xbc,0,0,0 preceded by plausible modrm
sites = [m.start() for m in re.finditer(re.escape(b'\xbc\x00\x00\x00'), td)]
cands = []
for off in sites:
    va = base + off
    # back-decode the instruction containing this disp
    for back in range(6, 20):
        s = va - back
        try:
            insns = list(md.disasm(td[s - base: s - base + back + 10], s))
        except Exception:
            continue
        if insns and insns[-1].address <= va and insns[-1].address + insns[-1].size >= va and '0xbc]' in insns[-1].op_str:
            insn = insns[-1]
            if insn.mnemonic.startswith('mov') and 'ptr [' in insn.op_str:
                # look ahead for imul/imul-style math
                code = td[insn.address - base + insn.size: insn.address - base + insn.size + 70]
                ahead = list(md.disasm(code, insn.address + insn.size))
                has_math = any(i.mnemonic in ('imul', 'mul') for i in ahead[:14])
                if has_math:
                    cands.append((insn, ahead))
            break

print(f'candidates: {len(cands)}')
for insn, ahead in cands[:8]:
    print(f'===== {hex(insn.address)}: {insn.mnemonic} {insn.op_str}')
    for i in ahead[:16]:
        print(f'    {hex(i.address)}: {i.mnemonic} {i.op_str}')
    print()
