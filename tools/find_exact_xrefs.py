import pefile
import capstone

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw_data = f.read()

text_sec = [s for s in pe.sections if b'.text' in s.Name][0]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

for target_va in [0x140f00a15, 0x141131d15]:
    print(f"\nSearching for all references to {hex(target_va)}:")
    # Check 1 to 7 byte instruction endings
    for i in range(len(text_data) - 4):
        disp = int.from_bytes(text_data[i:i+4], byteorder='little', signed=True)
        for instr_len in [4, 5, 6, 7]:
            if i + 4 >= instr_len:
                instr_start_va = text_base_va + (i + 4 - instr_len)
                instr_end_va = instr_start_va + instr_len
                if instr_end_va + disp == target_va:
                    instr_bytes = text_data[i + 4 - instr_len : i + 4]
                    for insn in md.disasm(instr_bytes, instr_start_va):
                        print(f"  Found at {hex(insn.address)}: {insn.mnemonic} {insn.op_str}")
