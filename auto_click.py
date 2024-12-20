import pyautogui
import time
import sys
import keyboard
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from datetime import datetime
import win32gui
import win32con

# 设置pyautogui的安全性，防止鼠标失控
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 1.0

class AutoClickerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Claude Auto Clicker")
        self.root.geometry("500x400")
        self.root.resizable(True, True)
        
        # 设置整体样式
        style = ttk.Style()
        style.configure('TButton', padding=5)
        style.configure('TFrame', padding=5)
        
        # 添加窗口状态跟踪
        self.claude_window_visible = False
        self.claude_window_handle = None
        
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
            width=20
        )
        self.toggle_button.pack(side=tk.LEFT, padx=5)
        
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
        
        # 日志区域框架
        log_area_frame = ttk.Frame(main_frame)
        log_area_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志标题行框架
        title_frame = ttk.Frame(log_area_frame)
        title_frame.pack(fill=tk.X, pady=(0, 2))
        
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
        
        self.interval_var = tk.StringVar(value="1.0")
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
            log_area_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            height=15
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        # 右侧设置区
        settings_frame = ttk.LabelFrame(
            main_frame,
            text="设置",
            padding=8,
            width=150  # 固定宽度
        )
        settings_frame.pack(side=tk.RIGHT, fill=tk.Y)
        settings_frame.pack_propagate(False)  # 禁止自动收缩
        
        # 底部提示
        tip_label = ttk.Label(
            main_frame,
            text="提示: 将鼠标移动到屏幕左上角可紧急停止程序",
            font=('Microsoft YaHei UI', 8),
            foreground='gray'
        )
        tip_label.pack(pady=(5, 0))
        
        self.running = False
        self.log('程序已启动，点击"开始自动点击"按钮开始运行')
        
        # 设置窗口最小尺寸
        self.root.update()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)

    def find_claude_window(self):
        """查找Claude窗口"""
        try:
            return win32gui.FindWindow(None, "Claude")
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
            
    def is_claude_window_active(self):
        """综合检查Claude窗口是否激活"""
        hwnd = self.find_claude_window()
        if not hwnd:
            return False, "等待Claude窗口"
            
        if not win32gui.IsWindowVisible(hwnd):
            return False, "Claude窗口未显示"
            
        if win32gui.IsIconic(hwnd):
            return False, "Claude窗口已最小化"
            
        if win32gui.GetForegroundWindow() != hwnd:
            return False, "Claude窗口未激活"
            
        try:
            rect = win32gui.GetWindowRect(hwnd)
            if rect[0] < -32000 or rect[1] < -32000:
                return False, "Claude窗口在屏幕外"
        except:
            return False, "无法获取窗口位置"
            
        return True, "Claude窗口已激活"

    def locate_and_click_button(self):
        try:
            # 确保图片文件存在
            button_image = str(Path(__file__).parent / 'allow_button.png')
            if not Path(button_image).exists():
                self.log(f"错误: 找不到图片文件 'allow_button.png'")
                return False
            
            try:
                # 使用较低的置信度以提高识别速度
                button_location = pyautogui.locateOnScreen(
                    button_image,
                    confidence=0.8,
                    grayscale=True
                )
            except pyautogui.ImageNotFoundException:
                return False  # 正常未找到图片，不记录错误
            except Exception as e:
                self.log(f"图像识别出错: {str(e)}")
                return False
            
            if button_location:
                try:
                    # 获取按钮中心坐标
                    x, y = pyautogui.center(button_location)
                    self.log(f"找到Allow按钮，位置: ({x}, {y})")
                    
                    # 保存当前鼠标位置
                    original_x, original_y = pyautogui.position()
                    
                    # 移动到按钮位置
                    pyautogui.moveTo(x, y, duration=0.2)
                    
                    # 确认鼠标已经移动到位
                    current_x, current_y = pyautogui.position()
                    if abs(current_x - x) > 5 or abs(current_y - y) > 5:
                        self.log(f"错误: 鼠标未能移动到正确位置 (目标:{x},{y}, 实际:{current_x},{current_y})")
                        return False
                    
                    # 执行点击
                    pyautogui.click(x, y)  # 直接在指定位置点击
                    self.log("点击执行完成")
                    
                    # 点击后短暂休眠，避免重复点击
                    time.sleep(0.5)
                    
                    # 恢复鼠标位置
                    pyautogui.moveTo(original_x, original_y, duration=0.2)
                    return True
                    
                except pyautogui.FailSafeException:
                    self.log("触发了PyAutoGUI的安全机制，请将鼠标移开屏幕左上角")
                    return False
                except Exception as e:
                    self.log(f"鼠标操作出错: {str(e)}")
                    return False
            
            return False
                
        except Exception as e:
            self.log(f"点击过程出错: {str(e) if str(e) else e.__class__.__name__}")
            return False

    def clicking_thread(self):
        last_status = ""
        error_count = 0  # 添加错误计数
        
        while self.running:
            try:
                # 综合检查窗口状态
                is_active, status = self.is_claude_window_active()
                
                # 状态发生变化时更新UI
                if status != last_status:
                    self.update_status(f"状态: {status}")
                    last_status = status
                    error_count = 0  # 重置错误计数
                
                # 只在窗口完全激活时执行图像识别
                if is_active:
                    try:
                        if self.locate_and_click_button():
                            error_count = 0  # 成功时重置错误计数
                            time.sleep(1.0)
                        else:
                            time.sleep(self.get_interval())
                    except Exception as e:
                        error_count += 1
                        if error_count >= 3:  # 连续错误超过3次
                            self.log(f"连续发生{error_count}次错误，暂停5秒")
                            time.sleep(5)
                            error_count = 0
                else:
                    error_count = 0  # 窗口未激活时重置错误计数
                    time.sleep(0.5)
                    
            except Exception as e:
                self.log(f"主循环错误: {str(e)}")
                time.sleep(1)
                
    def validate_interval(self, value):
        if value == "":
            return True
        try:
            float_val = float(value)
            return float_val >= 0.1 and float_val <= 60.0
        except ValueError:
            return False

    def get_interval(self):
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
        if not self.running:
            # 验证间隔输入
            if not self.validate_interval(self.interval_var.get()):
                self.log("错误: 检测间隔必须在0.1到60秒之间")
                return
                
            # 开始点击
            self.running = True
            self.toggle_button.config(text="停止自动点击")
            self.status_label.config(text="状态: 等待Claude窗口")
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
        self.root.mainloop()

if __name__ == "__main__":
    app = AutoClickerGUI()
    app.run()
