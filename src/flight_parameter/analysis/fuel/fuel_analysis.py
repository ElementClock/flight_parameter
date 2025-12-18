#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
燃油系统分析模块
===============

分析燃油系统数据，包括燃油消耗、油箱状态等关键参数。
"""

import logging
import re
from typing import Dict, Any

import pandas as pd

from ..analysis_interface import AnalysisInterface
from ..logger import get_analysis_logger, log_step
from ..utils import merge_continuous_time_periods
from ..config import FUEL_CONFIG
from ..column_config import FUEL_COLUMNS, GENERAL_COLUMNS
from .fuel_data_processor import FuelDataProcessor
from .fuel_report_generator import FuelReportGenerator

# 获取日志记录器
logger = get_analysis_logger(__name__)


class FuelAnalysis(AnalysisInterface):
    """燃油系统分析类
    
    该类提供了完整的燃油系统数据分析功能，包括数据解析、特征提取和报告生成。
    为了遵守单一职责原则，实际的数据处理和文本生成分别委托给专门的类。
    
    属性：
    ------
    _processor: FuelDataProcessor
        燃油数据处理器
    _generator: FuelReportGenerator
        燃油报告生成器
    
    方法：
    -----
    analyze(df, **kwargs) -> Dict[str, Any]
        分析燃油系统数据
    generate_text(fuel_data: Dict[str, Any]) -> str
        生成带标识符的燃油系统分析文本输出
    """
    
    def __init__(self):
        """初始化燃油系统分析器"""
        self._processor = FuelDataProcessor()
        self._generator = FuelReportGenerator()
    
    @log_step("燃油系统数据分析")
    def analyze(self, df, **kwargs) -> Dict[str, Any]:
        """
        分析燃油系统数据
        
        Args:
            df (pandas.DataFrame): 包含燃油系统数据的DataFrame
            **kwargs: 其他参数
            
        Returns:
            dict: 燃油系统分析结果
        """
        # 委托给专门的数据处理器
        return self._processor.analyze(df, **kwargs)
    
    def generate_text(self, fuel_data: Dict[str, Any]) -> str:
        """生成燃油系统分析的文本报告
        
        Args:
            fuel_data (dict): 燃油系统分析结果数据
            
        Returns:
            str: 格式化的文本结果
        """
        # 委托给专门的报告生成器
        return self._generator.generate_text(fuel_data)
