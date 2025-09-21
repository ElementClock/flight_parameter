#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CAS告警分析模块
===============

分析CAS告警数据，识别告警时间段、类型及持续时间统计。
"""

import logging
from datetime import datetime

import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


def find_alarm_periods(alarm_times):
    """找到连续告警的时间段
    
    Args:
        alarm_times: 告警时间序列
        
    Returns:
        list: 告警时间段列表
    """
    try:
        if alarm_times.empty:
            return []

        periods = []
        start_time = None

        for i, time in enumerate(alarm_times):
            if start_time is None:
                start_time = time

            # 判断是否连续，只要存在间断，则结束当前时间段
            if i < len(alarm_times) - 1 and (alarm_times.iloc[i + 1] - time).total_seconds() > 1:
                end_time = time
                periods.append((start_time, end_time))
                start_time = None
            elif i == len(alarm_times) - 1:
                end_time = time
                periods.append((start_time, end_time))

        return periods
    except Exception as e:
        logging.error(f"查找告警时间段时出错: {str(e)}")
        return []


def extract_alarm_periods(df_cas, column):
    """
    提取某一列的告警时间段
    
    Args:
        df_cas (pandas.DataFrame): CAS数据
        column (str): 列名
        
    Returns:
        list: 告警时间段列表
    """
    try:
        mask = df_cas[column] == 1
        assert mask.ndim == 1, f"索引条件 {column} 不是一维的"
        alarm_times = df_cas.loc[mask, '飞行时间']
        if isinstance(alarm_times, pd.DataFrame):
            alarm_times = alarm_times.squeeze()
        return find_alarm_periods(alarm_times) if not alarm_times.empty else []
    except KeyError:
        logging.warning(f"列 {column} 或 '飞行时间' 列存在问题")
        return []
    except AssertionError as e:
        logging.warning(f"断言错误: {e}")
        return []
    except Exception as e:
        logging.warning(f"提取告警时间段时出错: {e}")
        return []


def analyze_cas(df, engine_start_time, engine_end_time):
    """
    告警分析主函数
    
    Args:
        df (pandas.DataFrame): 飞行数据
        engine_start_time: 发动机启动时间
        engine_end_time: 发动机关车时间
        
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

        if '飞行时间' not in df.columns:
            cas_result['missing_time_column'] = True
            return cas_result

        alarm_columns = df.filter(like='显示告警系统').columns
        if alarm_columns.empty:
            cas_result['no_alarm_columns'] = True
            return cas_result

        # 优化内存使用：只选择需要的列进行处理
        selected_columns = ['飞行时间'] + alarm_columns.tolist()
        df_cas = df[selected_columns].copy()
        
        alarm_periods_dict = {}

        for column in alarm_columns:
            periods = extract_alarm_periods(df_cas, column)
            if periods:
                alarm_periods_dict[column] = periods

        # 新建 alarms 数据列表
        alarms = []
        for column, periods in alarm_periods_dict.items():
            for start, end in periods:
                # 添加时间范围过滤条件
                if (engine_start_time is None or start >= engine_start_time) and (engine_end_time is None or end <= engine_end_time):
                    duration = (end - start).total_seconds()+1
                    minutes, seconds = divmod(int(duration), 60)
                    duration_str = f"{minutes} 分钟 {seconds} 秒" if duration >= 60 else f"{duration:.0f} 秒"
                    alarms.append({
                        'name': column,
                        'start_time': start.strftime('%H:%M:%S'),
                        'end_time': end.strftime('%H:%M:%S'),
                        'duration': duration_str
                    })

        cas_result['alarms'] = alarms
        
        # 清理临时数据以释放内存
        del df_cas
        
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


def format_cas_output(cas_data):
    """生成带标识符的CAS分析文本输出
    
    Args:
        cas_data (dict): CAS分析数据
        
    Returns:
        str: 格式化的文本结果
    """
    try:
        result = []
        
        # 检查错误情况
        if cas_data['is_empty']:
            result.append("输入的 DataFrame 为空，请检查数据源")
            return "\n".join(result)
        if cas_data['missing_time_column']:
            result.append("缺少 '飞行时间' 列，请检查数据源")
            return "\n".join(result)
        if cas_data['no_alarm_columns']:
            result.append("没有找到告警相关的列，请检查数据源")
            return "\n".join(result)
        if 'errors' in cas_data:
            result.append("CAS分析过程中出错:")
            result.extend(cas_data['errors'])
            return "\n".join(result)

        # 检查告警数据
        if not cas_data['alarms']:
            result.append("没有发现告警")
            return "\n".join(result)

        # 格式化告警数据
        result.append("告警信息:")
        for alarm in cas_data['alarms']:
            result.append(f"{alarm['name']} - {alarm['start_time']} - {alarm['end_time']} - {alarm['duration']}")

        return "\n".join(result)
    except Exception as e:
        logging.error(f"格式化CAS输出时出错: {str(e)}")
        return f"格式化CAS输出时出错: {str(e)}"


def load_alarm_levels():
    """加载告警级别信息
    
    Returns:
        dict: 告警ID到告警级别的映射字典
    """
    try:
        alarm_levels = {
            1: '一级告警',
            2: '二级告警',
            3: '三级告警',
            4: '四级告警',
            5: '五级告警',
            6: '六级告警',
            7: '七级告警',
            8: '八级告警',
            9: '九级告警',
            10: '十级告警',
        }
        return alarm_levels
    except Exception as e:
        logging.error(f"加载告警级别信息时出错: {str(e)}")
        return {}