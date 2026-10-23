"""Find achievement badge source: gon icon refs + swf achievement sprites."""
import io, sys, os, re, struct, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 1. gon files with achievement + icon
for dp, _, fs in os.walk(r'game_assets\data'):
    for fn in fs:
        if 'achieve' in fn.lower() and fn.endswith('.gon'):
            p = os.path.join(dp, fn)
            print('GON:', p)
            t = open(p, encoding='utf-8', errors='replace').read()
            for m in list(re.finditer(r'^[ \t]*([A-Za-z_]*icon[A-Za-z_]*|frame|sprite)[^\n]*', t, re.M))[:12]:
                print('   ', m.group(0).strip()[:80])

# 2. swf strings for achievement icon sprites
for swf in ['ui.swf', 'map.swf']:
    data = open(r'game_assets\swfs' + '\\' + swf, 'rb').read()
    body = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
    hits = set()
    for m in re.finditer(rb'[\x20-\x7e]{3,60}', body):
        s = m.group().decode()
        if re.search(r'(achievement|AchIcon|checkmark|Accomplishment|Feat)', s, re.I) and not s.startswith('.?A'):
            hits.add(s)
    print(f'=== {swf}: {len(hits)}')
    for h in sorted(hits):
        print('  ', h)
