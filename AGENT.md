# AGENT.md — AI 编程代理指南 (Agent Guide)

本文件为在本仓库中工作的 AI 编码代理（Claude Code / DeepSeek Harness / Copilot 等）提供项目上下文、架构说明与开发约定。修改代码前请完整阅读本文件。

---

## 1. 项目概览 (Project Overview)

**meowcat** 是《Mewgenics（喵星人）》（Edmund McMillen & Tyler Glaiel 作品）的**猫咪属性修改器与存档编辑器**：

- 图形界面：**CustomTkinter**（Python 3.10+，Windows 桌面应用）。
- 存档格式：**SQLite 3 STRICT 数据库 + LZ4 块压缩**（`steamcampaign01.sav`）。
- 猫咪数据为自研二进制结构 `CatData`，通过逆向游戏 C++ 引擎获得，**没有官方文档**——所有偏移量见 `Mewgenics_Reverse_Engineering_Reference.md`。
- 交付物：单文件独立 EXE（PyInstaller，约 14MB）。

## 2. 仓库结构与关键文件 (Key Files)

```
meowcat/
├── MewgenicsCatEditor.py   # GUI 主程序 (~1500 行, CustomTkinter)。所有 UI 逻辑都在 MewgenicsApp 类中
├── mewgenics_core.py       # 核心引擎 (~650 行): MewgenicsSaveManager + CatRecord + MUTATION_SLOTS
├── mewgenics_game_data.json# 游戏解包数据库 (~540KB): 突变/技能/被动/失调/中文本地化。只读，勿手改
├── Mewgenics_Reverse_Engineering_Reference.md  # 二进制布局权威参考，改存档结构前必读
├── MewgenicsCatEditor.spec # PyInstaller 打包配置
├── Mewgenics_Trainer.CT    # Cheat Engine 内存修改表（独立交付物）
├── 启动猫咪修改器.bat       # Windows 启动脚本（优先 exe，回退 python）
├── requirements.txt        # customtkinter, lz4, pyinstaller, pefile, capstone
├── WIKI_INTEGRATION.md     # wiki 图鉴数据/贴图整合指南（csv 标签规范、编辑器接入示例）
├── game_assets/            # gpak 解包产物（textures/swfs/data，1.6GB，gitignore）
├── wiki_data/              # wiki 爬取产物（15 JSON + 4092 图标 + csv 标签，图标目录 gitignore）
└── tools/                  # ~110 个逆向/分析/解包一次性脚本（check_*.py, analyze_*.py 等）
```

**职责划分铁律**：
- `mewgenics_core.py`：所有二进制读写、SQLite 存取、LZ4 压缩。UI 层**禁止**直接操作 `raw_data` 偏移。
- `MewgenicsCatEditor.py`：仅 UI 与事件处理，通过 `MewgenicsSaveManager` / `CatRecord` 的公开 API 交互。
- `tools/`：探索性脚本，可随意新增，但不要从主程序 import 它们。

## 3. 核心领域概念 (Domain Model)

### 猫咪数据 `CatRecord`（`mewgenics_core.py`）
- 存档 `cats` 表：`key INTEGER PRIMARY KEY, data BLOB`，`data` 为 LZ4 压缩的 `CatData`。
- 定位锚点：在解压后的二进制中用正则搜索 voice 字符串（`male\d+|female\d+|robotom|spidercat|...`），voice 之前是 header+名字+头衔+部件块，之后是属性/技能区。**新增字段解析通常以 voice 偏移为基准**。
- 名字编码：**UTF-16LE**（`name_len` 为字符数，字节数 = `name_len * 2`）。
- 10 大突变部位见 `MUTATION_SLOTS`（偏移量常量表），每个部位有显性/隐性双等位基因；显性决定外观与属性，隐性仅参与遗传。
- 7 项属性（`str/dex/con/int/spd/cha/lck`）：`Total = Base(1~7, 可遗传) + 突变差值 + Bonus(0~7, 不可遗传)`。
- 被动系统三分支（v1.x 重构后）：**职业被动 (class passives)**、**技能升级 (ability upgrades)**、**失调 (disorders, 125 条数据库 + 协同预设)**。

### 存档全局资源（`properties` 表）
`house_gold` / `house_food` / `current_day` / `house_storage_upgrades` / `blank_collars` 等，直接改键值。

### 默认存档路径
`%APPDATA%\Glaiel Games\Mewgenics\<SteamID64>\saves\steamcampaign01.sav`

## 4. 构建与运行 (Build & Run)

```bash
# 安装依赖
pip install -r requirements.txt

# 从源码运行
python MewgenicsCatEditor.py

# 打包 EXE（用 .spec 文件，与 README 中的命令等价）
pyinstaller MewgenicsCatEditor.spec
```

- 无测试套件、无 CI、无 lint 配置。验证方式 = 运行 GUI + 对真实/备份存档做读写冒烟测试。
- 存档操作前 `MewgenicsSaveManager` 会自动生成带时间戳的备份；**保持这一行为不被绕过**。

## 5. 开发约定 (Conventions)

- **语言与注释**：UI 文案、注释、commit message 以中文为主（中英混合可）。保持现有风格。
- **编码**：所有源文件 UTF-8；二进制中的猫咪名字必须 UTF-16LE 无损读写，勿用 `errors='ignore'` 之外的方式静默截断。
- **字节序**：一律小端（`struct` 格式串用 `<` 前缀）。
- **修改二进制结构时**：先查 `Mewgenics_Reverse_Engineering_Reference.md` 的偏移表；新发现的偏移用 `tools/check_*.py` 风格的独立脚本在真实存档上验证后再合入主程序。
- **`mewgenics_game_data.json` 是生成物**：由解包工具产出，不要手工编辑；需要更新时改工具脚本重新生成。
- **数值安全限制**：UI 中属性滑块默认限制在游戏合法范围（如 0~14），"自由模式"需用户显式解锁；不要默认放开。
- **Git**：已提交的 EXE 为构建产物，修改源码后需重新打包才更新 EXE；commit 前确认 `.gitignore` 是否覆盖了 `dist/`、`build/`、`__pycache__`。

## 6. 常见任务速查 (Common Tasks)

| 任务 | 入口 |
| :--- | :--- |
| 新增一个猫咪可编辑字段 | `mewgenics_core.py` 的 `CatRecord.parse()` / 序列化方法 + GUI 面板 |
| 新增突变部位 | 修改 `MUTATION_SLOTS` 常量表（需先逆向确认偏移） |
| 改全局资源（金币/食物/天数） | `MewgenicsSaveManager` 的 properties 读写方法 |
| 更新技能/被动数据库 | `tools/` 解包脚本 → 重新生成 `mewgenics_game_data.json` |
| 解包游戏贴图/资源 | `tools/extract_gpak_assets.py` → `game_assets/`（详见 `WIKI_INTEGRATION.md`） |
| 爬取 wiki 图鉴与图标 | `tools/crawl_wiki_assets.py` → `wiki_data/`（增量爬取，CSV 打标签） |
| 重新打包发布 | `pyinstaller MewgenicsCatEditor.spec` → 校验 exe 可独立运行 |

## 7. 注意事项 (Gotchas)

- ⚠️ 偏移量硬编码较多（如 `MUTATION_SLOTS` 中的 `100 + 4`），改游戏版本后可能整体失效——游戏更新后需重新逆向验证。
- ⚠️ `CatRecord` 依赖 voice 字符串正则定位，若游戏新增 voice 类型（如已有 `demoncat`/`robotcat`），正则需同步扩展。
- ⚠️ EXE 打包依赖 `--add-data "mewgenics_game_data.json;."` 与 `--hidden-import lz4.block`；`get_resource_path()` 同时处理开发态与 PyInstaller `_MEIPASS` 运行态，新增资源文件时沿用该函数。
- ⚠️ 请勿上传真实用户存档（含 SteamID）到仓库。

---

*License: 仅供学习逆向工程与个人单机娱乐使用。*
