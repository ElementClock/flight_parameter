#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据加载事件处理器
==============

处理应用程序中的数据加载事件。
"""

import logging
import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import wx
from wx import ID_CANCEL, NOT_FOUND

# 导入我们的公共工具模块
from ..utils.file_utils import detect_encoding, is_safe_path, sanitize_filename

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# 在文件顶部导入BaseEventHandler，避免循环导入
from .base import BaseEventHandler, MAX_WORKERS


class DataLoaderHandler(BaseEventHandler):
    """数据加载事件处理器"""
    
    def __init__(self, app_frame):
        super().__init__(app_frame)
        self.current_progress = 0
        # 创建线程池
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        # 添加编码缓存以提高性能
        self.encoding_cache = {}
        
    def handle(self, event):
        """加载CSV数据文件"""
        try:
            with wx.FileDialog(
                    self.app_frame,
                    message="选择CSV文件",
                    wildcard="CSV文件 (*.csv)|*.csv",
                    style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE
            ) as fileDialog:
                if fileDialog.ShowModal() == ID_CANCEL:
                    return

                pathnames = fileDialog.GetPaths()
                # 显示正在加载的消息
                self.app_frame.content_panel.set_formatted_text("正在加载和分析数据，请稍候...")
                # 显示进度条
                self.app_frame.sidebar_panel.show_progress(True)

                # 使用线程池处理数据加载和分析，避免阻塞UI
                future = self.executor.submit(self.process_multiple_data, pathnames)
                # 可以在这里添加对future的处理，如添加回调函数
        except Exception as e:
            logging.error(f"加载数据时出错: {str(e)}")
            logging.error(f"加载数据时出错: {str(e)}")
            wx.MessageBox("加载数据时出错，请查看日志获取详细信息", "错误", wx.OK | wx.ICON_ERROR)
    
    def _update_analysis_progress(self, value, message=""):
        """更新分析进度的内部方法
        
        Args:
            value (int): 进度值(0-100)
            message (str): 进度消息
        """
        try:
            # 确保进度值在有效范围内
            value = max(0, min(100, value))
            self.current_progress = value
            wx.CallAfter(self.app_frame.sidebar_panel.update_progress, value, message)
        except Exception as e:
            logging.error(f"更新分析进度时出错: {str(e)}")
    
    def _detect_file_encoding(self, filepath, encodings=['utf-8', 'gbk', 'gb2312', 'latin1']):
        """
        尝试用不同编码读取文件来检测文件编码
        
        Args:
            filepath (str): 文件路径
            encodings (list): 尝试的编码列表
            
        Returns:
            str: 检测到的编码，如果无法检测则返回None
        """
        try:
            return detect_encoding(filepath)  # 修复：只传入文件路径
        except Exception as e:
            logging.error(f"检测文件编码时出错: {str(e)}")
            return None

    def _read_large_csv_in_chunks(self, pathname, encoding, chunksize=10000):
        """分块读取大型CSV文件以优化内存使用
        
        Args:
            pathname (str): 文件路径
            encoding (str): 文件编码
            chunksize (int): 每次读取的行数
            
        Returns:
            pandas.DataFrame: 读取的完整数据框
        """
        try:
            # 先读取列名以确定数据结构，指定日期列为字符串类型
            # nrows=5表示只读取前5行，dtype={3: str}表示将第4列（索引为3）强制作为字符串处理
            df_sample = pd.read_csv(pathname, encoding=encoding, nrows=5, dtype={3: str})
            columns = df_sample.columns.tolist()
            
            chunks = []
            total_rows = 0
            
            # 获取总行数用于进度计算
            with open(pathname, 'r', encoding=encoding) as f:
                total_rows = sum(1 for _ in f) - 1  # 减去标题行
            
            rows_read = 0
            # 分块读取文件，每块chunksize行
            for chunk in pd.read_csv(pathname, encoding=encoding, chunksize=chunksize, dtype={3: str}):
                chunks.append(chunk)
                rows_read += len(chunk)
                
                # 更新进度（前20%用于文件读取）
                progress_msg = f"正在读取文件: {os.path.basename(pathname)} ({rows_read}/{total_rows} 行)"
                wx.CallAfter(self.app_frame.sidebar_panel.update_progress, 
                             int((rows_read / total_rows) * 20), progress_msg)
            
            # 合并所有块，使用ignore_index=True减少内存占用
            df = pd.concat(chunks, ignore_index=True, copy=False)
            
            # 清理临时数据以释放内存
            del chunks
            
            return df
        except UnicodeDecodeError as e:
            logging.error(f"使用 {encoding} 编码分块读取CSV文件时出错: {str(e)}")
            raise e
        except Exception as e:
            logging.error(f"分块读取CSV文件时出错: {str(e)}")
            raise e
    
    def _process_single_file(self, pathname, index, total_files):
        """处理单个文件
        
        Args:
            pathname (str): 文件路径
            index (int): 文件索引
            total_files (int): 总文件数
        """
        try:
            # 更新进度
            progress_msg = f"正在处理文件 {index+1}/{total_files}: {os.path.basename(pathname)}"
            wx.CallAfter(self.app_frame.sidebar_panel.update_progress, 
                         int((index / total_files) * 10), progress_msg)  # 前10%用于文件准备
            
            # 首先尝试检测文件编码（使用缓存）
            detected_encoding = self._detect_file_encoding(pathname)
            
            # 定义尝试的编码列表
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
            if detected_encoding and detected_encoding not in encodings:
                # 将检测到的编码放在首位
                encodings.insert(0, detected_encoding)
            elif detected_encoding:
                # 如果检测到的编码在列表中，将其移到首位
                encodings.remove(detected_encoding)
                encodings.insert(0, detected_encoding)
            
            df = None
            last_error = None

            for encoding in encodings:
                try:
                    # 检查文件大小以决定是否使用分块读取
                    file_size = os.path.getsize(pathname)
                    size_threshold = 50 * 1024 * 1024  # 50MB阈值
                    
                    if file_size > size_threshold:
                        # 对大文件使用分块读取
                        df = self._read_large_csv_in_chunks(pathname, encoding)
                    else:
                        # 对小文件直接读取，指定第4列为字符串类型
                        df = pd.read_csv(pathname, encoding=encoding, dtype={3: str})
                    
                    # 添加数据到数据管理器，传递进度回调函数和原始路径
                    data_container, error = self.app_frame.data_manager.add_data(
                        df, 
                        os.path.basename(pathname),
                        progress_callback=self._update_analysis_progress,
                        original_path=pathname  # 传递原始文件路径
                    )
                    if error:
                        raise Exception(error)
                    
                    # 在UI线程中更新界面
                    wx.CallAfter(self.on_single_data_loaded, pathname, encoding, data_container)
                    break
                except UnicodeDecodeError as e:
                    last_error = e
                    logging.warning(f"使用 {encoding} 编码读取文件失败: {str(e)}")
                    continue
                except Exception as e:
                    logging.error(f"处理文件 {pathname} 时出错: {str(e)}")
                    raise e

            if df is None:
                error_msg = f"无法使用任何编码读取文件: {pathname}"
                logging.error(error_msg)
                raise last_error if last_error else Exception(error_msg)

        except Exception as e:
            # 在UI线程中显示错误消息
            logging.error(f"处理文件 {pathname} 时出错: {str(e)}")
            wx.CallAfter(self.on_data_load_error, pathname, "处理文件时出错，请查看日志获取详细信息")
    
    def process_multiple_data(self, pathnames):
        """在线程池中处理多个数据文件
        
        Args:
            pathnames (list): 文件路径列表
            
        Returns:
            list: 处理结果列表
        """
        try:
            results = []
            total_files = len(pathnames)
            
            # 更新进度（0%）
            wx.CallAfter(self.app_frame.sidebar_panel.update_progress, 0, f"准备处理 {total_files} 个文件")
            
            # 处理每个文件
            futures = []
            for i, pathname in enumerate(pathnames):
                future = self.executor.submit(self._process_single_file, pathname, i, total_files)
                futures.append(future)
            
            # 等待所有任务完成
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logging.error(f"处理文件时出错: {str(e)}")
                    results.append(None)
            
            # 更新进度（100%）
            wx.CallAfter(self.app_frame.sidebar_panel.update_progress, 100, "文件处理完成")
            
            return results
        except Exception as e:
            logging.error(f"处理多个数据文件时出错: {str(e)}")
            wx.CallAfter(self.app_frame.sidebar_panel.update_progress, 100, "文件处理出错")
            raise e

    def on_single_data_loaded(self, pathname, encoding, data_container):
        """当单个数据文件加载完成时调用
        
        Args:
            pathname (str): 文件路径
            encoding (str): 使用的编码
            data_container: 数据容器对象
        """
        try:
            if data_container:
                # 更新数据选择器
                self.app_frame.sidebar_panel.update_data_choice(self.app_frame.data_manager.get_data_keys())
                
                # 显示分析结果
                if data_container.analysis_result:
                    self.app_frame.content_panel.set_formatted_text(data_container.analysis_result)
                else:
                    self.app_frame.content_panel.set_formatted_text("数据加载完成，但未生成分析结果")
                
                # 显示成功消息
                wx.MessageBox(f"文件 {os.path.basename(pathname)} 加载成功\n使用编码: {encoding}", 
                              "成功", wx.OK | wx.ICON_INFORMATION)
            else:
                self.app_frame.content_panel.set_formatted_text("数据加载失败")
        except Exception as e:
            logging.error(f"处理单个数据加载完成事件时出错: {str(e)}")
            self.app_frame.content_panel.set_formatted_text("数据加载完成，但处理结果时出错")

    def on_data_load_error(self, pathname, error_message):
        """当数据加载出错时调用
        
        Args:
            pathname (str): 出错的文件路径
            error_message (str): 错误消息
        """
        try:
            # 隐藏进度条
            self.app_frame.sidebar_panel.show_progress(False)
            
            # 显示错误消息
            wx.MessageBox(error_message, "错误", wx.OK | wx.ICON_ERROR)
            
            # 清空内容区域
            self.app_frame.content_panel.set_formatted_text("")
        except Exception as e:
            logging.error(f"处理数据加载错误事件时出错: {str(e)}")