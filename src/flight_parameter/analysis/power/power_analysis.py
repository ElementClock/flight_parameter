#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
电源系统分析模块
===============

分析电源系统数据，包括发电机、电池状态等关键参数。
"""

import logging
from typing import Dict, Any

from ..analysis_interface import AnalysisInterface
from .power_data_processor import PowerDataProcessor
from .power_report_generator import PowerReportGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class PowerAnalysis(AnalysisInterface):
    """电源系统分析类"""
    
    def __init__(self):
        """初始化电源系统分析器"""
        self.data_processor = PowerDataProcessor()
        self.report_generator = PowerReportGenerator()
    
    def analyze(self, df, **kwargs) -> Dict[str, Any]:
        """
        分析电源系统数据
        
        Args:
            df (pandas.DataFrame): 包含电源系统数据的DataFrame
            **kwargs: 其他参数
            
        Returns:
            dict: 电源系统分析结果
        """
        # 委托给专门的数据处理器
        return self.data_processor.analyze(df, **kwargs)
    
    def generate_text(self, power_data: Dict[str, Any]) -> str:
        """生成电源系统分析结果文本
        
        Args:
            power_data (dict): 电源系统分析数据
            
        Returns:
            str: 格式化的文本结果
        """
        # 委托给专门的报告生成器
        return self.report_generator.generate_text(power_data)
