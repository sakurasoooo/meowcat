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

# Find function start before 0x1407749cc
# Walk backwards to find push rbp / sub rsp / etc.
target_va = 0x1407749cc
off = target_va - text_base

# Walk back to find int3 / ret / function prologue
fn_start = off
while fn_start > 0:
    # check for CC CC CC or ret (C3)
    if text_data[fn_start-1] in (0xcc, 0xc3):
        break
    fn_start -= 1

fn_va = text_base + fn_start
print(f"Function starts at VA: {hex(fn_va)} (length to target: {target_va - fn_va})")

# Disassemble from fn_va
dis_bytes = text_data[fn_start : off + 150]
for insn in md.disasm(dis_bytes, fn_va):
    prefix = "==> " if insn.address == target_va else "    "
    print(f"{prefix}{hex(insn.address)}: {insn.mnemonic:<10} {insn.op_str}")
