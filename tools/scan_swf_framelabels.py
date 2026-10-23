"""Scan ability_icons.swf Sprite 1346 FrameLabels -> map ability keys to frame numbers.
Minimal SWF tag walker (no external deps)."""
import io, sys, struct, zlib, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SWF = r'game_assets\swfs\ability_icons.swf'
TARGET_SPRITE = 1346

data = open(SWF, 'rb').read()
sig = data[:3]
ver = data[3]
file_len = struct.unpack_from('<I', data, 4)[0]
body = zlib.decompress(data[8:]) if sig == b'CWS' else data[8:]
print(f'{sig.decode()} swf{ver} body={len(body)}')

class BitReader:
    def __init__(self, b):
        self.b = b
        self.pos = 0  # bit position
    def read_ub(self, n):
        v = 0
        for _ in range(n):
            byte = self.b[self.pos >> 3]
            bit = (byte >> (7 - (self.pos & 7))) & 1
            v = (v << 1) | bit
            self.pos += 1
        return v
    def align(self):
        self.pos = (self.pos + 7) & ~7

def read_rect(b, off):
    nbits = (b[off] >> 3) & 0x1F
    br = BitReader(b[off:])
    br.read_ub(5)          # nbits 字段本身
    br.read_ub(nbits * 4)  # Xmin Xmax Ymin Ymax
    br.align()
    return off + (br.pos >> 3)

p = read_rect(body, 0)
p += 4  # frame rate (fixed8) + frame count (u16)

# walk top-level tags collecting DefineSprite bodies
sprites = {}
while p < len(body):
    code_len = struct.unpack_from('<H', body, p)[0]
    code = code_len >> 6
    length = code_len & 0x3F
    p += 2
    if length == 0x3F:
        length = struct.unpack_from('<I', body, p)[0]
        p += 4
    payload = body[p:p + length]
    p += length
    if code == 39:  # DefineSprite
        sid = struct.unpack_from('<H', payload, 0)[0]
        sprites[sid] = payload
    if code == 0 and length == 0:
        break

print(f'sprites found: {len(sprites)}; has {TARGET_SPRITE}: {TARGET_SPRITE in sprites}')

# walk DefineSprite sub-tags for FrameLabel (43)
payload = sprites[TARGET_SPRITE]
# DefineSprite: u16 id, u16 framecount, then tags
q = 4
labels = {}
while q < len(payload):
    code_len = struct.unpack_from('<H', payload, q)[0]
    code = code_len >> 6
    length = code_len & 0x3F
    q += 2
    if length == 0x3F:
        length = struct.unpack_from('<I', payload, q)[0]
        q += 4
    if code == 0 and length == 0:
        break
    if code == 43:  # FrameLabel
        raw = payload[q:q + length]
        s = raw.rstrip(b'\x00').decode('utf-8', errors='replace')
        labels[len(labels) + 1] = s  # frame number within sprite = order of FrameLabel tags
    q += length

print(f'FrameLabels in sprite {TARGET_SPRITE}: {len(labels)}')
labels_list = list(labels.items())
print('first 10:', labels_list[:10])

MOVE_KEYS = ['DefaultMove', 'BasicJump', 'Teleport', 'BasicDig', 'Shadowstep', 'SwapPositions',
             'SwimmerMove', 'TrampleMove', 'TrampleMoveOne', 'MaxTeleport', 'FloatMove']
ATTACK_KEYS = ['BasicMelee', 'BasicMelee_Fighter', 'BasicBigMelee', 'BasicRanged', 'BasicRanged_Hunter',
               'BasicRanged_1DMG', 'BasicShortRanged', 'BasicMagicShortRanged', 'BasicShortLobbed',
               'BasicStraightShot', 'BasicStraightShot_Thief', 'BasicMedicMelee', 'BasicMedicRanged',
               'BasicTankMelee', 'BasicMonkMelee', 'BasicMonkRanged', 'BasicButcherMelee', 'BasicButcherMeleeWide',
               'BasicButcherMeleeWideSpin', 'BasicButcherMeleeWideDoubleSpin', 'BasicDruidAbility',
               'BasicDruidAbilityVersatile', 'TinkererCraft', 'TinkererThrow', 'BasicPsychicPull',
               'BasicNecroRanged', 'BasicDrainMelee', 'BasicHook', 'BasicMagicMissile', 'BasicSuplex',
               'BasicTwoHitMelee', 'BasicPuke', 'BasicExplosiveShot', 'BasicPoke', 'GerdShot', 'BasicSpin',
               'BasicMetronome']

label_to_frame = {v: k for k, v in labels.items()}

def sprite_labels(payload):
    q = 4
    labels = {}
    while q < len(payload):
        code_len = struct.unpack_from('<H', payload, q)[0]
        code = code_len >> 6
        length = code_len & 0x3F
        q += 2
        if length == 0x3F:
            length = struct.unpack_from('<I', payload, q)[0]
            q += 4
        if code == 0 and length == 0:
            break
        if code == 43:
            s = payload[q:q + length].rstrip(b'\x00').decode('utf-8', errors='replace')
            labels[len(labels) + 1] = s
        q += length
    return labels

# 扫描所有 sprite，找包含移动技能标签的
print('\n=== 扫描全部 sprite 的移动技能标签 ===')
move_set = set(MOVE_KEYS)
for sid, payload in sorted(sprites.items()):
    labs = sprite_labels(payload)
    hit = [l for l in labs.values() if l in move_set]
    if hit:
        print(f'sprite {sid}: {len(labs)} labels, move hits: {hit}')
        json.dump(labs, open(f'tools/_labels_sprite{sid}.json', 'w'))

print('\n=== 移动键在 1346 中的存在情况 ===')
for k in MOVE_KEYS:
    print(f'MOVE {k:18s} frame={label_to_frame.get(k)}')
print()
missing_atk = [k for k in ATTACK_KEYS if k not in label_to_frame]
print('attack keys missing frame label:', missing_atk)

json.dump(labels, open('tools/_ability_frame_labels.json', 'w'))
print('labels saved to tools/_ability_frame_labels.json')
