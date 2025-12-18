#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据保存事件处理器
==============

处理应用程序中的数据保存事件。
"""

import logging
import os
from datetime import datetime

import wx

from .base import BaseEventHandler
from ..utils.file_utils import is_safe_path, sanitize_filename

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class DataSaveHandler(BaseEventHandler):
    """数据保存事件处理器"""
    
    def handle(self, event):
        """保存当前选中的数据"""
        try:
            current_container = self.app_frame.data_manager.get_current_data()
            if current_container:
                # 确定文件标识符 (F: 飞行架次, D: 地面试车, N: 未开车)
                identifier = "N"  # 默认为未开车
                if (hasattr(current_container, 'engine_data') and 
                    current_container.engine_data and 
                    current_container.engine_data.get('has_takeoff_info')):
                    # 检查是否有起飞信息来判断是飞行还是地面试验
                    start_time = current_container.engine_data.get('takeoff_start_time')
                    end_time = current_container.engine_data.get('takeoff_end_time')
                    
                    # 如果有明确的开关车时间，则认为是地面试验开车
                    if start_time and end_time:
                        identifier = "D"
                        
                        # 进一步检查是否是飞行架次（简单判断：持续时间超过一定阈值）
                        try:
                            duration = end_time - start_time
                            # 如果发动机运行时间超过10分钟，认为是飞行架次
                            if duration.total_seconds() > 600:
                                identifier = "F"
                        except:
                            pass
                
                # 生成默认文件名
                import os
                
                # 使用当前时间作为文件时间部分
                current_time = datetime.now().strftime("%Y%m%d")
                default_filename_base = f"{identifier}{current_time}"
                default_data_filename = f"{default_filename_base}.csv"
                
                # 获取原始文件的目录，如果有的话
                save_directory = os.getcwd()  # 默认为当前工作目录
                if hasattr(current_container, 'original_path') and current_container.original_path:
                    original_dir = os.path.dirname(current_container.original_path)
                    # 确保目录路径是安全的
                    if os.path.isdir(original_dir):
                        save_directory = original_dir
                
                # 构建完整默认路径
                default_data_path = os.path.join(save_directory, default_data_filename)
                
                with wx.FileDialog(
                    self.app_frame,
                    message="保存CSV数据",
                    defaultFile=default_data_path,  # 预填充默认文件名和路径
                    wildcard="CSV文件 (*.csv)|*.csv",
                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                ) as fileDialog:
                    if fileDialog.ShowModal() == wx.ID_CANCEL:
                        return

                    pathname = fileDialog.GetPath()
                    
                    # 检查路径安全性
                    if not is_safe_path(os.getcwd(), pathname):
                        wx.MessageBox("不允许保存到指定路径", "错误", wx.OK | wx.ICON_ERROR)
                        return
                    
                    # 清理文件名
                    dir_name = os.path.dirname(pathname)
                    file_name = sanitize_filename(os.path.basename(pathname))
                    pathname = os.path.join(dir_name, file_name)
                    
                    if not pathname.endswith('.csv'):
                        pathname += '.csv'
                    # 确保目录存在
                    os.makedirs(os.path.dirname(pathname) or '.', exist_ok=True)
                    
                    try:
                        current_container.df.to_csv(pathname, encoding='utf-8-sig', index=False)
                        self.app_frame.content_panel.set_formatted_text(f"数据已保存至: {pathname}")
                    except Exception as e:
                        logging.error(f"保存数据时出错: {str(e)}")
                        wx.MessageBox(f"保存文件时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            else:
                wx.MessageBox("暂无数据可保存", "提示", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            logging.error(f"保存当前数据时出错: {str(e)}")
            wx.MessageBox(f"保存当前数据时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)