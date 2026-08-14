# 拼豆图纸生成器

[![GitHub Release](https://img.shields.io/github/v/release/YxddxY/bean)](https://github.com/YxddxY/bean/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/YxddxY/bean/total)](https://github.com/YxddxY/bean/releases/latest)

**[下载可执行文件](https://github.com/YxddxY/bean/releases/latest/download/拼豆图纸生成器.exe)** — 无需安装 Python，直接运行。

将任意图片转换为拼豆图纸，输出带颜色编号的网格图案及用料统计。支持命令行和图形界面两种使用方式。

## 功能特性

- **CIE Lab 色彩匹配** — 基于 CIE76 ΔE 色差算法，在 291 种拼豆颜色中精确匹配最接近的色号
- **现代化 GUI** — 基于 customtkinter 的暗色主题界面，支持拖放导入图片
- **实时预览** — 生成前预览原图，生成后预览图纸
- **用料统计** — 自动统计每种颜色的用量及占比
- **灵活的参数** — 可自定义拼豆板尺寸、格子大小等参数
- **命令行支持** — 提供 CLI 接口，方便批量处理

## 项目结构

```
pingdou/
├── main.py           # 核心算法与命令行入口
├── gui.py            # 图形界面（customtkinter）
├── bead_colors.py    # 拼豆色卡定义（291 色）
├── requirements.txt  # 依赖列表
└── README.md
```

## 环境要求

- Python 3.8+
- Windows 系统（GUI 拖放功能依赖 `windnd`）

## 安装

```bash
# 克隆项目
git clone <repo-url>
cd pingdou

# 安装依赖
pip install -r requirements.txt
```

依赖包：
| 包名 | 用途 |
|---|---|
| `Pillow` | 图片加载、处理与图纸绘制 |
| `customtkinter` | 现代化 GUI 框架 |
| `windnd` | Windows 拖放文件支持 |

## 使用方式

### 图形界面

```bash
python gui.py
```

也可以直接传入图片路径快速打开：

```bash
python gui.py photo.png
```

界面操作：
1. 拖放图片或点击「浏览」选择图片文件
2. 设置拼豆板宽度、高度（颗数）和格子大小（像素）
3. 点击「生成图纸」
4. 图纸自动预览，用料统计显示在右侧面板

### 命令行

```bash
# 基本用法（默认 58×58 颗）
python main.py photo.png

# 指定尺寸和输出路径
python main.py photo.jpg -W 29 -H 29 -o output.png
```

参数说明：

| 参数 | 说明 | 默认值 |
|---|---|---|
| `image` | 输入图片路径 | 必填 |
| `-W`, `--max-width` | 最大宽度（颗数） | 58 |
| `-H`, `--max-height` | 最大高度（颗数） | 58 |
| `-o`, `--output` | 输出图片路径 | `<输入文件名>_bead.png` |

## 输出示例

生成的图纸包含：
- **网格图案** — 每个格子显示对应拼豆颜色的圆点及色号
- **5 格分隔线** — 加粗网格线方便数格子
- **颜色图例** — 右侧面板列出所有使用的色号、数量及占比

## 色卡

内置 291 种拼豆颜色，按字母分类：

| 分类 | 色系 | 编号范围 |
|---|---|---|
| A | 黄/橙色系 | A1 – A26 |
| B | 绿色系 | B1 – B32 |
| C | 蓝色系 | C1 – C29 |
| D | 紫色系 | D1 – D26 |
| E | 粉色系 | E1 – E24 |
| F | 红色系 | F1 – F25 |
| G | 棕/肤色系 | G1 – G21 |
| H | 黑/白/灰色系 | H1 – H23 |
| M | 莫兰迪色系 | M1 – M15 |
| P | 马卡龙色系 | P1 – P23 |
| Q | 荧光色系 | Q1 – Q5 |
| R | 彩虹色系 | R1 – R28 |
| T | 透明色系 | T1 |
| Y | 夜光色系 | Y1 – Y5 |
| ZG | 中国风色系 | ZG1 – ZG8 |

## 许可证

MIT License
