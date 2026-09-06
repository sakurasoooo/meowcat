import pefile
import capstone

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw_data = f.read()

text_sec = [s for s in pe.sections if b'.text' in s.Name][0]
text_base_va = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
text_data = raw_data[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]

for s_name in [b"MewSaveFile::Load", b"SQLSaveFile::LoadDataFromTable", b"CatData"]:
    pos = raw_data.find(s_name)
    if pos != -1:
        # Find VA
        for s in pe.sections:
            if s.PointerToRawData <= pos < s.PointerToRawData + s.SizeOfRawData:
                str_va = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress + (pos - s.PointerToRawData)
                print(f"'{s_name.decode()}' at VA {hex(str_va)}")
                # Search XREF
                for i in range(len(text_data) - 7):
                    if text_data[i] == 0x48 and text_data[i+1] == 0x8d:
                        disp = int.from_bytes(text_data[i+3:i+7], byteorder='little', signed=True)
                        curr_va = text_base_va + i
                        if curr_va + 7 + disp == str_va:
                            print(f"  XREF at VA {hex(curr_va)}")
