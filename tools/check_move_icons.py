"""Check abilities catalog structure + move/attack ability typing + icon coverage."""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

cat = json.load(open('assets/abilities_catalog.json', encoding='utf-8'))
print(type(cat).__name__, len(cat))
entry0 = cat[0] if isinstance(cat, list) else list(cat.values())[0]
print('sample:', json.dumps(entry0, ensure_ascii=False)[:300])

by_key = {}
for e in (cat if isinstance(cat, list) else cat.values()):
    by_key[e.get('key') or e.get('code')] = e

print()
for key in ['DefaultMove', 'Dash', 'Teleport', 'LongJump', 'BasicMelee', 'BasicShortRanged', 'Reach', 'HealBolt']:
    e = by_key.get(key)
    if e:
        icon = e.get('icon') or e.get('icon_path') or ''
        print(f"{key:20s} icon={icon!r:40s} name={e.get('name','?')!r} 其他键={[k for k in e.keys()]}")
    else:
        print(f"{key:20s} NOT IN CATALOG")

# icon 实际存在吗
icons_dir = 'assets/icons/abilities'
have = set(os.path.splitext(f)[0] for f in os.listdir(icons_dir))
print()
print('catalog entries without icon file:')
missing = [k for k, e in by_key.items() if (e.get('icon') or e.get('icon_path') or '').endswith('.png')
           and os.path.basename(e.get('icon') or e.get('icon_path')).replace('.png','') not in have]
print(len(missing), missing[:20])
no_icon_field = [k for k, e in by_key.items() if not (e.get('icon') or e.get('icon_path'))]
print('entries without icon field:', len(no_icon_field), no_icon_field[:20])

# 移动类技能有哪些？从 game data abilities 里找 move 类型标记
gd = json.load(open('mewgenics_game_data.json', encoding='utf-8'))
ab = gd.get('abilities', [])
print()
print('game_data abilities sample:', json.dumps(ab[0], ensure_ascii=False)[:200] if ab else 'EMPTY')
kinds = {}
for a in ab:
    kinds.setdefault(a.get('kind') or a.get('type') or '?', []).append(a['key'])
for k, v in kinds.items():
    print(f"kind={k}: {len(v)} -> {v[:12]}")
