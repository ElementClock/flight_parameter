#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
事件处理器基类模块
==============

定义事件处理器的基类和其他共享功能。
"""

import logging
import os
import multiprocessing
from abc import ABC, abstractmethod

import pandas as pd
import wx

# 项目模块导入
from ..utils.html_utils import HTMLGenerator
from ..resources.styles import get_css_styles
from ..utils.file_utils import is_safe_path, sanitize_filename

# 根据CPU核心数动态设置最大工作线程数
MAX_WORKERS = min(32, max(4, multiprocessing.cpu_count()))  # 至少4个，最多32个线程

# 文件处理常量
CHUNK_SIZE = 10000              # CSV文件分块读取大小
MIN_PROCESSING_TIME_THRESHOLD = 600  # 最小处理时间阈值（秒），用于区分地面试车和飞行架次
FILE_READ_BUFFER_SIZE = 1024    # 文件读取缓冲区大小

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class BaseEventHandler(ABC):
    """事件处理器基类"""
    
    def __init__(self, app_frame):
        """初始化事件处理器基类
        
        Args:
            app_frame: 应用程序主窗口实例
        """
        self.app_frame = app_frame

    @abstractmethod
    def handle(self, event):
        """处理事件的抽象方法"""
        pass