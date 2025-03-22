import tkinter as tk
from tkinter import ttk

class SettingsPanel:
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        
        # 创建变量
        self.confidence_var = tk.DoubleVar(value=config.confidence_threshold)
        self.click_method_var = tk.StringVar(value=config.click_method)
        self.clicks_var = tk.IntVar(value=config.click_count)
        self.click_interval_var = tk.DoubleVar(value=config.click_interval)
        self.x_offset_var = tk.IntVar(value=config.x_offset)
        self.y_offset_var = tk.IntVar(value=config.y_offset)
        self.window_title_var = tk.StringVar(value=config.window_title)
        self.start_minimized_var = tk.BooleanVar(value=config.start_minimized)
        self.auto_start_var = tk.BooleanVar(value=config.auto_start)
        self.save_screenshots_var = tk.BooleanVar(value=config.save_screenshots)
        
        self.setup_settings_area()
        
    def setup_settings_area(self):
        """设置高级设置区域"""
        # 创建设置框架
        settings_inner = ttk.Frame(self.parent, padding=10)
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
        
        # 匹配算法信息
        algorithm_label = ttk.Label(
            similarity_frame,
            text="匹配算法: TM_CCOEFF_NORMED (推荐)",
            font=('Microsoft YaHei UI', 9),
            foreground='gray'
        )
        algorithm_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=5)
        
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
        start_minimized_check = ttk.Checkbutton(
            other_frame,
            text="启动时最小化到托盘",
            variable=self.start_minimized_var
        )
        start_minimized_check.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        # 自动启动操作
        auto_start_check = ttk.Checkbutton(
            other_frame,
            text="启动时自动开始点击",
            variable=self.auto_start_var
        )
        auto_start_check.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        # 保存截图
        save_screenshots_check = ttk.Checkbutton(
            other_frame,
            text="保存截图和匹配结果",
            variable=self.save_screenshots_var
        )
        save_screenshots_check.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        
    def update_config(self):
        """更新配置"""
        self.config.confidence_threshold = self.confidence_var.get()
        self.config.click_method = self.click_method_var.get()
        self.config.click_count = self.clicks_var.get()
        self.config.click_interval = self.click_interval_var.get()
        self.config.x_offset = self.x_offset_var.get()
        self.config.y_offset = self.y_offset_var.get()
        self.config.window_title = self.window_title_var.get()
        self.config.start_minimized = self.start_minimized_var.get()
        self.config.auto_start = self.auto_start_var.get()
        self.config.save_screenshots = self.save_screenshots_var.get()
        
    def get_values(self):
        """获取设置值"""
        return {
            'confidence_var': self.confidence_var.get(),
            'click_method_var': self.click_method_var.get(),
            'clicks_var': self.clicks_var.get(),
            'click_interval_var': self.click_interval_var.get(),
            'x_offset_var': self.x_offset_var.get(),
            'y_offset_var': self.y_offset_var.get(),
            'window_title_var': self.window_title_var.get(),
            'start_minimized_var': self.start_minimized_var.get(),
            'auto_start_var': self.auto_start_var.get(),
            'save_screenshots_var': self.save_screenshots_var.get()
        }
