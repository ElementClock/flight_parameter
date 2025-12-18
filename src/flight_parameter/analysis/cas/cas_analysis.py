#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CAS告警分析模块
===============

分析CAS告警数据，识别告警时间段、类型及持续时间统计。

功能特性：
---------
1. 识别CAS告警时间段
2. 分析不同告警类型的发生时间
3. 提供告警持续时间统计
4. 按照警告级、戒备级、提示级、状态级对告警分类

使用方法：
--------
>>> analyzer = CasAnalysis()
>>> result = analyzer.analyze(dataframe)
>>> text_report = analyzer.generate_text(result)

注意事项：
--------
- 输入数据必须包含飞行时间和CAS告警相关列
- 需要cas_level.csv文件支持告警级别分类
"""

import logging
import os
from typing import Dict, Any
from datetime import datetime

import pandas as pd

from ..analysis_interface import AnalysisInterface
from ..config import CAS_CONFIG
from ..utils import merge_continuous_time_periods
from ..column_config import CAS_COLUMNS, GENERAL_COLUMNS
from .cas_data_processor import CasDataProcessor
from .cas_report_generator import CasReportGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class CasAnalysis(AnalysisInterface):
    """CAS告警分析类
    
    该类提供了完整的CAS告警数据分析功能，包括数据解析、特征提取和报告生成。
    为了遵守单一职责原则，实际的数据处理和文本生成分别委托给专门的类。
    
    属性：
    ------
    _processor: CasDataProcessor
        CAS数据处理器
    _generator: CasReportGenerator
        CAS报告生成器
    
    方法：
    -----
    analyze(df, engine_start_time=None, engine_end_time=None, **kwargs) -> Dict[str, Any]
        告警分析主函数
    generate_text(cas_data: Dict[str, Any]) -> str
        生成带标识符的CAS分析文本输出
    """
    
    def __init__(self):
        """初始化CAS分析器"""
        self._processor = CasDataProcessor()
        self._generator = CasReportGenerator()
    
    def get_name(self) -> str:
        """获取分析器名称
        
        Returns:
            str: 分析器名称
        """
        return "cas"
    
    def analyze(self, df, engine_start_time=None, engine_end_time=None, **kwargs) -> Dict[str, Any]:
        """
        告警分析主函数
        
        Args:
            df (pandas.DataFrame): 飞行数据
            engine_start_time: 发动机启动时间
            engine_end_time: 发动机关车时间
            **kwargs: 其他参数
            
        Returns:
            dict: CAS分析结果
        """
        # 委托给专门的数据处理器
        return self._processor.analyze(df, engine_start_time, engine_end_time, **kwargs)
    
    def generate_text(self, cas_data: Dict[str, Any]) -> str:
        """生成带标识符的CAS分析文本输出
        
        Args:
            cas_data (dict): CAS分析数据
            
        Returns:
            str: 格式化的文本结果
        """
        # 委托给专门的报告生成器
        return self._generator.generate_text(cas_data)
