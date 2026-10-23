"""Rename UPPERCASE icon files to game (PascalCase) codes; delete wrong-art/misnamed ones."""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DEST = 'assets/icons/passives'
RENAME = {
    'JAGGEDEDGE': 'JaggedEdges', 'FRENZY': 'BloodFrenzy', 'EMPTYVESSEL': 'EmptyVessels',
    'PROTECTIVE': 'ProtectiveAura', 'SWIFTLOOTER': 'Looter', 'IRONSKINTECHNIQUE': 'IronSkin',
    'STARTER_PLACEHOLDER': 'STARTER_PLACEHOLDER_Fighter', 'SYNTHESIZE': 'Synthesize',
}
# *SOUL 直接用游戏原名文件（若有），删除大写拷贝
DELETE_OR_SKIP = ['FIGHTERSOUL', 'HUNTERSOUL', 'MAGESOUL', 'CLERICSOUL', 'TANKSOUL', 'THIEFSOUL',
                  'MONKSOUL', 'BUTCHERSOUL', 'DRUIDSOUL', 'TINKERERSOUL', 'NECROMANCERSOUL',
                  'PSYCHICSOUL', 'SOULBOND']

for old, new in RENAME.items():
    oldp, newp = os.path.join(DEST, old + '.png'), os.path.join(DEST, new + '.png')
    if os.path.exists(oldp):
        if os.path.exists(newp):
            os.remove(oldp)
            print(f'{old}.png 删除（已有 {new}.png）')
        else:
            os.rename(oldp, newp)
            print(f'{old}.png -> {new}.png')
    else:
        print(f'{old}.png 不存在')

for key in DELETE_OR_SKIP:
    p = os.path.join(DEST, key + '.png')
    if os.path.exists(p):
        os.remove(p)
        print(f'{key}.png 删除')
