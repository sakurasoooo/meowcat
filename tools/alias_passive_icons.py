"""Alias remaining missing passives: copy existing icon whose normalized name matches."""
import io, sys, json, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def norm(s): return ''.join(c for c in s.lower() if c.isalnum())

DEST = 'assets/icons/passives'
pas_cat = json.load(open('assets/passives_catalog.json', encoding='utf-8'))
missing = [e['key'] for e in pas_cat if not os.path.exists(os.path.join(DEST, e['key'] + '.png'))]
# 现有文件(去扩展名)
existing_names = [os.path.splitext(f)[0] for f in os.listdir(DEST) if f.endswith('.png')]
# norm -> [names]
from collections import defaultdict
by_norm = defaultdict(list)
for n in existing_names:
    by_norm[norm(n)].append(n)

copied = []
still = []
for key in missing:
    k = norm(key)
    cands = by_norm.get(k)
    if cands:
        src_name = cands[0]
        shutil.copyfile(os.path.join(DEST, src_name + '.png'), os.path.join(DEST, key + '.png'))
        copied.append((key, src_name))
    else:
        still.append(key)

print('通过规范名别名补全:')
for key, s in copied:
    print(f'  {key:26s} <- {s}')
print()
print('仍缺失:', still)
