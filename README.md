# Mewgenics Cat Editor & Save Modifier (meowcat / 喵星人猫咪修改器)

A modern, comprehensive graphical cat editor, save modifier, and trainer for **Mewgenics** by Edmund McMillen & Tyler Glaiel. Built with CustomTkinter, reverse-engineered from the game engine and binary assets.

一个专为《Mewgenics（喵星人）》打造的高颜值、全功能图形化猫咪属性修改器与存档管理器。基于游戏底层 C++ 引擎与 SQLite + LZ4 结构深度逆向构建。

![Mewgenics Cat Editor](https://img.shields.io/badge/Release-v1.0.0-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)

---

## 🌟 核心特色功能 (Features)

### 1. 🧬 15 物理部位基因突变系统（左右不对称支持）
- **完整支持 10 大身体部位**：毛皮（`texture`）、身体（`body`）、头部（`head`）、尾巴（`tail`）、后腿（`legs`）、前腿/手臂（`arms`）、眼睛（`eyes`）、眉毛（`eyebrows`）、耳朵（`ears`）、嘴巴（`mouth`）。
- **真实机制（逆向验证）**：猫实际有 **15 个物理部位槽**——眼/耳/眉/臂/腿 5 个成对部位**左右独立**，可为不同变异（局内事件的 asymmetric 变异，上限 15）；繁殖时左右统一，后代最多 10 种变异。游戏内变异总数 >10 时会关闭详情悬浮列表（只显示计数徽章），本编辑器始终完整显示全部 15 槽。
- **左右侧独立编辑**：成对部位提供「左侧/右侧」两个图标按钮，属性加成双侧合并计算；支持设置 **部位缺失 (-2)**（出生缺陷）。
- **图标选择器（替代长下拉框）**：点击部位按钮弹出图标浏览面板——分类色块磁贴（✔正面绿 / ✖负面红 / ⚡特效蓝 / 🐣缺陷橙）、**搜索**（名称/描述/属性）、**翻页**（6×4 网格）、右侧详情卡实时显示属性加减与效果描述，当前部件高亮。
- **状态徽章标识**：成对部位自动标明 `[对称]` / `[⚡不对称]`；顶部摘要实时显示与游戏内一致的 **变异计数 / 出生缺陷计数**（双徽章口径）。
- **一键突变预设**：
  - ✨ **「一键极品正面突变全满」**：一键装配 10 个部位全正向极品突变（净增 +17 属性，零负面！左右对称写入，繁殖统一遗传）。
  - 🧼 **「一键清除全部突变 (纯血统)」**：一键恢复 15 个物理部件为原版纯种外观。

### 2. ⚔️ 战斗与 7+7 属性面板（游戏同款公式实时联动）
- **精确还原原版游戏计算公式**：
  $$\text{实效总和 (Total)} = \text{遗传底数 (Base)} + \text{15物理部件突变差值 (Mut +/-)} + \text{后天加成 (Bonus)}$$
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
- **偏好属性 (Boon)**：⚠️ 出生随机标记，游戏内无明显效果（疑似废弃机制）。

### 4. 🔮 技能、被动与外观
- 攻击能力（Basic Attack）与移动方式（Move Ability）自由选配。
- 4 槽位主动技能（830+ 全量法术库），每槽位支持技能升级（Ability Upgrades）强化。
- 被动系统三分支：
  - 🎖️ **职业被动（Class Passives）**：按 14 大职业分类装配专属被动。
  - 😵 **失调（Disorders）**：内置 125 条全量失调数据库，支持协同预设（Synergy Presets）一键搭配。

### 5. 🎒 仓库道具管理（顶层独立路由）
- 与猫咪编辑并列的独立页面，管理 **仓库 (Storage) / 背包 (Backpack) / 回收站 (Trash)** 三个箱子。
- 道具列表带 **wiki 官方图标 + 中文名 + 实例序列号 + 磨损度（当前耐久/最大耐久）**；选中后显示部位/稀有度/套装/属性/效果信息卡。
- 支持**更换道具类型**（1134 项全量图鉴下拉）、**添加新道具**、**删除道具**。
- **仓库容量限制**：按 `house_storage_upgrades` 等级计算容量（基础 3×3，每级 +1 圈，7 级后每格 +1），添加道具超出容量时阻止并提示。
- **🏪 商店与家园升级进度卡**（只读）：仓库商店(Butch)、家具店(Jack)、食品店(Tracy)、信息店(Tink)、器官店(Organ)、房屋升级、Beanies 任务进度。
- 存档格式：SQLite `files` 表 `inventory_*` blob（条目含可选扩展串、耐久、实例序列号，未知字段原样保留）；商店进度解析自 `npc_progress` / `house_unlocks`。

### 6. 🪑 家具管理（顶层独立路由）
- **主展示区 = 📦 家具仓库**（未放置家具：无房间且坐标 (0,0)）：支持**更换类型**（634 项全量图鉴带图标）、**移除**、**添加新家具入仓库**。
- **已放置家具（一层大厅/侧卧/阁楼/墙面装饰）🔒 只读**：仅展示属性，请在游戏中调整位置。
- 家具属性**中文映射显示**：舒适度、刺激度、吸引力、健康、繁殖抑制、变异促进、战斗奖励、战斗风险、食物储存。
- 存档格式：SQLite `furniture` 表（key + 类型名 + 房间 + 坐标 + 变体），字节级 round-trip 已验证。

### 7. 🏅 职业通关进度（顶层独立路由，只读）
- 对应游戏内职业页面的 **9 大章节角标**（`major_class_checkmarks`: 洞穴/乱葬岗/月球/地心/侏罗纪/终结/血肉世界/X维度/时间尽头）。
- 14 职业 × 9 角标矩阵一览：✔ 绿色 = 该职业已通关此章节（与游戏内角标点亮一致），并显示每职业 x/9 进度。
- 数据来源：存档 `npc_progress` 的 (章节, 职业) 记录逆向解析（字段 a = -1 即通关），**只读**。

### 8. 💰 全局家园资源
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
├── mutation_picker.py                   # 突变图标选择器 (图标网格/搜索/翻页/正负缺陷分类)
├── mewgenics_game_data.json             # 游戏解包全量数据库 (突变、技能、特性、中文本地化)
├── Mewgenics_Trainer.CT                 # Cheat Engine 内存修改器脚本 (CT 表)
├── CLASS_THEMES.md                        # 职业主题色调色板 + 项圈/通关角标/稀有度框贴图提取对照
├── Mewgenics_Reverse_Engineering_Reference.md # 完整的游戏 C++ 原生引擎逆向开发参考文档
├── 启动猫咪修改器.bat                    # Windows 快速启动脚本
├── requirements.txt                     # Python 依赖清单
├── AGENT.md                             # AI 编程代理开发指南（架构、约定、注意事项）
├── WIKI_INTEGRATION.md                  # Wiki 图鉴数据与游戏贴图整合指南
├── game_assets/                         # resources.gpak 解包产物：贴图/SWF/GON（1.6GB，不入库）
├── wiki_data/                           # mewcodex wiki 爬取：15 个 JSON 数据库 + 4092 张图标 + 打标签 CSV
├── .gitignore                           # Git 忽略配置
└── tools/                               # 逆向工程、符号分析、二进制解包工具脚本集 (~115 个脚本)
                                         #   含 test_inventory_furniture_roundtrip.py（库存/家具字节级回归哨兵）
                                         #   与 test_smoke_items_furniture.py（存档副本增删改冒烟测试）
```

---

## 🀄 中文文本来源

界面中的技能、天气、职业、章节等中文名称来自社区 beta 补丁 [mewcodex / Mewgenics-Chinese-Translation](https://github.com/mewcodex/Mewgenics-Chinese-Translation)，**尚未合入主游戏**，也不是发行版自带汉化。

---

## 📜 许可说明 (License)

本项目仅供学习逆向工程、游戏存档格式研究与个人单机游戏娱乐使用。
