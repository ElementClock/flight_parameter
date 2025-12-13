#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
事件处理器模块
==============

处理应用程序中的各种事件，包括数据加载、保存、分析等操作。
使用线程池管理并发任务，确保UI响应性。
"""

import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from abc import ABC, abstractmethod

import pandas as pd
import wx
from wx import ID_CANCEL, NOT_FOUND

# 设置最大工作线程数为4，避免过多线程竞争资源
MAX_WORKERS = 4

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


class DataLoaderHandler(BaseEventHandler):
    """数据加载事件处理器"""
    
    def __init__(self, app_frame):
        super().__init__(app_frame)
        self.current_progress = 0
        # 创建线程池
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        
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
            wx.MessageBox(f"加载数据时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
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
        # 读取文件的前几行进行测试
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    f.read(1024)  # 读取前1024个字符
                logging.info(f"使用 {encoding} 编码成功读取文件头部")
                return encoding
            except UnicodeDecodeError:
                logging.warning(f"使用 {encoding} 编码读取文件失败")
                continue
            except Exception as e:
                logging.warning(f"使用 {encoding} 编码读取文件时出现其他错误: {str(e)}")
                continue
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
            df_sample = pd.read_csv(pathname, encoding=encoding, nrows=5, dtype={3: str})
            columns = df_sample.columns.tolist()
            
            chunks = []
            total_rows = 0
            
            # 获取总行数用于进度计算
            with open(pathname, 'r', encoding=encoding) as f:
                total_rows = sum(1 for _ in f) - 1  # 减去标题行
            
            rows_read = 0
            for chunk in pd.read_csv(pathname, encoding=encoding, chunksize=chunksize, dtype={3: str}):
                chunks.append(chunk)
                rows_read += len(chunk)
                
                # 更新进度（前20%用于文件读取）
                progress_msg = f"正在读取文件: {os.path.basename(pathname)} ({rows_read}/{total_rows} 行)"
                wx.CallAfter(self.app_frame.sidebar_panel.update_progress, 
                             int((rows_read / total_rows) * 20), progress_msg)
            
            # 合并所有块
            df = pd.concat(chunks, ignore_index=True)
            
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
            
            # 首先尝试检测文件编码
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
            wx.CallAfter(self.on_data_load_error, pathname, str(e))
    
    def process_multiple_data(self, pathnames):
        """在线程池中处理多个数据文件
        
        Args:
            pathnames: 文件路径列表
        """
        try:
            total_files = len(pathnames)
            
            # 如果只有一个文件，直接在当前线程中处理
            if total_files == 1:
                self._process_single_file(pathnames[0], 0, total_files)
            else:
                # 对于多个文件，使用线程池并发处理
                futures = []
                for i, pathname in enumerate(pathnames):
                    # 提交任务到线程池
                    future = self.executor.submit(self._process_single_file, pathname, i, total_files)
                    futures.append(future)
                
                # 等待所有任务完成
                for future in as_completed(futures):
                    try:
                        future.result()  # 获取结果，如果有异常会抛出
                    except Exception as e:
                        logging.error(f"处理文件时出错: {str(e)}")
            
            # 完成所有文件处理后隐藏进度条
            wx.CallAfter(self.app_frame.sidebar_panel.show_progress, False)
        except Exception as e:
            logging.error(f"处理多个数据文件时出错: {str(e)}")
            wx.CallAfter(self.app_frame.sidebar_panel.show_progress, False)
            wx.CallAfter(self.on_data_load_error, "所有文件", str(e))
    
    def on_single_data_loaded(self, pathname, encoding, data_container):
        """在UI线程中更新界面 - 单个数据加载成功
        
        Args:
            pathname: 文件路径
            encoding: 文件编码
            data_container: 数据容器对象
        """
        try:
            # 更新下拉菜单
            choices = self.app_frame.data_manager.get_data_keys()
            self.app_frame.sidebar_panel.data_choice.Set(choices)
            
            # 设置当前加载的数据为选中状态
            if choices:
                self.app_frame.sidebar_panel.data_choice.SetSelection(len(choices) - 1)  # 选择最新添加的项
            
            # 使用富文本格式显示数据
            text_content = (
                f"成功加载文件({encoding}编码): {pathname}\n"
                f"文件名: {data_container.filename}\n"
                f"本次文件解析结果如下：\n{data_container.analysis_result}\n")
            
            self.app_frame.content_panel.set_formatted_text(text_content)
        except Exception as e:
            logging.error(f"显示加载数据时出错: {str(e)}")
            self.app_frame.content_panel.set_formatted_text(f"显示数据时出错: {str(e)}")
    
    def on_data_load_error(self, pathname, error_message):
        """在UI线程中更新界面 - 数据加载失败
        
        Args:
            pathname: 文件路径
            error_message: 错误信息
        """
        try:
            logging.error(f"无法读取文件 '{pathname}': {error_message}")
            wx.MessageBox(f"无法读取文件 '{pathname}': {error_message}", "错误", wx.OK | wx.ICON_ERROR)
            self.app_frame.content_panel.set_formatted_text(f"加载文件失败: {error_message}")
            # 隐藏进度条
            self.app_frame.sidebar_panel.show_progress(False)
        except Exception as e:
            logging.error(f"处理数据加载错误时出错: {str(e)}")


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
                from datetime import datetime
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
                from datetime import datetime
                import os
                
                # 使用当前时间作为文件时间部分
                current_time = datetime.now().strftime("%Y%m%d")
                default_filename_base = f"{identifier}{current_time}"
                default_analysis_filename = f"{default_filename_base}_分析.txt"
                
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
                    wildcard="文本文件 (*.txt)|*.txt",
                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                ) as fileDialog:
                    if fileDialog.ShowModal() == wx.ID_CANCEL:
                        return

                    pathname = fileDialog.GetPath()
                    if not pathname.endswith('.txt'):
                        pathname += '.txt'
                    # 确保目录存在
                    os.makedirs(os.path.dirname(pathname) or '.', exist_ok=True)
                    
                    try:
                        # 从当前数据容器中获取分析结果，并去除格式标记
                        plain_text = self.remove_format_markers(current_container.get_analysis_result())
                        with open(pathname, 'w', encoding='utf-8') as f:
                            f.write(plain_text)
                        self.app_frame.content_panel.set_formatted_text(f"分析结果已保存至: {pathname}")
                    except Exception as e:
                        logging.error(f"保存分析结果时出错: {str(e)}")
                        wx.MessageBox(f"保存文件时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            else:
                wx.MessageBox("暂无分析数据可保存", "提示", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            logging.error(f"保存分析结果时出错: {str(e)}")
            wx.MessageBox(f"保存分析结果时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            
    def remove_format_markers(self, text):
        """移除文本中的格式标记
        
        Args:
            text (str): 包含格式标记的文本
            
        Returns:
            str: 移除格式标记后的纯文本
        """
        try:
            import re
            # 移除所有格式标记，如 [[RED]]、[[/RED]] 等
            clean_text = re.sub(r'\[\[(?:RED|YELLOW|AMBER|BLUE|BOLD)\]\]', '', text)
            clean_text = re.sub(r'\[\[\/(?:RED|YELLOW|AMBER|BLUE|BOLD)\]\]', '', clean_text)
            # 移除居中对齐产生的多余连字符
            clean_text = re.sub(r'-+\s*(.*?)\s*-+', r'\1', clean_text)
            return clean_text
        except Exception as e:
            logging.error(f"移除格式标记时出错: {str(e)}")
            return text


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


class AnalysisClearHandler(BaseEventHandler):
    """分析清除事件处理器"""
    
    def handle(self, event):
        """清除分析数据框信息"""
        try:
            self.app_frame.content_panel.set_formatted_text("")
        except Exception as e:
            logging.error(f"清除分析时出错: {str(e)}")


class QuickSaveHandler(BaseEventHandler):
    """快捷保存事件处理器"""
    
    def handle(self, event):
        """处理单个文件导出按钮点击事件"""
        try:
            # 获取当前选中的数据容器
            current_container = self.app_frame.data_manager.get_current_data()
            
            if not current_container:
                wx.MessageBox("暂无数据可保存", "提示", wx.OK | wx.ICON_INFORMATION)
                return
            
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
            
            # 生成文件名
            from datetime import datetime
            import os
            
            # 获取原始文件的目录，如果有的话
            if hasattr(current_container, 'original_path') and current_container.original_path:
                save_directory = os.path.dirname(current_container.original_path)
            else:
                # 如果没有原始路径信息，则保存到当前工作目录
                save_directory = os.getcwd()
            
            # 使用飞行数据中的时间作为文件时间部分，而不是系统当前时间
            flight_time = None
            # 尝试从发动机数据获取时间
            if (hasattr(current_container, 'engine_data') and 
                current_container.engine_data):
                flight_time = current_container.engine_data.get('takeoff_start_time')
            
            # 如果发动机数据中没有时间，尝试从数据帧获取
            if flight_time is None and hasattr(current_container, 'df') and current_container.df is not None:
                if '飞行时间' in current_container.df.columns and len(current_container.df) > 0:
                    flight_time = current_container.df['飞行时间'].iloc[0]
            
            # 如果仍然没有时间数据，则使用当前时间
            if flight_time is not None:
                current_time = flight_time.strftime("%Y%m%d")
            else:
                current_time = datetime.now().strftime("%Y%m%d")
                
            default_filename_base = f"{identifier}{current_time}"
            
            # 创建保存数据和分析结果的默认路径
            default_data_filename = f"{default_filename_base}.csv"
            default_analysis_filename = f"{default_filename_base}_分析.txt"
            
            # 构建完整路径
            default_data_path = os.path.join(save_directory, default_data_filename)
            default_analysis_path = os.path.join(save_directory, default_analysis_filename)
            
            try:
                # 保存数据文件
                current_container.df.to_csv(default_data_path, encoding='utf-8-sig', index=False)
                
                # 保存分析结果文件（去除格式标记）
                plain_text = self.remove_format_markers(current_container.get_analysis_result())
                with open(default_analysis_path, 'w', encoding='utf-8') as f:
                    f.write(plain_text)
                
                # 显示保存结果
                message = f"快捷保存完成！\n\n数据文件已保存至: {default_data_path}\n分析结果已保存至: {default_analysis_path}"
                self.app_frame.content_panel.set_formatted_text(message)
                wx.MessageBox(message, "保存成功", wx.OK | wx.ICON_INFORMATION)
                
            except Exception as e:
                logging.error(f"快捷保存时出错: {str(e)}")
                wx.MessageBox(f"快捷保存时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
                
        except Exception as e:
            logging.error(f"处理快捷保存按钮点击事件时出错: {str(e)}")
            wx.MessageBox(f"快捷保存时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            
    def remove_format_markers(self, text):
        """移除文本中的格式标记
        
        Args:
            text (str): 包含格式标记的文本
            
        Returns:
            str: 移除格式标记后的纯文本
        """
        try:
            import re
            # 移除所有格式标记，如 [[RED]]、[[/RED]] 等
            clean_text = re.sub(r'\[\[(?:RED|YELLOW|AMBER|BLUE|BOLD)\]\]', '', text)
            clean_text = re.sub(r'\[\[\/(?:RED|YELLOW|AMBER|BLUE|BOLD)\]\]', '', clean_text)
            # 移除居中对齐产生的多余连字符
            clean_text = re.sub(r'-+\s*(.*?)\s*-+', r'\1', clean_text)
            return clean_text
        except Exception as e:
            logging.error(f"移除格式标记时出错: {str(e)}")
            return text


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


class BatchProcessHandler(BaseEventHandler):
    """批量处理事件处理器"""
    
    def __init__(self, app_frame):
        super().__init__(app_frame)
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.encoding_cache = {}  # 添加编码缓存以提高性能
        
    def handle(self, event):
        """处理批量处理按钮点击事件"""
        try:
            # 选择文件夹
            with wx.DirDialog(
                self.app_frame,
                message="选择包含CSV文件的文件夹",
                style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
            ) as dirDialog:
                if dirDialog.ShowModal() == wx.ID_CANCEL:
                    return
                    
                folder_path = dirDialog.GetPath()
                
            # 显示正在处理的消息
            self.app_frame.content_panel.set_formatted_text("正在扫描文件，请稍候...")
            self.app_frame.sidebar_panel.show_progress(True)
            self.app_frame.sidebar_panel.update_progress(0, "正在扫描文件...")
            
            # 使用线程池处理文件扫描和处理，避免阻塞UI
            future = self.executor.submit(self._process_folder, folder_path)
            # 注册回调函数处理结果
            future.add_done_callback(self._on_batch_process_complete)
        except Exception as e:
            logging.error(f"处理批量处理按钮点击事件时出错: {str(e)}")
            wx.MessageBox(f"批量处理时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            
    def _process_folder(self, folder_path):
        """处理文件夹中的所有CSV文件"""
        try:
            # 获取所有CSV文件（递归搜索）
            csv_files = self._find_csv_files(folder_path)
            
            # 过滤出不符合项目命名规则的文件
            unmatched_files = self._filter_unmatched_files(csv_files)
            
            total_files = len(unmatched_files)
            if total_files == 0:
                return "未找到需要处理的文件", [], 0, 0
                
            # 创建data_deal文件夹
            output_folder = self._create_output_folder(folder_path)
            
            # 使用线程池并行处理文件以提高I/O性能
            processed_count, error_files = self._process_files_in_parallel(unmatched_files, output_folder, total_files)
            
            # 完成处理
            wx.CallAfter(self.app_frame.sidebar_panel.update_progress, 100, "处理完成")
            return "批量处理完成", error_files, total_files, processed_count
        except Exception as e:
            logging.error(f"批量处理过程中出错: {str(e)}")
            raise e
    
    def _create_output_folder(self, folder_path):
        """创建输出文件夹
        
        Args:
            folder_path (str): 输入文件夹路径
            
        Returns:
            str: 输出文件夹路径
        """
        output_folder = os.path.join(folder_path, "data_deal")
        os.makedirs(output_folder, exist_ok=True)
        return output_folder
    
    def _process_files_in_parallel(self, unmatched_files, output_folder, total_files):
        """并行处理文件
        
        Args:
            unmatched_files (list): 需要处理的文件列表
            output_folder (str): 输出文件夹路径
            total_files (int): 总文件数
            
        Returns:
            tuple: (processed_count, error_files) 处理成功的文件数和错误文件列表
        """
        processed_count = 0
        error_files = []
        
        # 动态调整线程数：文件越多，使用的线程越多（但不超过系统限制）
        optimal_workers = min(MAX_WORKERS, max(1, total_files // 2))
        
        # 使用线程池并行处理文件
        futures = []
        with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
            for i, file_path in enumerate(unmatched_files):
                future = executor.submit(self._process_single_file, file_path, output_folder, i, total_files)
                futures.append((future, file_path, i))
            
            # 收集结果
            for future, file_path, index in futures:
                try:
                    future.result()  # 等待任务完成
                    processed_count += 1
                except Exception as e:
                    logging.error(f"处理文件 {file_path} 时出错: {str(e)}")
                    error_files.append((file_path, str(e)))
                
                # 更新进度
                progress = int(((processed_count + len(error_files)) / total_files) * 100)
                wx.CallAfter(self.app_frame.sidebar_panel.update_progress, progress, 
                             f"已完成: {processed_count}/{total_files}")
        
        return processed_count, error_files
            
    def _find_csv_files(self, folder_path):
        """递归查找文件夹中的所有CSV文件"""
        csv_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.csv'):
                    csv_files.append(os.path.join(root, file))
        return csv_files
        
    def _filter_unmatched_files(self, csv_files):
        """过滤出不符合项目命名规则的文件"""
        # 项目命名规则: [F|D|N][8位数字].csv
        import re
        pattern = re.compile(r'^[FDN]\d{8}\.csv$')
        
        unmatched_files = []
        for file_path in csv_files:
            filename = os.path.basename(file_path)
            if not pattern.match(filename):
                unmatched_files.append(file_path)
        return unmatched_files
        
    def _process_single_file(self, file_path, output_folder, index, total_files):
        """处理单个CSV文件"""
        try:
            # 更新进度
            filename = os.path.basename(file_path)
            wx.CallAfter(self.app_frame.sidebar_panel.update_progress, 
                         int((index / total_files) * 5), 
                         f"正在处理: {filename}")
            
            # 检测文件编码（使用缓存）
            encoding = self._detect_file_encoding_cached(file_path)
            
            # 读取CSV文件
            df = pd.read_csv(file_path, encoding=encoding)
            
            # 分析数据（复用DataManager实例）
            data_manager = self.app_frame.data_manager
            analysis_result = data_manager.data_analyzer.analyze(df)
            
            # 生成文件名前缀
            filename_prefix = self._generate_filename_prefix(analysis_result)
            
            # 保存数据文件
            data_file_path = os.path.join(output_folder, f"{filename_prefix}.csv")
            df.to_csv(data_file_path, encoding='utf-8-sig', index=False)
            
            # 保存分析结果
            analysis_file_path = os.path.join(output_folder, f"{filename_prefix}_分析.txt")
            with open(analysis_file_path, 'w', encoding='utf-8') as f:
                f.write(self._format_analysis_result(analysis_result))
                
        except Exception as e:
            logging.error(f"处理单个文件 {file_path} 时出错: {str(e)}")
            raise e
            
    def _detect_file_encoding_cached(self, filepath, encodings=['utf-8', 'gbk', 'gb2312', 'latin1']):
        """检测文件编码（带缓存）"""
        # 检查缓存
        if filepath in self.encoding_cache:
            return self.encoding_cache[filepath]
            
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    f.read(1024)  # 读取前1024个字符
                logging.info(f"使用 {encoding} 编码成功读取文件头部")
                self.encoding_cache[filepath] = encoding  # 缓存结果
                return encoding
            except UnicodeDecodeError:
                logging.warning(f"使用 {encoding} 编码读取文件失败")
                continue
        raise Exception(f"无法确定文件 {filepath} 的编码")
        
    def _generate_filename_prefix(self, analysis_result):
        """生成文件名前缀"""
        try:
            # 确定文件标识符 (F: 飞行架次, D: 地面试车, N: 未开车)
            identifier = "N"  # 默认为未开车
            
            engine_data = getattr(analysis_result, 'engine_data', {})
            if engine_data and engine_data.get('has_takeoff_info'):
                # 检查是否有起飞信息来判断是飞行还是地面试验
                start_time = engine_data.get('takeoff_start_time')
                end_time = engine_data.get('takeoff_end_time')
                
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
            
            # 使用飞行数据中的时间作为文件时间部分，而不是系统当前时间
            flight_time = None
            # 尝试从发动机数据获取时间
            if engine_data:
                flight_time = engine_data.get('takeoff_start_time')
            
            # 如果发动机数据中没有时间，尝试从数据帧获取
            df = getattr(analysis_result, 'df', None)
            if flight_time is None and df is not None:
                if '飞行时间' in df.columns and len(df) > 0:
                    flight_time = df['飞行时间'].iloc[0]
            
            # 如果仍然没有时间数据，则使用当前时间
            from datetime import datetime
            if flight_time is not None:
                current_time = flight_time.strftime("%Y%m%d")
            else:
                current_time = datetime.now().strftime("%Y%m%d")
                
            return f"{identifier}{current_time}"
        except Exception as e:
            logging.error(f"生成文件名前缀时出错: {str(e)}")
            from datetime import datetime
            return f"N{datetime.now().strftime('%Y%m%d')}"
            
    def _format_analysis_result(self, analysis_result):
        """格式化分析结果"""
        try:
            text_parts = []
            
            # 添加各个分析模块的结果
            if hasattr(analysis_result, 'text_engine') and analysis_result.text_engine:
                text_parts.append(analysis_result.text_engine)
            if hasattr(analysis_result, 'text_fuel') and analysis_result.text_fuel:
                text_parts.append(analysis_result.text_fuel)
            if hasattr(analysis_result, 'text_power') and analysis_result.text_power:
                text_parts.append(analysis_result.text_power)
            if hasattr(analysis_result, 'text_cas') and analysis_result.text_cas:
                text_parts.append(analysis_result.text_cas)
                
            return "\n".join(text_parts) if text_parts else "无分析结果"
        except Exception as e:
            logging.error(f"格式化分析结果时出错: {str(e)}")
            return "分析结果格式化失败"
            
    def _on_batch_process_complete(self, future):
        """批量处理完成回调"""
        try:
            message, error_files, total_files, processed_count = future.result()
            
            # 准备结果显示
            result_text = f"【{message}】\n\n"
            result_text += f"总计文件数: {total_files}\n"
            result_text += f"成功处理数: {processed_count}\n"
            result_text += f"处理失败数: {len(error_files)}\n"
            
            if error_files:
                result_text += "\n失败文件列表:\n"
                for file_path, error in error_files:
                    result_text += f"- {file_path}: {error}\n"
            
            # 在UI线程中更新界面
            wx.CallAfter(self._update_ui_after_processing, result_text)
        except Exception as e:
            logging.error(f"处理批量处理完成回调时出错: {str(e)}")
            wx.CallAfter(
                self._update_ui_after_processing, 
                f"【处理完成】\n\n处理过程中出现错误: {str(e)}"
            )
            
    def _update_ui_after_processing(self, result_text):
        """在UI线程中更新界面"""
        try:
            self.app_frame.content_panel.set_formatted_text(result_text)
            self.app_frame.sidebar_panel.show_progress(False)
            wx.MessageBox(result_text, "批量处理完成", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            logging.error(f"更新界面时出错: {str(e)}")


class EventHandlers:
    """事件处理类"""
    
    def __init__(self, app_frame):
        """初始化事件处理器
        
        Args:
            app_frame: 应用程序主窗口实例
        """
        try:
            self.app_frame = app_frame
            
            # 创建各类专门的事件处理器
            self.route_visualization_handler = RouteVisualizationHandler(app_frame)
            self.data_loader_handler = DataLoaderHandler(app_frame)
            self.data_save_handler = DataSaveHandler(app_frame)
            self.analysis_save_handler = AnalysisSaveHandler(app_frame)
            self.data_clear_handler = DataClearHandler(app_frame)
            self.analysis_clear_handler = AnalysisClearHandler(app_frame)
            self.quick_save_handler = QuickSaveHandler(app_frame)
            self.batch_process_handler = BatchProcessHandler(app_frame)  # 添加批量处理处理器
            self.data_choice_handler = DataChoiceHandler(app_frame)
            self.close_handler = CloseHandler(app_frame)
        except Exception as e:
            logging.error(f"初始化事件处理器时出错: {str(e)}")
            raise e
    
    def on_route_visualization(self, event):
        """处理航路点绘制按钮点击事件"""
        self.route_visualization_handler.handle(event)
    
    def load_data(self, event):
        """加载CSV数据文件"""
        self.data_loader_handler.handle(event)
    
    def save_current_data(self, event):
        """保存当前选中的数据"""
        self.data_save_handler.handle(event)
    
    def save_analysis(self, event):
        """保存分析结果"""
        self.analysis_save_handler.handle(event)
    
    def remove_current_data(self, event):
        """清除当前选中的数据"""
        self.data_clear_handler.handle(event)
    
    def remove_analysis(self, event):
        """清除分析数据框信息"""
        self.analysis_clear_handler.handle(event)
    
    def single_button_event_1(self, event):
        """处理单个文件导出按钮点击事件"""
        self.quick_save_handler.handle(event)
    
    def batch_process(self, event):
        """处理批量处理按钮点击事件"""
        self.batch_process_handler.handle(event)
    
    def on_data_choice(self, event):
        """处理数据选择变化事件"""
        self.data_choice_handler.handle(event)
    
    def on_close(self, event):
        """处理窗口关闭事件"""
        self.close_handler.handle(event)