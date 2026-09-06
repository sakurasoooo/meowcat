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

for target_str in [b"house_gold", b"house_food", b"current_day"]:
    pos = raw.find(target_str)
    if pos != -1:
        for s in pe.sections:
            if s.PointerToRawData <= pos < s.PointerToRawData + s.SizeOfRawData:
                str_va = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress + (pos - s.PointerToRawData)
                print(f"\nTarget '{target_str.decode()}' at VA {hex(str_va)}")
                
                # Check references in .text
                for i in range(len(text_data) - 7):
                    if text_data[i] == 0x48 and text_data[i+1] == 0x8d:
                        disp = int.from_bytes(text_data[i+3:i+7], byteorder='little', signed=True)
                        curr_va = text_base + i
                        if curr_va + 7 + disp == str_va:
                            print(f"  XREF at VA {hex(curr_va)}")
                            # Disassemble 15 instructions
                            dis_bytes = text_data[i - 20 : i + 60]
                            dis_va = curr_va - 20
                            print("  -- Disassembly --")
                            for insn in md.disasm(dis_bytes, dis_va):
                                prefix = "==> " if insn.address == curr_va else "    "
                                print(f"  {prefix}{hex(insn.address)}: {insn.mnemonic:<10} {insn.op_str}")
