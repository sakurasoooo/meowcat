# 猫咪存档二进制格式与写回约定

本文是编辑器写 `cats` 表时的权威说明。旧文档 `Mewgenics_Reverse_Engineering_Reference.md` 第四节把技能段写成「连续 16 个字符串」，**不完整且会写坏存档**。实现见 `mewgenics_core.py` 的 `CatRecord.parse` / `build_bytes`。

对照样本：675 只猫（`steamcampaign01.sav`，2026-09-07 备份）逐字节往返 675/675。闪退样本：`#778` 罗德莉卡。

---

## 1. 这次闪退怎么来的

游戏崩溃日志：`error: out of bounds`（`crash_2026-09-07-01-23-48.txt` 等）。

**不是**道具名非法（`TinksBow` / 蝴蝶结是正常 Tink 礼物）。**也不是** `#778` 的 Brave / Invincible 疾病 key 无效。根因是编辑器把一只猫**整段重写**时丢掉了字符串之间的间隔字节。

### 1.1 全表重写

早期「保存所有更改」即使只改仓库，也会对 **675 只猫** 各跑一遍 `build_bytes()`。旧实现不是逐字节往返，未改过的猫也被写成另一种布局，读档即炸。

现行规则：`MewgenicsSaveManager.save()` **只写脏块**。猫咪仅当 `cat.is_modified` 才重写。无脏数据则跳过备份和写盘。

### 1.2 固定 16 串 + 硬编码间隔

旧 `build_bytes` 假定每只猫恰好 16 个 ASCII 串，并且：

- 职业被动 / 疾病后面的等级一律写成 `int32 = 1`
- 第二疾病之后只写 **4** 组空装备槽 `05 00 00 00 00`（20 字节）
- **丢掉**帽子、瓶子、寄生虫等已装备物品串
- 性向 `double` 每次都改写成 `0.0 / 0.25 / 0.45`

真实文件里：

- 656/675 只猫是 16 串（无装备）
- 19 只猫是 17–21 串：第 16 串起、职业名之前是装备物品
- 无装备时，第二疾病后的间隔是 **29 字节** = `rank(4)` + **5** 组空槽（25 字节），不是 4 组
- 有装备时，空槽组数变少，物品串夹在疾病和职业之间，每件后面跟 26–46 字节元数据
- 等级不总是 1（存档里见过 `2`）

`#778` 把疾病从 `Anemia`(6) + `None`(4) 改成 `Brave`(5) + `Invincible`(10)（净多 5 字节），旧写入少了第 5 个空槽标记（正好 5 字节），总长仍是 934，游戏把 `Colorless` 当成第 5 件装备解析 → `out of bounds`。

修好后正确长度是 **939**（原 934 + 5 个字符，29 字节间隔保留）。

### 1.3 写回铁律

1. **解析时记下每两个字符串之间的原始间隔**（`str_gaps`），写回时原样接在新字符串后面。
2. **职业名永远是最后一串**。疾病 #2 与职业之间的串是装备，必须进 `extra_strings`，不得丢。
3. **不要**用「16 串 + 固定 rank + 20 字节标志」重建。
4. 性向只在用户改了下拉框时才改 `tail_data[+4]` 的 `double`；否则保留原始 8 字节。
5. 只写 `is_modified` 的猫。未改字段保持原 blob。
6. 改完后应用 675 只对照完好备份做一次 `parse → build_bytes == raw`。

---

## 2. 存档容器

路径：

```
%APPDATA%\Glaiel Games\Mewgenics\<SteamID64>\saves\steamcampaign01.sav
```

SQLite 3 STRICT。`cats` 表：`key INTEGER PRIMARY KEY`（猫咪编号，如 778），`data BLOB`：

```
[uint32 little-endian uncompressed_size] [LZ4 block, store_size=False]
```

解压得到 `raw_cat_data`。下文偏移均相对这块未压缩字节。全文件小端。

---

## 3. 头、名字、外观、声音、属性

| 偏移 | 类型 | 含义 |
| --- | --- | --- |
| `+0x00` | `u32` | 版本。样本里为 `19` |
| `+0x04` | `u64` | GUID |
| `+0x0C` | `u64` | 名字**字符数**（不是字节数） |
| `+0x14` | UTF-16LE | 名字。字节数 = 字符数 × 2 |

名字之后到 voice 长度前缀之前，整段称为 `pre_voice_body`：

```
[u64 title_len][ascii title][u32 post_title]
[parts_chunk … 约 368 字节外观]
```

`parts_chunk` 内突变 id 相对该块的偏移（`MUTATION_SLOTS`）：

| 部位 | 左 `i32` | 右 `i32`（成对部位） |
| --- | --- | --- |
| texture | 92 | — |
| body | 104 | — |
| head | 124 | — |
| tail | 144 | — |
| legs | 164 | 184 |
| arms | 204 | 224 |
| eyes | 244 | 264 |
| eyebrows | 284 | 304 |
| ears | 324 | 344 |
| mouth | 364 | — |

约定：`< 300` 基础外观，`>= 300` 突变，`-2` 部位缺失。成对部位左右可不同（局内 asymmetric）。其它色盘/旋转字节未建模，随 `pre_voice_body` 原样保存。

voice 用正则在整包里定位（`male\d+|female\d+|robotom|spidercat|demoncat|robotcat`），其前 8 字节是 `u64` 长度：

```
[u64 voice_len][ascii voice][f64 pitch][i32 base×7][i32 bonus×7]
```

属性顺序：`str dex con int spd cha lck`。实效 = base + 15 个物理部件突变加成 + bonus。

base/bonus 之后、第一串（boon）之前通常是 **28 字节** `mid_flags`（多为 0）。必须原样写回。

---

## 4. 技能 / 被动 / 装备 / 职业串

ASCII 串格式：`[u64 字节长度][ascii]`。长度只计字符，不含前缀。空槽写 `"None"`（boon 常见 `"none"`）。

**不能**当成 16 个紧挨着的串来读。职业被动、疾病后面有 `i32` 等级；装备前后有槽位标记和物品元数据。编辑器做法：从属性后线性扫描「像字符串的 `[u64][可打印 ASCII]`」，再保存相邻两串之间的原始字节为 `str_gaps[i]`。

标准顺序（下标从 0）：

| 下标 | 字段 | 后面常见间隔 |
| --- | --- | --- |
| 0 | boon | 14 字节（`post_boon_flags`，常以 `ffffff3f` 开头） |
| 1 | move | 空 |
| 2 | attack | 空 |
| 3–6 | 主动技能 ×4 | 空 |
| 7–10 | 先天/升级基因 ×4（与 4 个主动槽对齐） | 空 |
| 11–12 | 职业被动 ×2 | `i32` 等级（多为 1，见过 2） |
| 13–14 | 疾病 ×2 | `i32` 等级 |
| 15 … n-2 | **装备物品**（0 或多件） | 每件后 26–46 字节元数据 |
| 最后 | 职业名 | 之后是 `tail_data` |

无装备时共 16 串，下标 15 就是职业。有装备时 17–21 串。样本分布：16 串 656 只，17 串 13 只，18/19/21 各 1 只，20 串 3 只。

### 4.1 空装备槽标记

第二疾病的等级之后、下一串之前，是「还没被物品占掉的空槽」。无装备时完整形态：

```
01 00 00 00                         # 第二疾病等级
05 00 00 00 00                      # 空槽 ×5
05 00 00 00 00
05 00 00 00 00
05 00 00 00 00
05 00 00 00 00
```

共 29 字节。656 只无装备猫都是这 29 字节。有装备时前面的 `05 00 00 00 00` 会被物品串 + 元数据替换，剩余空槽变少；最后一组有时以 `…01` 结尾而不是 `…00`。

**少写一组空槽，游戏就会把职业名当成装备读，然后 out of bounds。**

### 4.2 装备串示例

`#4 Baba`（17 串）：疾病后只剩 14 字节间隔，然后是 `Callus` + 41 字节，最后 `Mage`。

`#68 Parchita`（21 串）：`LeatherHat` / `WhiteBelt` / `WaterFeeder` / `Kebab` / `BallOfBandages`，再 `Tank`。

编辑器目前不改装备，只原样保存 `extra_strings` + 对应 `str_gaps`。

---

## 5. 尾块与性向

最后一串（职业）之后整段是 `tail_data`（`#778` 为 115 字节）。已解码部分：

| 相对 tail | 类型 | 含义 |
| --- | --- | --- |
| `+0` | `u32` | 常见 0 |
| `+4` | `f64` | 性向。`≤0.05` 异性恋，`<0.33` 双性恋，否则同性恋 |
| `+12` | … | 未建模，原样保留 |

游戏里的真实值往往不是 0 / 0.25 / 0.45（`#778` 原值 `04 80 cc 22 0e 83 c2 3f`）。用户没改性向时禁止覆盖这 8 字节。

---

## 6. 写回算法（现行）

```
u32 version
u64 guid
u64 name_chars + UTF-16LE name
pre_voice_body                    # 含 title + parts
u64 voice_len + ascii voice
f64 pitch
i32[7] base + i32[7] bonus
mid_flags
for i, s in skill_string_list():  # 15 固定槽 + extra_strings + class
    u64 len(s) + ascii s
    if i < last:
        str_gaps[i] 或（仅无 gaps 时）fallback
if sexuality 被用户改过:
    pack f64 into tail_data[+4]
tail_data
```

`_fallback_gap_after` 只在没有解析过的对象上用：被动/疾病后写 `rank=1`，第二疾病后再写 5 个空槽。正常读档路径必须走 `str_gaps`。

LZ4 再包一层：`u32(len(raw)) + lz4.block.compress(raw, store_size=False)`，`INSERT OR REPLACE INTO cats`。

---

## 7. `#778` 罗德莉卡对照

| | 原始完好 | 旧编辑器写坏 | 修复后 |
| --- | --- | --- | --- |
| raw 长度 | 934 | 934 | 939 |
| 疾病 | Anemia, None | Brave, Invincible | Brave, Invincible |
| 属性 | 7,5,7,7,7,7,7 | 全 7 | 全 7 |
| 疾病后间隔 | 29 字节（5 空槽） | 24 字节（4 空槽） | 29 字节 |
| 性向 8 字节 | 原始 `…c23f` | 被改成 `0.25` | 恢复原始 |
| 游戏 | 可读 | `out of bounds` | 可读 |

坏档现场备份：`steamcampaign01.sav.backup_20260907_012736_before_778_fix`。

---

## 8. 和旧参考文档的差异

`Mewgenics_Reverse_Engineering_Reference.md` §四.5 仍写「被动 8 槽，后 4 槽带 rank」。实际是：

- 4 先天/升级基因（无 rank）
- 2 职业被动（各带 rank）
- 2 疾病（各带 rank）
- 0–N 件装备 + 空槽标记
- 职业名

改序列化前先读本文，再改 `CatRecord`。
