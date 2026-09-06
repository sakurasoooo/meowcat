"""职业主题色模块 —— 源自 game_assets/textures/palette.png 各职业调色板行采样。

调色板机制与采样分析详见 CLASS_THEMES.md。
深色（死灵/德鲁伊/灵能）自动提亮以保证暗色 UI 上的可读性。
"""

# palette.png 每职业行的槽 1(主色) 与槽 13(副色) 采样
CLASS_PALETTE = {
    'Colorless':   {'row': None, 'main': '#94a3b8', 'accent': '#c0c0c6'},
    'Fighter':     {'row': 54,   'main': '#b17373', 'accent': '#e88c8c'},
    'Hunter':      {'row': 50,   'main': '#425d3d', 'accent': '#9ccb8d'},
    'Mage':        {'row': 55,   'main': '#787899', 'accent': '#afafe6'},
    'Tank':        {'row': 51,   'main': '#857348', 'accent': '#d8d8d8'},
    'Medic':       {'row': 52,   'main': '#fdfdfd', 'accent': '#d8d8d8'},
    'Thief':       {'row': 53,   'main': '#fffbb5', 'accent': '#fffbb5'},
    'Tinkerer':    {'row': 63,   'main': '#b5eadc', 'accent': '#7cd6b5'},
    'Psychic':     {'row': 62,   'main': '#645379', 'accent': '#997dbb'},
    'Butcher':     {'row': 64,   'main': '#ac4457', 'accent': '#b6576b'},
    'Druid':       {'row': 65,   'main': '#5b4237', 'accent': '#a0c197'},
    'Monk':        {'row': 66,   'main': '#787878', 'accent': '#dcdcdc'},
    'Jester':      {'row': 67,   'main': '#b5eadc', 'accent': '#fffaff'},
    'Necromancer': {'row': 68,   'main': '#131313', 'accent': '#723b3c'},
}


def _hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb


def _luma(rgb):
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _lighten(rgb, target=120.0):
    """把暗色按比例提亮到目标亮度。"""
    cur = _luma(rgb)
    if cur >= target or cur <= 0:
        return rgb
    f = target / cur
    return tuple(min(255, int(c * f + 24)) for c in rgb) if f > 1 else rgb


def ui_color(cls):
    """返回适合暗色 UI 显示的职业色（自动选取主/副色中较亮者并提亮过暗色）。

    Colorless（通用技能）返回低调石板色，避免 2000+ 通用技能全是亮银色造成视觉噪音。
    """
    if not cls:
        return '#475569'
    p = CLASS_PALETTE.get(cls)
    if not p:
        return '#475569'
    if cls == 'Colorless':
        return '#566377'
    main = _hex_to_rgb(p['main'])
    accent = _hex_to_rgb(p['accent'])
    best = main if _luma(main) >= _luma(accent) else accent
    best = _lighten(best, 120.0)
    return _rgb_to_hex(best)
