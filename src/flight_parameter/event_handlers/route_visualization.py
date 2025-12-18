#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
航路点绘制事件处理器
==============

处理应用程序中的航路点绘制事件。
"""

import logging
import os
import sys

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


class RouteVisualizationHandler(BaseEventHandler):
    """航路点绘制事件处理器"""
    
    def handle(self, event):
        """处理航路点绘制按钮点击事件"""
        try:
            # 导入航线可视化模块
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from visualization.route_visualization import draw_route_from_sheet
            
            # 打开文件选择对话框选择Excel文件
            with wx.FileDialog(
                self.app_frame,
                message="选择航路点Excel文件",
                wildcard="Excel文件 (*.xlsx)|*.xlsx|Excel文件 (*.xls)|*.xls",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
            ) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return
                    
                pathname = fileDialog.GetPath()
                
                # 获取Excel文件中的所有工作表名称
                import pandas as pd
                excel_file = pd.ExcelFile(pathname)
                sheet_names = excel_file.sheet_names
                
                # 如果只有一个工作表，直接绘制
                if len(sheet_names) == 1:
                    draw_route_from_sheet(pathname, sheet_names[0])
                else:
                    # 如果有多个工作表，让用户选择
                    dialog = wx.SingleChoiceDialog(
                        self.app_frame,
                        "请选择要绘制的工作表:",
                        "选择工作表",
                        sheet_names
                    )
                    if dialog.ShowModal() == wx.ID_OK:
                        selected_sheet = dialog.GetStringSelection()
                        draw_route_from_sheet(pathname, selected_sheet)
                    dialog.Destroy()
                    
        except ImportError as e:
            logging.error(f"导入航线可视化模块时出错: {str(e)}")
            wx.MessageBox(f"无法导入航线可视化模块: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
        except Exception as e:
            logging.error(f"处理航路点绘制时出错: {str(e)}")
            wx.MessageBox(f"航路点绘制时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)