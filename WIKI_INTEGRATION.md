# Wiki 数据与游戏贴图整合指南 (Wiki & Texture Integration Guide)

本目录数据用于将 [Mewgenics Encyclopedia (mewcodex.github.io)](https://mewcodex.github.io/) 的图鉴数据与游戏贴图整合进 `MewgenicsCatEditor.py`。

---

## 1. 目录结构

```
meowcat/
├── game_assets/                  # resources.gpak 解包产物（1.6GB，已 gitignore）
│   ├── textures/                 #   53 张 PNG：地面/特效/噪点/调色板/鼠标光标
│   ├── swfs/                     #   115 个矢量资源包（ability_icons.swf、catparts.swf 等）
│   ├── data/                     #   227 个 GON 配置（abilities/passives/items/mutations/text 等）
│   └── game_textures.csv         #   贴图标签索引（category/尺寸/用途）
│
├── wiki_data/                    # wiki 爬取产物
│   ├── *.json                    #   15 个原始数据库 JSON（共 ~12.6MB）
│   ├── images/                   #   4092 张图标 PNG（已 gitignore，可重新爬取）
│   │   ├── AbilityIcon/<frame>.png
│   │   ├── PassiveIcon/<frame>.png
│   │   ├── CharacterPortrait/<sprite_id>/1.png
│   │   ├── FurnitureIcon/<sprite_id>/<frame>.png   # 多帧动画
│   │   ├── TrinketIcon|WeaponIcon|NeckItemIcon|FaceItemIcon|HeadItemIcon/<frame>.png
│   └── csv/                      #   打标签 CSV（utf-8-sig，Excel 可直接打开）
│       ├── items.csv             #   1134 件物品
│       ├── abilities.csv         #   2316 个主动技能（899 个带图标）
│       ├── passives.csv          #   511 个被动
│       ├── mutations.csv         #   760 个突变/先天缺陷
│       ├── characters.csv        #   719 个角色/敌人（带头像）
│       ├── furniture.csv         #   634 件家具（含多帧图标）
│       ├── events.csv            #   214 个事件
│       ├── weather.csv           #   59 种天气
│       ├── achievements.csv      #   成就/解锁表（quest → ref_code 关联 items/passives）
│       └── all_images.csv        #   4092 张贴图总索引
```

## 2. CSV 标签规范

所有 CSV 采用统一约定：

| 列名模式 | 含义 |
| :--- | :--- |
| `*_code` / `*_key` | 游戏内部标识符（与 `mewgenics_game_data.json`、存档中的 key 一致，**可作为编辑器联动的外键**） |
| `name_en` / `name_zh` | 英/中文名 |
| `desc_en` / `desc_zh` | 英/中文描述（升级版描述为 `desc_upgraded_*`） |
| `icon_url` | wiki 相对路径（`https://mewcodex.github.io/` + 该值） |
| `icon_local` | 本地路径（相对 `wiki_data/`，如 `images\PassiveIcon\191.png`） |
| `frame_number` / `frame` / `sprite_id` | 图标帧号 / 精灵图 ID |
| `stats` | JSON 字符串（如 `{"con": 1}`），用 `json.loads` 解析 |

### 图标 URL 规则（wiki 站根目录相对）

| 类别 | 规则 | 来源字段 |
| :--- | :--- | :--- |
| 被动 | `PassiveIcon/{frame_number}.png` | `passives_combined.json → frame_number` |
| 主动技能 | `AbilityIcon/{frame_number}.png` | `abilities_combined.json → frame_number` |
| 角色头像 | `CharacterPortrait/{sprite_id}/1.png`（单帧） | `characters_db.json → image_path` |
| 家具 | `FurnitureIcon/{sprite_id}/{frame}.png`（多帧，见 `image_frames`） | `furniture_db.json` |
| 物品 | `{kind}Icon/{frame}.png`，kind 映射：`trinket→Trinket, weapon→Weapon, neck→NeckItem, face→FaceItem, head→HeadItem` | `items_db.json → kind + frame` |
| 突变 | **wiki 无独立图标**（突变改变猫部位外观，矢量图在 `game_assets/swfs/catparts.swf`） | — |

## 3. 编辑器接入示例

```python
import csv, os
from PIL import Image, ImageTk
import customtkinter as ctk

WIKI_DIR = os.path.join(os.path.dirname(__file__), 'wiki_data')

def load_labeled_db(csv_name, key_col):
    """加载 wiki_data/csv/<csv_name>，返回 {key: row} 字典。"""
    path = os.path.join(WIKI_DIR, 'csv', csv_name)
    with open(path, encoding='utf-8-sig', newline='') as f:
        return {row[key_col]: row for row in csv.DictReader(f)}

passives_db = load_labeled_db('passives.csv', 'passive_code')
items_db    = load_labeled_db('items.csv', 'item_code')

def get_icon(row, size=(24, 24)):
    """按行的 icon_local 字段加载 PNG 为 CTkImage。"""
    rel = (row or {}).get('icon_local', '')
    full = os.path.join(WIKI_DIR, rel) if rel else ''
    if rel and os.path.exists(full):
        img = Image.open(full)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    return None

# 在技能/被动下拉框中显示图标 + 中文名 + 描述 tooltip：
row = passives_db.get('Putrefy')
icon = get_icon(row)
label = ctk.CTkLabel(parent, image=icon, text=f"{row['name_zh']} ({row['name_en']})")
# tooltip 文本 = row['desc_zh']
```

### 联动点建议（编辑器现有功能 ↔ wiki 数据）

| 编辑器模块 | 关联 CSV | 关联键 |
| :--- | :--- | :--- |
| 4 槽位主动技能下拉框 | `abilities.csv` | `ability_code` ↔ 存档技能 key |
| 被动/职业被动/失调面板 | `passives.csv` | `passive_code` ↔ `mewgenics_game_data.json` 的 passives |
| 突变面板（10 部位） | `mutations.csv` | `mutation_id` + `part` ↔ `MUTATION_SLOTS` |
| 家园资源 | `furniture.csv`、`items.csv` | 家具/物品图鉴浏览器（新 Tab） |
| 猫列表 | `characters.csv` | 敌人/NPC 图鉴（新 Tab） |

## 4. 重新生成

```bash
# 重新解包游戏资源（游戏更新后）
python tools/extract_gpak_assets.py
python tools/label_game_textures.py

# 重新爬取 wiki（增量：已存在的图片自动跳过）
python tools/crawl_wiki_assets.py
```

## 5. 注意事项

- ⚠️ wiki 为第三方粉丝站，数据仅供个人单机使用；图标版权归游戏作者 Edmund McMillen & Tyler Glaiel。
- ⚠️ `abilities.csv` 中 1417 个技能无 `frame_number`（wiki 未匹配到图标，多为升级变体/内部技能），`icon_local` 为空属正常。
- ⚠️ `game_assets/swfs/` 是矢量资源，如需从 SWF 导出位图，可用 FFDec (JPEXS) 或 swfextract；wiki 图标已覆盖常用需求，一般不必解析 SWF。
- ⚠️ CSV 为 `utf-8-sig` 编码，Python 读取时务必指定 `encoding='utf-8-sig'`。
