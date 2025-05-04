import pandas as pd
import numpy as np
import logging
from datetime import timedelta

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def find_alarm_periods(alarm_times):
    """找到连续告警的时间段"""
    if alarm_times.empty:
        return []

    periods = []
    start_time = None
    alarm_times = pd.to_datetime(alarm_times, format='%H:%M:%S')  # 确保时间格式一致

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


def extract_alarm_periods(df_cas, column):
    """
    提取某一列的告警时间段
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


def analyze_cas(df):
    """
    告警分析主函数
    """
    result = []

    if df.empty:
        result.append("输入的 DataFrame 为空，请检查数据源")
        return "\n".join(result)

    if '飞行时间' not in df.columns:
        result.append("DataFrame 中缺少 '飞行时间' 列")
        return "\n".join(result)

    alarm_columns = df.filter(like='显示告警系统').columns
    if alarm_columns.empty:
        result.append("未找到包含 '显示告警系统' 的列")
        return "\n".join(result)

    df_cas = df[['飞行时间'] + alarm_columns.tolist()]
    alarm_periods_dict = {}

    for column in alarm_columns:
        periods = extract_alarm_periods(df_cas, column)
        if periods:
            alarm_periods_dict[column] = periods

    for column, periods in alarm_periods_dict.items():
        result.append(f"{column}:")
        for start, end in periods:
            duration = (end - start).total_seconds()
            if duration >= 60:
                minutes, seconds = divmod(int(duration), 60)
                result.append(
                    f"  告警时间从 {start.strftime('%H:%M:%S')} 到 {end.strftime('%H:%M:%S')}，持续时间 {minutes} 分钟 {seconds} 秒")
            else:
                result.append(
                    f"  告警时间从 {start.strftime('%H:%M:%S')} 到 {end.strftime('%H:%M:%S')}，持续时间 {duration:.0f} 秒")

    return "\n".join(result)
