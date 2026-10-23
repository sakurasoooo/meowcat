"""Extract the mass-mutation event(s) and side-specific mutation target names."""
import json, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ev = json.load(open('wiki_data/events_combined.json', encoding='utf-8'))
events = ev['events']

for e in events:
    code = json.dumps(e, ensure_ascii=False)
    if 'count 10' in code or 'count 15' in code:
        print('=== event:', e.get('event_key'), '|', e.get('title_texts'))
        # show mutation blocks with context
        for m in re.finditer(r'random_mutation[^}]{0,200}', code):
            print('   ...', m.group(0).replace('\\n', ' | ')[:180])
        print()

# also collect side-specific target names used in random_mutation_from_set across all events
targets = set()
for e in events:
    code = json.dumps(e, ensure_ascii=False)
    for m in re.finditer(r'random_mutation_from_set\s*\{([^}]*)\}', code):
        for t in re.findall(r'([a-z]+\d?)\s+-?\d+', m.group(1)):
            targets.add(t)
print('mutation target names seen in events:', sorted(targets))
