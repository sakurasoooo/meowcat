---
name: mewgenics-asset-extractor
description: >-
  提取、解码与标准化处理《Mewgenics》游戏资产（法术技能、被动特性、疾病缺陷、猫咪身体部位与突变手绘外观），
  涵盖 GPak 解包、SWF 矢量元件逆向分析、FFDec 定向高速批处理、透明外边距智能裁切、多语言目录构建以及 PyInstaller 单文件打包。
---

# Mewgenics 游戏资产与贴图提取流水线 (Asset Extraction Runbook)

本 Skill 沉淀了从《Mewgenics》底层游戏资源文件（`resources.gpak` 及 Flash SWF 矢量包）中高效、无损提取全部法术、被动、疾病与基因突变手绘外观的完整工业化流水线。

---

## 🛠️ 核心环境与前置工具

| 工具组件 | 路径 / 配置 | 用途说明 |
|:---|:---|:---|
| **OpenJDK JRE 21** | `_extractor/jre/jdk-21.0.12.1+1-jre/bin/java.exe` | 免安装便携式 Java 运行时 |
| **FFDec CLI** | `_extractor/ffdec/ffdec-cli.jar` | JPEXS Flash Decompiler 命令行工具 |
| **Python + Pillow** | `python` (需已安装 `Pillow` 库) | 图像 Alpha 边界裁切与居中合成 |
| **GPak 解包器** | `tools/extract_gpak_assets.py` | 从游戏 `resources.gpak` 解包 SWF 与数据 |

---

## 🚀 核心提取流水线

```text
resources.gpak ──(LZ4解包)──▶ swfs/*.swf ──(SWF标签解析)──▶ 定位 DefineSprite & chid
                                                                  │
                                                                  ▼ (FFDec -selectid 定向导出)
标准规范透明 PNG ◀──(Pillow getbbox/Lanczos)── 临时 raw PNG 帧 ◀───┘
       │
       ▼ (关联 terms.json / .gon)
富文本 JSON 字典 (abilities/passives/disorders_catalog.json) ──▶ 单文件 EXE 打包 (assets/)
```

---

## 📖 阶段一：SWF 元件定位与 ID 映射规律

### 1. 法术技能与被动特性 (`swfs/ability_icons.swf`)
- **Sprite 1346**（841 帧）：**主动法术与普攻/移动技能**。每一帧的 `FrameLabel` 即为技能代码（如 `Reach`, `Dash`, `Fireball`）。
- **Sprite 515**（514 帧）：**被动特性与疾病缺陷**。每一帧的 `FrameLabel` 即为被动/疾病代号（如 `Adrenaline`, `Rabies`, `Depression`）。

### 2. 猫咪身体部位与基因突变 (`catparts.swf`)
- **核心规律：SWF 帧编号 (Frame) == 突变数据 ID (Mutation ID)**！
  例如：`head.gon` 中 ID 300（方头 Square head）精确对应 `CatHead` 的第 300 帧。
- **各部位元件字符 ID (chid) 对照表**：
  - **头部 (Head)**：`chid: 7132` (`CatHead`，1700 帧，突变 76 项)
  - **耳朵 (Ears)**：`chid: 8051` (`CatEar`，1505 帧，突变 98 项)
  - **尾巴 (Tail)**：`chid: 10982` (`CatTail`，1560 帧，突变 95 项)
  - **身体 (Body)**：`chid: 8845` (`CatBody`，1200 帧，突变 77 项)
  - **腿部 (Legs)**：`chid: 9925` (`CatLeg`，1505 帧，突变 100 项)
  - **眼睛 (Eyes)**：`chid: 5949` (`CatEye`，1088 帧，突变 102 项)
  - **嘴巴 (Mouth)**：`chid: 5947` (`CatMouth`，1502 帧，突变 85 项)
  - **眉毛 (Eyebrows)**：`chid: 5519` (`CatEyebrow`，1070 帧，突变 60 项)
  - **花纹 (Texture)**：`chid: 2674` (`CatTexture`，2800 帧，突变 61 项)
  - **普通原版外观 (Pure)**：各部位基准帧为第 `100` 帧（花纹为第 `246` 帧）。

---

## ⚡ 阶段二：FFDec 极速定向提取指令 (避坑必读)

> [!CAUTION]
> **严禁缺少 `-selectid` 参数！**
> 若仅传入 `-select <range>` 而省略 `-selectid <chid>`，FFDec 将触发全库遍历，尝试导出 `catparts.swf` 中全部 15,000+ 个矢量元件，导致程序假死与磁盘耗尽。
> **务必同时指定两者：`-selectid <chid> -select <chid>:<ranges>`**！

### 1. 提取指令模板
```bash
<java.exe> -jar <ffdec-cli.jar> \
  -format sprite:png \
  -ignorebackground \
  -zoom 2 \
  -selectid <chid> \
  -select <chid>:<连续区间如100,300-321,400-441> \
  -export sprite "<临时输出目录>" \
  "<swf路径>"
```

### 2. 连续区间聚合函数 (Python)
为避免超出 Windows 命令行长度限制，导出前先将无序 ID 列表压缩为连续区间：
```python
def group_into_ranges(ids):
    if not ids: return ""
    sorted_ids = sorted(list(set(ids)))
    ranges = []
    s = e = sorted_ids[0]
    for n in sorted_ids[1:]:
        if n == e + 1:
            e = n
        else:
            ranges.append(f"{s}-{e}" if s != e else f"{s}")
            s = e = n
    ranges.append(f"{s}-{e}" if s != e else f"{s}")
    return ",".join(ranges)
```

---

## 🖼️ 阶段三：图像规范化与居中合成 (Pillow)

SWF 导出的原始 PNG 画布极大（约 969x981），猫咪肢体居中偏小且周围环绕大量透明填充。必须进行 Alpha 边界裁切与居中等比缩放：

```python
from PIL import Image

def normalize_icon(src_png, dest_png, target_size=(72, 72), padding=6):
    with Image.open(src_png) as img:
        img = img.convert('RGBA')
        bbox = img.getbbox()  # 探测非透明内容边界
        if not bbox:
            return False
        cropped = img.crop(bbox)
        
        # 等比例居中缩放
        inner_w = target_size[0] - padding * 2
        inner_h = target_size[1] - padding * 2
        scale = min(inner_w / cropped.width, inner_h / cropped.height)
        new_w = max(1, int(cropped.width * scale))
        new_h = max(1, int(cropped.height * scale))
        resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # 居中粘贴到标准透明画布
        canvas = Image.new('RGBA', target_size, (0, 0, 0, 0))
        px = (target_size[0] - new_w) // 2
        py = (target_size[1] - new_h) // 2
        canvas.paste(resized, (px, py), resized)
        canvas.save(dest_png, 'PNG', optimize=True)
        return True
```

---

## 📚 阶段四：官方汉化与富文本机制关联

1. **官方术语表**：读取游戏目录下的 `terms.json`；
2. **键名映射规则**：
   - 法术：`ABILITY_<KEY>_NAME` / `ABILITY_<KEY>_DESC`
   - 被动：`PASSIVE_<KEY>_NAME` / `PASSIVE_<KEY>_DESC`
   - 疾病：`DISORDER_<KEY>_NAME` / `DISORDER_<KEY>_DESC`
3. **清洗富文本标记**：
   ```python
   tag_map = {
       '[img:shield]': '【护盾】',
       '[img:damage]': '【伤害】',
       '[img:mana]': '【魔能】',
       '[img:str]': '【力量】',
       '[img:dex]': '【敏捷】',
       '[img:con]': '【体质】',
       '[img:int]': '【智力】',
       '[img:spd]': '【速度】',
       '[img:cha]': '【魅力】',
       '[img:lck]': '【运气】',
   }
   ```
4. **输出标准 JSON 目录**：
   - `assets/abilities_catalog.json`
   - `assets/passives_catalog.json`
   - `assets/disorders_catalog.json`

---

## 📦 阶段五：PyInstaller 单文件无缝打包

在 `MewgenicsCatEditor.spec` 中统一配置：
```python
datas = [
    ('mewgenics_game_data.json', '.'),
    ('wiki_data/csv', 'wiki_data/csv'),
    ('assets', 'assets'),  # 包含 icons/ 与 catalog.json
]
hiddenimports = [
    'lz4.block', 'sqlite3', 'mewgenics_core', 'tooltip_manager',
    'picker_dialog', 'skill_card_widget', 'mutation_picker', 'PIL', 'PIL.Image'
]
```
使用 `python -m PyInstaller MewgenicsCatEditor.spec --noconfirm --clean` 进行编译，产出免安装可执行程序。
