#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
发动机分析模块
==============

分析飞行数据中的发动机相关信息。
"""

import logging
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime

from analysis.analysis_interface import AnalysisInterface

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class EngineAnalysis(AnalysisInterface):
    """发动机分析类"""
    
    def analyze(self, df, **kwargs) -> Dict[str, Any]:
        """分析发动机数据
        
        Args:
            df (pandas.DataFrame): 飞行数据
            **kwargs: 其他参数
            
        Returns:
            dict: 发动机分析结果
        """
        try:
            result = {}

            # 检查是否存在必要的列 - 使用更灵活的方式查找发动机转速列
            time_columns = [col for col in df.columns if '飞行时间' in col]
            engine_rpm_columns = [col for col in df.columns if '发动机' in col and '转速' in col]
            
            if not time_columns:
                result['errors'] = ["缺少时间列"]
                return result
                
            if not engine_rpm_columns:
                result['errors'] = ["缺少发动机转速列"]
                return result

            time_column = time_columns[0]  # 使用第一个找到的时间列

            # 获取时间范围
            result['start_time'] = df[time_column].min()
            result['end_time'] = df[time_column].max()

            # 查找发动机启动和关车时间
            result['takeoff_info'] = self._find_engine_takeoff_info(df, time_column)
            
            # 检查是否有任何发动机启动信息
            result['has_takeoff_info'] = any(len(info['start_times']) > 0 for info in result['takeoff_info'])
            
            # 如果有发动机启动信息，则获取第一次启动和最后一次关车时间
            if result['has_takeoff_info']:
                all_start_times = []
                all_end_times = []
                
                for info in result['takeoff_info']:
                    if info['start_times']:
                        all_start_times.extend(info['start_times'])
                    if info['end_times']:
                        all_end_times.extend(info['end_times'])
                
                if all_start_times:
                    result['takeoff_start_time'] = min(all_start_times)
                if all_end_times:
                    result['takeoff_end_time'] = max(all_end_times)

            return result
        except Exception as e:
            logging.error(f"分析发动机数据时出错: {str(e)}")
            return {
                'type': 'engine',
                'has_takeoff_info': False,
                'takeoff_info': [],
                'start_time': None,
                'end_time': None,
                'takeoff_start_time': None,
                'takeoff_end_time': None,
                'errors': [f"分析发动机数据时出错: {str(e)}"]
            }
    
    def _find_engine_takeoff_info(self, df, time_column) -> List[Dict[str, Any]]:
        """查找发动机启动和关车时间信息
        
        Args:
            df (pandas.DataFrame): 飞行数据
            time_column (str): 时间列名
            
        Returns:
            list: 发动机启动和关车时间信息列表
        """
        try:
            engines_info = []
            
            # 查找所有发动机转速列
            engine_rpm_columns = [col for col in df.columns if '发动机' in col and '转速' in col]
            
            # 遍历找到的发动机列
            for i, rpm_column in enumerate(engine_rpm_columns):
                # 从列名中提取发动机编号
                if '1' in rpm_column:
                    engine_id = 1
                elif '2' in rpm_column:
                    engine_id = 2
                elif '3' in rpm_column:
                    engine_id = 3
                elif '4' in rpm_column:
                    engine_id = 4
                else:
                    engine_id = i + 1  # 默认编号
                
                # 获取RPM数据
                rpm_series = df[rpm_column]
                time_series = df[time_column]
                
                # 查找发动机启动和关车时间点
                start_times = []
                end_times = []
                restart_times = []
                
                # 判断发动机是否启动的阈值（假设RPM大于10表示启动）
                threshold = 10
                is_running = False
                
                # 遍历数据查找启动和关车时间点
                for j in range(len(rpm_series)):
                    rpm = rpm_series.iloc[j]
                    time = time_series.iloc[j]
                    
                    # 检查是否为有效数值
                    if pd.isna(rpm):
                        continue
                    
                    # 如果发动机之前未启动且当前RPM超过阈值，则认为启动
                    if not is_running and rpm > threshold:
                        start_times.append(time)
                        is_running = True
                    # 如果发动机之前已启动且当前RPM低于阈值，则认为关车
                    elif is_running and rpm <= threshold:
                        end_times.append(time)
                        is_running = False
                
                # 查找重启时间（在运行过程中短暂停止后再次启动）
                if len(start_times) > 1:
                    for k in range(1, len(start_times)):
                        # 如果两次启动之间的时间间隔较短，认为是重启而不是完全关车
                        if (start_times[k] - start_times[k-1]).total_seconds() < 300:  # 5分钟内
                            restart_times.append(start_times[k])
                
                engines_info.append({
                    'engine_id': engine_id,
                    'start_times': start_times,
                    'end_times': end_times,
                    'restart_times': restart_times
                })
            
            # 确保有4个发动机的信息（即使某些发动机没有数据）
            existing_engines = {info['engine_id'] for info in engines_info}
            for engine_id in range(1, 5):
                if engine_id not in existing_engines:
                    engines_info.append({
                        'engine_id': engine_id,
                        'start_times': [],
                        'end_times': [],
                        'restart_times': []
                    })
            
            # 按发动机编号排序
            engines_info.sort(key=lambda x: x['engine_id'])
            
            return engines_info
        except Exception as e:
            logging.error(f"查找发动机启动信息时出错: {str(e)}")
            return []
    
    def generate_text(self, engine_data: Dict[str, Any]) -> str:
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
                
                if engine_data.get('takeoff_start_time') and engine_data.get('takeoff_end_time'):
                    gap_time = engine_data['takeoff_end_time'] - engine_data['takeoff_start_time']
                    result.append(f" 开关车时间为：{engine_data['takeoff_start_time']}-{engine_data['takeoff_end_time']}，耗时：{gap_time} ")
                
                # 添加发动机启动信息
                for info in engine_data['takeoff_info']:
                    if info['start_times']:
                        result.append(f"{info['engine_id']}号发动机首次开车时间为 {info['start_times'][0]}")
                        # 如果有重启，添加重启信息
                        if 'restart_times' in info and info['restart_times']:
                            restart_times_str = ", ".join([str(t) for t in info['restart_times']])
                            result.append(f"{info['engine_id']}号发动机存在 {len(info['restart_times'])} 次重启，重启时间点为: {restart_times_str}")
            # 新增逻辑：当所有发动机都未启动时，说明分析时间范围并提示无开车记录
            else:
                if engine_data.get('start_time') and engine_data.get('end_time'):
                    result.append(f"本文件时间为： {engine_data['start_time']} 到 {engine_data['end_time']}\n 本次数据分析：飞机未启动发动机，请检查数据" )
            
            return "\n".join(result)
        except Exception as e:
            logging.error(f"生成发动机分析文本时出错: {str(e)}")
            return f"生成发动机分析文本时出错: {str(e)}"