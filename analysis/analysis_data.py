from datetime import timedelta

import pandas as pd

from analysis.cas_analysis import analyze_cas
from analysis.engine_analysis import analyze_engine


def analysis_data(df):
    df = convert_flight_time(df)
    df = convert_flight_name(df)
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

def convert_flight_name(df):
    # 定义替换规则字典
    replacement_rules = {
        'ATA345_GNSU1全球卫星定位系统': '全球卫星定位系统1',
        'ATA345_GNSU2全球卫星定位系统': '全球卫星定位系统2',
        'ATA345_SMU短报文': '短报文',
        'ATA342_AHRU航姿基准系统': '航姿基准系统',
        'ATA341_ADRU1大气数据系统': '大气数据系统1',
        'ATA341_ADRU2大气数据系统': '大气数据系统2',
        'ATA341_ADRU3大气数据系统': '大气数据系统3',
        'ATA344_IRU1惯性基准系统': '惯性基准系统',
        'ATA344_IRU2惯性基准系统': '惯性基准系统',
        'ATA317_FMCC1飞行管理系统': '飞行管理系统1',
        'ATA317_FMCC2飞行管理系统': '飞行管理系统2',
        'ATA316_IDU1显示控制系统': '显示控制系统',
        'ATA344_RA1无线电高度表': '无线电高度表1',
        'ATA344_RA2无线电高度表': '无线电高度表2',
        'ATA344_RPU气象雷达': '气象雷达',
        'ATA341_ISI备份仪表': '备份仪表',
        'ATA315_CAS1显示告警系统': '显示告警系统',
        'ATA344_LIU_C1波段L综合系统': '波段L综合系统1',
        'ATA344_LIU_C2波段L综合系统': '波段L综合系统2',
        'ATA238_RIU1无线电接口单元': '无线电接口单元1',
        'ATA238_RIU2无线电接口单元': '无线电接口单元2',
        'ATA314_RDC1机电信息采集系统': '机电信息采集系统1',
        'ATA314_RDC2机电信息采集系统': '机电信息采集系统2',
        'ATA314_RDC3机电信息采集系统': '机电信息采集系统3',
        'ATA314_RDC4机电信息采集系统': '机电信息采集系统4',
        'ATA314_RDC5机电信息采集系统': '机电信息采集系统5',
        'ATA314_RDC6机电信息采集系统': '机电信息采集系统6',
        'ATA314_RDC7机电信息采集系统': '机电信息采集系统7',
        'ATA314_RDC8机电信息采集系统': '机电信息采集系统8',
        'ATA314_CPDC1机电信息采集': '机电信息采集',
        'ATA36气源系统': '气源系统',
        'ATA21空调系统': '空调系统',
        'ATA21_CPC1座舱压力系统': '座舱压力系统',
        'ATA21_CPSU座舱压力系统': '座舱压力系统',
        'ATA22_AFCC自动飞行系统': '自动飞行系统',
        'ATA22_AFCP自动飞行系统': '自动飞行系统',
        'ATA24_L_PDU左电源系统': '左电源系统',
        'ATA24_R_PDU右电源系统': '右电源系统',
        'ATA26_HKH17A防火系统': '防火系统',
        'ATA279_CAB1主飞控系统': '主飞控系统1',
        'ATA279_CAB2主飞控系统': '主飞控系统2',
        'ATA279_CAB3主飞控系统': '主飞控系统3',
        'ATA275_FECU1襟翼控制系统': '襟翼控制系统1',
        'ATA275_FECU2襟翼控制系统': '襟翼控制系统2',
        'ATA28_FQC燃油系统': '燃油系统',
        'ATA324_BCU刹车控制系统': '刹车控制系统',
        'ATA293_HECU液压电控系统': '液压电控系统',
        'ATA325_SCU前轮转弯系统': '前轮转弯系统',
        'ATA30_TBDI_TIMER防冰和除雨': '防冰和除雨',
        'ATA30_WTC1防冰和除雨': '防冰和除雨',
        'ATA30_PR_PHC防冰和除雨': '防冰和除雨',
        'ATA52_KZQ舱门系统': '舱门系统',
        'ATA25_WATERCU设备用具': '设备用具',
        'ATA32_PDCU1起落架系统': '起落架系统',
        'ATA48_FTC灭火任务系统': '灭火任务系统',
        'ATA48_FECC灭火任务系统': '灭火任务系统',
        'ATA344_SAVMU环境感知与视频管理系统': '环境感知与视频管理系统',
        'ATA42_NCPP1综合处理系统': '综合处理系统1',
        'ATA42_NCPP2综合处理系统': '综合处理系统2',
        'ATA42_HM_GPM1综合处理系统': '综合处理系统3',
        'ATA313_FDR飞参系统': '飞参系统',
        'ATA313_TACE飞参系统': '飞参系统',
        'ATA313_QAR飞参系统': '飞参系统',
        'ATA73_EUC燃油系统': '燃油系统'
    }
    
    # 创建列名映射字典
    column_mapping = {}
    for old_name in df.columns:
        new_name = old_name
        for pattern, replacement in replacement_rules.items():
            if pattern in old_name:
                new_name = old_name.replace(pattern, replacement)
                break
        column_mapping[old_name] = new_name
    
    # 重命名列
    df = df.rename(columns=column_mapping)
    
    return df