"""
拼豆图纸生成器
将图片转换为拼豆图纸，输出带颜色编号的网格图案及用料统计。
"""

import argparse
import math
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from bead_colors import BEAD_COLORS


# ---------------------------------------------------------------------------
# 核心算法 — CIE Lab 色彩空间 ΔE 颜色匹配
# ---------------------------------------------------------------------------

# D65 标准光源参考白点
_Xn, _Yn, _Zn = 0.95047, 1.00000, 1.08883


def _srgb_to_linear(c):
    """sRGB 通道值 (0-255) → 线性光强度"""
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _f_lab(t):
    """Lab 转换中的 f(t) 函数"""
    delta = 6 / 29
    return t ** (1 / 3) if t > delta ** 3 else t / (3 * delta ** 2) + 4 / 29


def rgb_to_lab(rgb):
    """将 sRGB (R,G,B 0-255) 转换为 CIE Lab (L, a, b)"""
    r, g, b = _srgb_to_linear(rgb[0]), _srgb_to_linear(rgb[1]), _srgb_to_linear(rgb[2])
    # 线性 RGB → XYZ (D65)
    x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b
    # XYZ → Lab
    L = 116 * _f_lab(y / _Yn) - 16
    a = 500 * (_f_lab(x / _Xn) - _f_lab(y / _Yn))
    b_val = 200 * (_f_lab(y / _Yn) - _f_lab(z / _Zn))
    return (L, a, b_val)


def delta_e(lab1, lab2):
    """CIE76 ΔE 色差（值越小越接近，<2 人眼几乎无法分辨）"""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(lab1, lab2)))


# 预计算所有拼豆颜色的 Lab 值，避免重复转换
_BEAD_LAB_CACHE = [(name, rgb_to_lab(rgb)) for name, rgb in BEAD_COLORS]


def find_nearest_bead_color(pixel_rgb):
    """找到与给定 RGB 最接近的拼豆颜色（基于 CIE Lab ΔE 色差）"""
    pixel_lab = rgb_to_lab(pixel_rgb)
    best = None
    best_dist = float("inf")
    for name, lab in _BEAD_LAB_CACHE:
        dist = delta_e(pixel_lab, lab)
        if dist < best_dist:
            best_dist = dist
            best = name
    return best


def load_and_resize(image_path, max_width, max_height):
    """加载图片并按比例缩放到目标拼豆板尺寸内"""
    img = Image.open(image_path).convert("RGB")
    w, h = img.size

    # 等比缩放，使图片完全放入 max_width x max_height 的网格
    scale = min(max_width / w, max_height / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    img = img.resize((new_w, new_h), Image.LANCZOS)
    return img


def image_to_bead_grid(img):
    """将图片的每个像素映射到最近的拼豆颜色，返回颜色名称二维列表"""
    w, h = img.size
    grid = []
    for y in range(h):
        row = []
        for x in range(w):
            pixel = img.getpixel((x, y))
            row.append(find_nearest_bead_color(pixel))
        grid.append(row)
    return grid


# ---------------------------------------------------------------------------
# 图纸绘制
# ---------------------------------------------------------------------------

def draw_bead_pattern(grid, bead_size=28, output_path="bead_pattern.png"):
    """
    绘制拼豆图纸：
    - 每个格子画一个彩色圆点
    - 格子间有细网格线
    - 每 5 格加粗分隔线，方便数数
    - 右侧附带颜色图例（色号 + 豆子数量）
    """
    rows = len(grid)
    cols = len(grid[0]) if rows else 0

    # 颜色名称 -> RGB 映射
    color_map = {name: rgb for name, rgb in BEAD_COLORS}

    # 统计每种颜色的用量
    counter = Counter()
    for row in grid:
        counter.update(row)

    # 字体加载
    try:
        font = ImageFont.truetype("msyh.ttc", 12)
        font_small = ImageFont.truetype("msyh.ttc", 10)
        font_title = ImageFont.truetype("msyh.ttc", 14)
        font_bead = ImageFont.truetype("msyh.ttc", 7)
    except (IOError, OSError):
        try:
            font = ImageFont.truetype("arial.ttf", 12)
            font_small = ImageFont.truetype("arial.ttf", 10)
            font_title = ImageFont.truetype("arial.ttf", 14)
            font_bead = ImageFont.truetype("arial.ttf", 7)
        except (IOError, OSError):
            font = ImageFont.load_default()
            font_small = font
            font_title = font
            font_bead = font

    # ===== 画布尺寸计算 =====
    margin = 40
    grid_w = cols * bead_size
    grid_h = rows * bead_size

    # 右侧图例面板宽度
    legend_panel_w = 220
    legend_gap = 30  # 网格与图例之间的间距
    canvas_w = margin + grid_w + legend_gap + legend_panel_w + margin
    canvas_h = max(grid_h + 2 * margin, 200)

    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)

    bead_radius = bead_size // 2 - 2

    # ===== 绘制拼豆网格 =====
    for r in range(rows):
        for c in range(cols):
            cx = margin + c * bead_size + bead_size // 2
            cy = margin + r * bead_size + bead_size // 2
            bead_name = grid[r][c]
            rgb = color_map[bead_name]

            draw.ellipse(
                [cx - bead_radius, cy - bead_radius, cx + bead_radius, cy + bead_radius],
                fill=rgb,
                outline=(60, 60, 60),
                width=1,
            )

            # 在拼豆上标注色号（根据背景亮度选择文字颜色）
            brightness = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
            text_color = (255, 255, 255) if brightness < 128 else (30, 30, 30)
            # 计算文字居中偏移
            bbox = draw.textbbox((0, 0), bead_name, font=font_bead)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text(
                (cx - tw // 2, cy - th // 2 - 1),
                bead_name, fill=text_color, font=font_bead
            )

    # 画网格线
    for r in range(rows + 1):
        y = margin + r * bead_size
        width = 2 if r % 5 == 0 else 1
        color = (100, 100, 100) if r % 5 == 0 else (200, 200, 200)
        draw.line([(margin, y), (margin + grid_w, y)], fill=color, width=width)

    for c in range(cols + 1):
        x = margin + c * bead_size
        width = 2 if c % 5 == 0 else 1
        color = (100, 100, 100) if c % 5 == 0 else (200, 200, 200)
        draw.line([(x, margin), (x, margin + grid_h)], fill=color, width=width)

    # ===== 绘制右侧图例面板 =====
    legend_x = margin + grid_w + legend_gap
    legend_top = margin
    swatch_size = 18  # 色块大小
    line_height = 26  # 每行高度

    # 图例标题
    draw.text((legend_x, legend_top), "颜色图例", fill=(30, 30, 30), font=font_title)
    legend_top += 28

    # 分隔线
    draw.line(
        [(legend_x, legend_top), (legend_x + legend_panel_w - 10, legend_top)],
        fill=(180, 180, 180), width=1
    )
    legend_top += 8

    # 表头
    draw.text((legend_x + swatch_size + 6, legend_top), "色号", fill=(80, 80, 80), font=font_small)
    draw.text((legend_x + 80, legend_top), "数量", fill=(80, 80, 80), font=font_small)
    legend_top += 22

    # 按用量从多到少排序
    total_beads = sum(counter.values())
    for name, count in counter.most_common():
        rgb = color_map[name]
        pct = count / total_beads * 100

        # 画色块
        sx = legend_x + 2
        sy = legend_top + 2
        draw.rectangle(
            [sx, sy, sx + swatch_size, sy + swatch_size],
            fill=rgb, outline=(120, 120, 120), width=1
        )

        # 色号名称
        draw.text((legend_x + swatch_size + 6, legend_top + 1), name, fill=(30, 30, 30), font=font_small)

        # 数量 + 占比
        count_text = f"{count} ({pct:.1f}%)"
        draw.text((legend_x + 80, legend_top + 1), count_text, fill=(60, 60, 60), font=font_small)

        legend_top += line_height

    # 总计行
    legend_top += 4
    draw.line(
        [(legend_x, legend_top), (legend_x + legend_panel_w - 10, legend_top)],
        fill=(180, 180, 180), width=1
    )
    legend_top += 6
    draw.text((legend_x + swatch_size + 6, legend_top), "总计", fill=(30, 30, 30), font=font)
    draw.text((legend_x + 80, legend_top), f"{total_beads} 颗", fill=(30, 30, 30), font=font)

    # 图例面板边框
    draw.rectangle(
        [legend_x - 2, margin - 2, legend_x + legend_panel_w + 2, legend_top + 30],
        outline=(200, 200, 200), width=1
    )

    canvas.save(output_path)
    print(f"图纸已保存: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# 统计信息
# ---------------------------------------------------------------------------

def print_statistics(grid):
    """打印拼豆用料统计"""
    counter = Counter()
    for row in grid:
        counter.update(row)

    total = sum(counter.values())
    rows = len(grid)
    cols = len(grid[0]) if rows else 0

    print(f"\n{'='*40}")
    print(f"  拼豆图纸统计")
    print(f"{'='*40}")
    print(f"  图纸尺寸: {cols} × {rows} 颗拼豆")
    print(f"  总用量:   {total} 颗")
    print(f"  使用颜色: {len(counter)} 种")
    print(f"{'─'*40}")
    print(f"  {'颜色':<8} {'数量':>6}  {'占比':>6}")
    print(f"{'─'*40}")

    for name, count in counter.most_common():
        pct = count / total * 100
        print(f"  {name:<8} {count:>6}  {pct:>5.1f}%")

    print(f"{'='*40}\n")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def generate_bead_pattern(image_path, max_width=58, max_height=58, output_path=None):
    """
    主函数：从图片生成拼豆图纸

    参数:
        image_path:   输入图片路径
        max_width:    拼豆板最大宽度（颗数），默认 58（约两块 29 格拼豆板）
        max_height:   拼豆板最大高度（颗数），默认 58
        output_path:  输出图片路径，默认为 输入文件名_bead.png
    """
    image_path = Path(image_path)
    if not image_path.exists():
        print(f"错误: 找不到图片文件 {image_path}")
        return

    if output_path is None:
        output_path = str(image_path.parent / f"{image_path.stem}_bead.png")

    print(f"正在处理: {image_path}")
    print(f"最大拼豆板尺寸: {max_width} × {max_height}")

    # 1. 加载并缩放图片
    img = load_and_resize(str(image_path), max_width, max_height)
    print(f"缩放后网格尺寸: {img.size[0]} × {img.size[1]}")

    # 2. 像素 -> 拼豆颜色映射
    grid = image_to_bead_grid(img)

    # 3. 绘制图纸
    draw_bead_pattern(grid, bead_size=28, output_path=output_path)

    # 4. 打印统计
    print_statistics(grid)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="拼豆图纸生成器 - 将图片转换为拼豆图纸",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py photo.png
  python main.py photo.jpg -W 29 -H 29 -o output.png
        """,
    )
    parser.add_argument("image", help="输入图片路径")
    parser.add_argument("-W", "--max-width", type=int, default=58, help="最大宽度（颗数），默认 58")
    parser.add_argument("-H", "--max-height", type=int, default=58, help="最大高度（颗数），默认 58")
    parser.add_argument("-o", "--output", default=None, help="输出图片路径")

    args = parser.parse_args()
    generate_bead_pattern(args.image, args.max_width, args.max_height, args.output)


if __name__ == "__main__":
    main()
