#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CAS数据分析核心模块
=================

专门负责CAS告警数据的分析处理，不涉及文本生成。
"""

import logging
import os
from typing import Dict, Any
from datetime import datetime

import pandas as pd

from ..config import CAS_CONFIG
from ..utils import merge_continuous_time_periods
from ..column_config import CAS_COLUMNS, GENERAL_COLUMNS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class CasDataProcessor:
    """CAS数据处理器类
    
    该类专门负责CAS告警数据的分析处理，严格遵守单一职责原则。
    """
    
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
        try:
            # 初始化返回数据
            cas_result = {
                'type': 'cas',
                'alarms': [],
                'is_empty': False,
                'missing_time_column': False,
                'no_alarm_columns': False
            }

            if df.empty:
                cas_result['is_empty'] = True
                return cas_result

            time_columns = [col for col in df.columns if GENERAL_COLUMNS['FLIGHT_TIME'] in col]
            if not time_columns:
                cas_result['missing_time_column'] = True
                return cas_result

            time_column = time_columns[0]  # 使用第一个找到的时间列

            alarm_columns = df.filter(like=CAS_COLUMNS['ALARM']).columns
            if len(alarm_columns) == 0:
                # 尝试其他可能的告警列名模式
                alarm_columns = [col for col in df.columns if '告警' in col]
                if not alarm_columns:
                    cas_result['no_alarm_columns'] = True
                    return cas_result

            # 优化内存使用：只选择需要的列进行处理
            selected_columns = [time_column] + list(alarm_columns)
            df_cas = df[selected_columns].copy()
            
            alarm_periods_dict = {}

            for column in alarm_columns:
                periods = self.extract_alarm_periods(df_cas, column, time_column)
                if periods:
                    alarm_periods_dict[column] = periods

            # 新建 alarms 数据列表
            alarms = []
            for column, periods in alarm_periods_dict.items():
                for start, end in periods:
                    # 添加时间范围过滤条件
                    # 确保engine_start_time和engine_end_time是datetime类型
                    if engine_start_time is not None and not isinstance(engine_start_time, (pd.Timestamp, datetime)):
                        logging.warning(f"engine_start_time不是datetime类型: {type(engine_start_time)}")
                        engine_start_time = None
                    if engine_end_time is not None and not isinstance(engine_end_time, (pd.Timestamp, datetime)):
                        logging.warning(f"engine_end_time不是datetime类型: {type(engine_end_time)}")
                        engine_end_time = None
                        
                    if (engine_start_time is None or start >= engine_start_time) and (engine_end_time is None or end <= engine_end_time):
                        # 确保start和end是datetime类型
                        if not isinstance(start, (pd.Timestamp, datetime)) or not isinstance(end, (pd.Timestamp, datetime)):
                            logging.warning(f"start或end不是datetime类型: start={type(start)}, end={type(end)}")
                            continue
                            
                        duration = (end - start).total_seconds() + 1
                        minutes, seconds = divmod(int(duration), 60)
                        duration_str = f"{minutes} 分钟 {seconds} 秒" if duration >= 60 else f"{duration:.0f} 秒"
                        alarms.append({
                            'name': column,
                            'start_time': start.strftime('%H:%M:%S'),
                            'end_time': end.strftime('%H:%M:%S'),
                            'duration': duration_str
                        })

            cas_result['alarms'] = alarms
            
            return cas_result
        except Exception as e:
            logging.error(f"CAS分析过程中出错: {e}")
            return {
                'type': 'cas',
                'alarms': [],
                'is_empty': False,
                'missing_time_column': False,
                'no_alarm_columns': False,
                'errors': [f"CAS分析过程中出错: {str(e)}"]
            }
    
    def extract_alarm_periods(self, df_cas, column, time_column):
        """
        提取某一列的告警时间段
        
        Args:
            df_cas (pandas.DataFrame): CAS数据
            column (str): 列名
            time_column (str): 时间列名
            
        Returns:
            list: 告警时间段列表
        """
        try:
            mask = df_cas[column] == 1
            assert mask.ndim == 1, f"索引条件 {column} 不是一维的"
            alarm_times = df_cas.loc[mask, time_column]
            if isinstance(alarm_times, pd.DataFrame):
                alarm_times = alarm_times.squeeze()
            
            # 使用通用的时间段合并函数
            periods = merge_continuous_time_periods(alarm_times)
            return [(period['start_time'], period['end_time']) for period in periods]
        except KeyError:
            logging.warning(f"列 {column} 或 '{time_column}' 列存在问题")
            return []
        except AssertionError as e:
            logging.warning(f"断言错误: {e}")
            return []
        except Exception as e:
            logging.warning(f"提取告警时间段时出错: {e}")
            return []