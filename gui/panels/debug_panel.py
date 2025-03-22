import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class DebugPanel:
    def __init__(self, parent, debug_dir, log_func=None):
        self.parent = parent
        self.debug_dir = debug_dir
        self.log_func = log_func
        
        # 调试状态
        self.last_screen = None
        self.last_match_result = None
        self.last_match_location = None
        self.last_match_value = 0
        
        self.setup_debug_panel()
        
    def log(self, message):
        """输出日志"""
        if self.log_func:
            self.log_func(message)
        else:
            print(message)
            
    def setup_debug_panel(self):
        """设置调试面板"""
        debug_inner = ttk.Frame(self.parent, padding=10)
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
        
    def update_debug_panel(self, screen, result_img, template=None):
        """更新调试面板显示"""
        try:
            # 保存调试信息
            self.last_screen = screen
            self.last_match_result = result_img
            
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
                f"匹配算法: {self.algorithm}\n"
                f"{template_info}"
                f"匹配位置: {self.last_match_location}\n"
                f"匹配值: {self.last_match_value:.4f}\n"
                f"相似度阈值: {self.confidence_threshold:.2f}\n"
                f"点击偏移: X={self.x_offset}, Y={self.y_offset}"
            )
            
            self.match_info.config(text=match_info_text)
            
        except Exception as e:
            self.log(f"更新调试面板失败: {str(e)}")
            
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
            
    def set_match_params(self, algorithm, confidence_threshold, x_offset, y_offset):
        """设置匹配参数"""
        self.algorithm = algorithm
        self.confidence_threshold = confidence_threshold
        self.x_offset = x_offset
        self.y_offset = y_offset
