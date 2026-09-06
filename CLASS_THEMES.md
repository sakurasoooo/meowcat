# 职业主题色与 UI 贴图提取对照 (Class Themes & UI Asset Map)

> **编辑器应用**：技能选择器网格卡片描边、技能卡（`SkillCardWidget`）名称与边框、选择器职业分类按钮文字，均按所属职业主题色显示（`class_theme.py`，暗色下自动提亮）。

> 数据来源：`resources.gpak` 解包 → `game_assets/`（调色板 + SWF 矢量件）。
> 提取工具：FFDec CLI（`_extractor/ffdec/ffdec-cli.jar`），Skill 参见 `.agents/skills/mewgenics-asset-extractor`。

---

## 1. 职业主题色（项圈配色）

### 机制
- 每个职业在 `data/classes/*.gon` 的 `graphics.palette <N>` 声明一个**调色板行号**。
- 主调色板 `textures/palette.png`（16 色 × 256 行）中对应行的配色会**染色该职业的项圈/服装贴图**。
- 槽位布局（行内 16 色）：

| 槽位 | 用途 |
|---|---|
| 0 | 描边黑 |
| 1-2 | **主题主色** |
| 3-4 | 主色暗部（衣褶） |
| 5-6 | 主色更暗部 |
| 7-8 | 共享奶油色 |
| 9-12 | 共享粉色（鼻头/肉垫/舌头） |
| 13-14 | **职业副色/亮色** |
| 15 | 白 |

### 14 职业主题色表

| 职业 | 官方名 | 调色板行 | 主色 | 暗部 | 副色 | 主题印象 |
|---|---|---|---|---|---|---|
| Colorless | 无项圈 | — | （不染色，自然毛色） | — | — | 银色基础狗牌 |
| Fighter | 战士 | 54 | `#b17373` | `#8d5959` | `#e88c8c` | 红棕拳套 |
| Hunter | 猎人 | 50 | `#425d3d` | `#2f432b` | `#9ccb8d` | 军绿猎装 |
| Mage | 法师 | 55 | `#787899` | `#cac8da` | `#afafe6` | 蓝紫星袍 |
| Tank | 坦克 | 51 | `#857348` | `#53472b` | `#d8d8d8` | 棕金重甲 |
| Medic | 牧师 | 52 | `#fdfdfd` | `#f2efef` | `#d8d8d8` | 纯白牧袍 |
| Thief | 盗贼 | 53 | `#fffbb5` | `#d8d5a0` | `#fffbb5` | 淡黄金币 |
| Tinkerer | 工匠 | 63 | `#b5eadc` | `#79ceb7` | `#7cd6b5` | 薄荷工装 |
| Psychic | 灵能者 | 62 | `#645379` | `#40354e` | `#997dbb` | 暗紫法眼 |
| Butcher | 屠夫 | 64 | `#ac4457` | `#7c2f3c` | `#b6576b` | 血红围裙 |
| Druid | 德鲁伊 | 65 | `#5b4237` | `#3a2922` | `#a0c197` | 棕皮绿叶 |
| Monk | 武僧 | 66 | `#787878` | `#a2a2a2` | `#dcdcdc` | 灰色僧袍 |
| Jester | 小丑 | 67 | `#b5eadc` | `#79ceb7` | `#fffaff` | 彩色骰帽 |
| Necromancer | 死灵法师 | 68 | `#131313` | `#212121` | `#723b3c` | 漆黑棺材 |

> 采样脚本：调色板行 `y` 的槽 1/3/5/13（见上表列）。示例 `Fighter`：`palette.png` 像素 (1,54)。

---

## 2. 已提取贴图对照

### 2.1 职业项圈（`ui.swf`）
- **图标整版**：sprite **chid 753**（帧 1-17 = 17 枚项圈狗牌：银爪=无项圈、红爪=战士、金色军牌=坦克、绿盾箭=猎人、黄骨$=盗贼、蓝紫星=法师、白心=牧师、紫法眼=灵能者、骰帽=小丑、锤扳手=工匠、红肉骨=屠夫、棕叶=德鲁伊、太极=武僧、黑棺材=死灵法师；另有黑爪/灰圈等锁定态）
- 存放：`game_assets/extracted/collars_frames/`（单帧）与 `class753_sheet.png`（对照表）
- 相关：`chid 3631` = 背包 UI 羊皮纸底；`chid 3757` = 背包/仓库/回收站界面（帧标签 `backpack`/`storage`/`trash`/`collars`）

### 2.2 通关角标（`ui.swf` sprite **chid 3521**）
对应 `chapter_id_enum.gon` 的 `major_class_checkmarks` 9 章节（每章一帧图案 + 帧区间内的 ✘/✔/★ 状态件）：

| 帧 | 图案 | 章节 |
|---|---|---|
| 1 | 🕷️ 蜘蛛 | caves 洞穴 |
| 2 | 🦇 蝙蝠 | boneyard 白骨墓园 |
| 3 | ⭐ 五芒星 | core 地核 |
| 4 | 🌙 月亮 | moon 月球 |
| 5 | 🦖 恐龙 | jurassic 侏罗纪 |
| 6 | 💀 骷髅 | theend 终点 |
| 7 | 🥩 肉块 | meatworld 搏动领域 |
| 8 | 💜 裂隙水晶 | dimensionx 裂隙 |
| 9 | ♾️ 无限 | endoftime 无限界 |
| 10 | 空卡 | incomplete 未完成 |
| 11-40 | ✘/✔/★ | 状态叠件 |

- 存放：`game_assets/extracted/completion_marks/` + `marks_sheet.png`

### 2.3 道具稀有度框（`catparts.swf` sprite **chid 17**）
帧标签即稀有度（Frame → 名称严格对应）：

| 帧 | FrameLabel | 稀有度 | 视觉 |
|---|---|---|---|
| 1 | common | 普通 | 无边框 |
| 2 | consumable_common | 耗材·普通 | 无边框 |
| 3 | uncommon | 优秀 | 灰色圆 |
| 4 | consumable_uncommon | 耗材·优秀 | 灰色圆 |
| 5 | rare | 稀有 | 橄榄绿三角 |
| 6 | consumable_rare | 耗材·稀有 | 橄榄绿三角 |
| 7 | very_rare | 极稀有 | 红色菱形 |
| 8 | consumable_very_rare | 耗材·极稀有 | 红色菱形 |
| 9 | unique | 专属 | — |
| 10 | quest | 任务 | 绿色方 |
| 11 | sidequest | 支线 | 紫色方 |
| 12 | unknown | 未知 | — |
| 13 | cursed | 被诅咒 | 暗紫墨渍 |
| 14 | questcursed | 任务·诅咒 | 绿墨渍 |
| 15 | sidequestcursed | 支线·诅咒 | 紫墨渍 |

- 存放：`game_assets/extracted/rarity_frames/` + `rarity_sheet.png`
- 同 sprite 还有装备槽位帧标签：`weapon/head/neck/face/trinket/consumable`

---

## 3. 复现提取命令（FFDec 定向导出）

> ⚠️ **必须 `-selectid <chid>` 与 `-select <chid>:<frames>` 同时给出**，否则全库遍历假死。

```bash
# 通关角标
java -jar _extractor/ffdec/ffdec-cli.jar -format sprite:png -ignorebackground -zoom 2 ^
  -selectid 3521 -select 3521:1-40 -export sprite _extract_assets\marks game_assets\swfs\ui.swf

# 职业项圈
java -jar _extractor/ffdec/ffdec-cli.jar -format sprite:png -ignorebackground -zoom 1 ^
  -selectid 753 -select 753:1-75 -export sprite _extract_assets\class753 game_assets\swfs\ui.swf

# 稀有度框
java -jar _extractor/ffdec/ffdec-cli.jar -format sprite:png -ignorebackground -zoom 2 ^
  -selectid 17 -select 17:1-25 -export sprite _extract_assets\rarity game_assets\swfs\catparts.swf
```

辅助脚本：
- `tools/swf_export_scan.py` — SWF 标签/导出名扫描
- `tools/list_sprite_labels.py <chid>` — 列出指定 sprite 的 FrameLabel
- `tools/find_label_sprites.py` — 从 ffdec dump 定位 FrameLabel 所属 sprite（先 `-dumpSWF` 输出到 `_dump_ui.txt`）
- `tools/decode_swf_atlas.py` — 直接解码 SWF 内 DefineBitsLossless2 图集
