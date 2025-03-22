import cv2
import numpy as np
from PIL import ImageGrab, Image
import win32gui
import os
import pyautogui

def capture_screen(hwnd=None):
    """捕获屏幕区域"""
    try:
        # 使用pyautogui截取全屏，确保识别一致性
        screenshot = pyautogui.screenshot()
        # 转换为OpenCV格式
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"截屏错误: {str(e)}")
        return None

def find_template_match(screen, template, method_name=None):
    """在屏幕图像中查找模板匹配"""
    try:
        # 如果template是字符串（路径），则使用pyautogui方式查找
        if isinstance(template, str) and os.path.exists(template):
            # 直接使用路径查找图像
            location = pyautogui.locateOnScreen(template, confidence=0.6, grayscale=True)
            if location:
                # 获取按钮中心坐标
                x, y = pyautogui.center(location)
                x, y = int(x), int(y)
                return 1.0, (x, y), location  # 匹配度设为1，返回中心点和位置信息
            return 0.0, None, None  # 未找到匹配
        
        # 如果template不是路径而是图像数据，使用OpenCV匹配
        else:
            # 使用最佳匹配算法 TM_CCOEFF_NORMED
            match_method = cv2.TM_CCOEFF_NORMED
            
            # 模板匹配
            result = cv2.matchTemplate(screen, template, match_method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # TM_CCOEFF_NORMED 算法下值越大表示匹配度越高
            match_val = max_val
            match_loc = max_loc
            
            return match_val, match_loc, result
    except Exception as e:
        print(f"图像匹配错误: {str(e)}")
        return 0.0, None, None

def get_match_method(method_name=None):
    """获取匹配算法的OpenCV常量
    现在总是返回最佳算法 TM_CCOEFF_NORMED
    """
    return cv2.TM_CCOEFF_NORMED

def draw_match_result(screen, template, match_loc, center_offset_x=0, center_offset_y=0):
    """在屏幕截图上标记匹配位置"""
    if isinstance(template, str) and os.path.exists(template):
        # 如果template是路径，加载图像
        template = cv2.imread(template)
    
    h, w = template.shape[:2] if hasattr(template, 'shape') else (50, 150)  # 默认尺寸
    marked_screen = screen.copy()
    
    # 画一个绿色矩形框标记位置
    cv2.rectangle(
        marked_screen,
        (match_loc[0], match_loc[1]),
        (match_loc[0] + w, match_loc[1] + h),
        (0, 255, 0),
        2
    )
    
    # 计算中心点坐标（考虑偏移）
    center_x = match_loc[0] + w // 2 + center_offset_x
    center_y = match_loc[1] + h // 2 + center_offset_y
    
    # 在中心位置画一个红色十字
    cv2.drawMarker(
        marked_screen,
        (center_x, center_y),
        (0, 0, 255),
        cv2.MARKER_CROSS,
        20,
        2
    )
    
    return marked_screen, (center_x, center_y)

def locate_on_screen(image_path, confidence=0.6):
    """直接使用pyautogui定位图像，返回坐标"""
    try:
        location = pyautogui.locateOnScreen(image_path, confidence=confidence, grayscale=True)
        if location:
            x, y = pyautogui.center(location)
            return True, (int(x), int(y)), 1.0  # 返回成功标志、坐标和置信度
        return False, None, 0.0
    except Exception as e:
        print(f"定位图像失败: {str(e)}")
        return False, None, 0.0
