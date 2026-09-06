import ctypes
import re

dbghelp = ctypes.windll.dbghelp
# UnDecorateSymbolName(name, outputString, maxStringLength, flags)
undecorate = dbghelp.UnDecorateSymbolName
undecorate.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint32]
undecorate.restype = ctypes.c_uint32

def demangle(mangled):
    buf = ctypes.create_string_buffer(2048)
    res = undecorate(mangled.encode('latin1'), buf, 2048, 0)
    if res > 0:
        return buf.value.decode('latin1')
    return mangled

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
with open(exe_path, 'rb') as f:
    data = f.read()

symbols = re.findall(b'\?[a-zA-Z0-9_@$]+', data)
print(f"Total symbol-like strings: {len(symbols)}")

catdata_symbols = []
for s in symbols:
    s_str = s.decode('latin1', errors='ignore')
    if 'CatData' in s_str or 'MewSaveFile' in s_str or 'CatPart' in s_str or 'CatDatabase' in s_str:
        dm = demangle(s_str)
        if dm != s_str:
            catdata_symbols.append(dm)

print(f"Demangled Cat/Save symbols ({len(catdata_symbols)}):")
for s in sorted(set(catdata_symbols))[:100]:
    print(" ", s)
