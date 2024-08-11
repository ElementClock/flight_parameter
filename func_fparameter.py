import glob
import os
import pandas as pd
from tkinter import filedialog


def single_abstract(df_idx):
    """"单个飞参文件提取,返回df, text_analyze"""
    f_path = filedialog.askopenfilename()
    df = None  # 初始化df为None，确保总是返回一个值
    text_analyze = None
    if f_path:
        df_original = pd.read_csv(f_path, encoding='gbk')
        df = extract_flight_parameter(df_original, df_idx)
        # 确保文件名至少有15个字符来生成输出文件名
        if len(f_path) >= 15:
            out_path = f_path[:-15] + '(数据提取).csv'
        else:
            out_path = '提取数据.csv'  # 使用默认文件名
        df.to_csv(out_path, index=False, encoding='utf-8-sig')
        text_analyze = single_analyze(df)
    else:
        return

    return df, text_analyze


def multi_abstract(df_idx):
    """"多个飞参文件提取"""
    folder_path = filedialog.askdirectory()  # 返回选定的文件夹路径
    if not folder_path:
        # print("未选择文件夹。")
        return  # 如果没有选择文件夹，则直接返回
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


def single_analyze(df):
    """单文件数据分析"""
    # 起落架统计
    text_landing = landing_gear_analyze(df)
    # 开车时间统计
    text_engine = engine_analyze(df)
    # 总汇报
    text_analyze = f"{text_landing}\n{text_engine}\n"
    return text_analyze


def engine_analyze(df):
    engine_columns = ["1发转速", "2发转速", "3发转速", "4发转速"]
    # 提取每列的第一次和最后一次不为0的时间
    times = [(df.loc[df[df[col] != 0].index.min(), "飞行时间"],
              df.loc[df[df[col] != 0].index.max(), "飞行时间"])
             for col in engine_columns if not df[df[col] != 0].empty]
    if times:
        # 解压得到所有的第一次和最后一次时间列表，分别使用min和max来找出最早和最晚的时间
        first_times, last_times = zip(*times)
        text = f"开车时间: {min(first_times)}, 关车时间: {max(last_times)}"
    else:
        text = "本次数据分析飞机没有开车"
    return text


def landing_gear_analyze(df):
    """起落架专业分析"""
    landing_gear_up = df['起落架收']
    landing_gear_down = df['起落架放']
    changes1 = landing_gear_up.diff(1) != 0
    changes2 = landing_gear_down.diff(1) != 0
    landing_gear_up = (changes1.sum() - 1) // 2
    landing_gear_down = (changes2.sum() - 1) // 2
    if landing_gear_up == landing_gear_down:
        text = f'起落架收放次数为{landing_gear_up}'
    else:
        text = '起落架收放计数存在异常，请检查相关数据'
    return text
