import pefile
import capstone

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw = f.read()

text_sec = [s for s in pe.sections if b'.text' in s.Name][0]
text_base = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
text_data = raw[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

for va in [0x1403c22a0, 0x1403c2350, 0x1403c3d50, 0x1403c2400, 0x1403c24b0]:
    print(f"\n--- Function at {hex(va)} ---")
    start = va - text_base
    dis_bytes = text_data[start : start + 30]
    for insn in md.disasm(dis_bytes, va):
        print(f"  {hex(insn.address)}: {insn.mnemonic:<10} {insn.op_str}")
