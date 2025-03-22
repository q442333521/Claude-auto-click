import os
import cv2
import time
import threading
from datetime import datetime
from pathlib import Path
from utils.window_utils import find_window, check_window_status
from utils.image_utils import capture_screen, find_template_match, draw_match_result, locate_on_screen

class ImageDetector:
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger
        
        # 调试状态
        self.last_screen = None
        self.last_match_result = None
        self.last_match_location = None
        self.last_match_value = 0
        self.debug_dir = Path(__file__).parent.parent / "debug"
        self.debug_dir.mkdir(exist_ok=True)
    
    def log(self, message):
        """记录日志"""
        if self.logger:
            self.logger(message)
        else:
            print(message)
    
    def locate_target(self, target_images, debug_mode=False, pause=False):
        """定位目标图像"""
        try:
            # 检查是否有图片需要识别
            if not target_images:
                self.log("错误: 没有设置识别图片")
                return None, None
                
            # 调试模式暂停检查
            if debug_mode and pause:
                time.sleep(0.1)  # 短暂休眠，减少CPU占用
                return None, None
                
            # 查找目标窗口
            hwnd = find_window(self.config.window_title)
            
            # 截取屏幕 - 用于调试显示
            screen = capture_screen(hwnd)
            if screen is None:
                return None, None
                
            # 保存调试信息
            self.last_screen = screen
            
            # 使用PyAutoGUI直接识别图像 - 尝试每个目标图片
            for img_path in target_images:
                if not os.path.exists(img_path):
                    self.log(f"错误: 找不到图片文件 '{img_path}'")
                    continue
                
                # 使用PyAutoGUI直接识别
                found, position, confidence = locate_on_screen(
                    img_path, 
                    confidence=self.config.confidence_threshold
                )
                
                if found:
                    # 更新匹配信息
                    self.last_match_location = position
                    self.last_match_value = confidence
                    
                    # 在调试模式下显示匹配结果
                    if debug_mode:
                        # 在匹配结果图像上标记位置 - 创建可视化效果
                        template = cv2.imread(img_path)
                        if template is not None:
                            marked_screen, click_point = draw_match_result(
                                screen, 
                                template, 
                                (position[0] - template.shape[1]//2, position[1] - template.shape[0]//2),
                                self.config.x_offset, 
                                self.config.y_offset
                            )
                            
                            # 保存匹配结果
                            self.last_match_result = marked_screen
                            
                            # 显示匹配详情
                            self.log(f"找到图片: {os.path.basename(img_path)}")
                            self.log(f"匹配度: {confidence:.4f}, 点击位置: ({position[0]}, {position[1]})")
                    
                    # 添加偏移量
                    click_x = position[0] + self.config.x_offset
                    click_y = position[1] + self.config.y_offset
                    
                    # 保存截图
                    if self.config.save_screenshots:
                        self.save_debug_info()
                    
                    return (click_x, click_y), hwnd
            
            # 如果所有图片都没有匹配成功
            if debug_mode:
                self.log("没有找到匹配")
            return None, None
                
        except Exception as e:
            self.log(f"检测出错: {str(e)}")
            return None, None
    
    def save_debug_info(self):
        """保存当前调试信息"""
        if self.last_screen is not None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # 保存截图
            screen_path = self.debug_dir / f"screen_{timestamp}.png"
            cv2.imwrite(str(screen_path), self.last_screen)
            
            # 如果有匹配结果，保存匹配结果
            if self.last_match_result is not None:
                result_path = self.debug_dir / f"result_{timestamp}.png"
                cv2.imwrite(str(result_path), self.last_match_result)
                
            # 保存匹配信息
            info_path = self.debug_dir / f"info_{timestamp}.txt"
            with open(str(info_path), 'w', encoding='utf-8') as f:
                f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"目标窗口: {self.config.window_title}\n")
                f.write(f"相似度阈值: {self.config.confidence_threshold:.2f}\n")
                f.write(f"匹配算法: {self.config.algorithm}\n")
                f.write(f"匹配坐标: {self.last_match_location}\n")
                f.write(f"匹配值: {self.last_match_value:.4f}\n")
                f.write(f"点击方式: {self.config.click_method}\n")
                f.write(f"点击偏移: X={self.config.x_offset}, Y={self.config.y_offset}\n")
                
            self.log(f"调试信息已保存到 {self.debug_dir}")
            
        else:
            self.log("无调试信息可保存")
