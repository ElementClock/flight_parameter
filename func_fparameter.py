import glob
import os
import pandas as pd
from tkinter import filedialog


def single_abstract(df_idx):
    """"单个飞参文件提取"""
    f_path = filedialog.askopenfilename()
    df_original = pd.read_csv(f_path, encoding='gbk')
    # 数据提取
    df = extract_flight_parameter(df_original, df_idx)
    out_path = f_path[:-15] + '(数据提取).csv'
    df.to_csv(out_path, index=False, encoding='utf-8-sig')

    return df


def multi_abstract(df_idx):
    """"多个飞参文件提取"""
    folder_path = filedialog.askdirectory()  # 返回选定的文件夹路径
    # 定义匹配规则
    pattern = '*_00_001_Phy.csv'
    # 使用glob找到所有匹配的文件
    matching_files = glob.glob(os.path.join(folder_path, pattern))
    # 遍历所有匹配的文件并进行处理
    for f_path in matching_files:
        df_original = pd.read_csv(f_path, encoding='gbk')
        # 数据提取
        df = extract_flight_parameter(df_original, df_idx)
        out_path = f_path[:-15] + '(数据提取).csv'
        df.to_csv(out_path, index=False, encoding='utf-8-sig')
    return df


def extract_flight_parameter(df_original, df_idx):
    """提取需要参数并修改名称"""
    columns_to_extract = df_idx.iloc[:, 0].tolist()
    df = df_original[columns_to_extract]
    new_column_names = df_idx['简化参数名'].tolist()
    df.columns = new_column_names
    # 格林威治标准时间转为北京时间
    df_time = df.loc[:, ('飞行日期', '飞行时间')]
    df_time.loc[:, '飞行日期'] = df_time['飞行日期'].apply(lambda x: f'20{x[:2]}-{x[3:5]}-{x[6:]}')
    df_time.loc[:, 'UTC时间'] = pd.to_datetime(df_time['飞行日期'] + ' ' + df_time['飞行时间'])
    df_time.loc[:, '北京时间'] = df_time['UTC时间'] + pd.Timedelta(hours=8)
    df.loc[:, '飞行日期'] = pd.to_datetime(df_time['北京时间']).dt.date
    df.loc[:, '飞行时间'] = pd.to_datetime(df_time['北京时间']).dt.time
    return df
