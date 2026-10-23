"""Decode custom-SWF big payloads (DefineBitsLossless-like atlases) to PNG."""
import zlib, struct, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from PIL import Image

def get_big_payloads(path, min_size=100000):
    data = open(path, 'rb').read()
    body = zlib.decompress(data[8:]) if data[:3] in (b'CWS', b'ZWS') else data[8:]
    p = 0
    nbits = body[0] >> 3
    p += (5 + nbits * 4 + 7) // 8 + 2
    out = []
    while p + 2 <= len(body):
        cl = struct.unpack_from('<H', body, p)[0]; p += 2
        code = cl >> 6; ln = cl & 0x3F
        if ln == 0x3F:
            ln = struct.unpack_from('<I', body, p)[0]; p += 4
        if ln >= min_size:
            out.append((code, body[p:p+ln]))
        p += ln
    return out

def try_lossless(payload, out_png):
    """尝试按 DefineBitsLossless2 (format 5) 解码: [u16 charid][u8 fmt][u16 w][u16 h][zlib ARGB]"""
    for off in (0, 1, 2, 4):  # 头部偏移可能因自定义格式微调
        try:
            cid = struct.unpack_from('<H', payload, off)[0]
            fmt = payload[off+2]
            w, h = struct.unpack_from('<HH', payload, off+3)
            if not (0 < w <= 8192 and 0 < h <= 8192):
                continue
            raw = zlib.decompress(payload[off+7:])
            need = w * h * 4
            if len(raw) < need:
                continue
            if fmt == 5:  # ARGB byte order per spec: actually BG? DefineBitsLossless2 = ARGB little endian -> bytes A,R,G,B? spec: packed as ARGB
                img = Image.frombytes('RGBA', (w, h), raw[:need], 'raw', 'BGRA')
            elif fmt == 3:  # indexed
                ncolors = payload[off+7]
                cmask = 4 - (ncolors % 4) if ncolorcolors % 4 else 0
                continue
            else:
                continue
            img.save(out_png)
            print(f'OK off={off}: charid={cid} fmt={fmt} {w}x{h} -> {out_png}')
            return True
        except Exception:
            continue
    return False

base = 'game_assets/swfs'
outdir = 'game_assets/extracted_atlas'
os.makedirs(outdir, exist_ok=True)
for fn in ['catparts.swf', 'ui.swf', 'map.swf', 'house.swf']:
    for i, (code, pl) in enumerate(get_big_payloads(os.path.join(base, fn))):
        out = os.path.join(outdir, f'{fn[:-4]}_{code}.png')
        if not try_lossless(pl, out):
            print(f'{fn} tag{code}: {len(pl)} bytes -- direct decode failed, saved raw')
            open(out + '.bin', 'wb').write(pl[:64])
