import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')
from event_catalog import load_event_catalog, filter_events, lookup_name, _event_zh

evs = load_event_catalog()
print('total', len(evs), 'visible', len(filter_events(evs)))
print('Beepis', lookup_name('item', 'Beepis'), 'Neverstone', lookup_name('item', 'Neverstone'))

no_prompt = [e['key'] for e in evs if not e.get('hidden') and not (e.get('prompt') or e.get('prompt_alts') or e.get('options'))]
print('visible empty', no_prompt)

for key in ('Frank2', 'BloodStain', 'SealedCrypt', 'ExtraLife', 'Happening', 'Tragedy'):
    e = next(x for x in evs if x['key'] == key)
    print('====', e['key'], e['title'], 'opts', len(e.get('options') or []), 'alts', len(e.get('prompt_alts') or []))
    print(' prompt:', (e.get('prompt') or '')[:70].replace('\n', ' / '))
    if e.get('options'):
        o0 = e['options'][0]
        print('  label', o0['label'], 'outcomes', len(o0.get('outcomes') or []))
        if o0.get('outcomes'):
            print('  out0', (o0['outcomes'][0].get('prompt') or '')[:70].replace('\n', ' / '))

# overlay coverage: titles
miss_title = []
for e in evs:
    if e.get('hidden'):
        continue
    # titles come from overlay or wiki
    if not e.get('title'):
        miss_title.append(e['key'])
print('visible untitled', miss_title)

print('EVENT_FRANK2_QUES', _event_zh('EVENT_FRANK2_QUES')[:40].replace('\n', '/'))
print('search 毕皮斯', [e['key'] for e in filter_events(query='毕皮斯')])
print('search 一只新猫', [e['key'] for e in filter_events(query='一只新猫')])
print('search 浓雾开始弥漫', [e['key'] for e in filter_events(query='浓雾开始弥漫')])
