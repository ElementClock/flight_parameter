#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
发动机分析模块
==============

分析飞行数据中的发动机相关信息，包括发动机启动和关车时间、转速变化、点火状态等。

功能特性：
---------
1. 自动识别发动机启动和关车时间点
2. 检测发动机转速变化情况
3. 分析发动机点火状态
4. 识别发动机起飞状态时间段
5. 检测发动机重启事件

使用方法：
--------
>>> analyzer = EngineAnalysis()
>>> result = analyzer.analyze(dataframe)
>>> text_report = analyzer.generate_text(result)

注意事项：
--------
- 输入数据必须包含飞行时间和发动机转速列
- 发动机转速单位为百分比（0-100）
- 发动机启动阈值为10%，关车阈值为10%
"""

import logging
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime

from ..analysis_interface import AnalysisInterface
from ..logger import get_analysis_logger, log_step
from ..config import ENGINE_CONFIG
from ..column_config import ENGINE_COLUMNS, GENERAL_COLUMNS
from .engine_data_processor import EngineDataProcessor
from .engine_report_generator import EngineReportGenerator

# 获取日志记录器
logger = get_analysis_logger(__name__)


class EngineAnalysis(AnalysisInterface):
    """发动机分析类
    
    该类提供了完整的发动机数据分析功能，包括数据解析、特征提取和报告生成。
    为了遵守单一职责原则，实际的数据处理和文本生成分别委托给专门的类。
    
    属性：
    ------
    _processor: EngineDataProcessor
        发动机数据处理器
    _generator: EngineReportGenerator
        发动机报告生成器
    
    方法：
    -----
    analyze(df, **kwargs) -> Dict[str, Any]
        分析发动机数据
    generate_text(engine_data: Dict[str, Any]) -> str
        生成带标识符的发动机分析文本输出
    """
    
    def __init__(self):
        """初始化发动机分析器"""
        self._processor = EngineDataProcessor()
        self._generator = EngineReportGenerator()
    
    def get_name(self) -> str:
        """获取分析器名称
        
        Returns:
            str: 分析器名称
        """
        return "engine"
    
    @log_step("发动机数据分析")
    def analyze(self, df, **kwargs) -> Dict[str, Any]:
        """分析发动机数据
        
        Args:
            df (pandas.DataFrame): 飞行数据
            **kwargs: 其他参数，包括可能由其他分析模块传递的参数
            
        Returns:
            dict: 发动机分析结果
        """
        # 委托给专门的数据处理器
        return self._processor.analyze(df, **kwargs)
    
    def generate_text(self, engine_data: Dict[str, Any]) -> str:
        """生成带标识符的发动机分析文本输出
        
        Args:
            engine_data (dict): 包含发动机分析结果的字典，可能包含错误信息
            
        Returns:
            str: 格式化的文本结果，包含错误信息或正常分析结果
        """
        # 委托给专门的报告生成器
        return self._generator.generate_text(engine_data)
