"""Extract area icons (map.swf sprite 1828) and move ability icons
(ability_icons.swf sprite 1346, by thematic frame), normalize into assets/. """
import io as _io, sys as _sys, os, subprocess, glob
_sys.stdout = _io.TextIOWrapper(_sys.stdout.buffer, encoding='utf-8')
from PIL import Image

JAVA = r'_extractor\jre\jdk-21.0.12.1+1-jre\bin\java.exe'
FFDEC = r'_extractor\ffdec\ffdec-cli.jar'

def ffdec_extract(sprite, frames, swf, tmp):
    os.makedirs(tmp, exist_ok=True)
    # frames: list of 1-based frame numbers
    rng = ','.join(str(f) for f in frames)
    subprocess.run([JAVA, '-jar', FFDEC, '-format', 'sprite:png', '-ignorebackground', '-zoom', '1',
                    '-selectid', str(sprite), '-select', f'{sprite}:{rng}', '-export', 'sprite', tmp, swf],
                   capture_output=True, timeout=180)
    # FFDec names files by frame number
    out = {}
    for p in glob.glob(os.path.join(tmp, '**', '*.png'), recursive=True):
        fn = os.path.basename(p)
        try:
            out[int(os.path.splitext(fn)[0])] = p
        except ValueError:
            pass
    return out

def norm(src, dest, target=64, pad=4):
    img = Image.open(src).convert('RGBA')
    bbox = img.getbbox()
    if not bbox:
        return False
    img = img.crop(bbox)
    inner = target - pad * 2
    s = min(inner / img.width, inner / img.height)
    img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
    canvas = Image.new('RGBA', (target, target), (0, 0, 0, 0))
    canvas.paste(img, ((target - img.width) // 2, (target - img.height) // 2), img)
    canvas.save(dest, 'PNG', optimize=True)
    return True

# ---- 区域图标 (sprite 1828, map.swf): 0-based frame +1 = FFDec 帧 ----
ZONES = {
    'caves': 4, 'boneyard': 5, 'moon': 9, 'core': 10, 'jurassic': 14,
    'theend': 16, 'meatworld': 17, 'dimensionx': 18, 'endoftime': 19,
}
tmp = r'tools\_swf_tmp\areas'
os.makedirs(r'assets\icons\areas', exist_ok=True)
got = ffdec_extract(1828, list(ZONES.values()), r'game_assets\swfs\map.swf', tmp)
for zone, f1 in ZONES.items():
    src = got.get(f1)
    if src and norm(src, os.path.join(r'assets\icons\areas', f'{zone}.png')):
        print(f'AREA {zone:12s} frame{f1} OK')
    else:
        print(f'AREA {zone:12s} frame{f1} MISSING')

# ---- 移动图标 (sprite 1346, ability_icons.swf): 0-based +1 = FFDec 帧 ----
MOVES = {
    'DefaultMove': 799, 'BasicJump': 148, 'Teleport': 235, 'BasicDig': 438,
    'Shadowstep': 190, 'SwapPositions': 205, 'TrampleMove': 123, 'TrampleMoveOne': 122,
    'MaxTeleport': 239, 'SwimmerMove': 629, 'FloatMove': 558,
}
tmp2 = r'tools\_swf_tmp\moves'
got2 = ffdec_extract(1346, list(MOVES.values()), r'game_assets\swfs\ability_icons.swf', tmp2)
for mv, f1 in MOVES.items():
    src = got2.get(f1)
    if src and norm(src, os.path.join(r'assets\icons\abilities', f'{mv}.png')):
        print(f'MOVE {mv:18s} frame{f1} OK')
    else:
        print(f'MOVE {mv:18s} frame{f1} MISSING')
