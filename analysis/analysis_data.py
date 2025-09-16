from datetime import timedelta

import pandas as pd

from analysis.cas_analysis import analyze_cas
from analysis.engine_analysis import analyze_engine


class AnalysisResult:
    """封装分析结果的数据类"""
    
    def __init__(self, **kwargs):
        # 动态设置所有传入的属性
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __getattr__(self, name):
        # 为不存在的属性提供默认值
        return None


def analysis_data(df):
    df = convert_flight_time(df)
    df = convert_flight_name(df)
    # 动力专业汇报
    engine_data = analyze_engine(df)
    
    # CAS汇报
    cas_data = analyze_cas(df, engine_data.get('takeoff_start_time'), engine_data.get('takeoff_end_time'))

    # 生成带标识符的文本输出
    text_engine = generate_engine_text_with_markers(engine_data)
    text_cas = generate_cas_text_with_markers(cas_data)

    # 将所有结果封装到AnalysisResult对象中
    result = AnalysisResult(
        text_engine=text_engine,
        text_cas=text_cas,
        engine_start_time=engine_data.get('takeoff_start_time'),
        engine_end_time=engine_data.get('takeoff_end_time'),
        df=df,
        engine_data=engine_data,
        cas_data=cas_data
    )
    return result


def generate_engine_text_with_markers(engine_data):
    """生成带标识符的发动机分析文本输出"""
    result = []
    
    # 检查是否有错误信息
    if 'errors' in engine_data:
        result.extend(engine_data['errors'])
        return "\n".join(result)
    
    # 检查是否有发动机启动信息
    if engine_data['has_takeoff_info']:
        # 使用标识符标记标题行
        title = "[[BOLD]]动力分析结果[[/BOLD]]"
        formatted_title = title.center(100, '-')
        result.append(formatted_title)
        
        if engine_data['takeoff_start_time'] and engine_data['takeoff_end_time']:
            gap_time = engine_data['takeoff_end_time'] - engine_data['takeoff_start_time']
            result.append(f" 开关车时间为：{engine_data['takeoff_start_time']}-{engine_data['takeoff_end_time']}，耗时：{gap_time} ")
        
        # 添加发动机启动信息
        for info in engine_data['takeoff_info']:
            result.append(f"{info['engine_id']}号发动机首次开车时间为 {info['start_time']}")
            # 如果有重启，添加重启信息
            if 'restart_times' in info:
                restart_times_str = ", ".join([str(t) for t in info['restart_times']])
                result.append(f"{info['engine_id']}号发动机存在 {len(info['restart_times'])} 次重启，重启时间点为: {restart_times_str}")
    # 新增逻辑：当所有发动机都未启动时，说明分析时间范围并提示无开车记录
    else:
        if engine_data['start_time'] and engine_data['end_time']:
            result.append(f"本文件时间为： {engine_data['start_time']} 到 {engine_data['end_time']}\n 本次数据分析：飞机未启动发动机，请检查数据" )
    
    return "\n".join(result)


def generate_cas_text_with_markers(cas_data):
    """生成带标识符的CAS分析文本输出"""
    result = []
    
    # 检查错误情况
    if cas_data['is_empty']:
        result.append("输入的 DataFrame 为空，请检查数据源")
        return "\n".join(result)
    
    if cas_data['missing_time_column']:
        result.append("DataFrame 中缺少 '飞行时间' 列")
        return "\n".join(result)
        
    if cas_data['no_alarm_columns']:
        result.append("未找到包含 '显示告警系统' 的列")
        return "\n".join(result)

    # 使用标识符标记标题行
    title = "[[BOLD]]CAS告警分析结果[[/BOLD]]"
    formatted_title = title.center(100, '-')
    result.append(formatted_title)

    # 自定义格式化输出
    # 初始化当前告警变量为None，用于后续判断是否为同一个告警
    current_alarm = None

    # 遍历告警数据
    for alarm in cas_data['alarms']:
        # 提取当前行的告警信息
        alarm_name = alarm['name']
        start_time = alarm['start_time']
        end_time = alarm['end_time']
        duration = alarm['duration']

        time_info = (
            f"{' '.ljust(30, ' ')}"
            f" 时间：{start_time}-{end_time.ljust(15)}"
            f" 持续时间：{duration}"
        )
        # 判断当前告警与上一条告警是否相同
        if alarm_name != current_alarm:
            # 如果不相同，先输出告警名称
            result.append(f"{alarm_name}")
            result.append(time_info)
            # 更新当前告警变量
            current_alarm = alarm_name
        else:
            result.append(time_info)

    return "\n".join(result)


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