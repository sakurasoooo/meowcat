# Mewgenics Cat Editor & Save Modifier (meowcat / 喵星人猫咪修改器)

A modern, comprehensive graphical cat editor, save modifier, and trainer for **Mewgenics** by Edmund McMillen & Tyler Glaiel. Built with CustomTkinter, reverse-engineered from the game engine and binary assets.

一个专为《Mewgenics（喵星人）》打造的高颜值、全功能图形化猫咪属性修改器与存档管理器。基于游戏底层 C++ 引擎与 SQLite + LZ4 结构深度逆向构建。

![Mewgenics Cat Editor](https://img.shields.io/badge/Release-v1.0.0-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)

---

## 🌟 核心特色功能 (Features)

### 1. 🧬 10 大身体部位基因突变系统（孟德尔双等位基因）
- **完整支持 10 大身体部位**：毛皮（`texture`）、身体（`body`）、头部（`head`）、尾巴（`tail`）、后腿（`legs`）、前腿/手臂（`arms`）、眼睛（`eyes`）、眉毛（`eyebrows`）、耳朵（`ears`）、嘴巴（`mouth`）。
- **显性表达 + 隐性携带双轨展示**：
  - **显性基因（Dominant）**：直接决定当前外观、技能与战斗属性加减，支持自由修改。
  - **隐性基因（Recessive）**：存留在等位基因链中遗传给子代。默认锁定只读，避免误改；支持勾选右上角一键解锁自由修改隐性遗传库。
- **状态徽章标识**：自动标明 `[纯合显性]`、`[隐性携带]`、`[杂合表达]`、`[双突杂合]` 或 `[单基因]`。
- **一键突变预设**：
  - ✨ **「一键极品正面突变全满」**：一键装配 10 个部位全正向极品突变（净增 +17 属性，零负面！纯合显性 100% 稳定遗传）。
  - 🧼 **「一键清除全部突变 (纯血统)」**：一键恢复 10 个部位为原版纯种外观。

### 2. ⚔️ 战斗与 7+7 属性面板（游戏同款公式实时联动）
- **精确还原原版游戏计算公式**：
  $$\text{实效总和 (Total)} = \text{遗传底数 (Base)} + \text{10大部位突变差值 (Mut +/-)} + \text{后天加成 (Bonus)}$$
- **严格区分可遗传 vs 不可遗传**：
  - **遗传基础 (Base 1~7)**：自然繁衍的底数，稳定遗传给子代。
  - **后天加成 (Bonus 0~7)**：后天事件与锻炼奖励，不参与遗传。
- **一键极品属性预设**：纯种满遗传 (全7)、极品战神 (7+7=14)、偏科狂战 (力体7+7)、偏科法师 (智敏7+7)。
- **自由模式解锁**：支持一键解除安全限制，自由拖动滑块至 0~99。

### 3. 🏠 生理繁衍、生活环境与身份调配
- **房间自由调配**：可将猫咪自由安置至一层大厅（`Floor1_Large`）、一层侧卧（`Floor1_Small`）、阁楼（`Attic`），或移出家园；**支持将历史谱系中的猫咪直接召回家中居住**。
- **生理取向 (Sexuality)**：支持修改为异性恋（`Straight`）、双性恋（`Bisexual`）或同性恋（`Gay`），影响同居繁殖配对机制。
- **繁衍欲望与攻击性**：可调控冷淡/正常/旺盛，温顺/平衡/暴躁。
- **猫咪中文命名**：UTF-16LE 编码原生无损支持中英文。
- **偏好属性 (Boon)**：设定升级成长偏好资质（力量/灵巧/体质/智力/速度/魅力/运气）。

### 4. 🔮 技能、被动与外观
- 攻击能力（Basic Attack）与移动方式（Move Ability）自由选配。
- 4 槽位主动技能（830+ 全量法术库），每槽位支持技能升级（Ability Upgrades）强化。
- 被动系统三分支：
  - 🎖️ **职业被动（Class Passives）**：按 14 大职业分类装配专属被动。
  - 😵 **失调（Disorders）**：内置 125 条全量失调数据库，支持协同预设（Synergy Presets）一键搭配。

### 5. 💰 全局家园资源
- 实时修改家园金币、食物储备、天数，支持一键满资源 (+999,999)。
- 每次保存自动生成带时间戳的安全备份。

---

## 🚀 快速开始 (Quick Start)

### 方式 A：直接运行免安装独立 EXE（推荐）
无需配置 Python 环境，直接双击运行：
👉 **`MewgenicsCatEditor.exe`**

### 方式 B：从源码运行
```bash
# 1. 克隆代码仓库
git clone https://github.com/your-username/meowcat.git
cd meowcat

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动修改器
python MewgenicsCatEditor.py
```

### 方式 C：重新打包独立 EXE
```bash
pyinstaller --noconsole --onefile --name "MewgenicsCatEditor" --add-data "mewgenics_game_data.json;." --collect-all customtkinter --hidden-import lz4.block --hidden-import sqlite3 --hidden-import mewgenics_core MewgenicsCatEditor.py
```

---

## 📂 项目结构 (Repository Layout)

```
meowcat/
├── MewgenicsCatEditor.exe               # 编译好的 14.4MB 单文件独立可执行程序
├── MewgenicsCatEditor.py                # 图形化修改器主界面源码 (CustomTkinter)
├── mewgenics_core.py                    # 核心数据模型与存档读写引擎 (SQLite + LZ4)
├── mewgenics_game_data.json             # 游戏解包全量数据库 (突变、技能、特性、中文本地化)
├── Mewgenics_Trainer.CT                 # Cheat Engine 内存修改器脚本 (CT 表)
├── Mewgenics_Reverse_Engineering_Reference.md # 完整的游戏 C++ 原生引擎逆向开发参考文档
├── 启动猫咪修改器.bat                    # Windows 快速启动脚本
├── requirements.txt                     # Python 依赖清单
├── AGENT.md                             # AI 编程代理开发指南（架构、约定、注意事项）
├── WIKI_INTEGRATION.md                  # Wiki 图鉴数据与游戏贴图整合指南
├── game_assets/                         # resources.gpak 解包产物：贴图/SWF/GON（1.6GB，不入库）
├── wiki_data/                           # mewcodex wiki 爬取：15 个 JSON 数据库 + 4092 张图标 + 打标签 CSV
├── .gitignore                           # Git 忽略配置
└── tools/                               # 逆向工程、符号分析、二进制解包工具脚本集 (~110 个脚本)
```

---

## 📜 许可说明 (License)

本项目仅供学习逆向工程、游戏存档格式研究与个人单机游戏娱乐使用。
