"""Hunt the achievement-style area badge icons: search swf sprite exports + frame labels + png."""
import io, sys, os, re, struct, zlib, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 1. 所有 swf 的导出名里找 achievement/checkmark/badge/medal/area 图标
SYM_PAT = re.compile(r'(achievement|checkmark|badge|medal|areaicon|areabadge|clearbadge|AchIcon|FeatIcon|ChapterIcon)', re.I)
for swf in glob.glob(r'game_assets\swfs\*.swf'):
    data = open(swf, 'rb').read()
    body = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
    hits = set()
    for m in re.finditer(rb'[\x20-\x7e]{3,55}', body):
        s = m.group().decode()
        if SYM_PAT.search(s) and not s.startswith('.?A'):
            hits.add(s)
    if hits:
        print(f'=== {os.path.basename(swf)} ===')
        for h in sorted(hits):
            print('   ', h)

# 2. 纹理目录里找 achievement badge png
print()
for p in glob.glob(r'game_assets\textures\**\*.png', recursive=True):
    if re.search(r'(achieve|badge|medal|checkmark|area_|chapter)', os.path.basename(p), re.I):
        print('TEX:', p)
for p in glob.glob(r'game_assets\data\**\*.gon', recursive=True):
    t = open(p, encoding='utf-8', errors='replace').read()
    if re.search(r'(achievement|ach_icon|badge_icon|medal)', t, re.I):
        for m in list(re.finditer(r'^[ \t]*[A-Za-z_]*[Bb]adge[A-Za-z_]*[^\n]*', t, re.M))[:3]:
            print('GON:', p.replace('game_assets\\',''), '|', m.group(0).strip()[:80])
