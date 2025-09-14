from datetime import timedelta

import pandas as pd

from analysis.cas_analysis import analyze_cas
from analysis.engine_analysis import analyze_engine


def analysis_data(df):
    df = convert_flight_time(df)

    # 动力专业汇报
    text_engine, engine_start_time, engine_end_time = analyze_engine(df)
    
    # CAS汇报
    text_cas = analyze_cas(df, engine_start_time, engine_end_time)

    # 总汇报
    text_analyze = (f"{text_engine}\n"
                    f"{text_cas}\n\n")
    
    return text_analyze, df

def convert_flight_time(df):
    """
    将飞参数据中的时间列转换为标准的北京时间格式
    
    参数:
        df (pandas.DataFrame): 包含飞参数据的DataFrame
        
    返回:
        pandas.DataFrame: 时间列已转换的DataFrame
    """
    # 获取第一列和第四列的列名
    first_col = df.columns[0]   # 飞参内部时间列 (格式: hh:mm:ss.fff)
    fourth_col = df.columns[3]  # 日期列 (格式: yy-mm-dd)
    
    # 将两列数据合并为完整的日期时间字符串
    # 格式: hh:mm:ss.fff + 年份-月份-日
    datetime_combined = df[first_col].astype(str) + ' ' + df[fourth_col].astype(str)
    
    # 转换为datetime对象，支持两位数年份格式（如25-07-11表示2025年7月11日）
    df['_datetime'] = pd.to_datetime(datetime_combined, format='%H:%M:%S.%f %y-%m-%d', errors='coerce')
    
    # 将UTC时间转换为北京时间(UTC+8)
    df['_datetime'] = df['_datetime'] + timedelta(hours=8)
    
    # 更新原数据列
    df[first_col] = df['_datetime']

    # 删除临时列
    df.rename(columns={first_col: '飞行时间'}, inplace=True)
    df.drop('_datetime', axis=1, inplace=True)

    
    return df