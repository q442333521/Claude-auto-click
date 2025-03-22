import os
import sys
import time
import threading
import keyboard
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# 导入配置
from config import Config

# 导入面板组件
from gui.panels.log_panel import LogPanel
from gui.panels.image_panel import ImagePanel
from gui.panels.settings_panel import SettingsPanel
from gui.panels.debug_panel import DebugPanel

# 导入功能模块
from core.detector import ImageDetector
from core.clicker import MouseClicker
from core.tray_handler import TrayIconHandler

class AutoClickerGUI:
    def __init__(self):
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("Claude Auto Clicker")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 初始化配置
        self.config = Config()
        
        # 设置应用图标
        if os.path.exists(self.config.icon_path):
            try:
                self.root.iconphoto(True, tk.PhotoImage(file=self.config.icon_path))
            except:
                pass
        
        # 设置整体样式
        style = ttk.Style()
        style.configure('TButton', padding=5)
        style.configure('TFrame', padding=5)
        
        # 共享变量
        self.running = False
        self.pause = False  # 调试时暂停
        self.debug_mode = tk.BooleanVar(value=False)  # 调试模式
        self.interval_var = tk.StringVar(value=str(self.config.interval))  # 检测间隔
        self.ignore_window_state = tk.BooleanVar(value=True)  # 忽略窗口状态
        
        # 调试状态
        self.debug_dir = Path(__file__).parent.parent / "debug"
        self.debug_dir.mkdir(exist_ok=True)
        
        # 创建主框架
        self.create_main_ui()
        
        # 系统托盘支持
        self.setup_tray()
        
        # 创建功能组件
        self.detector = ImageDetector(self.config, self.log)
        self.clicker = MouseClicker(self.log)
        
        # 设置ESC键停止监听
        keyboard.add_hotkey('esc', self.force_stop)
        
        # 设置窗口最小尺寸
        self.root.update()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())
        
        # 初始日志
        self.log('程序已启动，点击"开始自动点击"按钮开始运行')

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
        
        # 忽略窗口状态复选框
        ignore_window_check = ttk.Checkbutton(
            left_control,
            text="忽略窗口状态",
            variable=self.ignore_window_state
        )
        ignore_window_check.pack(side=tk.LEFT, padx=5)
        
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
        debug_panel_frame = ttk.Frame(notebook)
        notebook.add(debug_panel_frame, text="调试面板")
        
        # 设置日志区域
        self.log_panel = LogPanel(log_frame, self.interval_var)
        
        # 设置图片区域
        self.image_panel = ImagePanel(image_frame, self.config, self.log)
        
        # 设置高级设置区域
        self.settings_panel = SettingsPanel(settings_frame, self.config)
        
        # 设置调试面板
        self.debug_panel = DebugPanel(debug_panel_frame, self.debug_dir, self.log)
        
        # 底部提示
        tip_label = ttk.Label(
            main_frame,
            text="提示: 按ESC键可强制停止点击，调试模式下可查看识别过程和点击位置",
            font=('Microsoft YaHei UI', 8),
            foreground='gray'
        )
        tip_label.pack(pady=(5, 0))
        
        # 添加默认图片
        self.image_panel.add_default_images()

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
        self.detector.save_debug_info()

    def force_stop(self):
        """强制停止点击"""
        if self.running:
            self.running = False
            self.toggle_button.config(text="开始自动点击")
            self.status_label.config(text="状态: 已强制停止")
            self.log_panel.enable_interval_entry(True)
            self.log("强制停止点击 (ESC键被按下)")

    def log(self, message):
        """添加日志"""
        try:
            self.log_panel.log(message)
        except:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")

    def setup_tray(self):
        """设置系统托盘"""
        self.tray_handler = TrayIconHandler(
            self.config.icon_path,
            "Claude Auto Clicker",
            self.show_window,
            self.toggle_clicking,
            self.quit_app
        )
        self.tray_handler.setup_tray()

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
            # 移除键盘钩子
            keyboard.unhook_all()
            if hasattr(self, 'tray_handler'):
                self.tray_handler.stop()
        except:
            pass
        self.root.destroy()
        sys.exit(0)

    def toggle_clicking(self):
        """切换点击状态"""
        # 从面板更新配置
        self.settings_panel.update_config()
        
        if not self.running:
            # 验证间隔输入
            try:
                interval = float(self.interval_var.get())
                if interval < 0.1 or interval > 60.0:
                    self.log("错误: 检测间隔必须在0.1到60秒之间")
                    return
                self.config.interval = interval
            except ValueError:
                self.log("错误: 检测间隔必须是有效的数字")
                return
            
            # 验证是否有识别图片
            target_images = self.image_panel.get_target_images()
            if not target_images:
                messagebox.showwarning("警告", "请先添加至少一张识别图片")
                return
                
            # 更新调试面板参数
            self.debug_panel.set_match_params(
                self.config.algorithm,
                self.config.confidence_threshold,
                self.config.x_offset,
                self.config.y_offset
            )
                
            # 开始点击
            self.running = True
            self.toggle_button.config(text="停止自动点击")
            self.status_label.config(text="状态: 等待目标窗口")
            self.log_panel.enable_interval_entry(False)  # 禁用输入
            self.log(f"开始自动点击，检测间隔: {self.config.interval}秒")
            threading.Thread(target=self.clicking_thread, daemon=True).start()
        else:
            # 停止点击
            self.running = False
            self.toggle_button.config(text="开始自动点击")
            self.status_label.config(text="状态: 已停止")
            self.log_panel.enable_interval_entry(True)  # 启用输入
            self.log("停止自动点击")

    def clicking_thread(self):
        """点击线程"""
        last_status = ""
        
        while self.running:
            try:
                # 获取目标图片
                target_images = self.image_panel.get_target_images()
                
                # 检查窗口状态
                from utils.window_utils import check_window_status
                is_active, status = check_window_status(self.config.window_title)
                
                # 状态发生变化时更新UI
                if status != last_status:
                    self.update_status(f"状态: {status}")
                    last_status = status
                
                # 检查是否忽略窗口状态
                if self.ignore_window_state.get() or is_active:
                    # 定位目标
                    result = self.detector.locate_target(
                        target_images, 
                        self.debug_mode.get(), 
                        self.pause
                    )
                    
                    if result and result[0]:
                        click_pos, hwnd = result
                        
                        # 执行点击操作
                        if not self.debug_mode.get() or not self.pause:
                            self.clicker.perform_click(
                                click_pos[0], 
                                click_pos[1], 
                                hwnd, 
                                self.config.click_method, 
                                self.config.click_count, 
                                self.config.click_interval
                            )
                            # 点击成功后等待较长时间
                            time.sleep(0.5)
                        else:
                            # 调试模式下等待用户单步操作
                            time.sleep(0.1)
                    else:
                        # 未找到按钮时使用设定的间隔
                        time.sleep(self.config.interval)
                else:
                    # 窗口未激活时使用较长的休眠时间
                    time.sleep(0.5)
                    
            except Exception as e:
                self.log(f"发生错误: {str(e)}")
                time.sleep(1)

    def update_status(self, status):
        """更新状态标签"""
        try:
            self.status_label.config(text=status)
        except:
            pass

    def run(self):
        """运行应用"""
        # 检查是否自动启动
        if self.config.auto_start:
            self.toggle_clicking()
            
        # 检查是否最小化启动
        if self.config.start_minimized:
            self.hide_window()
            
        self.root.mainloop()
