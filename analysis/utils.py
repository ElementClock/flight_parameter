#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分析模块通用工具函数
==================

提供分析模块中常用的工具函数，避免代码重复。
"""

import logging
from typing import List, Dict, Any
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


def merge_continuous_time_periods(times: pd.Series, values: pd.Series = None, time_threshold: float = 1.0) -> List[Dict[str, Any]]:
    """将连续的时间点合并为时间段
    
    Args:
        times (pd.Series): 时间序列
        values (pd.Series, optional): 对应的值序列
        time_threshold (float): 判断连续的时间阈值（秒）
        
    Returns:
        List[Dict[str, Any]]: 时间段列表，每个元素包含start_time、end_time和可选的特征值
    """
    if len(times) == 0:
        return []
    
    time_periods = []
    
    # 初始化第一个时间段
    start_time = times.iloc[0]
    end_time = times.iloc[0]
    
    # 如果提供了值序列，则跟踪特征值
    if values is not None:
        if callable(getattr(values, 'iloc', None)):
            feature_value = values.iloc[0]
            min_value = feature_value if pd.notna(feature_value) else None
            max_value = feature_value if pd.notna(feature_value) else None
        else:
            min_value = None
            max_value = None
    else:
        min_value = None
        max_value = None
    
    # 遍历所有时间点
    for i in range(1, len(times)):
        current_time = times.iloc[i]
        # 检查是否与前一个时间点连续（时间差不超过阈值）
        time_diff = (current_time - times.iloc[i-1]).total_seconds()
        if time_diff <= time_threshold:
            # 更新结束时间和特征值
            end_time = current_time
            if values is not None and callable(getattr(values, 'iloc', None)):
                current_value = values.iloc[i]
                if pd.notna(current_value):
                    if min_value is None or current_value < min_value:
                        min_value = current_value
                    if max_value is None or current_value > max_value:
                        max_value = current_value
        else:
            # 结束当前时间段并开始新时间段
            period = {
                'start_time': start_time,
                'end_time': end_time
            }
            if min_value is not None:
                period['min_value'] = min_value
            if max_value is not None:
                period['max_value'] = max_value
                
            time_periods.append(period)
            
            # 开始新的时间段
            start_time = current_time
            end_time = current_time
            if values is not None and callable(getattr(values, 'iloc', None)):
                feature_value = values.iloc[i]
                min_value = feature_value if pd.notna(feature_value) else None
                max_value = feature_value if pd.notna(feature_value) else None
            else:
                min_value = None
                max_value = None
    
    # 添加最后一个时间段
    period = {
        'start_time': start_time,
        'end_time': end_time
    }
    if min_value is not None:
        period['min_value'] = min_value
    if max_value is not None:
        period['max_value'] = max_value
        
    time_periods.append(period)
    
    return time_periods


def format_exception(e: Exception, context: str = "") -> str:
    """格式化异常信息
    
    Args:
        e (Exception): 异常对象
        context (str): 异常上下文描述
        
    Returns:
        str: 格式化的异常信息
    """
    if context:
        return f"{context}: {str(e)}"
    else:
        return str(e)


def safe_get_statistic(series: pd.Series, statistic: str) -> Any:
    """安全地获取数据统计值
    
    Args:
        series (pd.Series): 数据序列
        statistic (str): 统计类型 ('mean', 'min', 'max', 'first', 'last')
        
    Returns:
        Any: 统计值，如果出错则返回None
    """
    try:
        if len(series) == 0:
            return None
            
        if statistic == 'mean':
            return series.mean() if len(series) > 0 else None
        elif statistic == 'min':
            return series.min() if len(series) > 0 else None
        elif statistic == 'max':
            return series.max() if len(series) > 0 else None
        elif statistic == 'first':
            return series.iloc[0] if len(series) > 0 else None
        elif statistic == 'last':
            return series.iloc[-1] if len(series) > 0 else None
        else:
            return None
    except Exception:
        return None