import re

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
with open(exe_path, 'rb') as f:
    data = f.read()

queries = re.findall(b'SELECT [^\x00;]+;', data, re.IGNORECASE)
for q in queries:
    print(q.decode('latin1'))

print("\n--- INSERT / UPDATE queries ---")
queries2 = re.findall(b'(?:INSERT|UPDATE|DELETE|REPLACE) [^\x00;]+;', data, re.IGNORECASE)
for q in queries2:
    print(q.decode('latin1'))
