import glob
import os
import re
from tkinter import filedialog

import numpy as np
import pandas as pd


# 提取飞行日期和时间列
def extract_flight_date_time(df_original):
    flight_date_col = None
    flight_time_col = None
    for col in df_original.columns:
        if "全球卫星定位系统" in col and "年月日" in col:
            flight_date_col = df_original[col]
        elif "全球卫星定位系统" in col and "时分秒" in col:
            flight_time_col = df_original[col]
    return flight_date_col, flight_time_col


# 转换时间为北京时间
def convert_to_beijing_time(df):
    df_time = df.loc[:, ('飞行日期', '飞行时间')]
    df_time.loc[:, '飞行日期'] = df_time['飞行日期'].apply(lambda x: f'20{x[:2]}-{x[3:5]}-{x[6:]}')
    df_time.loc[:, 'UTC时间'] = pd.to_datetime(df_time['飞行日期'] + ' ' + df_time['飞行时间'])
    df_time.loc[:, '北京时间'] = df_time['UTC时间'] + pd.Timedelta(hours=8)
    df.loc[:, '飞行日期'] = pd.to_datetime(df_time['北京时间']).dt.date
    df.loc[:, '飞行时间'] = pd.to_datetime(df_time['北京时间']).dt.time
    return df


# 处理列名
def process_column_name(col_name):
    # 替换类似 _CD-013、_CLG-002 等的字符为 _，但保留包含 "TAWS", "TCAS" 的部分
    if "TAWS" not in col_name and "TCAS" not in col_name:
        col_name = re.sub(r'_[A-Z]+-\d+', '_', col_name)
    # 替换类似 _L261_ 的字符为 _
    col_name = re.sub(r'_L\d+_', '_', col_name)
    # 替换类似 _SS21-001 的字符为 _
    col_name = re.sub(r'_SS\d+-\d+', '_', col_name)
    return col_name


def single_abstract(df_idx):
    """
    单个飞参文件提取,返回:df, text_analyze
    使用自定义函数
    extract_flight_parameter
    single_analyze
    """
    f_path = filedialog.askopenfilename()
    df = None  # 初始化返回变量
    text_analyze = ""  # 初始化返回变量
    if f_path:
        try:
            df_original = pd.read_csv(f_path, encoding='gbk')
            df = extract_flight_parameter(df_original, df_idx)
            # 确保文件名至少有15个字符来生成输出文件名
            if len(f_path) >= 15:
                out_path = f_path[:-15] + '(数据提取).csv'
            else:
                out_path = '提取数据.csv'  # 使用默认文件名
            df.to_csv(out_path, index=False, encoding='utf-8-sig')
            text_analyze = single_analyze(df, df_original, f_path)
        except FileNotFoundError:
            text_analyze = f"文件 {f_path} 未找到。"
        except UnicodeDecodeError:
            text_analyze = f"文件 {f_path} 编码格式错误。"
        except KeyError as e:
            text_analyze = f"文件 {f_path} 缺少列: {e}"
        except Exception as e:
            text_analyze = f"处理文件 {f_path} 时出现错误: {e}"
    return df, text_analyze


def multi_abstract(df_idx):
    """多个飞参文件提取"""
    folder_path = filedialog.askdirectory()  # 返回选定的文件夹路径
    if not folder_path:
        return  # 如果没有选择文件夹，则直接返回
    # 定义匹配规则
    pattern = '*_00_001_Phy.csv'
    # 使用glob找到所有匹配的文件
    matching_files = glob.glob(os.path.join(folder_path, pattern))
    # 遍历所有匹配的文件并进行处理
    for f_path in matching_files:
        try:
            df_original = pd.read_csv(f_path, encoding='gbk')
            # 数据提取
            df = extract_flight_parameter(df_original, df_idx)
            out_path = f_path[:-15] + '(数据提取).csv'
            df.to_csv(out_path, index=False, encoding='utf-8-sig')
        except FileNotFoundError:
            print(f"文件 {f_path} 未找到。")
        except UnicodeDecodeError:
            print(f"文件 {f_path} 编码格式错误。")
        except KeyError as e:
            print(f"文件 {f_path} 缺少列: {e}")
        except Exception as e:
            print(f"处理文件 {f_path} 时出现错误: {e}")


def extract_flight_parameter(df_original, df_idx):
    """提取需要参数并修改名称"""
    if '原始参数' in df_idx.columns and '简化参数' in df_idx.columns:
        columns_to_extract = df_idx.loc[:, '原始参数'].tolist()
        try:
            df = df_original[columns_to_extract]
        except KeyError as e:
            print(f"数据中缺少列: {e}")
            return None
        new_column_names = df_idx['简化参数'].tolist()
        df.columns = new_column_names
    elif 'system' in df_idx.columns and 'selected' in df_idx.columns:
        selected_systems = df_idx[df_idx['selected'] == True]['system'].tolist()
        original_columns = df_original.columns
        columns_to_extract = []
        new_column_names = []
        for system in selected_systems:
            for col in original_columns:
                if system in col:
                    columns_to_extract.append(col)
                    # 找到提取词的位置
                    index = col.find(system)
                    # 截取提取词及其后面的字符
                    new_col_name = col[index:].lstrip('_')
                    new_col_name = process_column_name(new_col_name)
                    new_column_names.append(new_col_name)

        try:
            df = df_original[columns_to_extract]
            df.columns = new_column_names
        except KeyError as e:
            print(f"数据中缺少列: {e}")
            return None
    else:
        print("df_idx 格式不支持，请检查列名。")
        return None

    # 提取飞行日期和飞行时间列
    flight_date_col, flight_time_col = extract_flight_date_time(df_original)

    if flight_date_col is not None and flight_time_col is not None:
        df.insert(0, "飞行时间", flight_time_col)
        df.insert(0, "飞行日期", flight_date_col)

    # 格林威治标准时间转为北京时间
    df = convert_to_beijing_time(df)
    df = df.drop('飞行日期', axis=1)  # 删除这一列，在dia分析中用不着
    return df


def single_analyze(df, df_original, f_path):
    """单文件数据分析"""
    if df is None:
        return f"文件 {f_path} 数据处理失败，无法进行分析。"
    # 起落架统计
    text_landing = landing_gear_analyze(df)
    # 开车时间统计
    text_engine = engine_analyze(df)
    # 总体汇报
    text_ps = performance_stability_analyze(df)
    # CAS汇报
    # text_cas = cas_analyze(df, df_original)
    # 总汇报
    text_analyze = (f"本次分析文件为{f_path[-29:]}\n"
                    f"{text_engine}\n"
                    f"{text_landing}\n"
                    f"{text_ps}\n"
                    # f"{text_cas}\n"
                    f"\n")
    return text_analyze


def engine_analyze(df):
    """动力专业分析"""
    engine_columns = ["1发转速", "2发转速", "3发转速", "4发转速"]
    # 提取每列的第一次和最后一次不为0的时间
    times = []
    for col in engine_columns:
        non_zero_indices = df[df[col] != 0].index
        if not non_zero_indices.empty:
            first_time = df.loc[non_zero_indices.min(), "飞行时间"]
            last_time = df.loc[non_zero_indices.max(), "飞行时间"]
            times.append((first_time, last_time))
    if times:
        # 解压得到所有的第一次和最后一次时间列表，分别使用min和max来找出最早和最晚的时间
        first_times, last_times = zip(*times)
        text = f"开车时间: {min(first_times)}，关车时间： {max(last_times)}"
    else:
        text = "数据显示本次飞机没有开车"
    return text


def landing_gear_analyze(df):
    """起落架专业分析"""

    def changes_count(landing_count, flag):
        changes = landing_count.diff(1) != 0
        if flag == 1:
            indices = landing_count.index[changes].tolist()
            # 计算相邻差值
            diffs = np.diff(indices)
            # 找到差值超过阈值的位置
            split_indices = np.where(diffs > 90)[0] + 1
            # 使用split函数分割数组
            clusters = np.split(indices, split_indices)
            count = len(clusters) - 2  # 首位数字必定为被分割和初始起飞与最终降落被分割
            if count < 0:
                count = 0
        else:
            count = (changes.sum() - 1) // 2
        return count

    landing_gear_ups = changes_count(df['起落架收'], 0)
    landing_gear_downs = changes_count(df['起落架放'], 0)
    landing_load1 = changes_count(df['前轮载1'], 1)
    landing_load2 = changes_count(df['前轮载2'], 1)
    landing_load3 = changes_count(df['左主起轮载1'], 1)
    landing_load4 = changes_count(df['左主起轮载2'], 1)
    landing_load5 = changes_count(df['右主起轮载1'], 1)
    landing_load6 = changes_count(df['右主起轮载2'], 1)
    if landing_gear_ups == landing_gear_downs:
        landing_load = max(landing_load1, landing_load2, landing_load3, landing_load4, landing_load5, landing_load6)
        text = f'起落架收放 {landing_gear_ups} 次\n飞机着陆起降 {landing_load} 次'
    else:
        text = '起落架收放计数存在异常，请检查相关数据'
    return text


def performance_stability_analyze(df):
    """性能操稳专业**简要分析**，起飞高度，最大飞行高度，飞行距离，最大飞行速度"""
    high_max = df['气压高度'].max()
    high_min = df['气压高度'].min()
    v_max = df['校准空速'].max()
    v_min = df['校准空速'].min()
    text = f'起飞高度为 {high_min} m，最大飞行高度为 {high_max} m，最大飞行速度为 {v_max} km/h'
    return text


def cas_analyze(df, df_original):
    """告警分析，出现告警参数以及告警的时间段"""
    selected_columns = df_original.filter(like='显示告警系统').columns
    # 存储结果
    result = []
    # 遍历每一个告警系统列
    for column in selected_columns:
        if column not in df.columns:
            continue
        # 获取该列值为 1 的时间段
        alarm_times = df[df[column] == 1]['飞行时间']
        if not alarm_times.empty:
            start_time = None
            # 遍历每个时间点，找到连续时间段
            for i, time in enumerate(alarm_times):
                if start_time is None:
                    start_time = time
                # 如果下一个时间点与当前时间点不连续，则输出一个时间段
                if i == len(alarm_times) - 1 or (
                        pd.to_datetime(alarm_times.iloc[i + 1]) - pd.to_datetime(time)).seconds > 600:  # 超过10分钟不连续
                    end_time = time
                    result.append(f"{column}：告警时间从 {start_time} 到 {end_time}")
                    start_time = None
    text = "\n".join(result)
    return text
