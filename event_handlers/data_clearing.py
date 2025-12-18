#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据清除事件处理器
==============

处理应用程序中的数据清除事件。
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


class DataClearHandler(BaseEventHandler):
    """数据清除事件处理器"""
    
    def handle(self, event):
        """清除当前选中的数据"""
        try:
            current_key = self.app_frame.data_manager.current_data_key
            if current_key:
                # 从数据管理器中移除数据
                success = self.app_frame.data_manager.remove_data(current_key)
                
                if success:
                    # 更新下拉菜单选项
                    choices = self.app_frame.data_manager.get_data_keys()
                    self.app_frame.sidebar_panel.data_choice.Set(choices)
                    
                    # 如果还有其他数据，选择第一个；否则清空当前选择
                    if choices:
                        self.app_frame.data_manager.select_data(choices[0])
                        self.app_frame.sidebar_panel.data_choice.SetSelection(0)
                        # 显示选中的数据
                        self.display_current_data()
                    else:
                        self.app_frame.content_panel.set_formatted_text("所有数据已清除")
                else:
                    wx.MessageBox("没有选中的数据可清除", "提示", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox("没有选中的数据可清除", "提示", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            logging.error(f"清除当前数据时出错: {str(e)}")
            wx.MessageBox(f"清除当前数据时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
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