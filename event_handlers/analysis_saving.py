#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分析结果保存事件处理器
==============

处理应用程序中的分析结果保存事件。
"""

import logging
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# 导入我们的公共工具模块
from src.flight_parameter.utils.common import save_as_pdf, remove_format_markers

import wx

from .base import BaseEventHandler
from html_generator import HTMLGenerator
from styles import GLOBAL_CSS, TABLE_STYLE_FIXED, TABLE_STYLE_AUTO, SMALL_EMPTY_LINE_STYLE
from utils import is_safe_path, sanitize_filename

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class AnalysisSaveHandler(BaseEventHandler):
    """分析结果保存事件处理器"""
    
    def handle(self, event):
        """保存分析结果"""
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
                default_analysis_filename = f"{default_filename_base}_分析.pdf"  # 更改为PDF扩展名
                
                # 获取原始文件的目录，如果有的话
                if hasattr(current_container, 'original_path') and current_container.original_path:
                    save_directory = os.path.dirname(current_container.original_path)
                else:
                    # 如果没有原始路径信息，则保存到当前工作目录
                    save_directory = os.getcwd()
                
                # 构建完整默认路径
                default_analysis_path = os.path.join(save_directory, default_analysis_filename)
                
                with wx.FileDialog(
                    self.app_frame,
                    message="保存分析结果",
                    defaultFile=default_analysis_path,  # 预填充默认文件名和路径
                    wildcard="PDF文件 (*.pdf)|*.pdf|Markdown文件 (*.md)|*.md|文本文件 (*.txt)|*.txt",
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
                    
                    # 确保目录存在
                    os.makedirs(os.path.dirname(pathname) or '.', exist_ok=True)
                    
                    try:
                        # 获取当前数据容器中的分析结果
                        analysis_result = current_container.get_analysis_result()
                        
                        # 保存分析结果
                        self._save_analysis_result(pathname, analysis_result)
                        
                        self.app_frame.content_panel.set_formatted_text(f"分析结果已保存至: {pathname}")
                    except Exception as e:
                        logging.error(f"保存分析结果时出错: {str(e)}")
                        wx.MessageBox(f"保存文件时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            else:
                wx.MessageBox("暂无分析数据可保存", "提示", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            logging.error(f"保存分析结果时出错: {str(e)}")
            wx.MessageBox(f"保存分析结果时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            
    def _save_analysis_result(self, pathname, analysis_result):
        """保存分析结果到文件
        
        Args:
            pathname (str): 保存路径
            analysis_result (str): 分析结果文本
        """
        try:
            # 检查路径安全性
            if not is_safe_path(os.getcwd(), pathname):
                raise ValueError(f"不允许保存到指定路径: {pathname}")
            
            # 确保目录存在
            directory = os.path.dirname(pathname)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # 根据文件扩展名确定保存格式
            _, ext = os.path.splitext(pathname.lower())
            
            if ext == '.pdf':
                # 保存为PDF格式
                save_as_pdf(pathname, analysis_result)
            elif ext == '.md':
                # 保存为Markdown格式
                self._save_as_markdown(pathname, analysis_result)
            else:
                # 默认保存为文本格式
                self._save_as_text(pathname, analysis_result)
                
        except Exception as e:
            logging.error(f"保存分析结果时出错: {str(e)}")
            raise e

    def _save_as_text(self, pathname, analysis_result):
        """将分析结果保存为文本文件
        
        Args:
            pathname (str): 保存路径
            analysis_result (str): 分析结果文本
        """
        try:
            # 移除格式标记
            plain_text = remove_format_markers(analysis_result)
            
            with open(pathname, 'w', encoding='utf-8') as f:
                f.write(plain_text)
        except Exception as e:
            logging.error(f"保存文本时出错: {str(e)}")
            raise e

    def _save_as_markdown(self, pathname, analysis_result):
        """将分析结果保存为Markdown文件
        
        Args:
            pathname (str): 保存路径
            analysis_result (str): 分析结果文本
        """
        try:
            # 将自定义标记转换为Markdown
            markdown_text = self._convert_custom_markup_to_markdown(analysis_result)
            
            with open(pathname, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
        except Exception as e:
            logging.error(f"保存Markdown时出错: {str(e)}")
            raise e
            
    def _convert_custom_markup_to_markdown(self, text):
        """将自定义标记转换为Markdown标记
        
        Args:
            text (str): 包含自定义标记的文本
            
        Returns:
            str: 转换为Markdown格式的文本
        """
        try:
            # 对于已经是Markdown格式的文本，直接返回
            return text
        except Exception as e:
            logging.error(f"转换自定义标记为Markdown时出错: {str(e)}")
            return text
