#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
时间处理模块
==============

处理飞行数据中的时间相关列，将其转换为标准的北京时间格式。
"""

import logging
from datetime import timedelta

import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


def convert_flight_time(df):
    """
    将飞参数据中的时间列转换为标准的北京时间格式
    
    修改说明：
    - 获取第4、5、6列数据
    - 第4列为日期数据（格式：2025/10/13 或 25-10-13）
    - 第5列为标识符数据（1为可信，0为不可信）
    - 第6列为时间数据（格式：1:01:55）
    - 只保留标识符为1的可信数据
    - 合并日期和时间数据转换为datetime对象
    - 将飞行时间列移动到第一列
    
    参数:
        df (pandas.DataFrame): 包含飞参数据的DataFrame
        
    返回:
        pandas.DataFrame: 时间列已转换并移动到第一列的DataFrame
    """
    try:
        # 获取第4、5、6列的列名
        date_column, flag_column, time_column = _get_time_column_names(df)
        
        # 过滤标识符为1的可信数据
        df_filtered = _filter_reliable_data(df, flag_column)
        
        if df_filtered.empty:
            logging.warning("过滤后没有可信数据")
            return df
            
        # 解析日期列
        parsed_dates = _parse_date_column(df_filtered, date_column)
        
        # 将日期和时间数据合并为完整的日期时间字符串
        # 格式: 2025/10/13 1:01:55
        datetime_combined = parsed_dates.astype(str) + ' ' + df_filtered[time_column].astype(str)
        
        # 转换为datetime对象，支持标准日期时间格式
        df_filtered['_datetime'] = pd.to_datetime(datetime_combined, errors='coerce')
        
        # 检查是否所有时间都是NaT（Not a Time）
        if df_filtered['_datetime'].isna().all():
            logging.warning("所有时间数据都无法解析")
            # 尝试直接解析原始的时间列
            df_filtered['_datetime'] = pd.to_datetime(df_filtered[time_column], errors='coerce')
        
        # 将时间转换为北京时间(UTC+8)
        df_filtered['_datetime'] = df_filtered['_datetime'] + timedelta(hours=8)
        
        # 更新原数据列
        df_filtered[date_column] = df_filtered['_datetime']
        
        # 删除临时列和不再需要的标识符、时间列
        df_filtered.rename(columns={date_column: '飞行时间'}, inplace=True)
        if '_datetime' in df_filtered.columns:
            df_filtered.drop(['_datetime'], axis=1, inplace=True)
        if flag_column in df_filtered.columns:
            df_filtered.drop([flag_column], axis=1, inplace=True)
        if time_column in df_filtered.columns and time_column != '飞行时间':
            df_filtered.drop([time_column], axis=1, inplace=True)
        
        # 将"飞行时间"列移动到第一列
        if '飞行时间' in df_filtered.columns:
            flight_time_col = df_filtered.pop('飞行时间')
            # 使用pd.concat替代insert以避免DataFrame碎片化警告
            df_filtered = pd.concat([flight_time_col, df_filtered], axis=1)
        
        return df_filtered
    except Exception as e:
        logging.error(f"转换飞行时间时出错: {e}")
        return df


def _get_time_column_names(df):
    """获取时间相关列的列名
    
    Args:
        df (pandas.DataFrame): 包含飞参数据的DataFrame
        
    Returns:
        tuple: (date_col, flag_col, time_col) 日期列、标识符列和时间列的列名
    """
    if len(df.columns) < 6:
        # 如果列数不足，尝试查找时间相关的列
        time_columns = [col for col in df.columns if '时间' in col or '日期' in col]
        if len(time_columns) >= 3:
            date_column = time_columns[0]
            flag_column = time_columns[1] 
            time_column = time_columns[2]
        else:
            # 如果找不到足够的时间列，直接返回原始数据
            # 抛出异常或返回默认值
            raise ValueError("无法找到足够的时间相关列")
    else:
        date_column = df.columns[3]    # 第4列：日期数据
        flag_column = df.columns[4]    # 第5列：标识符数据
        time_column = df.columns[5]    # 第6列：时间数据
        
    return date_column, flag_column, time_column


def _filter_reliable_data(df, flag_column):
    """过滤标识符为1的可信数据
    
    Args:
        df (pandas.DataFrame): 原始数据
        flag_column (str): 标识符列名
        
    Returns:
        pandas.DataFrame: 过滤后的数据
    """
    if flag_column in df.columns:
        return df[df[flag_column] == 1].copy()
    else:
        return df.copy()


def _parse_date_column(df_filtered, date_column):
    """解析日期列
    
    Args:
        df_filtered (pandas.DataFrame): 过滤后的数据
        date_column (str): 日期列名
        
    Returns:
        pandas.Series: 解析后的日期数据
    """
    sample_date = str(df_filtered[date_column].iloc[0]) if not df_filtered.empty else ""
    parsed_dates = None
    
    # 根据字符长度判断日期格式
    # 通过检查样本日期的长度来推测日期格式类型
    if len(sample_date) >= 10:  # "2025/10/13" 格式，长度至少为10
        # 尝试使用 %Y/%m/%d 格式解析（年份为四位数）
        try:
            parsed_dates = pd.to_datetime(df_filtered[date_column], format='%Y/%m/%d', errors='coerce')
            # 检查是否成功解析了大部分数据
            # 如果超过一半无法解析，则认为此格式不匹配，重置为None继续尝试其他格式
            if parsed_dates.isna().sum() / len(parsed_dates) > 0.5:  # 如果超过一半无法解析
                parsed_dates = None  # 重置，尝试其他格式
        except Exception:
            parsed_dates = None
            
    elif len(sample_date) >= 8 and len(sample_date) < 10:  # "25-10-13" 格式，长度通常为8
        # 尝试使用 %y-%m-%d 格式解析（年份为两位数）
        try:
            parsed_dates = pd.to_datetime(df_filtered[date_column], format='%y-%m-%d', errors='coerce')
            # 检查是否成功解析了大部分数据
            # 如果超过一半无法解析，则认为此格式不匹配，重置为None继续尝试其他格式
            if parsed_dates.isna().sum() / len(parsed_dates) > 0.5:  # 如果超过一半无法解析
                parsed_dates = None  # 重置，尝试其他格式
        except Exception:
            parsed_dates = None
    
    # 如果基于长度的判断失败，则尝试其他方法
    if parsed_dates is None:
        # 尝试自动解析，pandas会自动尝试多种常见格式
        parsed_dates = pd.to_datetime(df_filtered[date_column], errors='coerce')
        
        # 如果自动解析失败较多（超过50%数据无法解析），则尝试指定格式进行精确解析
        if not df_filtered.empty and parsed_dates.isna().sum() / len(parsed_dates) > 0.5:
            # 尝试 %Y/%m/%d 格式
            try:
                parsed_dates_y = pd.to_datetime(df_filtered[date_column], format='%Y/%m/%d', errors='coerce')
                # 如果这种格式解析效果更好（缺失值更少），则使用
                if parsed_dates_y.isna().sum() < parsed_dates.isna().sum():
                    parsed_dates = parsed_dates_y
            except Exception:
                pass
                
            # 尝试 %y-%m-%d 格式
            try:
                parsed_dates_yy = pd.to_datetime(df_filtered[date_column], format='%y-%m-%d', errors='coerce')
                # 如果这种格式解析效果更好（缺失值更少），则使用
                if parsed_dates_yy.isna().sum() < parsed_dates.isna().sum():
                    parsed_dates = parsed_dates_yy
            except Exception:
                pass
                
    return parsed_dates