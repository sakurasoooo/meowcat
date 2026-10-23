"""Check file size/alpha of ThouShaltNotKill + map missing passives to SWF labels (fuzzy)."""
import io, sys, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from PIL import Image

for k in ['ThouShaltNotKill', 'THOUSHALTNOTKILL', 'FightersSoul', 'FIGHTERSOUL', 'BULLSEYE']:
    p = os.path.join('assets/icons/passives', k + '.png')
    if os.path.exists(p):
        im = Image.open(p).convert('RGBA')
        bbox = im.getbbox()
        print(f'{k}: {os.path.getsize(p)}b size={im.size} bbox={bbox}')
    else:
        print(f'{k}: MISSING')

# 缺的43个 vs SWF 标签（模糊匹配：去撇号、大小写）
pas_cat = json.load(open('assets/passives_catalog.json', encoding='utf-8'))
missing = [e['key'] for e in pas_cat if not os.path.exists(os.path.join('assets/icons/passives', e['key'] + '.png'))]
# 用之前 scan 提取的 515 标签
import struct, zlib
class BR:
    def __init__(s, b): s.b=b; s.pos=0
    def ub(s, n):
        v=0
        for _ in range(n):
            byte=s.b[s.pos>>3]; bit=(byte>>(7-(s.pos&7)))&1; v=(v<<1)|bit; s.pos+=1
        return v
    def al(s): s.pos=(s.pos+7)&~7
def rr(b,o):
    n=(b[o]>>3)&0x1F; br=BR(b[o:]); br.ub(5); br.ub(n*4); br.al(); return o+(br.pos>>3)
def slabels(path, want):
    data=open(path,'rb').read(); body=zlib.decompress(data[8:]) if data[:3]==b'CWS' else data[8:]
    p=rr(body,0)+4; target=None
    while p<len(body):
        try: cl=struct.unpack_from('<H',body,p)[0]
        except struct.error: break
        c,l=cl>>6,cl&0x3F; p+=2
        if l==0x3F:
            if p+4>len(body): break
            l=struct.unpack_from('<I',body,p)[0]; p+=4
        pl=body[p:p+l]; p+=l
        if c==39:
            sd=struct.unpack_from('<H',pl,0)[0]
            if sd==want: target=pl
        if c==0 and l==0: break
    if target is None: return {}
    q=4; fr=0; lab={}
    while q<len(target):
        try: cl=struct.unpack_from('<H',target,q)[0]
        except struct.error: break
        c,l=cl>>6,cl&0x3F; q+=2
        if l==0x3F:
            if q+4>len(target): break
            l=struct.unpack_from('<I',target,q)[0]; q+=4
        if c==0 and l==0: break
        if c==1: fr+=1
        elif c==43: lab[fr]=target[q:q+l].rstrip(b'\x00').decode('utf-8','replace')
        q+=l
    return lab

p515 = slabels(r'game_assets\swfs\ability_icons.swf', 515)
p1346 = slabels(r'game_assets\swfs\ability_icons.swf', 1346)
def norm(s): return ''.join(c for c in s.lower() if c.isalnum())
p515n = {norm(v): (f, v) for f, v in p515.items()}
p1346n = {norm(v): (f, v) for f, v in p1346.items()}
print('\n== 缺失被动 → 可映射的 515 帧 ==')
for k in missing:
    nk = norm(k)
    hit = p515n.get(nk) or p1346n.get(nk)
    print(f'  {k:22s} -> {"515 #%d %s" % hit if hit else ("1346 #%d %s" % p1346n.get(nk) if p1346n.get(nk) else "NO MATCH")}')
