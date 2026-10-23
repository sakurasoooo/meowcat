"""Find mutation-granting events, esp. mass-mutation ones (the forum's '微光' event)."""
import json, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ev = json.load(open('wiki_data/events_combined.json', encoding='utf-8'))
print(type(ev), list(ev.keys())[:5] if isinstance(ev, dict) else len(ev))
events = ev['events'] if isinstance(ev, dict) and 'events' in ev else ev
print('event sample keys:', list(events[0].keys()))

for e in events:
    name = e.get('event_name') or e.get('name') or e.get('id') or '?'
    disp = e.get('display_name') or e.get('name_en') or ''
    code = json.dumps(e, ensure_ascii=False)
    n = code.count('random_mutation')
    if n >= 2 or 'glimmer' in code.lower() or 'shimmer' in code.lower() or '微光' in code:
        print(f'--- {name} | {disp} | random_mutation x{n}')
        for m in re.findall(r'(?:party_)?random_mutation(?:_from_set)?[^\n]{0,80}', code)[:8]:
            print('    ', m.strip()[:110])
