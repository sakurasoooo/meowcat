"""Empirical breeding test: do kittens always have symmetric paired parts (L==R)?
Also: do kitten parts match a parent's side (inheritance), favoring mutations?"""
import io, sys, struct, sqlite3, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from mewgenics_core import MewgenicsSaveManager

mgr = MewgenicsSaveManager(); mgr.load()
cats = mgr.cats
OFFS = [('legs', 164, 184), ('arms', 204, 224), ('eyes', 244, 264), ('brows', 284, 304), ('ears', 324, 344)]

def sides(c):
    return {n: (struct.unpack_from('<i', c.parts_chunk, a)[0], struct.unpack_from('<i', c.parts_chunk, b)[0])
            for n, a, b in OFFS}

p = os.path.expandvars(r'%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav')
blob = sqlite3.connect(p).execute("SELECT data FROM files WHERE key='pedigree'").fetchone()[0]
ped = {}
for i in range(0, len(blob) - 23, 32):
    child, pa, pb = struct.unpack_from('<3q', blob, i)
    ped[child] = (pa, pb)

kittens = [cats[k] for k in ped if k in cats]
asym_k = [(c.name, c.key, n, l, r) for c in kittens for n, (l, r) in sides(c).items() if l != r]
non_k = [c for c in cats.values() if c.key not in ped]
asym_nk = [(c.name, c.key, n, l, r) for c in non_k for n, (l, r) in sides(c).items() if l != r]

print(f'kittens={len(kittens)}  asymmetric parts in kittens: {len(asym_k)}')
for t in asym_k[:10]:
    print('   ', t)
print(f'non-kittens={len(non_k)}  asymmetric parts: {len(asym_nk)}')
for t in asym_nk[:10]:
    print('   ', t)

# inheritance source check: for kittens with a mutated paired part, does the id match a parent's L or R?
print()
print('=== inheritance source for mutated paired parts (sample) ===')
matched = {'mom': 0, 'dad': 0, 'neither': 0, 'both': 0}
shown = 0
for c in kittens:
    pa, pb = ped[c.key]
    if pa not in cats or pb not in cats:
        continue
    A, B = sides(cats[pa]), sides(cats[pb])
    for n, (l, r) in sides(c).items():
        if l < 300:  # not a mutation
            continue
        in_a = l in A[n]
        in_b = l in B[n]
        if in_a and in_b: matched['both'] += 1
        elif in_a: matched['mom'] += 1
        elif in_b: matched['dad'] += 1
        else: matched['neither'] += 1
        if shown < 8:
            print(f'  kitten {c.name}({c.key}) {n}={l}  parentA sides={A[n]} parentB sides={B[n]}')
            shown += 1
print('match summary (A/B = two parents):', matched)
