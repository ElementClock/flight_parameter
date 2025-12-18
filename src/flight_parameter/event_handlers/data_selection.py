#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据选择事件处理器
==============

处理应用程序中的数据选择事件。
"""

import logging

import wx
from wx import NOT_FOUND

from .base import BaseEventHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class DataChoiceHandler(BaseEventHandler):
    """数据选择事件处理器"""
    
    def handle(self, event):
        """处理数据选择变化事件"""
        try:
            selection = self.app_frame.sidebar_panel.data_choice.GetSelection()
            if selection != NOT_FOUND:
                choices = self.app_frame.sidebar_panel.data_choice.GetItems()
                key = choices[selection]
                self.app_frame.data_manager.select_data(key)
                self.display_current_data()
        except Exception as e:
            logging.error(f"处理数据选择变化时出错: {str(e)}")
            self.app_frame.content_panel.set_formatted_text(f"处理数据选择变化时出错: {str(e)}")
    
    def display_current_data(self):
        """显示当前选中数据的分析结果"""
        try:
            current_container = self.app_frame.data_manager.get_current_data()
            if current_container:
                text_content = (
                    f"文件名: {current_container.filename}\n"
                    f"本次文件解析结果如下：\n{current_container.get_analysis_result()}\n")
                self.app_frame.content_panel.set_formatted_text(text_content)
        except Exception as e:
            logging.error(f"显示当前数据时出错: {str(e)}")
            self.app_frame.content_panel.set_formatted_text(f"显示当前数据时出错: {str(e)}")