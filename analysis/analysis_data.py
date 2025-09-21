from datetime import timedelta
import pandas as pd
import os
import logging

from analysis.cas_analysis import analyze_cas
from analysis.engine_analysis import analyze_engine

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class AnalysisResult:
    """封装分析结果的数据类"""
    
    def __init__(self, **kwargs):
        """初始化分析结果对象
        
        Args:
            **kwargs: 任意数量的属性键值对
        """
        # 动态设置所有传入的属性
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __getattr__(self, name):
        """为不存在的属性提供默认值
        
        Args:
            name: 属性名称
            
        Returns:
            None: 当属性不存在时返回None
        """
        return None


def analysis_data(df, progress_callback=None):
    """分析飞行数据主函数
    
    Args:
        df (pandas.DataFrame): 飞行数据
        progress_callback (callable): 进度更新回调函数
        
    Returns:
        AnalysisResult: 包含分析结果的对象
    """
    try:
        if progress_callback:
            progress_callback(10, "正在转换飞行时间...")
        df = convert_flight_time(df)
        
        if progress_callback:
            progress_callback(30, "正在转换列名...")
        df = convert_flight_name(df)
        
        # 动力专业汇报
        if progress_callback:
            progress_callback(50, "正在分析发动机数据...")
        engine_data = analyze_engine(df)
        
        # CAS汇报
        if progress_callback:
            progress_callback(70, "正在分析CAS告警...")
        cas_data = analyze_cas(df, engine_data.get('takeoff_start_time'), engine_data.get('takeoff_end_time'))

        # 生成带标识符的文本输出
        if progress_callback:
            progress_callback(90, "正在生成分析报告...")
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
        
        if progress_callback:
            progress_callback(100, "分析完成")
            
        # 清理临时变量以释放内存
        del engine_data, cas_data, text_engine, text_cas
        
        return result
    except Exception as e:
        logging.error(f"分析飞行数据时出错: {str(e)}")
        # 返回一个包含错误信息的AnalysisResult对象
        return AnalysisResult(
            errors=[f"分析飞行数据时出错: {str(e)}"]
        )


def generate_engine_text_with_markers(engine_data):
    """生成带标识符的发动机分析文本输出
    
    Args:
        engine_data (dict): 包含发动机分析结果的字典，可能包含错误信息
        
    Returns:
        str: 格式化的文本结果，包含错误信息或正常分析结果
    """
    try:
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
    except Exception as e:
        logging.error(f"生成发动机分析文本时出错: {str(e)}")
        return f"生成发动机分析文本时出错: {str(e)}"


def generate_cas_text_with_markers(cas_data):
    """生成带标识符的CAS分析文本输出
    
    Args:
        cas_data (dict): 包含CAS分析结果的字典，可能包含错误信息
        
    Returns:
        str: 格式化的文本结果，包含错误信息或正常分析结果
    """
    try:
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

        # 读取告警等级信息
        alarm_levels = load_alarm_levels()
        
        # 按告警级别分组
        grouped_alarms = group_alarms_by_level(cas_data['alarms'], alarm_levels)
        
        # 按指定顺序排列告警级别
        level_order = ['警告级', '戒备级', '提示级', '状态级']
        
        # 初始化当前告警变量为None，用于后续判断是否为同一个告警
        current_alarm = None

        # 按级别顺序输出告警
        for level in level_order:
            if level in grouped_alarms and grouped_alarms[level]:
                # 根据不同级别添加不同颜色标识符
                level_line = f"{level}".center(89, '-')
                if level == '警告级':
                    result.append("[[RED]]" + level_line + "[[/RED]]")
                elif level == '戒备级':
                    result.append("[[AMBER]]" + level_line + "[[/AMBER]]")
                elif level == '提示级':
                    result.append("[[BLUE]]" + level_line + "[[/BLUE]]")
                elif level == '状态级':
                    result.append("[[BOLD]]" + level_line + "[[/BOLD]]")
                else:
                    result.append(level_line)
                    
                # 遍历该级别的告警数据
                for alarm in grouped_alarms[level]:
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
    except Exception as e:
        logging.error(f"生成CAS分析文本时出错: {str(e)}")
        return f"生成CAS分析文本时出错: {str(e)}"


def load_alarm_levels():
    """加载告警级别信息
    
    Returns:
        dict: 告警ID到告警级别的映射字典
    """
    try:
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cas_level_path = os.path.join(project_root, 'cas_level.csv')
        
        # 读取CSV文件
        df = pd.read_csv(cas_level_path, header=0)
        
        # 提取C列(编号)和G列(告警等级)
        # 注意：pandas默认0索引，C列是第2列(索引为2)，G列是第6列(索引为6)
        alarm_levels = {}
        for _, row in df.iterrows():
            # 忽略大小写进行匹配
            alarm_id = str(row.iloc[2]).strip().lower() if pd.notna(row.iloc[2]) else None
            alarm_level = row.iloc[6] if pd.notna(row.iloc[6]) else None
            
            if alarm_id and alarm_level:
                alarm_levels[alarm_id] = alarm_level
                
        return alarm_levels
    except FileNotFoundError:
        logging.error(f"告警级别文件未找到: {cas_level_path}")
        return {}
    except Exception as e:
        logging.error(f"加载告警级别信息时出错: {e}")
        return {}


def group_alarms_by_level(alarms, alarm_levels):
    """根据告警级别对告警进行分组
    
    Args:
        alarms (list): 告警列表
        alarm_levels (dict): 告警ID到告警级别的映射字典
        
    Returns:
        dict: 按告警级别分组的告警字典
    """
    try:
        grouped = {
            '警告级': [],
            '戒备级': [],
            '提示级': [],
            '状态级': [],
            '未知级别': []
        }
        
        # 遍历所有告警级别定义
        for alarm_id, level in alarm_levels.items():
            # 对于每个告警级别，检查所有告警项
            for alarm in alarms:
                alarm_name = alarm['name']
                # 如果alarm_levels中的ID在告警名称中，则将该告警归类到对应级别
                if alarm_id.lower() in alarm_name.lower():
                    grouped[level].append(alarm)
        
        # 将未匹配到级别的告警归类到'未知级别'
        # 先找出已匹配的告警
        matched_alarms = []
        for level_alarms in grouped.values():
            matched_alarms.extend(level_alarms)
        
        # 将未匹配的告警添加到'未知级别'
        for alarm in alarms:
            if alarm not in matched_alarms:
                grouped['未知级别'].append(alarm)
        
        return grouped
    except Exception as e:
        logging.error(f"告警分组时出错: {str(e)}")
        return {}


def convert_flight_time(df):
    """
    将飞参数据中的时间列转换为标准的北京时间格式
    
    参数:
        df (pandas.DataFrame): 包含飞参数据的DataFrame
        
    返回:
        pandas.DataFrame: 时间列已转换的DataFrame
    """
    try:
        # 优化内存使用：创建新的DataFrame而不是修改原数据
        df_new = df.copy()
        
        # 获取第一列和第四列的列名
        first_col = df_new.columns[0]   # 飞参内部时间列 (格式: hh:mm:ss.fff)
        fourth_col = df_new.columns[3]  # 日期列 (格式: yy-mm-dd)
        
        # 将两列数据合并为完整的日期时间字符串
        # 格式: hh:mm:ss.fff + 年份-月份-日
        datetime_combined = df_new[first_col].astype(str) + ' ' + df_new[fourth_col].astype(str)
        
        # 转换为datetime对象，支持两位数年份格式（如25-07-11表示2025年7月11日）
        df_new['_datetime'] = pd.to_datetime(datetime_combined, format='%H:%M:%S.%f %y-%m-%d', errors='coerce')
        
        # 将UTC时间转换为北京时间(UTC+8)
        df_new['_datetime'] = df_new['_datetime'] + timedelta(hours=8)
        
        # 更新原数据列
        df_new[first_col] = df_new['_datetime']

        # 删除临时列
        df_new.rename(columns={first_col: '飞行时间'}, inplace=True)
        df_new.drop('_datetime', axis=1, inplace=True)
        
        return df_new
    except Exception as e:
        logging.error(f"转换飞行时间时出错: {e}")
        return df
    
def convert_flight_name(df):
    """转换飞行数据列名
    
    Args:
        df (pandas.DataFrame): 飞行数据
        
    Returns:
        pandas.DataFrame: 列名已转换的DataFrame
    """
    try:
        # 优化内存使用：创建新的DataFrame而不是修改原数据
        df_new = df.copy()
        
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
        for old_name in df_new.columns:
            new_name = old_name
            for pattern, replacement in replacement_rules.items():
                if pattern in old_name:
                    new_name = old_name.replace(pattern, replacement)
                    break
            column_mapping[old_name] = new_name
        
        # 重命名列
        df_new = df_new.rename(columns=column_mapping)
        
        return df_new
    except Exception as e:
        logging.error(f"转换飞行数据列名时出错: {e}")
        return df