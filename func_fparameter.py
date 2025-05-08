import glob
import logging
import os
import re
from tkinter import filedialog
import pandas as pd
# 新增并行处理依赖包
import concurrent.futures  # 删除:from analysis.cas_analysis import analyze_cas

from analysis.cas_analysis import analyze_cas
from analysis.engine_analysis import analyze_engine
# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# 提取飞行日期和时间列
def extract_flight_date_time(df_original):
    flight_date_col = None
    flight_time_col = None
    for col in df_original.columns:
        if "全球卫星定位系统" in col and "年月日" in col:
            # 获取出现次数最多的值（众数）
            most_common_value = df_original[col].mode()[0]
            # 将该列所有值替换为出现次数最多的值
            flight_date_col = df_original[col].apply(lambda x: most_common_value)

        elif col == "飞参内部时间":  # 直接匹配列名
            flight_time_col = df_original[col]
    return flight_date_col, flight_time_col


# 转换时间为北京时间
def convert_to_beijing_time(df):
    df_time = df.loc[:, ('飞行日期', '飞行时间')]
    df_time.loc[:, '飞行日期'] = df_time['飞行日期'].apply(lambda x: f'20{x[:2]}-{x[3:5]}-{x[6:]}')
    df_time.loc[:, 'UTC时间'] = pd.to_datetime(df_time['飞行日期'] + ' ' + df_time['飞行时间'])
    df_time.loc[:, '北京时间'] = df_time['UTC时间'] + pd.Timedelta(hours=8)
    df.loc[:, '飞行时间'] = pd.to_datetime(df_time['北京时间'])
    df = df.drop('飞行日期', axis=1)  # 删除不再需要的列
    return df


# 重命名处理列名
def process_column_name(col_name):
    # 替换类似 _L261_ 的字符为 _
    col_name = re.sub(r'_L\d+_', '_', col_name)
    return col_name


# 新增多文件并行处理函数
def multi_abstract_parallel(df_idx):
    """
    并行处理多个飞参文件（新增函数）
    使用线程池实现文件并行处理
    """
    folder_path = filedialog.askdirectory()
    if not folder_path:
        return
    
    pattern = '*_00_001_Phy.csv'
    matching_files = glob.glob(os.path.join(folder_path, pattern))
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 提交所有文件处理任务
        future_to_file = {
            executor.submit(single_abstract, df_idx, f_path): f_path 
            for f_path in matching_files
        }
        
        # 处理执行结果
        for future in concurrent.futures.as_completed(future_to_file):
            f_path = future_to_file[future]
            try:
                future.result()  # 获取执行结果
            except Exception as e:
                logging.error(f"并行处理文件 {f_path} 时出现错误: {e}")
                print(f"并行处理文件 {f_path} 时出现错误: {e}")

# 修改单文件处理函数签名，增加文件路径参数
def single_abstract(df_idx, f_path=None):
    """
    单个飞参文件提取,返回:df, text_analyze
    使用自定义函数 extract_flight_parameter 和 single_analyze
    """
    if not f_path:  # 如果未提供文件路径
        f_path = filedialog.askopenfilename()  # 保留原有手动选择功能
        
    df = None
    text_analyze = ""
    
    if f_path:
        try:
            df_original = pd.read_csv(f_path, encoding='gbk')
            df = extract_flight_parameter(df_original, df_idx)
            [text_analyze, engine_start_time, engine_end_time] = single_analyze(df, f_path)
            
            # 新增机载列检测逻辑
            has_engine_col = any("机载信息采集系统" in col for col in df.columns)
            # 文件名生成逻辑修改
            if has_engine_col:
                if engine_start_time is not None and engine_end_time is not None:
                    date_str = engine_start_time.strftime('%Y%m%d')
                    filename = f"{date_str}-{engine_start_time.strftime('%Hh%Mm')}-{engine_end_time.strftime('%Hh%Mm')}-开车.csv"
                else:
                    first_time = df['飞行时间'].iloc[0]
                    last_time = df['飞行时间'].iloc[-1]
                    filename = f"{first_time.strftime('%Y%m%d')}-{first_time.strftime('%Hh%Mm')}-{last_time.strftime('%Hh%Mm')}-未开车.csv"
            else:
                first_time = df['飞行时间'].iloc[0]
                last_time = df['飞行时间'].iloc[-1]
                filename = f"{first_time.strftime('%Y%m%d')}-{first_time.strftime('%Hh%Mm')}-{last_time.strftime('%Hh%Mm')}.csv"
                
            out_path = os.path.join(os.path.dirname(f_path), filename)
            df.to_csv(out_path, index=False, encoding='utf-8-sig')
            
        except FileNotFoundError:
            text_analyze = f"文件 {f_path} 未找到。"
        except UnicodeDecodeError:
            text_analyze = f"文件 {f_path} 编码格式错误。"
        except KeyError as e:
            text_analyze = f"文件 {f_path} 缺少列: {e}"
        except Exception as e:
            text_analyze = f"处理文件 {f_path} 时出现错误: {e}"
            
    return df, text_analyze


def extract_flight_parameter(df_original, df_idx):
    """提取需要参数并修改名称

    Args:
        df_original: 原始数据DataFrame
        df_idx: 包含参数映射关系的DataFrame

    Returns:
        提取并处理后的DataFrame
    """
    # 检查df_idx格式并提取所需列
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

        # 根据选择的系统提取相关列
        for system in selected_systems:
            for col in original_columns:
                if system in col:
                    columns_to_extract.append(col)
                    # 处理列名
                    index = col.find(system)
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

    # 提取并插入飞行日期和时间列
    flight_date_col, flight_time_col = extract_flight_date_time(df_original)
    if flight_date_col is not None and flight_time_col is not None:
        df.insert(0, "飞行时间", flight_time_col)
        df.insert(0, "飞行日期", flight_date_col)

    # 转换时区并清理数据
    df = convert_to_beijing_time(df)
    return df


def single_analyze(df, f_path):
    """单文件数据分析"""
    if df is None:
        return f"文件 {f_path} 数据处理失败，无法进行分析。"
    # 动力专业汇报
    [text_engine, engine_start_time, engine_end_time] = analyze_engine(df)
    # CAS汇报
    text_cas = analyze_cas(df, engine_start_time, engine_end_time)

    # 总汇报
    text_analyze = (f"本次分析文件为{f_path[-29:]}\n"
                    f"{text_engine}\n"
                    f"{text_cas}\n"
                    f"\n")
    return text_analyze, engine_start_time, engine_end_time




