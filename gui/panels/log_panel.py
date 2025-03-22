import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime

class LogPanel:
    def __init__(self, parent, interval_var):
        self.parent = parent
        self.interval_var = interval_var
        self.setup_log_area()
        
    def setup_log_area(self):
        """设置日志区域"""
        # 日志标题行框架
        title_frame = ttk.Frame(self.parent)
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
        
        # 验证函数
        vcmd = (self.parent.register(self.validate_interval), '%P')
        
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
            self.parent,
            wrap=tk.WORD,
            font=('Consolas', 9),
            height=15
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def validate_interval(self, value):
        """验证间隔输入"""
        if value == "":
            return True
        try:
            float_val = float(value)
            return float_val >= 0.1 and float_val <= 60.0
        except ValueError:
            return False
            
    def log(self, message):
        """添加日志"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_area.see(tk.END)
        except:
            pass
            
    def enable_interval_entry(self, enabled=True):
        """启用或禁用间隔输入"""
        self.interval_entry.config(state='normal' if enabled else 'disabled')
