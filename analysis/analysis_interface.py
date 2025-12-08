#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分析接口模块
============

定义分析模块的接口和数据结构，确保符合接口隔离原则。
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class AnalysisResult:
    """封装分析结果的数据类"""
    
    def __init__(self, **kwargs):
        """初始化分析结果对象
        
        Args:
            **kwargs: 任意数量的属性键值对
        """
        # 动态设置所有传入的属性
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __getattr__(self, name):
        """为不存在的属性提供默认值
        
        Args:
            name: 属性名称
            
        Returns:
            None: 当属性不存在时返回None
        """
        return None


class AnalysisInterface(ABC):
    """分析接口基类"""
    
    @abstractmethod
    def analyze(self, df, **kwargs) -> Dict[str, Any]:
        """分析数据的抽象方法
        
        Args:
            df: 要分析的数据
            **kwargs: 其他参数
            
        Returns:
            dict: 分析结果
        """
        pass
    
    @abstractmethod
    def generate_text(self, analysis_data: Dict[str, Any]) -> str:
        """生成分析结果文本的抽象方法
        
        Args:
            analysis_data: 分析数据
            
        Returns:
            str: 格式化的文本结果
        """
        pass