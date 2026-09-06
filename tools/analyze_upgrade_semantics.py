"""Determine semantics of the 4 'upgrade' slots by correlating with gon variant_of chains."""
import sys, io, os, re, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mewgenics_core import MewgenicsSaveManager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1) parse all ability gon files: name -> variant_of
variant_of = {}
gon_dir = os.path.join(ROOT, 'game_assets', 'data', 'abilities')
for fn in os.listdir(gon_dir):
    if not fn.endswith('.gon'):
        continue
    text = open(os.path.join(gon_dir, fn), encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'^(\w+)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', text, re.M):
        name, body = m.group(1), m.group(2)
        vm = re.search(r'variant_of\s+(\w+)', body)
        if vm:
            variant_of[name] = vm.group(1)

def root_of(a, seen=None):
    seen = seen or set()
    while a in variant_of and a not in seen:
        seen.add(a)
        a = variant_of[a]
    return a

def chain(a):
    out = [a]
    while a in variant_of:
        a = variant_of[a]
        out.append(a)
    return out

# check specific observed pairs
for a, b in [('Spit', 'PokeWound'), ('Roll', 'ForbiddenFart'), ('Till2', 'Till'), ('Reach', 'Reach'), ('HealBolt', 'HealBolt')]:
    print(f'{a:20s} chain={chain(a)}   {b:15s} chain={chain(b)}')

# 2) statistical analysis over all cats
mgr = MewgenicsSaveManager(); mgr.load()
cats = list(mgr.cats.values()) if isinstance(mgr.cats, dict) else mgr.cats

rel = collections.Counter()
examples = collections.defaultdict(list)
for c in cats:
    for i in range(4):
        a = c.active_abilities[i] if i < len(c.active_abilities) else 'None'
        u = c.ability_upgrades[i] if i < len(c.ability_upgrades) else 'None'
        if u == 'None' or u == a:
            continue
        ra, ru = root_of(a), root_of(u)
        if ru == a:
            key = 'upgrade_slot是active的祖先(降级链)'
        elif ra == u:
            key = 'upgrade_slot是active的后代(升级链)'
        elif ra == ru:
            key = '同根不同支'
        else:
            key = '无variant关系'
        rel[key] += 1
        if len(examples[key]) < 8:
            examples[key].append(f'{c.name}: slot{i} active={a} upgrade={u}')

print()
for k, n in rel.most_common():
    print(f'{k}: {n}')
    for e in examples[k]:
        print('   ', e)

# 3) unfought cats like 银月: upgrades == actives pattern
mirror = sum(1 for c in cats if c.ability_upgrades == c.active_abilities)
slot0_only = sum(1 for c in cats if c.ability_upgrades[0] == c.active_abilities[0]
                 and all(u == 'None' for u in c.ability_upgrades[1:]))
print(f'\ncats with upgrades==actives exactly: {mirror}')
print(f'cats with only slot0 mirrored, rest None: {slot0_only}')
