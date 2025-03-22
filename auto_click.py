import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageTk, ImageGrab
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import win32gui
import win32con
import win32api
import ctypes
import cv2
import numpy as np
import pystray
from pystray import MenuItem as item

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        # 重新以管理员身份运行程序
        ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            sys.executable, 
            " ".join(sys.argv), 
            None, 
            1
        )
        sys.exit()

class AutoClickerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Claude Auto Clicker")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 获取默认图标
        default_icons = ["1.png", "2.png", "3.png", "allow_button.png"]
        self.icon_path = None
        for icon in default_icons:
            path = str(Path(__file__).parent / icon)
            if os.path.exists(path):
                self.icon_path = path
                break
                
        if not self.icon_path:
            self.icon_path = str(Path(__file__).parent / "1.png")
        
        # 设置应用图标
        if os.path.exists(self.icon_path):
            try:
                self.root.iconphoto(True, tk.PhotoImage(file=self.icon_path))
            except:
                pass
        
        # 设置整体样式
        style = ttk.Style()
        style.configure('TButton', padding=5)
        style.configure('TFrame', padding=5)
        
        # 添加窗口状态跟踪
        self.claude_window_visible = False
        self.claude_window_handle = None
        
        # 共享变量
        self.running = False
        self.pause = False  # 调试时暂停
        self.debug_mode = tk.BooleanVar(value=False)  # 调试模式
        self.target_images = []  # 存储目标图片路径列表
        self.confidence_var = tk.DoubleVar(value=0.7)  # 相似度阈值
        self.interval_var = tk.StringVar(value="0.2")  # 检测间隔
        self.click_method_var = tk.StringVar(value="auto")  # 点击方式
        
        # 调试状态
        self.last_screen = None
        self.last_match_result = None
        self.last_match_location = None
        self.last_match_value = 0
        self.debug_dir = Path(__file__).parent / "debug"
        self.debug_dir.mkdir(exist_ok=True)
        
        # 创建主框架
        self.create_main_ui()
        
        # 系统托盘支持
        self.setup_tray()
        
        # 添加默认图片
        for img_file in ["1.png", "2.png", "3.png"]:
            img_path = str(Path(__file__).parent / img_file)
            if os.path.exists(img_path):
                self.add_image(img_path)
                
        if not self.target_images and os.path.exists(self.icon_path):
            self.add_image(self.icon_path)
            
        self.log('程序已启动，点击"开始自动点击"按钮开始运行')
        
        # 设置窗口最小尺寸
        self.root.update()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

    def create_main_ui(self):
        """创建主界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 控制按钮框架
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 左侧控制区
        left_control = ttk.Frame(control_frame)
        left_control.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 开始/停止按钮
        self.toggle_button = ttk.Button(
            left_control,
            text="开始自动点击",
            command=self.toggle_clicking,
            width=15
        )
        self.toggle_button.pack(side=tk.LEFT, padx=5)
        
        # 调试模式复选框
        debug_check = ttk.Checkbutton(
            left_control,
            text="调试模式",
            variable=self.debug_mode,
            command=self.toggle_debug_mode
        )
        debug_check.pack(side=tk.LEFT, padx=5)
        
        # 调试控制按钮（默认隐藏）
        self.debug_frame = ttk.Frame(left_control)
        self.debug_frame.pack(side=tk.LEFT, padx=5)
        self.debug_frame.pack_forget()  # 默认隐藏
        
        # 单步执行按钮
        self.step_button = ttk.Button(
            self.debug_frame,
            text="单步执行",
            command=self.step_debug,
            width=10
        )
        self.step_button.pack(side=tk.LEFT, padx=2)
        
        # 保存调试信息按钮
        self.save_debug_button = ttk.Button(
            self.debug_frame,
            text="保存调试信息",
            command=self.save_debug_info,
            width=12
        )
        self.save_debug_button.pack(side=tk.LEFT, padx=2)
        
        # 右侧状态区
        right_control = ttk.Frame(control_frame)
        right_control.pack(side=tk.RIGHT)
        
        # 状态标签
        self.status_label = ttk.Label(
            right_control,
            text="状态: 等待Claude窗口",
            font=('Microsoft YaHei UI', 9),
            width=20,
            anchor='e'
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # 创建顶部面板 (Notebook)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 日志面板
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="运行日志")
        
        # 图片面板
        image_frame = ttk.Frame(notebook)
        notebook.add(image_frame, text="识别图片")
        
        # 设置面板
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="高级设置")
        
        # 调试面板
        self.debug_panel = ttk.Frame(notebook)
        notebook.add(self.debug_panel, text="调试面板")
        
        # 设置日志区域
        self.setup_log_area(log_frame)
        
        # 设置图片区域
        self.setup_image_area(image_frame)
        
        # 设置高级设置区域
        self.setup_settings_area(settings_frame)
        
        # 设置调试面板
        self.setup_debug_panel(self.debug_panel)
        
        # 底部提示
        tip_label = ttk.Label(
            main_frame,
            text="提示: 调试模式下可查看识别过程和点击位置，并进行单步调试",
            font=('Microsoft YaHei UI', 8),
            foreground='gray'
        )
        tip_label.pack(pady=(5, 0))

    def setup_log_area(self, parent):
        """设置日志区域"""
        # 日志标题行框架
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=(5, 2))
        
        # 日志标签
        log_label = ttk.Label(
            title_frame,
            text="运行日志:",
            font=('Microsoft YaHei UI', 9, 'bold')
        )
        log_label.pack(side=tk.LEFT)
        
        # 检测间隔设置
        interval_frame = ttk.Frame(title_frame)
        interval_frame.pack(side=tk.RIGHT)
        
        interval_label = ttk.Label(
            interval_frame,
            text="检测间隔(秒):",
            font=('Microsoft YaHei UI', 9)
        )
        interval_label.pack(side=tk.LEFT, padx=(0, 5))
        
        vcmd = (self.root.register(self.validate_interval), '%P')
        self.interval_entry = ttk.Entry(
            interval_frame,
            textvariable=self.interval_var,
            width=6,
            justify='center',
            validate='key',
            validatecommand=vcmd
        )
        self.interval_entry.pack(side=tk.LEFT)
        
        # 日志文本框
        self.log_area = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=('Consolas', 9),
            height=15
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def setup_image_area(self, parent):
        """设置图片区域"""
        # 图片操作框架
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # 添加图片按钮
        add_btn = ttk.Button(
            control_frame,
            text="添加图片",
            command=self.browse_image,
            width=15
        )
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # 删除所选图片按钮
        remove_btn = ttk.Button(
            control_frame,
            text="删除所选图片",
            command=self.remove_selected_image,
            width=15
        )
        remove_btn.pack(side=tk.LEFT, padx=5)
        
        # 测试所选图片按钮
        test_btn = ttk.Button(
            control_frame,
            text="测试所选图片",
            command=self.test_selected_image,
            width=15
        )
        test_btn.pack(side=tk.LEFT, padx=5)
        
        # 图片预览区域框架
        preview_frame = ttk.LabelFrame(parent, text="图片预览")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建画布用于显示图片
        self.canvas = tk.Canvas(preview_frame, bg='#f0f0f0')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # 创建内部框架来放置图片
        self.images_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.images_frame, anchor="nw")
        
        # 图片容器
        self.image_labels = []  # 存储图片标签
        self.image_tk_refs = []  # 保持对Tkinter PhotoImage对象的引用

    def setup_settings_area(self, parent):
        """设置高级设置区域"""
        # 创建设置框架
        settings_inner = ttk.Frame(parent, padding=10)
        settings_inner.pack(fill=tk.BOTH, expand=True)
        
        # 相似度设置
        similarity_frame = ttk.LabelFrame(settings_inner, text="图像识别设置", padding=8)
        similarity_frame.pack(fill=tk.X, pady=5)
        
        # 相似度阈值滑块
        similarity_label = ttk.Label(
            similarity_frame,
            text="识别相似度阈值:",
            font=('Microsoft YaHei UI', 9)
        )
        similarity_label.grid(row=0, column=0, sticky="w", pady=5)
        
        similarity_scale = ttk.Scale(
            similarity_frame,
            from_=0.1,
            to=1.0,
            variable=self.confidence_var,
            length=200,
            orient="horizontal"
        )
        similarity_scale.grid(row=0, column=1, padx=5, pady=5)
        
        self.similarity_value_label = ttk.Label(
            similarity_frame,
            text=f"{self.confidence_var.get():.1f}",
            width=5
        )
        self.similarity_value_label.grid(row=0, column=2, padx=5)
        
        # 更新相似度标签
        def update_similarity_label(*args):
            self.similarity_value_label.config(text=f"{self.confidence_var.get():.1f}")
        
        self.confidence_var.trace("w", update_similarity_label)
        
        # 匹配算法选择
        algorithm_label = ttk.Label(
            similarity_frame,
            text="匹配算法:",
            font=('Microsoft YaHei UI', 9)
        )
        algorithm_label.grid(row=1, column=0, sticky="w", pady=5)
        
        self.algorithm_var = tk.StringVar(value="TM_CCOEFF_NORMED")
        algorithm_combo = ttk.Combobox(
            similarity_frame,
            textvariable=self.algorithm_var,
            values=["TM_CCOEFF_NORMED", "TM_CCORR_NORMED", "TM_SQDIFF_NORMED"],
            width=20,
            state="readonly"
        )
        algorithm_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # 点击方式设置
        click_frame = ttk.LabelFrame(settings_inner, text="点击方式设置", padding=8)
        click_frame.pack(fill=tk.X, pady=5)
        
        # 点击方式单选按钮
        ttk.Radiobutton(
            click_frame,
            text="自动选择",
            variable=self.click_method_var,
            value="auto"
        ).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        ttk.Radiobutton(
            click_frame,
            text="前台点击(移动鼠标)",
            variable=self.click_method_var,
            value="foreground"
        ).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        ttk.Radiobutton(
            click_frame,
            text="后台点击(不移动鼠标)",
            variable=self.click_method_var,
            value="background"
        ).grid(row=2, column=0, sticky="w", padx=5, pady=2)
        
        # 点击次数和间隔设置
        click_detail_frame = ttk.Frame(click_frame)
        click_detail_frame.grid(row=3, column=0, sticky="w", padx=5, pady=5)
        
        # 点击次数
        clicks_label = ttk.Label(click_detail_frame, text="点击次数:")
        clicks_label.grid(row=0, column=0, sticky="w", padx=5)
        
        self.clicks_var = tk.IntVar(value=2)
        clicks_spin = ttk.Spinbox(
            click_detail_frame,
            from_=1,
            to=5,
            width=5,
            textvariable=self.clicks_var
        )
        clicks_spin.grid(row=0, column=1, padx=5)
        
        # 点击间隔
        click_interval_label = ttk.Label(click_detail_frame, text="点击间隔(秒):")
        click_interval_label.grid(row=0, column=2, sticky="w", padx=5)
        
        self.click_interval_var = tk.DoubleVar(value=0.05)
        click_interval_spin = ttk.Spinbox(
            click_detail_frame,
            from_=0.01,
            to=1.0,
            increment=0.01,
            width=5,
            textvariable=self.click_interval_var
        )
        click_interval_spin.grid(row=0, column=3, padx=5)
        
        # 点击偏移设置
        offset_frame = ttk.Frame(click_frame)
        offset_frame.grid(row=4, column=0, sticky="w", padx=5, pady=5)
        
        # X偏移
        x_offset_label = ttk.Label(offset_frame, text="X偏移:")
        x_offset_label.grid(row=0, column=0, sticky="w", padx=5)
        
        self.x_offset_var = tk.IntVar(value=0)
        x_offset_spin = ttk.Spinbox(
            offset_frame,
            from_=-50,
            to=50,
            width=5,
            textvariable=self.x_offset_var
        )
        x_offset_spin.grid(row=0, column=1, padx=5)
        
        # Y偏移
        y_offset_label = ttk.Label(offset_frame, text="Y偏移:")
        y_offset_label.grid(row=0, column=2, sticky="w", padx=5)
        
        self.y_offset_var = tk.IntVar(value=0)
        y_offset_spin = ttk.Spinbox(
            offset_frame,
            from_=-50,
            to=50,
            width=5,
            textvariable=self.y_offset_var
        )
        y_offset_spin.grid(row=0, column=3, padx=5)
        
        # 窗口设置
        window_frame = ttk.LabelFrame(settings_inner, text="窗口设置", padding=8)
        window_frame.pack(fill=tk.X, pady=5)
        
        # 窗口标题设置
        window_label = ttk.Label(
            window_frame,
            text="目标窗口标题:",
            font=('Microsoft YaHei UI', 9)
        )
        window_label.grid(row=0, column=0, sticky="w", pady=5)
        
        self.window_title_var = tk.StringVar(value="Claude")
        window_title_entry = ttk.Entry(
            window_frame,
            textvariable=self.window_title_var,
            width=25
        )
        window_title_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # 其他设置
        other_frame = ttk.LabelFrame(settings_inner, text="其他设置", padding=8)
        other_frame.pack(fill=tk.X, pady=5)
        
        # 启动时最小化到托盘
        self.start_minimized_var = tk.BooleanVar(value=False)
        start_minimized_check = ttk.Checkbutton(
            other_frame,
            text="启动时最小化到托盘",
            variable=self.start_minimized_var
        )
        start_minimized_check.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        # 自动启动操作
        self.auto_start_var = tk.BooleanVar(value=False)
        auto_start_check = ttk.Checkbutton(
            other_frame,
            text="启动时自动开始点击",
            variable=self.auto_start_var
        )
        auto_start_check.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        # 保存截图
        self.save_screenshots_var = tk.BooleanVar(value=False)
        save_screenshots_check = ttk.Checkbutton(
            other_frame,
            text="保存截图和匹配结果",
            variable=self.save_screenshots_var
        )
        save_screenshots_check.grid(row=2, column=0, sticky="w", padx=5, pady=2)

    def setup_debug_panel(self, parent):
        """设置调试面板"""
        debug_inner = ttk.Frame(parent, padding=10)
        debug_inner.pack(fill=tk.BOTH, expand=True)
        
        # 分割窗口
        paned = ttk.PanedWindow(debug_inner, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧 - 显示原始截图
        left_frame = ttk.LabelFrame(paned, text="屏幕截图")
        paned.add(left_frame, weight=1)
        
        self.screen_canvas = tk.Canvas(left_frame, bg='black')
        self.screen_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 右侧 - 显示匹配结果
        right_frame = ttk.LabelFrame(paned, text="匹配结果")
        paned.add(right_frame, weight=1)
        
        right_inner = ttk.Frame(right_frame)
        right_inner.pack(fill=tk.BOTH, expand=True)
        
        # 添加右侧的匹配结果图片
        self.result_canvas = tk.Canvas(right_inner, bg='black')
        self.result_canvas.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        # 匹配详情
        info_frame = ttk.Frame(right_inner)
        info_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        # 匹配信息标签
        self.match_info = ttk.Label(
            info_frame,
            text="等待匹配...",
            font=('Consolas', 9),
            justify='left'
        )
        self.match_info.pack(side=tk.LEFT, padx=5)
        
        # 底部控制栏
        control_frame = ttk.Frame(debug_inner)
        control_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        # 清除调试信息按钮
        clear_btn = ttk.Button(
            control_frame,
            text="清除调试信息",
            command=self.clear_debug_info,
            width=15
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 打开调试文件夹按钮
        open_folder_btn = ttk.Button(
            control_frame,
            text="打开调试文件夹",
            command=self.open_debug_folder,
            width=15
        )
        open_folder_btn.pack(side=tk.LEFT, padx=5)

    def toggle_debug_mode(self):
        """切换调试模式"""
        if self.debug_mode.get():
            self.debug_frame.pack(side=tk.LEFT, padx=5)
            self.log("已开启调试模式")
        else:
            self.debug_frame.pack_forget()
            self.log("已关闭调试模式")

    def step_debug(self):
        """单步执行调试"""
        if self.running and self.debug_mode.get():
            self.pause = False
            self.log("执行单步调试...")

    def save_debug_info(self):
        """保存当前调试信息"""
        if self.last_screen is not None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # 保存截图
            screen_path = self.debug_dir / f"screen_{timestamp}.png"
            cv2.imwrite(str(screen_path), self.last_screen)
            
            # 如果有匹配结果，保存匹配结果
            if self.last_match_result is not None:
                result_path = self.debug_dir / f"result_{timestamp}.png"
                cv2.imwrite(str(result_path), self.last_match_result)
                
            # 保存匹配信息
            info_path = self.debug_dir / f"info_{timestamp}.txt"
            with open(str(info_path), 'w', encoding='utf-8') as f:
                f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"目标窗口: {self.window_title_var.get()}\n")
                f.write(f"相似度阈值: {self.confidence_var.get():.2f}\n")
                f.write(f"匹配算法: {self.algorithm_var.get()}\n")
                f.write(f"匹配坐标: {self.last_match_location}\n")
                f.write(f"匹配值: {self.last_match_value:.4f}\n")
                f.write(f"点击方式: {self.click_method_var.get()}\n")
                f.write(f"点击偏移: X={self.x_offset_var.get()}, Y={self.y_offset_var.get()}\n")
                f.write(f"目标图片: {', '.join([os.path.basename(p) for p in self.target_images])}\n")
            
            self.log(f"调试信息已保存到 {self.debug_dir}")
            
        else:
            self.log("无调试信息可保存")

    def clear_debug_info(self):
        """清除调试面板信息"""
        self.screen_canvas.delete("all")
        self.result_canvas.delete("all")
        self.match_info.config(text="等待匹配...")
        self.last_screen = None
        self.last_match_result = None
        self.last_match_location = None
        self.last_match_value = 0
        self.log("已清除调试信息")

    def open_debug_folder(self):
        """打开调试文件夹"""
        try:
            os.startfile(str(self.debug_dir))
        except:
            self.log(f"无法打开文件夹: {self.debug_dir}")

    def on_canvas_configure(self, event):
        """调整画布大小"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # 调整内部框架的宽度以匹配画布宽度
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def setup_tray(self):
        """设置系统托盘"""
        try:
            # 尝试使用现有图标
            if os.path.exists(self.icon_path):
                tray_image = Image.open(self.icon_path)
            else:
                # 创建一个简单的默认图标
                tray_image = Image.new('RGB', (16, 16), color=(255, 0, 0))
                
            # 创建系统托盘图标
            menu = (
                item('显示', self.show_window),
                item('开始/停止', self.toggle_clicking),
                item('退出', self.quit_app)
            )
            
            self.tray_icon = pystray.Icon("Claude Auto Clicker", tray_image, "Claude Auto Clicker", menu)
            
            # 在单独的线程中运行系统托盘图标
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            # 如果创建托盘图标失败，记录错误但不中断程序
            print(f"创建系统托盘图标失败: {str(e)}")

    def show_window(self):
        """显示主窗口"""
        self.root.deiconify()
        self.root.state('normal')
        self.root.focus_force()

    def hide_window(self):
        """隐藏主窗口到托盘"""
        self.root.withdraw()

    def on_closing(self):
        """窗口关闭事件处理"""
        self.hide_window()

    def quit_app(self):
        """完全退出应用"""
        try:
            self.running = False
            self.tray_icon.stop()
        except:
            pass
        self.root.destroy()
        sys.exit(0)

    def add_image(self, image_path):
        """添加图片到预览区域"""
        if not os.path.exists(image_path):
            return
            
        # 将图片路径添加到目标列表
        if image_path not in self.target_images:
            self.target_images.append(image_path)
            
        # 创建图片框架
        img_frame = ttk.Frame(self.images_frame)
        img_frame.pack(fill=tk.X, pady=5, padx=5)
        
        try:
            # 打开图片并缩放
            img = Image.open(image_path)
            img.thumbnail((150, 150))
            img_tk = ImageTk.PhotoImage(img)
            
            # 保持引用
            self.image_tk_refs.append(img_tk)
            
            # 创建图片标签
            img_label = ttk.Label(img_frame, image=img_tk)
            img_label.image = img_tk  # 保持引用
            img_label.pack(side=tk.LEFT, padx=5, pady=5)
            
            # 创建图片信息标签
            info_frame = ttk.Frame(img_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
            
            # 文件名标签
            name_label = ttk.Label(
                info_frame,
                text=f"文件: {os.path.basename(image_path)}",
                font=('Microsoft YaHei UI', 9)
            )
            name_label.pack(anchor="w", pady=2)
            
            # 分辨率标签
            size_label = ttk.Label(
                info_frame,
                text=f"尺寸: {img.width}x{img.height}",
                font=('Microsoft YaHei UI', 9)
            )
            size_label.pack(anchor="w", pady=2)
            
            # 路径标签
            path_label = ttk.Label(
                info_frame,
                text=f"路径: {image_path}",
                font=('Microsoft YaHei UI', 8),
                foreground='gray'
            )
            path_label.pack(anchor="w", pady=2)
            
            # 点击切换选择状态
            def on_click(event, frame=img_frame, path=image_path):
                if frame.cget('style') == 'Selected.TFrame':
                    frame.configure(style='TFrame')
                else:
                    # 先清除所有选择
                    for f in self.images_frame.winfo_children():
                        f.configure(style='TFrame')
                    # 设置当前选择
                    style = ttk.Style()
                    style.configure('Selected.TFrame', background='#e1e1ff')
                    frame.configure(style='Selected.TFrame')
                    # 记录当前选择的图片
                    self.selected_image = path
            
            # 绑定点击事件
            img_label.bind("<Button-1>", on_click)
            info_frame.bind("<Button-1>", on_click)
            
            # 添加到标签列表
            self.image_labels.append((img_frame, image_path))
            
            # 更新滚动区域
            self.images_frame.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            self.log(f"已添加图片: {os.path.basename(image_path)}")
            
        except Exception as e:
            self.log(f"添加图片失败: {str(e)}")

    def browse_image(self):
        """浏览并添加图片"""
        file_paths = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[
                ("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
                ("所有文件", "*.*")
            ]
        )
        
        for file_path in file_paths:
            self.add_image(file_path)

    def remove_selected_image(self):
        """移除所选图片"""
        for frame, path in self.image_labels:
            if frame.cget('style') == 'Selected.TFrame':
                # 从列表中移除
                self.image_labels.remove((frame, path))
                if path in self.target_images:
                    self.target_images.remove(path)
                # 销毁框架
                frame.destroy()
                self.log(f"已移除图片: {os.path.basename(path)}")
                # 更新滚动区域
                self.images_frame.update_idletasks()
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
                return

    def test_selected_image(self):
        """测试所选图片的识别效果"""
        # 检查是否有选中的图片
        selected_image = None
        for frame, path in self.image_labels:
            if frame.cget('style') == 'Selected.TFrame':
                selected_image = path
                break
                
        if not selected_image:
            messagebox.showinfo("提示", "请先选择一张图片")
            return
            
        # 截取屏幕
        self.log(f"测试识别图片: {os.path.basename(selected_image)}")
        screen = self.capture_screen()
        
        if screen is not None:
            # 读取目标图片
            template = cv2.imread(selected_image)
            if template is None:
                self.log(f"错误: 无法读取图片 '{selected_image}'")
                return
                
            # 获取匹配算法
            match_method = self.get_match_method()
            
            # 模板匹配
            result = cv2.matchTemplate(screen, template, match_method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 判断匹配结果
            match_val = max_val if match_method != cv2.TM_SQDIFF_NORMED else 1.0 - min_val
            match_loc = max_loc if match_method != cv2.TM_SQDIFF_NORMED else min_loc
            
            # 更新调试信息
            self.last_screen = screen
            self.last_match_value = match_val
            self.last_match_location = match_loc
            
            # 在屏幕截图上标记匹配位置
            h, w = template.shape[:2]
            marked_screen = screen.copy()
            
            # 画一个绿色矩形框标记位置
            cv2.rectangle(
                marked_screen,
                (match_loc[0], match_loc[1]),
                (match_loc[0] + w, match_loc[1] + h),
                (0, 255, 0),
                2
            )
            
            # 在中心位置画一个红色十字
            center_x = match_loc[0] + w // 2
            center_y = match_loc[1] + h // 2
            cv2.drawMarker(
                marked_screen,
                (center_x, center_y),
                (0, 0, 255),
                cv2.MARKER_CROSS,
                20,
                2
            )
            
            # 保存匹配结果
            self.last_match_result = marked_screen
            
            # 更新调试面板
            self.update_debug_panel(screen, marked_screen, template)
            
            # 显示匹配结果
            if match_val >= self.confidence_var.get():
                self.log(f"匹配成功! 匹配度: {match_val:.2f}, 位置: {match_loc}")
                messagebox.showinfo("匹配成功", f"匹配度: {match_val:.2f}\n位置: {match_loc}")
            else:
                self.log(f"匹配失败! 匹配度: {match_val:.2f} < 阈值: {self.confidence_var.get():.2f}")
                messagebox.showinfo("匹配失败", f"匹配度: {match_val:.2f}\n阈值: {self.confidence_var.get():.2f}")
                
            # 保存调试信息
            if self.save_screenshots_var.get():
                self.save_debug_info()
        else:
            self.log("截图失败，无法测试")

    def update_debug_panel(self, screen, result_img, template=None):
        """更新调试面板显示"""
        try:
            # 更新屏幕截图
            screen_rgb = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)
            screen_pil = Image.fromarray(screen_rgb)
            
            # 缩放以适应画布
            canvas_width = self.screen_canvas.winfo_width()
            canvas_height = self.screen_canvas.winfo_height()
            
            if canvas_width > 10 and canvas_height > 10:  # 检查画布是否已初始化
                screen_pil.thumbnail((canvas_width, canvas_height))
                
            screen_tk = ImageTk.PhotoImage(screen_pil)
            
            # 清除画布并显示新图片
            self.screen_canvas.delete("all")
            self.screen_canvas.create_image(0, 0, anchor=tk.NW, image=screen_tk)
            self.screen_canvas.image = screen_tk  # 保持引用
            
            # 更新结果图片
            result_rgb = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
            result_pil = Image.fromarray(result_rgb)
            
            # 缩放以适应画布
            canvas_width = self.result_canvas.winfo_width()
            canvas_height = self.result_canvas.winfo_height()
            
            if canvas_width > 10 and canvas_height > 10:  # 检查画布是否已初始化
                result_pil.thumbnail((canvas_width, canvas_height))
                
            result_tk = ImageTk.PhotoImage(result_pil)
            
            # 清除画布并显示新图片
            self.result_canvas.delete("all")
            self.result_canvas.create_image(0, 0, anchor=tk.NW, image=result_tk)
            self.result_canvas.image = result_tk  # 保持引用
            
            # 更新匹配信息
            template_info = ""
            if template is not None:
                h, w = template.shape[:2]
                template_info = f"模板大小: {w}x{h}\n"
                
            match_info_text = (
                f"匹配算法: {self.algorithm_var.get()}\n"
                f"{template_info}"
                f"匹配位置: {self.last_match_location}\n"
                f"匹配值: {self.last_match_value:.4f}\n"
                f"相似度阈值: {self.confidence_var.get():.2f}\n"
                f"点击偏移: X={self.x_offset_var.get()}, Y={self.y_offset_var.get()}"
            )
            
            self.match_info.config(text=match_info_text)
            
        except Exception as e:
            self.log(f"更新调试面板失败: {str(e)}")

    def log(self, message):
        """添加日志"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_area.see(tk.END)
        except:
            pass

    def find_target_window(self):
        """查找目标窗口"""
        try:
            return win32gui.FindWindow(None, self.window_title_var.get())
        except:
            return None
            
    def is_window_foreground(self, hwnd):
        """检查窗口是否在前台"""
        if not hwnd:
            return False
        try:
            # 方法1: 检查是否是前台窗口
            foreground_window = win32gui.GetForegroundWindow()
            if foreground_window != hwnd:
                return False
                
            # 方法2: 检查窗口是否可见
            if not win32gui.IsWindowVisible(hwnd):
                return False
                
            # 方法3: 检查窗口状态
            if win32gui.IsIconic(hwnd):  # 是否最小化
                return False
                
            # 方法4: 获取窗口位置，检查是否在屏幕内
            try:
                rect = win32gui.GetWindowRect(hwnd)
                if rect[0] < -32000 or rect[1] < -32000:  # 检查是否在屏幕外
                    return False
            except:
                return False
                
            return True
        except:
            return False
            
    def is_target_window_active(self):
        """综合检查目标窗口是否激活"""
        window_title = self.window_title_var.get()
        hwnd = self.find_target_window()
        if not hwnd:
            return False, f"等待{window_title}窗口"
            
        if not win32gui.IsWindowVisible(hwnd):
            return False, f"{window_title}窗口未显示"
            
        if win32gui.IsIconic(hwnd):
            return False, f"{window_title}窗口已最小化"
            
        if win32gui.GetForegroundWindow() != hwnd:
            return False, f"{window_title}窗口未激活"
            
        try:
            rect = win32gui.GetWindowRect(hwnd)
            if rect[0] < -32000 or rect[1] < -32000:
                return False, f"{window_title}窗口在屏幕外"
        except:
            return False, "无法获取窗口位置"
            
        return True, f"{window_title}窗口已激活"

    def get_match_method(self):
        """获取匹配算法的OpenCV常量"""
        method_name = self.algorithm_var.get()
        if method_name == "TM_SQDIFF_NORMED":
            return cv2.TM_SQDIFF_NORMED
        elif method_name == "TM_CCORR_NORMED":
            return cv2.TM_CCORR_NORMED
        else:
            return cv2.TM_CCOEFF_NORMED  # 默认使用这个

    def locate_and_click_button(self):
        """定位并点击按钮"""
        try:
            # 检查是否有图片需要识别
            if not self.target_images:
                self.log("错误: 没有设置识别图片")
                return False
                
            # 调试模式暂停检查
            if self.debug_mode.get() and self.pause:
                time.sleep(0.1)  # 短暂休眠，减少CPU占用
                return False
                
            # 调试模式下设置暂停等待单步
            if self.debug_mode.get():
                self.pause = True
                
            # 截取屏幕
            screen = self.capture_screen()
            if screen is None:
                return False
                
            # 保存调试信息
            self.last_screen = screen
            
            # 获取匹配算法
            match_method = self.get_match_method()
            
            # 对每个目标图片进行匹配
            best_match = None
            best_val = -1 if match_method != cv2.TM_SQDIFF_NORMED else 2
            best_loc = None
            best_template = None
            best_img_path = None
            
            for img_path in self.target_images:
                if not os.path.exists(img_path):
                    self.log(f"错误: 找不到图片文件 '{img_path}'")
                    continue
                
                # 读取目标图片
                template = cv2.imread(img_path)
                if template is None:
                    self.log(f"错误: 无法读取图片 '{img_path}'")
                    continue
                
                # 模板匹配
                result = cv2.matchTemplate(screen, template, match_method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                # 根据匹配方法选择最佳匹配
                if match_method == cv2.TM_SQDIFF_NORMED:
                    # 对于SQDIFF方法，值越小表示匹配度越高
                    match_val = 1.0 - min_val  # 转换为0-1范围，值越大越好
                    match_loc = min_loc
                    if min_val < best_val:  # 注意这里是小于
                        best_match = result
                        best_val = min_val
                        best_loc = min_loc
                        best_template = template
                        best_img_path = img_path
                else:
                    # 对于其他方法，值越大表示匹配度越高
                    match_val = max_val
                    match_loc = max_loc
                    if max_val > best_val:  # 这里是大于
                        best_match = result
                        best_val = max_val
                        best_loc = max_loc
                        best_template = template
                        best_img_path = img_path
                
                # 在调试模式下记录匹配值
                if self.debug_mode.get():
                    self.log(f"图片 {os.path.basename(img_path)} 匹配度: {match_val:.4f}")
                    
            # 检查是否找到匹配
            if best_match is None:
                if self.debug_mode.get():
                    self.log("没有找到匹配")
                return False
                
            # 转换最终匹配值为0-1范围
            match_score = best_val if match_method != cv2.TM_SQDIFF_NORMED else 1.0 - best_val
            
            # 保存匹配位置和值
            self.last_match_location = best_loc
            self.last_match_value = match_score
            
            # 4. 检查匹配度是否超过阈值
            if match_score >= self.confidence_var.get():
                # 计算按钮中心坐标
                h, w = best_template.shape[:2]
                
                # 应用偏移
                center_x = best_loc[0] + w // 2 + self.x_offset_var.get()
                center_y = best_loc[1] + h // 2 + self.y_offset_var.get()
                
                # 在调试模式下显示匹配结果
                if self.debug_mode.get():
                    # 在匹配结果图像上标记位置
                    marked_screen = screen.copy()
                    
                    # 画一个绿色矩形框标记位置
                    cv2.rectangle(
                        marked_screen,
                        (best_loc[0], best_loc[1]),
                        (best_loc[0] + w, best_loc[1] + h),
                        (0, 255, 0),
                        2
                    )
                    
                    # 在中心位置画一个红色十字
                    cv2.drawMarker(
                        marked_screen,
                        (center_x, center_y),
                        (0, 0, 255),
                        cv2.MARKER_CROSS,
                        20,
                        2
                    )
                    
                    # 保存匹配结果
                    self.last_match_result = marked_screen
                    
                    # 更新调试面板
                    self.update_debug_panel(screen, marked_screen, best_template)
                    
                    # 显示匹配详情
                    self.log(f"找到图片: {os.path.basename(best_img_path)}")
                    self.log(f"匹配度: {match_score:.4f}, 位置: ({best_loc[0]}, {best_loc[1]}), 点击位置: ({center_x}, {center_y})")
                
                # 保存截图
                if self.save_screenshots_var.get():
                    self.save_debug_info()
                
                # 执行点击操作
                if not self.debug_mode.get() or not self.pause:
                    self.perform_click(center_x, center_y)
                    return True
                    
            return False
                
        except Exception as e:
            self.log(f"点击出错: {str(e)}")
            return False

    def capture_screen(self):
        """捕获屏幕"""
        try:
            # 只截取活动窗口区域，减少处理量
            hwnd = self.find_target_window()
            if hwnd and win32gui.IsWindowVisible(hwnd):
                try:
                    # 获取窗口位置
                    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                    # 截取窗口区域
                    screen = np.array(ImageGrab.grab((left, top, right, bottom)))
                    # 转换为OpenCV格式
                    return cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
                except Exception as e:
                    self.log(f"窗口区域截图失败: {str(e)}")
                    # 如果窗口区域获取失败，截取全屏
                    screen = np.array(ImageGrab.grab())
                    return cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
            else:
                # 如果窗口不可见，截取全屏
                screen = np.array(ImageGrab.grab())
                return cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
                
        except Exception as e:
            self.log(f"截屏错误: {str(e)}")
            return None

    def perform_click(self, x, y):
        """执行点击操作"""
        hwnd = self.find_target_window()
        if not hwnd:
            self.log("无法获取目标窗口句柄")
            return False
        
        click_method = self.click_method_var.get()
        
        # 判断点击方式
        if click_method == "auto":
            # 自动选择点击方式
            is_foreground = self.is_window_foreground(hwnd)
            click_method = "foreground" if is_foreground else "background"
        
        # 获取点击次数和间隔
        click_count = self.clicks_var.get()
        click_interval = self.click_interval_var.get()
        
        # 前台点击模式
        if click_method == "foreground":
            self.log("使用前台点击模式")
            # 保存当前鼠标位置
            original_x, original_y = win32api.GetCursorPos()
            
            try:
                # 获取窗口位置以计算相对坐标
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                
                # 移动鼠标并点击
                win32api.SetCursorPos((left + x, top + y))
                
                # 执行点击操作指定次数
                for i in range(click_count):
                    time.sleep(click_interval)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    time.sleep(click_interval)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                
                # 恢复鼠标位置
                win32api.SetCursorPos((original_x, original_y))
                self.log(f"完成前台点击操作 ({click_count}次)")
                return True
            except Exception as e:
                self.log(f"前台点击错误: {str(e)}")
                # 尝试恢复鼠标位置
                try:
                    win32api.SetCursorPos((original_x, original_y))
                except:
                    pass
                return False
        
        # 后台点击模式
        else:
            self.log("使用后台点击模式")
            try:
                # 获取窗口位置以计算相对坐标
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                
                # 将屏幕坐标转换为窗口客户区坐标
                client_point = win32gui.ScreenToClient(hwnd, (left + x, top + y))
                
                # 构造鼠标点击消息的参数
                lparam = win32api.MAKELONG(client_point[0], client_point[1])
                
                # 执行点击操作指定次数
                for i in range(click_count):
                    # 发送鼠标左键按下和释放消息
                    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
                    time.sleep(click_interval)
                    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
                    time.sleep(click_interval)
                
                self.log(f"完成后台点击操作 ({click_count}次)")
                return True
            except Exception as e:
                self.log(f"后台点击错误: {str(e)}")
                return False

    def clicking_thread(self):
        """点击线程"""
        last_status = ""
        
        while self.running:
            try:
                # 综合检查窗口状态
                is_active, status = self.is_target_window_active()
                
                # 状态发生变化时更新UI
                if status != last_status:
                    self.update_status(f"状态: {status}")
                    last_status = status
                
                # 只在窗口完全激活时执行图像识别
                if is_active:
                    if self.locate_and_click_button():
                        # 点击成功后等待较长时间
                        time.sleep(0.5)
                    else:
                        # 未找到按钮时使用设定的间隔
                        time.sleep(self.get_interval())
                else:
                    # 窗口未激活时使用较长的休眠时间
                    time.sleep(0.5)
                    
            except Exception as e:
                self.log(f"发生错误: {str(e)}")
                time.sleep(1)

    def validate_interval(self, value):
        """验证间隔输入"""
        if value == "":
            return True
        try:
            float_val = float(value)
            return float_val >= 0.1 and float_val <= 60.0
        except ValueError:
            return False

    def get_interval(self):
        """获取间隔值"""
        try:
            return float(self.interval_var.get())
        except ValueError:
            return 1.0

    def update_status(self, status):
        """更新状态标签"""
        try:
            self.status_label.config(text=status)
        except:
            pass

    def toggle_clicking(self):
        """切换点击状态"""
        if not self.running:
            # 验证间隔输入
            if not self.validate_interval(self.interval_var.get()):
                self.log("错误: 检测间隔必须在0.1到60秒之间")
                return
            
            # 验证是否有识别图片
            if not self.target_images:
                messagebox.showwarning("警告", "请先添加至少一张识别图片")
                return
                
            # 开始点击
            self.running = True
            self.toggle_button.config(text="停止自动点击")
            self.status_label.config(text="状态: 等待目标窗口")
            self.interval_entry.config(state='disabled')  # 禁用输入
            self.log(f"开始自动点击，检测间隔: {self.get_interval()}秒")
            threading.Thread(target=self.clicking_thread, daemon=True).start()
        else:
            # 停止点击
            self.running = False
            self.toggle_button.config(text="开始自动点击")
            self.status_label.config(text="状态: 已停止")
            self.interval_entry.config(state='normal')  # 启用输入
            self.log("停止自动点击")
            self.claude_window_visible = False
            self.claude_window_handle = None

    def run(self):
        """运行应用"""
        # 检查是否自动启动
        if self.auto_start_var.get():
            self.toggle_clicking()
            
        # 检查是否最小化启动
        if self.start_minimized_var.get():
            self.hide_window()
            
        self.root.mainloop()

if __name__ == "__main__":
    run_as_admin()  # 检查并提升权限
    app = AutoClickerGUI()
    app.run()
