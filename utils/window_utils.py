import win32gui
import win32con
import win32api

def find_window(title):
    """根据窗口标题查找窗口"""
    try:
        return win32gui.FindWindow(None, title)
    except:
        return None

def is_window_foreground(hwnd):
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

def check_window_status(window_title):
    """综合检查目标窗口是否激活"""
    hwnd = find_window(window_title)
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

def get_window_rect(hwnd):
    """获取窗口矩形区域"""
    try:
        return win32gui.GetWindowRect(hwnd)
    except:
        return None

def screen_to_client(hwnd, point):
    """屏幕坐标转窗口客户坐标"""
    try:
        return win32gui.ScreenToClient(hwnd, point)
    except:
        return point

def make_long_param(x, y):
    """生成鼠标消息的参数"""
    return win32api.MAKELONG(x, y)
