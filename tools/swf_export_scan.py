"""解压 SWF 并提取导出符号名，定位 项圈/角标/稀有度 等UI矢量资源。"""
import zlib, re, struct, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def swf_tags(path):
    data = open(path, 'rb').read()
    sig = data[:3]
    if sig == b'CWS' or sig == b'ZWS':
        body = zlib.decompress(data[8:])
    elif sig == b'FWS':
        body = data[8:]
    else:
        raise ValueError('not swf')
    # skip rect + framerate
    p = 0
    nbits = body[0] >> 3
    rect_len = (5 + nbits * 4 + 7) // 8
    p += rect_len + 2
    tags = []
    while p + 2 <= len(body):
        code_len = struct.unpack_from('<H', body, p)[0]
        p += 2
        code = code_len >> 6
        length = code_len & 0x3F
        if length == 0x3F:
            length = struct.unpack_from('<I', body, p)[0]
            p += 4
        tags.append((code, body[p:p+length]))
        p += length
    return tags

TAG_EXPORT = 56   # ExportAssets
TAG_SYMBOLCLASS = 87

def exports(path):
    out = []
    for code, payload in swf_tags(path):
        if code == TAG_EXPORT:
            count = struct.unpack_from('<H', payload, 0)[0]
            p = 2
            for _ in range(count):
                cid = struct.unpack_from('<H', payload, p)[0]; p += 2
                end = payload.index(b'\x00', p)
                out.append(payload[p:end].decode('utf-8', errors='replace'))
                p = end + 1
    return out

base = 'game_assets/swfs'
for fn in ['ui.swf', 'catparts.swf', 'map.swf', 'house.swf']:
    p = os.path.join(base, fn)
    try:
        ex = exports(p)
    except Exception as e:
        print(fn, 'ERROR', e)
        continue
    print(f'=== {fn}: {len(ex)} exports')
    pat = re.compile(r'collar|mark|badge|rarity|rare|complete|check|star|stamp|trophy|class', re.I)
    hits = [e for e in ex if pat.search(e)]
    for h in hits[:40]:
        print('   ', h)
