"""Byte-pattern scan for [reg+disp32] where disp32 in {0x798, 0x7b8, 0x7d0, 0x7f0}; validate by back-disassembly.
Reliable vs linear sweep (which desyncs on embedded data)."""
import pefile, capstone, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path, fast_load=True)
raw_data = open(exe_path, 'rb').read()
text_sec = next(s for s in pe.sections if b'.text' in s.Name)
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

TARGETS = {0x798: 'boon?', 0x7b8: 'obj@7b8', 0x7d0: 'move?', 0x7f0: 'attack?'}

results = {k: [] for k in TARGETS}
for off, name in TARGETS.items():
    needle = off.to_bytes(4, 'little')
    pos = 0
    while True:
        i = text_data.find(needle, pos)
        if i < 0:
            break
        pos = i + 1
        # candidate: instruction ends here; disp32 is the last 4 bytes; try to decode instruction by
        # back-disassembling a window and checking an instruction operand ends exactly at i+4 with this disp
        win_start = max(0, i - 10)
        va_win = text_base_va + win_start
        found = None
        for insn in md.disasm(text_data[win_start:i+4], va_win):
            if insn.address + insn.size == text_base_va + i + 4 and f'{hex(off)}]' in insn.op_str:
                found = insn
        if found:
            results[off].append((found.address, found.mnemonic, found.op_str))

for off, name in TARGETS.items():
    print(f'=== [{name}] disp={hex(off)}: {len(results[off])} validated hits ===')
    for addr, mn, ops in results[off]:
        print(f'  {hex(addr)}: {mn} {ops}')
