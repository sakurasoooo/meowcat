import pefile
import capstone

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe"
pe = pefile.PE(exe_path)
image_base = pe.OPTIONAL_HEADER.ImageBase

with open(exe_path, "rb") as f:
    data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

start_rva = 0xe3e00
end_rva = 0xe4150
offset = pe.get_offset_from_rva(start_rva)
chunk = data[offset : offset + (end_rva - start_rva)]

print("Disassembly of Cat Tooltip / Info formatting:")
for insn in md.disasm(chunk, image_base + start_rva):
    print(f"  {hex(insn.address)}: {insn.mnemonic:8s} {insn.op_str}")