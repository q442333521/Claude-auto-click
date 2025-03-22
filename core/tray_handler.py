import os
import sys
import threading
from PIL import Image
import pystray
from pystray import MenuItem as item

class TrayIconHandler:
    def __init__(self, icon_path, title="Auto Clicker", on_show=None, on_toggle=None, on_quit=None):
        self.icon_path = icon_path
        self.title = title
        self.on_show = on_show
        self.on_toggle = on_toggle
        self.on_quit = on_quit
        self.tray_icon = None
        
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
                item('显示', self.on_show if self.on_show else self._dummy_action),
                item('开始/停止', self.on_toggle if self.on_toggle else self._dummy_action),
                item('退出', self.on_quit if self.on_quit else self._quit_app)
            )
            
            self.tray_icon = pystray.Icon(self.title, tray_image, self.title, menu)
            
            # 在单独的线程中运行系统托盘图标
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            return True
        except Exception as e:
            # 如果创建托盘图标失败，记录错误但不中断程序
            print(f"创建系统托盘图标失败: {str(e)}")
            return False
    
    def _dummy_action(self):
        """空操作"""
        pass
        
    def _quit_app(self):
        """默认退出操作"""
        try:
            self.tray_icon.stop()
        except:
            pass
        sys.exit(0)
        
    def stop(self):
        """停止托盘图标"""
        try:
            if self.tray_icon:
                self.tray_icon.stop()
        except:
            pass
