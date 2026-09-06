"""Find cat 银月 in the live save and dump its ability/upgrade strings."""
import sys, io, os, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mewgenics_core import MewgenicsSaveManager

mgr = MewgenicsSaveManager()
print('save path:', mgr.file_path)
mgr.load()
cats = mgr.cats
if isinstance(cats, dict):
    cats = list(cats.values())

print(f'total cats: {len(cats)}')
for c in cats:
    if '银月' in (c.name or ''):
        print('=' * 60)
        print(f'key={c.key} name={c.name} class={c.cat_class}')
        print('base_stats :', c.base_stats)
        print('bonus_stats:', c.bonus_stats)
        print('boon       :', c.boon)
        print('move       :', c.move_ability)
        print('attack     :', c.attack_ability)
        print('actives    :', c.active_abilities)
        print('upgrades   :', c.ability_upgrades)
        print('class_pasv :', c.class_passives)
        print('disorders  :', c.disorders)
        print('all strings:')
        for off, slen, s in c.str_records:
            print(f'  @{off:5d} len={slen:2d} {s}')
