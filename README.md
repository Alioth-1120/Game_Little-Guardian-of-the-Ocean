# Little Guardian of the Ocean

<p align="center">
  [<strong>English</strong>] | [<strong>简体中文</strong>]
</p>

---

## English

### Project Overview
"Little Guardian of the Ocean" is a 2D interactive program. The primary goal of this project is not to release a complete commercial game, but to serve as a **validation project for an AI-assisted rapid prototyping workflow**.

This project explores how to quickly build underlying render loops and state machines using controllable generative AI tools (such as Large Language Models) during the early stages of development. It validates the feasibility of "Human-in-the-loop" collaborative development within the interactive media pipeline.

### Core Gameplay & AI Validation Points
The game is inspired by the classic "Gold Miner" gameplay loop. Players control a hook from a boat to clean up ocean trash and interact with marine life.
During development, core logic such as collision detection, event listener frameworks, and some mathematical vector calculations were generated with the assistance of AI through precise Context Prompting. The human developer then performed logic fine-tuning and closed-loop testing.

### Project Structure
```text
Little Guardian of the Ocean.py
art_resources/
requirements.txt

```

* `Little Guardian of the Ocean.py`: Main game program and core logic.
* `art_resources/`: UI and object art assets used in-game.
* `requirements.txt`: Python dependencies list.

### Requirements & How to Run

Python 3.9 or higher is recommended.

1. Install dependencies:

```bash
pip install -r requirements.txt

```

2. Run the program:

```bash
python "Little Guardian of the Ocean.py"

```

### Controls

* **Mouse Click**: Select menu buttons, skip intro screens, and launch the hook during gameplay.

### Generated Files

The program will generate the following state cache files after running locally:

```text
gamecache.sav
highscore.sav
save_load.log
__pycache__/

```

For the sake of version control standardization, these local saves, logs, and Python cache files are explicitly excluded from the codebase via `.gitignore` rules to ensure a clean repository.

---

## 简体中文

### 项目简介 (Project Overview)

《Little Guardian of the Ocean》是一个 2D 互动程序。本项目的主要目的并非发布一款完整的商业游戏，而是作为一个**基于 AI 辅助编程的快速原型（Rapid Prototyping）工作流验证项目**。

本项目探索了在开发早期阶段，如何通过可控的生成式 AI 工具（如大语言模型）快速搭建底层渲染循环、状态机，并验证“人机协同开发（Human-in-the-loop）”在互动媒体管线中的可行性。

### 核心玩法与 AI 验证点 (Core Gameplay & AI Validation)

游戏受经典“黄金矿工”玩法启发。玩家控制船上的钩爪清理海洋垃圾并与海洋生物交互。
在开发过程中，核心的碰撞检测逻辑、事件监听框架以及部分数学向量计算，均通过向 AI 提供精确的上下文约束（Context Prompting）辅助生成，并由人类开发者进行逻辑微调与闭环测试。

### 项目结构 (Project Structure)

```text
Little Guardian of the Ocean.py
art_resources/
requirements.txt

```

* `Little Guardian of the Ocean.py`: 游戏主程序与核心逻辑。
* `art_resources/`: 游戏内使用的 UI 及对象美术资产。
* `requirements.txt`: Python 依赖清单。

### 运行环境与启动 (Requirements & How to Run)

推荐使用 Python 3.9 或更高版本。

1. 安装依赖:

```bash
pip install -r requirements.txt

```

2. 运行程序:

```bash
python "Little Guardian of the Ocean.py"

```

### 操作说明 (Controls)

* **鼠标点击**: 选择菜单按钮，跳过介绍界面，以及在游戏过程中发射钩爪。

### 关于生成文件 (Generated Files)

程序在本地运行后会生成以下状态缓存文件：

```text
gamecache.sav
highscore.sav
save_load.log
__pycache__/

```

出于版本控制的规范性，这些本地存档、日志和 Python 缓存文件已通过 `.gitignore` 规则被明确排除在代码库之外，以确保仓库的纯净。
