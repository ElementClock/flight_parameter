#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据管理模块
============

管理飞行数据的加载、存储和分析结果。
"""

import logging
from typing import Dict, Any, Optional

import pandas as pd

from ..analysis.data_analyzer import DataAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class DataContainer:
    """数据容器类，用于存储单个文件的数据和分析结果"""
    
    def __init__(self, df: pd.DataFrame, filename: str, analysis_result=None):
        """初始化数据容器
        
        Args:
            df: 原始数据DataFrame
            filename: 文件名
            analysis_result: 分析结果对象
        """
        try:
            self.df = df
            self.filename = filename
            self.original_path = None  # 保存原始文件路径
            
            # 初始化分析结果文本
            text_parts = []
            
            # 添加各个分析模块的结果
            # 检查分析结果对象是否包含特定模块的结果，并将其添加到文本部分列表中
            if hasattr(analysis_result, 'text_engine') and analysis_result.text_engine:
                text_parts.append(analysis_result.text_engine)
            if hasattr(analysis_result, 'text_fuel') and analysis_result.text_fuel:
                text_parts.append(analysis_result.text_fuel)
            if hasattr(analysis_result, 'text_power') and analysis_result.text_power:
                text_parts.append(analysis_result.text_power)
            if hasattr(analysis_result, 'text_cas') and analysis_result.text_cas:
                text_parts.append(analysis_result.text_cas)
            
            # 将所有文本部分用换行符连接，如果没有文本部分则设为空字符串
            self.analysis_result = "\n".join(text_parts) if text_parts else ""
            
            # 保存特定的分析数据
            # 使用getattr安全地从分析结果对象中提取数据，如果不存在则返回默认值
            self.df = getattr(analysis_result, 'df', None)
            self.engine_data = getattr(analysis_result, 'engine_data', None)
            self.fuel_data = getattr(analysis_result, 'fuel_data', None)
            self.power_data = getattr(analysis_result, 'power_data', None)
            self.cas_data = getattr(analysis_result, 'cas_data', None)
            self.engine_start_time = getattr(analysis_result, 'engine_start_time', None)
            self.engine_end_time = getattr(analysis_result, 'engine_end_time', None)
        except Exception as e:
            logging.error(f"初始化数据容器时出错: {str(e)}")
            raise e

    def get_analysis_result(self):
        """获取分析结果文本"""
        return self.analysis_result


class DataManager:
    """数据管理器类，用于管理多个数据容器"""
    
    def __init__(self):
        """初始化数据管理器"""
        try:
            self.data_containers: Dict[str, DataContainer] = {}
            self.current_data_key: Optional[str] = None
            self.data_analyzer = DataAnalyzer()
        except Exception as e:
            logging.error(f"初始化数据管理器时出错: {str(e)}")
            raise e
    
    def add_data(self, df: pd.DataFrame, filename: str, progress_callback=None, original_path=None):
        """添加数据并进行分析
        
        Args:
            df: 原始数据DataFrame
            filename: 文件名
            progress_callback: 进度回调函数
            original_path: 原始文件路径
            
        Returns:
            tuple: (数据容器对象, 错误信息)
        """
        try:
            # 分析数据
            analysis_result = self.data_analyzer.analyze(df, progress_callback=progress_callback)
            
            # 创建数据容器
            container = DataContainer(df, filename, analysis_result)
            container.original_path = original_path  # 保存原始路径
            
            # 使用文件名作为键存储数据容器
            self.data_containers[filename] = container
            
            # 设置为当前数据
            self.current_data_key = filename
            
            return container, None
        except Exception as e:
            logging.error(f"添加数据时出错: {str(e)}")
            return None, str(e)
    
    def remove_data(self, key: str) -> bool:
        """移除指定的数据
        
        Args:
            key: 数据键名
            
        Returns:
            bool: 是否成功移除
        """
        try:
            if key in self.data_containers:
                del self.data_containers[key]
                if self.current_data_key == key:
                    self.current_data_key = None
                return True
            return False
        except Exception as e:
            logging.error(f"移除数据时出错: {str(e)}")
            return False
    
    def select_data(self, key: str):
        """选择当前数据
        
        Args:
            key: 数据键名
        """
        try:
            if key in self.data_containers:
                self.current_data_key = key
        except Exception as e:
            logging.error(f"选择数据时出错: {str(e)}")
    
    def get_current_data(self) -> Optional[DataContainer]:
        """获取当前选中的数据容器
        
        Returns:
            DataContainer: 当前数据容器，如果没有则返回None
        """
        try:
            if self.current_data_key and self.current_data_key in self.data_containers:
                return self.data_containers[self.current_data_key]
            return None
        except Exception as e:
            logging.error(f"获取当前数据时出错: {str(e)}")
            return None
    
    def get_data_keys(self):
        """获取所有数据键名列表
        
        Returns:
            list: 数据键名列表
        """
        try:
            return list(self.data_containers.keys())
        except Exception as e:
            logging.error(f"获取数据键名时出错: {str(e)}")
            return []