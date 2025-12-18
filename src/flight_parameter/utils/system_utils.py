"""
系统工具模块
"""

import ctypes
import platform
from typing import Tuple


def calculate_window_geometry() -> Tuple[int, int, int, int]:
    """
    根据屏幕尺寸自动计算窗口大小和位置
    
    Returns:
        tuple: (width, height, x_position, y_position)
    """
    try:
        # 获取屏幕尺寸
        if platform.system() == "Windows":
            # Windows系统使用ctypes获取屏幕信息
            user32 = ctypes.windll.user32
            screen_width = user32.GetSystemMetrics(0)
            screen_height = user32.GetSystemMetrics(1)
        else:
            # 其他系统使用默认值
            screen_width = 1920
            screen_height = 1080
            
        # 计算窗口尺寸（屏幕的80%）
        window_width = int(screen_width * 0.6)
        window_height = int(screen_height * 0.6)
        
        # 计算窗口位置（居中）
        window_x = int((screen_width - window_width) / 2)
        window_y = int((screen_height - window_height) / 2)
        
        return window_width, window_height, window_x, window_y
    except Exception:
        # 出现异常时返回默认值
        return 1200, 800, 100, 100