import re
import pefile

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe"
with open(exe_path, "rb") as f:
    data = f.read()

# Search for sexuality, gender, breeding related words in CatData context
keywords = [
    rb"gender", rb"sexuality", rb"orientation", rb"fertile", rb"sterile",
    rb"pregnant", rb"hetero", rb"homo", rb"bisexual", rb"asexual",
    rb"libido", rb"mutation", rb"disease", rb"father", rb"mother", rb"parent"
]

for kw in keywords:
    matches = set(re.findall(rb"[a-zA-Z0-9_]*" + kw + rb"[a-zA-Z0-9_]*", data, re.IGNORECASE))
    print(f"Matches for '{kw.decode('ascii')}':", [m.decode('ascii', errors='ignore') for m in list(matches)[:10]])
