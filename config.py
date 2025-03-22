import os
from pathlib import Path

class Config:
    def __init__(self):
        # 基本设置
        self.window_title = "Claude"
        self.confidence_threshold = 0.6  # 降低默认匹配阈值以提高成功率
        self.algorithm = "TM_CCOEFF_NORMED"  # 使用最佳匹配算法
        self.interval = 0.2
        
        # 点击设置
        self.click_method = "auto"
        self.click_count = 2
        self.click_interval = 0.05
        self.x_offset = 0
        self.y_offset = 0
        
        # 应用设置
        self.start_minimized = False
        self.auto_start = False
        self.save_screenshots = False
        
        # 资源文件
        self.icon_path = self._find_default_icon()
        
    def _find_default_icon(self):
        """查找默认图标"""
        default_icons = ["1.png", "2.png", "3.png", "4.png", "allow_button.png"]
        for icon in default_icons:
            path = str(Path(__file__).parent / icon)
            if os.path.exists(path):
                return path
                
        return str(Path(__file__).parent / "1.png")
        
    def update_from_gui(self, gui_vars):
        """从GUI变量更新配置"""
        # 基本设置
        self.window_title = gui_vars.get('window_title_var', "Claude")
        self.confidence_threshold = gui_vars.get('confidence_var', 0.6)
        # 固定使用最佳算法
        self.algorithm = "TM_CCOEFF_NORMED"
        self.interval = gui_vars.get('interval_var', 0.2)
        
        # 点击设置
        self.click_method = gui_vars.get('click_method_var', "auto")
        self.click_count = gui_vars.get('clicks_var', 2)
        self.click_interval = gui_vars.get('click_interval_var', 0.05)
        self.x_offset = gui_vars.get('x_offset_var', 0)
        self.y_offset = gui_vars.get('y_offset_var', 0)
        
        # 应用设置
        self.start_minimized = gui_vars.get('start_minimized_var', False)
        self.auto_start = gui_vars.get('auto_start_var', False)
        self.save_screenshots = gui_vars.get('save_screenshots_var', False)

    def save_to_file(self, path=None):
        """保存配置到文件"""
        if path is None:
            path = Path(__file__).parent / "settings.ini"
            
        with open(path, 'w', encoding='utf-8') as f:
            f.write("[窗口设置]\n")
            f.write(f"窗口标题={self.window_title}\n")
            
            f.write("\n[识别设置]\n")
            f.write(f"相似度阈值={self.confidence_threshold}\n")
            f.write(f"匹配算法={self.algorithm}\n")
            f.write(f"检测间隔={self.interval}\n")
            
            f.write("\n[点击设置]\n")
            f.write(f"点击方式={self.click_method}\n")
            f.write(f"点击次数={self.click_count}\n")
            f.write(f"点击间隔={self.click_interval}\n")
            f.write(f"X偏移={self.x_offset}\n")
            f.write(f"Y偏移={self.y_offset}\n")
            
            f.write("\n[应用设置]\n")
            f.write(f"启动时最小化={int(self.start_minimized)}\n")
            f.write(f"自动开始点击={int(self.auto_start)}\n")
            f.write(f"保存截图={int(self.save_screenshots)}\n")
        
        return True
        
    def load_from_file(self, path=None):
        """从文件加载配置"""
        if path is None:
            path = Path(__file__).parent / "settings.ini"
            
        if not os.path.exists(path):
            return False
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if not line or line.startswith("[") or "=" not in line:
                    continue
                    
                key, value = line.split("=", 1)
                
                if key == "窗口标题":
                    self.window_title = value
                elif key == "相似度阈值":
                    self.confidence_threshold = float(value)
                elif key == "匹配算法":
                    # 忽略从文件读取的算法，始终使用最佳算法
                    pass
                elif key == "检测间隔":
                    self.interval = float(value)
                elif key == "点击方式":
                    self.click_method = value
                elif key == "点击次数":
                    self.click_count = int(value)
                elif key == "点击间隔":
                    self.click_interval = float(value)
                elif key == "X偏移":
                    self.x_offset = int(value)
                elif key == "Y偏移":
                    self.y_offset = int(value)
                elif key == "启动时最小化":
                    self.start_minimized = bool(int(value))
                elif key == "自动开始点击":
                    self.auto_start = bool(int(value))
                elif key == "保存截图":
                    self.save_screenshots = bool(int(value))
                    
            return True
        except Exception as e:
            print(f"加载配置文件出错: {str(e)}")
            return False
