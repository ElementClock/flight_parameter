#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分析清除事件处理器
==============

处理应用程序中的分析清除事件。
"""

import logging

import wx

from .base import BaseEventHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class AnalysisClearHandler(BaseEventHandler):
    """分析清除事件处理器"""
    
    def handle(self, event):
        """清除分析数据框信息"""
        try:
            self.app_frame.content_panel.set_formatted_text("")
        except Exception as e:
            logging.error(f"清除分析时出错: {str(e)}")