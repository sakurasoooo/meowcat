exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
with open(exe_path, 'rb') as f:
    data = f.read()

pos = 0x1112b4d
start = max(0, pos - 500)
end = min(len(data), pos + 1000)

chunk = data[start:end]
strs = [s.decode('ascii', errors='ignore') for s in chunk.split(b'\x00') if len(s) > 1 and all(32 <= b <= 126 for b in s)]
print("Strings around StringToCatPartID:")
for s in strs:
    print(f"  '{s}'")
