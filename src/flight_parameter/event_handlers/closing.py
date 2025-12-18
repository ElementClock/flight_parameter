#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
关闭事件处理器
==============

处理应用程序中的关闭事件。
"""

import logging
from concurrent.futures import ThreadPoolExecutor

import wx

from .base import BaseEventHandler, MAX_WORKERS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class CloseHandler(BaseEventHandler):
    """关闭事件处理器"""
    
    def __init__(self, app_frame):
        super().__init__(app_frame)
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        
    def handle(self, event):
        """处理窗口关闭事件"""
        try:
            # 关闭线程池
            self.executor.shutdown(wait=True)
            # 销毁窗口
            self.app_frame.Destroy()
        except Exception as e:
            logging.error(f"处理窗口关闭事件时出错: {str(e)}")