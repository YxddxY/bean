"""
拼豆图纸生成器 - 现代化图形界面
基于 customtkinter，圆角卡片风格。
"""

import sys
import threading
from pathlib import Path
from collections import Counter

import customtkinter as ctk
import windnd
from PIL import Image, ImageTk

from main import load_and_resize, image_to_bead_grid, draw_bead_pattern

# 支持的图片扩展名
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff", ".tif"}

# 主题配色
COLORS = {
    "bg": "#1e1e2e",
    "card": "#2a2a3d",
    "card_border": "#3a3a52",
    "accent": "#7c6ff7",
    "accent_hover": "#6a5ce7",
    "success": "#4ade80",
    "text": "#e0e0e0",
    "text_dim": "#8888aa",
    "input_bg": "#1a1a2e",
    "input_border": "#3a3a55",
}


class BeadPatternGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("拼豆图纸生成器")
        self.root.geometry("1060x740")
        self.root.minsize(900, 620)

        # customtkinter 主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.image_path = None
        self.output_path = None
        self.preview_image = None

        self._build_ui()
        self._setup_drag_drop()

    # ==================================================================
    #  UI 构建
    # ==================================================================

    def _build_ui(self):
        # 主容器 — 带内边距
        main = ctk.CTkFrame(self.root, fg_color=COLORS["bg"], corner_radius=0, border_width=0)
        main.pack(fill="both", expand=True)

        # ---------- 顶部标题栏 ----------
        header = ctk.CTkFrame(main, fg_color=COLORS["bg"], corner_radius=0, border_width=0)
        header.pack(fill="x", padx=0, pady=(12, 4))

        ctk.CTkLabel(
            header, text="  拼豆图纸生成器",
            font=ctk.CTkFont("Microsoft YaHei UI", 22, weight="bold"),
            text_color=COLORS["text"]
        ).pack(side="left", padx=20)

        ctk.CTkLabel(
            header, text="Perler Bead Pattern Generator",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=COLORS["text_dim"]
        ).pack(side="left", pady=8)

        # ---------- 卡片：文件选择 ----------
        file_card = self._card(main, "文件选择")
        file_card.pack(fill="x", padx=20, pady=(8, 6))

        row1 = ctk.CTkFrame(file_card, fg_color="transparent", corner_radius=0)
        row1.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(row1, text="输入图片", width=80, anchor="w",
                      font=ctk.CTkFont("Microsoft YaHei UI", 13), text_color=COLORS["text_dim"]).pack(side="left")
        self.input_entry = ctk.CTkEntry(row1, placeholder_text="拖入图片或点击浏览...",
                                         font=ctk.CTkFont("Microsoft YaHei UI", 13),
                                         fg_color=COLORS["input_bg"], border_color=COLORS["input_border"],
                                         border_width=1, corner_radius=8, height=36)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(12, 8))
        self.btn_browse_in = ctk.CTkButton(row1, text="浏览", width=80, height=36, corner_radius=8,
                                            font=ctk.CTkFont("Microsoft YaHei UI", 13),
                                            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                            command=self._browse_input)
        self.btn_browse_in.pack(side="left")

        row2 = ctk.CTkFrame(file_card, fg_color="transparent", corner_radius=0)
        row2.pack(fill="x", padx=16, pady=(6, 12))

        ctk.CTkLabel(row2, text="输出路径", width=80, anchor="w",
                      font=ctk.CTkFont("Microsoft YaHei UI", 13), text_color=COLORS["text_dim"]).pack(side="left")
        self.output_entry = ctk.CTkEntry(row2, placeholder_text="自动生成（可修改）",
                                          font=ctk.CTkFont("Microsoft YaHei UI", 13),
                                          fg_color=COLORS["input_bg"], border_color=COLORS["input_border"],
                                          border_width=1, corner_radius=8, height=36)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(12, 8))
        self.btn_browse_out = ctk.CTkButton(row2, text="浏览", width=80, height=36, corner_radius=8,
                                             font=ctk.CTkFont("Microsoft YaHei UI", 13),
                                             fg_color=COLORS["card_border"], hover_color=COLORS["accent"],
                                             command=self._browse_output)
        self.btn_browse_out.pack(side="left")

        # ---------- 卡片：参数设置 ----------
        param_card = self._card(main, "参数设置")
        param_card.pack(fill="x", padx=20, pady=6)

        param_row = ctk.CTkFrame(param_card, fg_color="transparent", corner_radius=0)
        param_row.pack(fill="x", padx=16, pady=12)

        self._param_field(param_row, "宽度 (颗)", "58", 70)
        self._param_field(param_row, "高度 (颗)", "58", 70)
        self._param_field(param_row, "格子大小 (px)", "28", 90)

        # 生成按钮
        self.generate_btn = ctk.CTkButton(
            param_row, text="  生成图纸  ", height=40, corner_radius=10,
            font=ctk.CTkFont("Microsoft YaHei UI", 15, weight="bold"),
            fg_color=COLORS["success"], hover_color="#38c96e",
            text_color="#111111",
            command=self._on_generate
        )
        self.generate_btn.pack(side="right", padx=(16, 0))

        # 进度条
        self.progress = ctk.CTkProgressBar(param_row, height=8, corner_radius=4,
                                            fg_color=COLORS["input_bg"], progress_color=COLORS["accent"])
        self.progress.pack(side="right", padx=(0, 16))
        self.progress.set(0)

        # ---------- 主内容区 ----------
        content = ctk.CTkFrame(main, fg_color=COLORS["bg"], corner_radius=0, border_width=0)
        content.pack(fill="both", expand=True, padx=20, pady=(6, 12))

        # 左侧：预览
        preview_card = self._card(content, "图纸预览")
        preview_card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.canvas_frame = ctk.CTkFrame(preview_card, fg_color=COLORS["input_bg"], corner_radius=10, border_width=0)
        self.canvas_frame.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        self.canvas = ctk.CTkCanvas(self.canvas_frame, bg=COLORS["input_bg"],
                                     highlightthickness=0, borderwidth=0)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)

        # 拖放提示
        self.drop_hint = ctk.CTkLabel(
            self.canvas,
            text="将图片拖放到此处\n或点击上方「浏览」选择文件",
            font=ctk.CTkFont("Microsoft YaHei UI", 16),
            text_color=COLORS["text_dim"],
            bg_color=COLORS["input_bg"]
        )

        # 右侧：统计
        stats_card = self._card(content, "用料统计", width=300)
        stats_card.pack(side="right", fill="y", padx=(8, 0))
        stats_card.pack_propagate(False)

        self.stats_text = ctk.CTkTextbox(
            stats_card, font=ctk.CTkFont("Cascadia Code", 12),
            fg_color=COLORS["input_bg"], border_width=0, corner_radius=8,
            text_color=COLORS["text"], activate_scrollbars=True
        )
        self.stats_text.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        self.stats_text.configure(state="disabled")

        # ---------- 底部状态栏 ----------
        self.status_bar = ctk.CTkFrame(main, fg_color=COLORS["card"], corner_radius=0, border_width=0, height=32)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            self.status_bar, text="  就绪", anchor="w",
            font=ctk.CTkFont("Microsoft YaHei UI", 12),
            text_color=COLORS["text_dim"]
        )
        self.status_label.pack(fill="x", padx=16)

    # ==================================================================
    #  辅助组件
    # ==================================================================

    def _card(self, parent, title, width=None):
        """创建带标题的卡片容器"""
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12,
                            border_width=1, border_color=COLORS["card_border"])
        if width:
            card.configure(width=width)

        header = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0, border_width=0)
        header.pack(fill="x", padx=16, pady=(12, 0))

        # 标题前的装饰条
        bar = ctk.CTkFrame(header, fg_color=COLORS["accent"], width=4, height=18, corner_radius=2)
        bar.pack(side="left", padx=(0, 8))
        bar.pack_propagate(False)

        ctk.CTkLabel(header, text=title, font=ctk.CTkFont("Microsoft YaHei UI", 14, weight="bold"),
                      text_color=COLORS["text"]).pack(side="left")
        return card

    def _param_field(self, parent, label, default, entry_width):
        """创建参数输入字段"""
        grp = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        grp.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(grp, text=label, font=ctk.CTkFont("Microsoft YaHei UI", 13),
                      text_color=COLORS["text_dim"]).pack(anchor="w", pady=(0, 4))
        entry = ctk.CTkEntry(grp, width=entry_width, height=36, corner_radius=8,
                              font=ctk.CTkFont("Microsoft YaHei UI", 14),
                              fg_color=COLORS["input_bg"], border_color=COLORS["input_border"],
                              border_width=1)
        entry.insert(0, default)
        entry.pack()
        return entry

    # ==================================================================
    #  拖放支持
    # ==================================================================

    def _setup_drag_drop(self):
        windnd.hook_dropfiles(self.root, func=self._on_drop_files)

    def _on_drop_files(self, file_list):
        for f in file_list:
            if isinstance(f, bytes):
                try:
                    f = f.decode("gbk")
                except UnicodeDecodeError:
                    f = f.decode("utf-8", errors="replace")
            path = Path(f)
            if path.suffix.lower() in IMAGE_EXTS:
                self._load_dropped_image(str(path))
                return
            try:
                Image.open(str(path))
                self._load_dropped_image(str(path))
                return
            except Exception:
                continue
        self._show_msg("不支持的文件", "拖放的文件不是有效的图片格式！", "warning")

    def _load_dropped_image(self, path):
        self.image_path = path
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, path)
        if not self.output_entry.get():
            default_out = str(Path(path).parent / f"{Path(path).stem}_bead.png")
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, default_out)
        self._status(f"已加载图片: {Path(path).name}")
        self._show_source_preview(path)

    def _show_source_preview(self, image_path):
        try:
            img = Image.open(image_path)
            cw, ch = self._canvas_size()
            img.thumbnail((cw - 20, ch - 20), Image.LANCZOS)
            self.preview_image = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self._hide_drop_hint()
            self.canvas.create_image(cw // 2, ch // 2, image=self.preview_image, anchor="center")
        except Exception as e:
            self._status(f"预览失败: {e}")

    def _show_drop_hint(self):
        try:
            cw, ch = self._canvas_size()
            if cw > 100 and ch > 100:
                self.canvas.create_window(cw // 2, ch // 2, window=self.drop_hint, tags="drop_hint")
        except Exception:
            pass

    def _hide_drop_hint(self):
        try:
            self.canvas.delete("drop_hint")
        except Exception:
            pass

    # ==================================================================
    #  事件处理
    # ==================================================================

    def _browse_input(self):
        path = ctk.filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("所有文件", "*.*")]
        )
        if path:
            self._load_dropped_image(path)

    def _browse_output(self):
        path = ctk.filedialog.asksaveasfilename(
            title="保存图纸", defaultextension=".png",
            filetypes=[("PNG 图片", "*.png"), ("所有文件", "*.*")]
        )
        if path:
            self.output_path = path
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, path)

    def _on_generate(self):
        img_path = self.input_entry.get().strip()
        if not img_path or not Path(img_path).exists():
            self._show_msg("错误", "请先选择有效的输入图片！", "error")
            return
        try:
            max_w = int(self.width_entry.winfo_children()[1].get())
            max_h = int(self.height_entry.winfo_children()[1].get())
            bead_size = int(self.bead_size_entry.winfo_children()[1].get())
        except (ValueError, IndexError):
            self._show_msg("错误", "参数必须为整数！", "error")
            return

        output = self.output_entry.get().strip() or None

        self.generate_btn.configure(state="disabled")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self._status("正在生成图纸...")
        self.stats_text.configure(state="normal")
        self.stats_text.delete("1.0", "end")
        self.stats_text.configure(state="disabled")
        self.canvas.delete("all")

        thread = threading.Thread(target=self._generate_worker,
                                  args=(img_path, max_w, max_h, bead_size, output), daemon=True)
        thread.start()

    def _generate_worker(self, img_path, max_w, max_h, bead_size, output):
        try:
            img = load_and_resize(img_path, max_w, max_h)
            grid = image_to_bead_grid(img)
            if output is None:
                output = str(Path(img_path).parent / f"{Path(img_path).stem}_bead.png")
            draw_bead_pattern(grid, bead_size=bead_size, output_path=output)

            counter = Counter()
            for row in grid:
                counter.update(row)
            total = sum(counter.values())
            rows, cols = len(grid), len(grid[0]) if grid else 0

            lines = [
                f"图纸尺寸  {cols} x {rows} 颗",
                f"总用量    {total} 颗",
                f"使用颜色  {len(counter)} 种",
                "",
            ]
            for name, count in counter.most_common():
                pct = count / total * 100
                lines.append(f"  {name:<8} {count:>6}  ({pct:.1f}%)")

            self.root.after(0, self._on_complete, output, "\n".join(lines))
        except Exception as e:
            self.root.after(0, self._on_error, str(e))

    def _on_complete(self, output_path, stats_text):
        self.progress.stop()
        self.generate_btn.configure(state="normal")
        self._status(f"完成！已保存: {Path(output_path).name}")

        self.stats_text.configure(state="normal")
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", stats_text)
        self.stats_text.configure(state="disabled")

        self._hide_drop_hint()
        self._show_preview(output_path)

    def _on_error(self, error_msg):
        self.progress.stop()
        self.generate_btn.configure(state="normal")
        self._status("生成失败")
        self._show_msg("生成失败", error_msg, "error")

    def _show_preview(self, image_path):
        try:
            img = Image.open(image_path)
            cw, ch = self._canvas_size()
            img.thumbnail((cw - 20, ch - 20), Image.LANCZOS)
            self.preview_image = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(cw // 2, ch // 2, image=self.preview_image, anchor="center")
        except Exception as e:
            self._status(f"预览失败: {e}")

    # ==================================================================
    #  工具方法
    # ==================================================================

    def _canvas_size(self):
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        return (max(cw, 400), max(ch, 300))

    def _status(self, text):
        self.status_label.configure(text=f"  {text}")

    def _show_msg(self, title, msg, kind="info"):
        if kind == "error":
            ctk.CTkMessagebox(title=title, message=msg, icon="cancel", option_1="确定")
        elif kind == "warning":
            ctk.CTkMessagebox(title=title, message=msg, icon="warning", option_1="确定")
        else:
            ctk.CTkMessagebox(title=title, message=msg, icon="info", option_1="确定")


def main():
    root = ctk.CTk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = BeadPatternGUI(root)
    if len(sys.argv) > 1:
        img_path = sys.argv[1]
        if Path(img_path).exists():
            root.update_idletasks()
            app._load_dropped_image(img_path)
    root.mainloop()


if __name__ == "__main__":
    main()
