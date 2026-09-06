import pefile

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe"
with open(exe_path, "rb") as f:
    data = f.read()

start = 0xeff500
end = 0xeff700
chunk = data[start:end]
for s in chunk.split(b'\x00'):
    if len(s) > 2:
        print("  *", s.decode('ascii', errors='ignore'))