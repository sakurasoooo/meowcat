"""Compare actives vs upgrades across diverse cats to understand slot semantics."""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mewgenics_core import MewgenicsSaveManager

mgr = MewgenicsSaveManager()
mgr.load()
cats = list(mgr.cats.values()) if isinstance(mgr.cats, dict) else mgr.cats

# pick cats with different profiles
interesting = []
for c in cats:
    fought = any(b != 0 for b in c.bonus_stats) or c.cat_class != 'Colorless'
    if any(a != 'None' for a in c.active_abilities):
        interesting.append((fought, c))

interesting.sort(key=lambda t: not t[0])  # fought first
shown = 0
for fought, c in interesting[:15]:
    print(f"[{'战斗过' if fought else '未战斗'}] key={c.key} {c.name} ({c.cat_class})")
    print(f"   actives : {c.active_abilities}")
    print(f"   upgrades: {c.ability_upgrades}")
    print(f"   cls_pasv: {c.class_passives}  disorders: {c.disorders}")
    shown += 1

# stats: how often upgrades == actives
same = diff = 0
for c in cats:
    for a, u in zip(c.active_abilities, c.ability_upgrades):
        if a == u:
            same += 1
        else:
            diff += 1
            if diff <= 15:
                print(f"DIFF key={c.key} {c.name}: active={a!r} upgrade={u!r}")
print(f"\nslots identical: {same}, different: {diff}, total cats: {len(cats)}")
