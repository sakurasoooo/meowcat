import pefile
import capstone
import struct

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe"
pe = pefile.PE(exe_path)
image_base = pe.OPTIONAL_HEADER.ImageBase

with open(exe_path, "rb") as f:
    data = f.read()

# RVA of "straight" and "sexuality"
pos_sex = data.find(b"sexuality\x00")
rva_sex = pe.get_rva_from_offset(pos_sex)
print(f"'sexuality' RVA: {hex(rva_sex)}")

# Find RIP-relative refs
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

for i in range(len(data) - 7):
    if data[i] in [0x48, 0x4C] and data[i+1] in [0x8D, 0x8B]:
        modrm = data[i+2]
        if (modrm & 0xC7) == 0x05:
            disp = struct.unpack("<i", data[i+3:i+7])[0]
            insn_rva = pe.get_rva_from_offset(i)
            if insn_rva is not None and insn_rva + 7 + disp == rva_sex:
                print(f"Reference to 'sexuality' at RVA: {hex(insn_rva)}")
                offset = pe.get_offset_from_rva(insn_rva)
                chunk = data[offset - 30 : offset + 100]
                for insn in md.disasm(chunk, image_base + insn_rva - 30):
                    m = "===> " if insn.address == image_base + insn_rva else "     "
                    print(f"  {m} {hex(insn.address)}: {insn.mnemonic:8s} {insn.op_str}")