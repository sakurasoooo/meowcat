import pefile

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
pe = pefile.PE(exe_path)

with open(exe_path, 'rb') as f:
    raw = f.read()

text_sec = [s for s in pe.sections if b'.text' in s.Name][0]
text_base = pe.OPTIONAL_HEADER.ImageBase + text_sec.VirtualAddress
text_data = raw[text_sec.PointerToRawData : text_sec.PointerToRawData + text_sec.SizeOfRawData]

def get_aob_and_test(va, length=16, mask_rips=True):
    off = va - text_base
    chunk = text_data[off : off + length]
    hex_list = []
    for b in chunk:
        hex_list.append(f"{b:02X}")
    pattern = ' '.join(hex_list)
    cnt = raw.count(chunk)
    return pattern, cnt

# Check AOB at 0x1403a6d13
p1, c1 = get_aob_and_test(0x1403a6d13, 20)
print(f"House Load AOB at 0x1403a6d13: {p1} (Matches: {c1})")

# Check AOB at 0x1403a6db9 (current_day)
p2, c2 = get_aob_and_test(0x1403a6db9, 20)
print(f"Current Day AOB at 0x1403a6db9: {p2} (Matches: {c2})")

# Check AOB at 0x1407749cc (Living cats check)
p3, c3 = get_aob_and_test(0x1407749c9, 24)
print(f"Living Cats Check AOB at 0x1407749c9: {p3} (Matches: {c3})")
