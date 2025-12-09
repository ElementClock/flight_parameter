#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CAS告警分析模块
===============

分析CAS告警数据，识别告警时间段、类型及持续时间统计。

功能特性：
---------
1. 识别CAS告警时间段
2. 分析不同告警类型的发生时间
3. 提供告警持续时间统计
4. 按照警告级、戒备级、提示级、状态级对告警分类

使用方法：
--------
>>> analyzer = CasAnalysis()
>>> result = analyzer.analyze(dataframe)
>>> text_report = analyzer.generate_text(result)

注意事项：
--------
- 输入数据必须包含飞行时间和CAS告警相关列
- 需要cas_level.csv文件支持告警级别分类
"""

import logging
import os
from typing import Dict, Any
from datetime import datetime

import pandas as pd

from analysis.analysis_interface import AnalysisInterface

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# 全局缓存变量，用于存储告警级别信息
_cached_alarm_levels = None
_cached_alarm_levels_timestamp = None


class CasAnalysis(AnalysisInterface):
    """CAS告警分析类
    
    该类提供了完整的CAS告警数据分析功能，包括数据解析、特征提取和报告生成。
    
    属性：
    ------
    无
    
    方法：
    -----
    analyze(df, engine_start_time=None, engine_end_time=None, **kwargs) -> Dict[str, Any]
        告警分析主函数
    find_alarm_periods(alarm_times) -> list
        找到连续告警的时间段
    extract_alarm_periods(df_cas, column, time_column) -> list
        提取某一列的告警时间段
    load_alarm_levels() -> dict
        加载告警级别信息
    group_alarms_by_level(alarms, alarm_levels) -> dict
        根据告警级别对告警进行分组
    generate_text(cas_data: Dict[str, Any]) -> str
        生成带标识符的CAS分析文本输出
    """
    
    def get_name(self) -> str:
        """获取分析器名称
        
        Returns:
            str: 分析器名称
        """
        return "cas"
    
    def analyze(self, df, engine_start_time=None, engine_end_time=None, **kwargs) -> Dict[str, Any]:
        """
        告警分析主函数
        
        Args:
            df (pandas.DataFrame): 飞行数据
            engine_start_time: 发动机启动时间
            engine_end_time: 发动机关车时间
            **kwargs: 其他参数
            
        Returns:
            dict: CAS分析结果
        """
        try:
            # 初始化返回数据
            cas_result = {
                'type': 'cas',
                'alarms': [],
                'is_empty': False,
                'missing_time_column': False,
                'no_alarm_columns': False
            }

            if df.empty:
                cas_result['is_empty'] = True
                return cas_result

            time_columns = [col for col in df.columns if '飞行时间' in col]
            if not time_columns:
                cas_result['missing_time_column'] = True
                return cas_result

            time_column = time_columns[0]  # 使用第一个找到的时间列

            alarm_columns = df.filter(like='显示告警系统').columns
            if len(alarm_columns) == 0:
                # 尝试其他可能的告警列名模式
                alarm_columns = [col for col in df.columns if '告警' in col]
                if not alarm_columns:
                    cas_result['no_alarm_columns'] = True
                    return cas_result

            # 优化内存使用：只选择需要的列进行处理
            selected_columns = [time_column] + list(alarm_columns)
            df_cas = df[selected_columns].copy()
            
            alarm_periods_dict = {}

            for column in alarm_columns:
                periods = self.extract_alarm_periods(df_cas, column, time_column)
                if periods:
                    alarm_periods_dict[column] = periods

            # 新建 alarms 数据列表
            alarms = []
            for column, periods in alarm_periods_dict.items():
                for start, end in periods:
                    # 添加时间范围过滤条件
                    if (engine_start_time is None or start >= engine_start_time) and (engine_end_time is None or end <= engine_end_time):
                        duration = (end - start).total_seconds()+1
                        minutes, seconds = divmod(int(duration), 60)
                        duration_str = f"{minutes} 分钟 {seconds} 秒" if duration >= 60 else f"{duration:.0f} 秒"
                        alarms.append({
                            'name': column,
                            'start_time': start.strftime('%H:%M:%S'),
                            'end_time': end.strftime('%H:%M:%S'),
                            'duration': duration_str
                        })

            cas_result['alarms'] = alarms
            
            return cas_result
        except Exception as e:
            logging.error(f"CAS分析过程中出错: {e}")
            return {
                'type': 'cas',
                'alarms': [],
                'is_empty': False,
                'missing_time_column': False,
                'no_alarm_columns': False,
                'errors': [f"CAS分析过程中出错: {str(e)}"]
            }
    
    def find_alarm_periods(self, alarm_times):
        """找到连续告警的时间段
        
        Args:
            alarm_times: 告警时间序列
            
        Returns:
            list: 告警时间段列表
        """
        try:
            if alarm_times.empty:
                return []

            periods = []
            start_time = None

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
        except Exception as e:
            logging.error(f"查找告警时间段时出错: {str(e)}")
            return []

    def extract_alarm_periods(self, df_cas, column, time_column):
        """
        提取某一列的告警时间段
        
        Args:
            df_cas (pandas.DataFrame): CAS数据
            column (str): 列名
            time_column (str): 时间列名
            
        Returns:
            list: 告警时间段列表
        """
        try:
            mask = df_cas[column] == 1
            assert mask.ndim == 1, f"索引条件 {column} 不是一维的"
            alarm_times = df_cas.loc[mask, time_column]
            if isinstance(alarm_times, pd.DataFrame):
                alarm_times = alarm_times.squeeze()
            return self.find_alarm_periods(alarm_times) if not alarm_times.empty else []
        except KeyError:
            logging.warning(f"列 {column} 或 '{time_column}' 列存在问题")
            return []
        except AssertionError as e:
            logging.warning(f"断言错误: {e}")
            return []
        except Exception as e:
            logging.warning(f"提取告警时间段时出错: {e}")
            return []
    
    def load_alarm_levels(self):
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
            # 使用向量化操作替代iterrows
            for idx in range(len(df)):
                # 忽略大小写进行匹配
                alarm_id = str(df.iloc[idx, 2]).strip().lower() if pd.notna(df.iloc[idx, 2]) else None
                alarm_level = df.iloc[idx, 6] if pd.notna(df.iloc[idx, 6]) else None
                
                if alarm_id and alarm_level:
                    alarm_levels[alarm_id] = alarm_level
                    
            return alarm_levels
        except FileNotFoundError:
            logging.error(f"告警级别文件未找到: {cas_level_path}")
            return {}
        except Exception as e:
            logging.error(f"加载告警级别信息时出错: {e}")
            return {}

    def group_alarms_by_level(self, alarms, alarm_levels):
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
    
    def generate_text(self, cas_data: Dict[str, Any]) -> str:
        """生成带标识符的CAS分析文本输出
        
        Args:
            cas_data (dict): CAS分析数据
            
        Returns:
            str: 格式化的文本结果
        """
        try:
            result = []
            
            # 检查错误情况
            if cas_data['is_empty']:
                result.append("输入的 DataFrame 为空，请检查数据源")
                return "\n".join(result)
            if cas_data['missing_time_column']:
                result.append("缺少 '飞行时间' 列，请检查数据源")
                return "\n".join(result)
            if cas_data['no_alarm_columns']:
                result.append("没有找到告警相关的列，请检查数据源")
                return "\n".join(result)
            if 'errors' in cas_data:
                result.append("CAS分析过程中出错:")
                result.extend(cas_data['errors'])
                return "\n".join(result)

            # 检查告警数据
            if not cas_data['alarms']:
                result.append("没有发现告警")
                return "\n".join(result)

            # 添加标题
            title = "[[BOLD]]CAS告警分析结果[[/BOLD]]"
            formatted_title = title.center(100, '-')
            result.append(formatted_title)

            # 读取告警等级信息
            alarm_levels = self.load_alarm_levels()
            
            # 按告警级别分组
            grouped_alarms = self.group_alarms_by_level(cas_data['alarms'], alarm_levels)
            
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
            logging.error(f"格式化CAS输出时出错: {str(e)}")
            return f"格式化CAS输出时出错: {str(e)}"