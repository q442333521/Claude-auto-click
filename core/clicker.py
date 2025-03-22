import time
import win32gui
import win32con
import win32api
from utils.window_utils import find_window, screen_to_client, make_long_param

class MouseClicker:
    def __init__(self, logger=None):
        self.logger = logger
    
    def log(self, message):
        """记录日志"""
        if self.logger:
            self.logger(message)
        else:
            print(message)
    
    def perform_click(self, x, y, hwnd, click_method="auto", click_count=2, click_interval=0.05):
        """执行点击操作"""
        if not hwnd:
            self.log("无法获取目标窗口句柄")
            return False
        
        # 判断点击方式
        if click_method == "auto":
            # 自动选择点击方式
            is_foreground = win32gui.GetForegroundWindow() == hwnd
            click_method = "foreground" if is_foreground else "background"
        
        # 前台点击模式
        if click_method == "foreground":
            self.log("使用前台点击模式")
            return self._perform_foreground_click(x, y, hwnd, click_count, click_interval)
        
        # 后台点击模式
        else:
            self.log("使用后台点击模式")
            return self._perform_background_click(x, y, hwnd, click_count, click_interval)
    
    def _perform_foreground_click(self, x, y, hwnd, click_count, click_interval):
        """前台点击模式（移动鼠标）"""
        # 保存当前鼠标位置
        original_x, original_y = win32api.GetCursorPos()
        
        try:
            # 获取窗口位置以计算相对坐标
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            
            # 确保窗口可见
            if not win32gui.IsWindowVisible(hwnd):
                self.log("窗口不可见，尝试激活")
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.1)
            
            # 尝试激活窗口
            if win32gui.GetForegroundWindow() != hwnd:
                self.log("窗口未激活，尝试激活")
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.1)
            
            # 移动鼠标到指定位置
            try:
                # 尝试直接移动到绝对坐标
                win32api.SetCursorPos((x, y))
            except:
                # 如果失败，尝试移动到窗口相对坐标
                win32api.SetCursorPos((left + x - left, top + y - top))
            
            time.sleep(0.1)
            
            # 执行点击操作指定次数
            for i in range(click_count):
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(click_interval)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                time.sleep(click_interval)
            
            # 额外增加一次点击以提高成功率
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
    
    def _perform_background_click(self, x, y, hwnd, click_count, click_interval):
        """后台点击模式（发送消息）"""
        try:
            # 获取窗口位置以计算相对坐标
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            
            # 将屏幕坐标转换为窗口客户区坐标
            client_point = screen_to_client(hwnd, (x, y))
            
            # 构造鼠标点击消息的参数
            lparam = win32api.MAKELONG(client_point[0], client_point[1])
            
            # 尝试多种点击方法
            
            # 方法1: SendMessage - 这种方法会等待消息处理完毕
            for i in range(click_count):
                # 发送鼠标左键按下和释放消息
                win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
                time.sleep(click_interval)
                win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
                time.sleep(click_interval)
            
            # 方法2: PostMessage - 这种方法不等待处理完毕
            for i in range(1):  # 额外发送一次提高成功率
                win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
                time.sleep(click_interval)
                win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
            
            self.log(f"完成后台点击操作 ({click_count}次)")
            return True
        except Exception as e:
            self.log(f"后台点击错误: {str(e)}")
            return False
