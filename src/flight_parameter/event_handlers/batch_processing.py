#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量处理事件处理器
==============

处理应用程序中的批量处理事件。
"""

import logging
import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import multiprocessing

import pandas as pd
import wx
from wx import ID_CANCEL, NOT_FOUND

# 导入我们的公共工具模块
from ..utils.file_utils import detect_encoding, is_safe_path, sanitize_filename
from .base import BaseEventHandler, MAX_WORKERS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class BatchProcessHandler(BaseEventHandler):
    """批量处理事件处理器"""
    
    def __init__(self, app_frame):
        super().__init__(app_frame)
        # 根据系统资源动态调整线程数
        optimal_workers = min(MAX_WORKERS, max(2, (multiprocessing.cpu_count() or 4) + 2))
        self.executor = ThreadPoolExecutor(max_workers=optimal_workers)
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
        
        # 动态调整线程数：根据CPU核心数和文件数量确定最优线程数
        cpu_count = multiprocessing.cpu_count() or 4
        # 线程数不超过CPU核心数的2倍，也不超过文件总数，最大不超过MAX_WORKERS
        optimal_workers = min(MAX_WORKERS, max(2, min(total_files, cpu_count * 2)))
        
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
        # F表示飞行架次文件，D表示地面试车文件，N表示未开车文件
        # 8位数字表示日期，格式为YYYYMMDD
        import re
        pattern = re.compile(r'^[FDN]\d{8}\.csv$')
        
        unmatched_files = []
        for file_path in csv_files:
            filename = os.path.basename(file_path)
            # 如果文件名不匹配命名规则，则加入待处理列表
            if not pattern.match(filename):
                unmatched_files.append(file_path)
        return unmatched_files
        
    def _process_single_file(self, file_path, output_folder, index, total_files):
        """处理单个CSV文件"""
        try:
            # 检查路径安全性
            if not is_safe_path(os.getcwd(), file_path):
                raise ValueError(f"不允许访问的文件路径: {file_path}")
                
            # 更新进度
            filename = sanitize_filename(os.path.basename(file_path))
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
            
            # 清理文件名
            filename_prefix = sanitize_filename(filename_prefix)
            
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
            
    def _detect_file_encoding_cached(self, filepath):
        """检测文件编码（带缓存）"""
        try:
            # 检查路径安全性
            if not is_safe_path(os.getcwd(), filepath):
                raise ValueError(f"不允许访问的文件路径: {filepath}")
                
            # 检查缓存
            if filepath in self.encoding_cache:
                return self.encoding_cache[filepath]
                
            # 使用公共工具函数检测编码
            encoding = detect_encoding(filepath)
            
            logging.info(f"使用 {encoding} 编码成功读取文件头部")
            self.encoding_cache[filepath] = encoding  # 缓存结果
            return encoding
        except Exception as e:
            logging.error(f"检测文件编码时出错: {str(e)}")
            raise e

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
                        # 如果发动机运行时间超过10分钟(600秒)，认为是飞行架次
                        # 这是一个经验阈值，用于区分短时间的地面试车和实际飞行
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
                # 使用飞行数据中的时间戳
                current_time = flight_time.strftime("%Y%m%d")
            else:
                # 如果没有可用的飞行时间数据，则使用当前系统时间
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
                
            return "\n\n".join(text_parts) if text_parts else "无分析结果"
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