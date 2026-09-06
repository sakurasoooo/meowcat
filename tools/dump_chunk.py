import pefile

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe"
with open(exe_path, "rb") as f:
    data = f.read()

start = 0xeda000
end = 0xeda300
chunk = data[start:end]

# Split by null bytes and filter printable strings
strs = [s.decode('ascii', errors='ignore') for s in chunk.split(b'\x00') if len(s) >= 2]
print(f"Strings in CatData chunk (0x{start:x} - 0x{end:x}):")
for s in strs:
    print("  *", s)