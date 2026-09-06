import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from event_catalog import load_event_catalog, filter_events, list_event_types

evs = load_event_catalog()
print('total', len(evs), 'hidden', sum(1 for e in evs if e['hidden']), 'types', len(list_event_types(evs)))
print('visible', len(filter_events(evs)))
for key in ('ABeggar', 'AFewCoins', 'Baphomet'):
    e = next(x for x in evs if x['key'] == key)
    print('====', e['key'], e['title'], e['type_zh'], 'opts', len(e['options']))
    print('prompt:', e['prompt'][:90].replace('\n', ' / '))
    for o in e['options']:
        print('  -', o['label'], o['stat_zh'], 'outcomes', len(o['outcomes']))
        for r in o['outcomes'][:5]:
            acts = ', '.join(f"{a['title']} {a['body']}".strip() for a in r['actions'][:4])
            print('    ', r['side'], r['rarity'], 'w=' + str(r['weight']), '|',
                  (r['prompt'] or '')[:40].replace('\n', ' '), '|', acts[:90])
