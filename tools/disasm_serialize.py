import pefile
import capstone
import struct

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe"
pe = pefile.PE(exe_path)
image_base = pe.OPTIONAL_HEADER.ImageBase

with open(exe_path, "rb") as f:
    data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Find references to string at 0xf0099e
rva_str = 0xf0099e
print("Looking for references to string at RVA:", hex(rva_str))

for i in range(len(data) - 7):
    if data[i] in [0x48, 0x4C] and data[i+1] in [0x8D, 0x8B]:
        modrm = data[i+2]
        if (modrm & 0xC7) == 0x05:
            disp = struct.unpack("<i", data[i+3:i+7])[0]
            insn_rva = pe.get_rva_from_offset(i)
            if insn_rva is not None and insn_rva + 7 + disp == rva_str:
                print(f"Found code ref at RVA: {hex(insn_rva)}, VA: {hex(image_base + insn_rva)}")
                offset = pe.get_offset_from_rva(insn_rva)
                chunk = data[offset - 50 : offset + 150]
                for insn in md.disasm(chunk, image_base + insn_rva - 50):
                    m = "===> " if insn.address == image_base + insn_rva else "     "
                    print(f"  {m} {hex(insn.address)}: {insn.mnemonic:8s} {insn.op_str}")
