# Mewgenics (喵星人) 逆向工程与修改器开发技术全文档

## 一、 游戏引擎与架构概览

- **游戏开发商 / 引擎作者**: Edmund McMillen & Tyler Glaiel (Glaiel Games)
- **底层架构**: 纯 C++ 原生引擎 (x86_64, Windows 64-bit)，未混淆，保留完整 MSVC RTTI 类型描述符。
- **渲染框架**: OpenGL 3.2.0 + 自定义矢量网格细分器 (`glaielswf::Tesselator`, `glaielswf::BitmapFillAtlas`)，配合 Flash SWF 文件 (`unicodefont.swf`, `catanis.swf`, `catparts.swf`) 提供高帧率无损矢量缩放。
- **游戏配置数据格式**: **GON (Glaiel Object Notation)**，Tyler Glaiel 开源的结构化配置语言。
- **资源包结构**: `resources.gpak` (5.1 GB)，采用无压缩紧凑文件列表 + 顺序负载存储格式。
- **存档系统**: **SQLite 3 STRICT 数据库 + LZ4 块压缩**。

---

## 二、 核心资源包 `resources.gpak` 格式解析

`resources.gpak` 内部打包了 19,979 个游戏数据文件，格式解析规则如下：

1. **包头 (Header)**:
   - `0x0000..0x0003`: `uint32_t file_count` (文件总数，例如 19,979)。
2. **索引列表 (Index Entries)**:
   - 紧随包头依次排列每一个文件的元信息：
     - `uint16_t filename_length` (文件名长度，例如 20)。
     - `char filename[filename_length]` (UTF-8 文件相对路径，如 `audio/combat_sfx.gon`)。
     - `uint32_t file_size` (文件实际字节大小)。
3. **数据负载段 (Data Payloads)**:
   - 索引列表读取完成后即为数据区起点（偏移 `0x000C9575`）。
   - 文件内容按索引顺序物理连续存储，无需单独计算偏移：`Offset(N) = DataStart + Sum(Size(0..N-1))`。

---

## 三、 存档系统与 SQLite 数据库架构

- **物理存储路径**:  
  `%APPDATA%\Glaiel Games\Mewgenics\<SteamID64>\saves\steamcampaign01.sav`
- **数据库类型**: SQLite 3 (带 STRICT 模式约束)。

### 1. 数据表定义与功能

| 表名 (Table) | 模式 (Schema) | 存储内容说明 |
| :--- | :--- | :--- |
| `cats` | `(key INTEGER PRIMARY KEY, data BLOB) STRICT` | 历代所有猫咪数据（在生、死后、图鉴）。`data` 为 LZ4 压缩包。 |
| `properties` | `(key TEXT PRIMARY KEY, data ANY) STRICT` | 全局状态键值对（金币、食物、天数、关卡解锁、天气解锁等）。 |
| `files` | `(key TEXT PRIMARY KEY, data BLOB) STRICT` | 家园状态 (`house_state`)、家谱 (`pedigree`)、封面猫咪 (`save_file_cat`) 等。 |
| `furniture` | `(key INTEGER PRIMARY KEY, data BLOB) STRICT` | 收集与放置的家具对象数据。 |
| `winning_teams`| `(key INTEGER PRIMARY KEY, data BLOB) STRICT` | 通关获胜的探险队伍荣誉殿堂。 |

### 2. 全局关键属性 (`properties` 表)

修改 `properties` 表中的对应键值即可直接控制游戏资源：

- `house_gold` (INTEGER): 当前家园黄金总数。
- `house_food` (INTEGER): 当前家园食物总数。
- `current_day` (INTEGER): 当前经营游戏天数。
- `house_storage_upgrades` (INTEGER): 储物空间升级等级。
- `blank_collars` (INTEGER): 空白项圈数量。
- `mapflag_*` (INTEGER 1): 对应区域（下水道、墓地、核心区等）地图解锁标记。

---

## 四、 `CatData` (猫咪数据结构) 二进制布局规范

在 `cats` 表中，每一条记录的 `data` 格式为：
```
[uint32_t uncompressed_size] + [LZ4_CompressBlock(raw_cat_data)]
```
解压后的 `raw_cat_data` 结构严密，字段顺序如下：

### 1. 基础标识与命名段
- `+0x00`: `uint32_t version` (当前版本固定为 `19`)。
- `+0x04`: `uint64_t guid` (猫咪唯一 64 位基因/哈希标识)。
- `+0x0C`: `uint64_t name_length` (名称字符数)。
- `+0x14`: `wchar_t name[name_length]` (猫咪名称，**UTF-16LE 编码**，原生支持中文与英文字符)。

### 2. 头衔与身体外观部件段 (`CatPartID`)
- 位于名称后：
  - `uint64_t title_length` + `char title[]` (称号，如 `"None"`, `"star2"`)。
  - `uint32_t post_title_flag` (通常为 `1`)。
  - **368 字节部件外貌块**: 存放 10 个解剖身体部位的部件 ID、色盘编号（如 `0xF6`, `0xE2`, `0xC0`）、眼睛异色/旋转等基因参数。
    - 部件枚举 (`CatPartID`):
      - `0 = Body` (身体)
      - `1 = Head` (头部)
      - `2 = Tail` (尾巴)
      - `3 = Legs` (腿部)
      - `4 = Arms` (手臂)
      - `6 = Eyes` (眼睛，15 为左眼，16 为右眼)
      - `7 = Eyebrows` (眉毛，17 为左眉，18 为右眉)
      - `8 = Ears` (耳朵，19 为左耳，20 为右耳)
      - `9 = Mouth` (嘴巴)
      - `10 = Texture` (毛皮斑纹)
    - 部件突变规则：基础部位编号为 `0~299`，**突变器官编号从 `300` 开始**。

### 3. 声音与性别段
- `uint64_t voice_length` + `char voice[]`: 声音特征字符串（例如 `"male55"`, `"female50"`, `"male109"`, `"spidercat"`, `"robotom"`）。
- `double voice_pitch` (8 字节双精度浮点数，控制喵叫音调高低，一般在 `0.5 ~ 2.0`)。

### 4. 核心属性值段 (7 维基础属性 + 7 维附加加成)
紧随 `voice_pitch` 之后连续存放 **14 个 32 位有符号整数** (`int32_t[14]`)：

```
+0x00: int32_t base_str;  // 基础力量 (Strength)
+0x04: int32_t base_dex;  // 基础敏捷 (Dexterity)
+0x08: int32_t base_con;  // 基础体质 (Constitution)
+0x0C: int32_t base_int;  // 基础智力 (Intelligence)
+0x10: int32_t base_spd;  // 基础速度 (Speed)
+0x14: int32_t base_cha;  // 基础魅力 (Charisma)
+0x18: int32_t base_lck;  // 基础幸运 (Luck)

+0x1C: int32_t bonus_str; // 附加力量加成
+0x20: int32_t bonus_dex; // 附加敏捷加成
+0x24: int32_t bonus_con; // 附加体质加成
+0x28: int32_t bonus_int; // 附加智力加成
+0x2C: int32_t bonus_spd; // 附加速度加成
+0x30: int32_t bonus_cha; // 附加魅力加成
+0x34: int32_t bonus_lck; // 附加幸运加成
```

### 5. 技能与职业段 (字符串序列)
紧随属性段后，存放游戏内技能与特性，每个字符串均带 8 字节 `uint64_t` 长度前缀：
1. **Boon / 偏好属性**: `"none"`, `"str"`, `"dex"`, `"lck"` 等。
2. **移动技能**: 默认 `"DefaultMove"`。
3. **普通攻击**: `"BasicMelee"`, `"BasicShortRanged"`, `"BasicTankMelee"`, `"BasicShortLobbed"` 等。
4. **主动技能槽 1~4**: `"Spit"`, `"Block"`, `"Roll"`, `"MageSwap"`, `"None"` 等。
5. **被动特性槽 1~8**:
   - 前 4 个槽为遗传固有特性（如 `"SelfAssured"`, `"HotBlooded"`）。
   - 后 4 个槽为成长进阶特性（每个特性后跟 4 字节整数 `rank = 1`）。
6. **职业 (Class)**: `"Colorless"`, `"Fighter"`, `"Mage"`, `"Hunter"`, `"Tank"`, `"Medic"`, `"Thief"`, `"Necromancer"`, `"Butcher"`, `"Druid"`, `"Monk"`, `"Psychic"`, `"Tinkerer"`, `"Jester"`。

---

---

## 五、 二进制逆向与 Cheat Engine 运行时内存分析

### 1. 二进制文件与源码树逆向 (`Mewgenics.exe`)
- **文件路径**: `C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe` (22,019,072 字节)
- **基址与入口**: `ImageBase = 0x140000000`，入口点 `RVA = 0xd3e8ac` (VA: `0x140d3e8ac`)。
- **源码工程树结构**: 通过二进制断言与符号提取出完整的 89 个 C++ 源码文件模块：
  - **存档与家园管理**: `MewSaveFile.cpp`、`HouseInventory.cpp`、`Inventory.cpp`、`SQLSaveFile.cpp`
  - **猫咪数据与遗传**: `CatData.cpp`、`CatArt.cpp`、`CatSelector.cpp`、`Pedigree.cpp` (家谱育种)
  - **战术战斗系统**: `TacticsGrid.cpp`、`TacticsLayer.cpp`、`TurnControl.cpp`、`DamageInstance.cpp`
  - **技能与状态**: `Ability.cpp`、`Passive.cpp`、`BasicStatuses.cpp`、`DashAttackAbility.cpp`、`SpawnAbility.cpp`
  - **关卡与地图**: `MapGeneration.cpp`、`MapNode.cpp`、`MapScreen.cpp`、`Level.cpp`、`Shop.cpp`

### 2. 运行时核心全局指针与变量地址 (Global Pointers)

| 静态 VA 地址 | RVA 偏移 | 类型与功能说明 |
| :--- | :--- | :--- |
| `0x1413c1920` | `+0x13c1920` | `int64_t g_CurrentDay`: 游戏全局天数实时状态变量 |
| `0x1412f6c48` | `+0x12f6c48` | `void* g_HouseState`: 全局家园状态对象句柄 |
| `0x1413c5530` | `+0x13c5530` | `AbilityDatabase* g_AbilityDB`: 运行时全量技能元数据注册中心 |
| `0x1413c79d0` | `+0x13c79d0` | `CatManager* g_CatManager`: 活跃猫咪实例管理对象 |

### 3. 家园控制器 `House* (r12)` 核心结构偏移

在 Hook 点 `0x1403a6d13` 捕获寄存器 `r12` 即为 `House*` 实例：
- `[r12 + 0x038]`: `SQLSaveFile*` (底层 SQLite 存档文件与内存属性映射句柄)
- `[r12 + 0x580]`: `current_day` (当前游戏天数，4 字节整数)
- `[r12 + 0x588]`: `house_gold` (家园黄金总数，4 字节整数)
- `[r12 + 0x590]`: `house_food` (家园食物总数，4 字节整数)
- `[r12 + 0x598]`: `storage_capacity` (储物箱容量上限，4 字节整数)
- `[r12 + 0x5A0]`: `blank_collars` (空白项圈总数，4 字节整数)
- `[r12 + 0x5A8]`: `furniture_boxes` (家具箱总数，4 字节整数)

### 4. 猫咪实体 `CatData* (r13)` 运行时内存结构偏移

通过 `0x1407a35df` 例程分析逆向获得的活跃猫咪对象内存布局：
- `[r13 + 0x000]`: `void* vftable` (虚拟函数表指针)
- `[r13 + 0x008]`: `uint64_t guid` (猫咪唯一 64 位全局 GUID)
- `[r13 + 0x018]`: `ComponentList*` (包含战斗数值、Buff 状态、血量的数据组件链表)
- `[r13 + 0x7d0]`: `std::string move_ability` (当前绑定的移动技能，默认 `"DefaultMove"`)
- `[r13 + 0x7f0]`: `std::string attack_ability` (当前绑定的普通攻击技能，默认 `"BasicMelee"`)

### 5. 关键函数地址对照表 (Function RVAs)

| 虚拟地址 (VA) | RVA 偏移 | 函数功能命名与说明 |
| :--- | :--- | :--- |
| `0x1403a6db9` | `+0x3a6db9` | `House::LoadProperties()`: 读取 `current_day` 等属性写入 `[r12 + 0x580]` |
| `0x14022c5e0` | `+0x22c5e0` | `SQLSaveFile::GetIntProperty(const char* key, int def)`: 从数据库读取整型配置 |
| `0x14022cef0` | `+0x22cef0` | `SQLSaveFile::SetProperty(const char* key, ...)`: 向数据库写入状态 |
| `0x1407a35df` | `+0x7a35df` | `CatData::InitializeAbilities()`: 绑定普攻与移动技能至 `[r13 + 0x7d0/7f0]` |
| `0x14008f936` | `+0x8f936` | `House::SaveHouseState()`: 序列化 `house_state` 二进制块至 `files` 表 |

### 6. AOB 内存挂钩特征码与 CE 辅助表
- **House 控制器挂钩 AOB**:  
  `41 B8 04 00 00 00 48 8D 15 ?? ?? ?? ?? 48 8D 4C 24 30` (唯一匹配，`r12 = House*`)
- **配套 Cheat Engine 表**:  
  [`Mewgenics_Trainer.CT`](file:///c:/Users/10107/Documents/github/cheatenginemcp/Mewgenics_Trainer.CT)：直接附加游戏进程后勾选即可实时读写与锁定资源。

---

## 六、 独立单文件 EXE 修改器与新建猫咪工具

为了方便用户直接使用，已将修改器完整编译打包为**独立免安装单文件 EXE**：

### 1. 程序路径与启动
- **免安装单文件版（推荐直接使用）**:  
  👉 **[`MewgenicsCatEditor.exe`](file:///c:/Users/10107/Documents/github/cheatenginemcp/MewgenicsCatEditor.exe)** (14.4 MB)
- **快捷批处理**:  
  [启动猫咪修改器.bat](file:///c:/Users/10107/Documents/github/cheatenginemcp/%E5%90%AF%E5%8A%A8%E7%8C%AB%E5%92%AA%E4%BF%AE%E6%94%B9%E5%99%A8.bat)
- **源码入口**:  
  [`MewgenicsCatEditor.py`](file:///c:/Users/10107/Documents/github/cheatenginemcp/MewgenicsCatEditor.py)

### 2. 核心功能清单
1. **自动寻址与安全备份**:
   - 自动递归扫描 Steam 存档目录，自动识别 `steamcampaign01.sav`。
   - **修改时自动在同目录下生成带时间戳的安全备份**（`.backup_YYYYMMDD_HHMMSS`）。
2. **猫咪列表与即时筛选**:
   - 实时列出全部猫咪，支持按猫咪名称（含中文）、ID 编号或职业即时过滤。
3. **猫咪全属性自由修改**:
   - **7 基础属性 + 7 附加点数**（力量、敏捷、体质、智力、速度、魅力、幸运），精准滑块与输入框，支持 0~99 突破。
   - **一键属性预设**: 全 99 神猫、全 25 满级、狂战士力量型、大魔导智力型、血牛防御型。
   - **身份与声音**: 支持中文/英文名字改名、自由切换 14 种职业、调节喵叫音调（Pitch）滑块与声音类型。
   - **全量技能/特性配置**: 内置解包提取的 830+ 种技能与 370+ 种被动特质下拉选项。
4. **新建专属猫咪 (Create New Cat)**:
   - 点击「+ 新建猫咪」，输入名称并选择职业、性别和初始数值模板，自动生成合法 64 位 GUID 与外观基因块安全写入存档。
5. **克隆与删除**:
   - 一键克隆优质猫咪用于培育繁衍；支持安全删除不需要的记录。
6. **全局家园资源修改**:
   - 支持一键将金币和食物调整至 999,999。
