import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
from utils.image_utils import capture_screen, find_template_match

class ImagePanel:
    def __init__(self, parent, config, log_func=None):
        self.parent = parent
        self.config = config
        self.log_func = log_func
        
        # 图片相关变量
        self.target_images = []  # 存储目标图片路径列表
        self.image_labels = []  # 存储图片标签
        self.image_tk_refs = []  # 保持对Tkinter PhotoImage对象的引用
        self.selected_image = None  # 当前选中的图片
        
        self.setup_image_area()
        
    def log(self, message):
        """输出日志"""
        if self.log_func:
            self.log_func(message)
        else:
            print(message)
            
    def setup_image_area(self):
        """设置图片区域"""
        # 图片操作框架
        control_frame = ttk.Frame(self.parent)
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
        preview_frame = ttk.LabelFrame(self.parent, text="图片预览")
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
        
    def on_canvas_configure(self, event):
        """调整画布大小"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # 调整内部框架的宽度以匹配画布宽度
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        
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
                    self.selected_image = None
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
                self.selected_image = None
                return
                
    def test_selected_image(self):
        """测试所选图片的识别效果"""
        # 检查是否有选中的图片
        if not self.selected_image:
            messagebox.showinfo("提示", "请先选择一张图片")
            return
            
        # 截取屏幕
        self.log(f"测试识别图片: {os.path.basename(self.selected_image)}")
        screen = capture_screen()
        
        if screen is not None:
            # 读取目标图片
            template = cv2.imread(self.selected_image)
            if template is None:
                self.log(f"错误: 无法读取图片 '{self.selected_image}'")
                return
                
            # 模板匹配
            match_val, match_loc, _ = find_template_match(
                screen, 
                template, 
                self.config.algorithm
            )
            
            # 判断匹配结果
            if match_val >= self.config.confidence_threshold:
                self.log(f"匹配成功! 匹配度: {match_val:.2f}, 位置: {match_loc}")
                messagebox.showinfo("匹配成功", f"匹配度: {match_val:.2f}\n位置: {match_loc}")
            else:
                self.log(f"匹配失败! 匹配度: {match_val:.2f} < 阈值: {self.config.confidence_threshold:.2f}")
                messagebox.showinfo("匹配失败", f"匹配度: {match_val:.2f}\n阈值: {self.config.confidence_threshold:.2f}")
        else:
            self.log("截图失败，无法测试")
            
    def add_default_images(self):
        """添加默认图片"""
        # 添加默认图片
        for img_file in ["1.png", "2.png", "3.png"]:
            img_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), img_file)
            if os.path.exists(img_path):
                self.add_image(img_path)
                
        if not self.target_images and os.path.exists(self.config.icon_path):
            self.add_image(self.config.icon_path)
            
    def get_target_images(self):
        """获取目标图片列表"""
        return self.target_images
