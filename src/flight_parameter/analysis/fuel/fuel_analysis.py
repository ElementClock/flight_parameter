#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
燃油系统分析模块
===============

分析燃油系统数据，包括燃油消耗、油箱状态等关键参数。
"""

import logging
import re
from typing import Dict, Any

import pandas as pd

from ..analysis_interface import AnalysisInterface
from ..logger import get_analysis_logger, log_step
from ..utils import merge_continuous_time_periods
from ..config import FUEL_CONFIG
from ..column_config import FUEL_COLUMNS, GENERAL_COLUMNS

# 获取日志记录器
logger = get_analysis_logger(__name__)


class FuelAnalysis(AnalysisInterface):
    """燃油系统分析类"""
    
    @log_step("燃油系统数据分析")
    def analyze(self, df, **kwargs) -> Dict[str, Any]:
        """
        分析燃油系统数据
        
        Args:
            df (pandas.DataFrame): 包含燃油系统数据的DataFrame
            **kwargs: 其他参数
            
        Returns:
            dict: 燃油系统分析结果
        """
        try:
            logger.info(f"开始分析燃油系统数据，数据形状: {df.shape if hasattr(df, 'shape') else '未知'}")
            # 初始化返回数据
            fuel_result = {
                'type': 'fuel',
                'has_fuel_info': False,
                'fuel_tanks': [],
                'total_fuel_consumption': None,
                'start_time': None,
                'end_time': None,
                'warnings': [],
                'low_fuel_events': [],
                'imbalance_fuel_events': []
            }
            
            # 查找燃油相关列
            # 使用配置文件中的模式匹配燃油油箱列，如"Ⅰ号油箱油量"、"Ⅱ号油箱油量"等
            fuel_tank_pattern = re.compile(FUEL_COLUMNS['TANK_LEVEL'])
            fuel_temp_pattern = re.compile(FUEL_COLUMNS['TANK_TEMPERATURE'])
            engine_fuel_consumption_pattern = re.compile(FUEL_COLUMNS['ENGINE_CONSUMPTION'])
            
            # 提取燃油油量、温度和发动机耗油量列
            fuel_tank_columns = [col for col in df.columns if fuel_tank_pattern.search(col)]
            fuel_temp_columns = [col for col in df.columns if fuel_temp_pattern.search(col)]
            engine_fuel_consumption_columns = [col for col in df.columns if engine_fuel_consumption_pattern.search(col)]
            
            logger.debug(f"找到油箱列: {fuel_tank_columns}")
            logger.debug(f"找到油箱温度列: {fuel_temp_columns}")
            logger.debug(f"找到发动机耗油量列: {engine_fuel_consumption_columns}")
            
            # 检查是否有燃油数据
            if not fuel_tank_columns and not engine_fuel_consumption_columns:
                logger.warning("未找到燃油系统相关数据列")
                fuel_result['errors'] = ["未找到燃油系统相关数据列"]
                return fuel_result
                
            # 优化内存使用：只选择需要的列进行处理
            selected_columns = [col for col in df.columns if GENERAL_COLUMNS['FLIGHT_TIME'] in col]
            if fuel_tank_columns:
                selected_columns.extend(fuel_tank_columns)
            if fuel_temp_columns:
                selected_columns.extend(fuel_temp_columns)
            if engine_fuel_consumption_columns:
                selected_columns.extend(engine_fuel_consumption_columns)
                
            df_selected = df[selected_columns].copy()
            
            # 处理重复传感器数据（相差值小于20时取平均值，差异过高时报出问题）
            processed_tank_data = {}
            tank_groups = {}  # 用于分组相同编号的油箱数据
            
            # 按油箱编号分组
            for col in fuel_tank_columns:
                tank_match = fuel_tank_pattern.search(col)
                if tank_match:
                    tank_number = tank_match.group(1)
                    if tank_number not in tank_groups:
                        tank_groups[tank_number] = []
                    tank_groups[tank_number].append(col)
            
            # 处理每组油箱数据
            for tank_number, columns in tank_groups.items():
                logger.debug(f"处理 {tank_number} 号油箱，传感器数量: {len(columns)}")
                if len(columns) == 1:
                    # 只有一个传感器，直接使用
                    processed_tank_data[tank_number] = df_selected[columns[0]]
                else:
                    # 多个传感器，检查差异
                    tank_data_list = [df_selected[col] for col in columns]
                    tank_data_df = pd.concat(tank_data_list, axis=1)
                    
                    # 计算传感器间最大差异
                    max_diff = tank_data_df.max(axis=1) - tank_data_df.min(axis=1)
                    
                    # 检查是否有差异过高的情况
                    high_diff_mask = max_diff > FUEL_CONFIG['SENSOR_DIFFERENCE_THRESHOLD']
                    if high_diff_mask.any():
                        warning_msg = f"{tank_number}号油箱传感器间存在差异过高的情况 ({(high_diff_mask.sum())} 个时间点差异超过20)"
                        fuel_result['warnings'].append(warning_msg)
                        logger.warning(warning_msg)
                    
                    # 计算平均值
                    processed_tank_data[tank_number] = tank_data_df.mean(axis=1)
            
            # 分析各油箱数据
            tank_info = []
            total_start_fuel = 0
            total_end_fuel = 0
            
            for tank_number, fuel_data in processed_tank_data.items():
                logger.debug(f"分析 {tank_number} 号油箱数据，数据点数: {len(fuel_data)}")
                # 获取初始和最终燃油量
                start_fuel = fuel_data.iloc[0] if len(fuel_data) > 0 else 0
                end_fuel = fuel_data.iloc[-1] if len(fuel_data) > 0 else 0
                consumption = start_fuel - end_fuel
                
                # 获取温度数据（如果存在）
                temp_data = None
                temp_match = None
                for col in fuel_temp_columns:
                    temp_match = fuel_temp_pattern.search(col)
                    if temp_match and temp_match.group(1) == tank_number:
                        temp_data = df_selected[col]
                        break
                
                tank_info.append({
                    'tank_name': f"{tank_number}号",
                    'start_fuel': start_fuel,
                    'end_fuel': end_fuel,
                    'consumption': consumption,
                    'temperature_data': temp_data,
                    'fuel_data': fuel_data  # 保存全过程油量数据用于后续分析
                })
                
                total_start_fuel += start_fuel
                total_end_fuel += end_fuel
            
            # 分析发动机耗油量
            engine_fuel_consumption_info = []
            total_engine_fuel_consumption = 0
            
            for col in engine_fuel_consumption_columns:
                engine_match = engine_fuel_consumption_pattern.search(col)
                if engine_match:
                    engine_number = engine_match.group(1)
                    fuel_data = df_selected[col]
                    
                    # 发动机总耗油量是累计值，取最终值作为总耗油量
                    total_consumption = fuel_data.iloc[-1] if len(fuel_data) > 0 else 0
                    
                    engine_fuel_consumption_info.append({
                        'engine_name': f"{engine_number}发",
                        'total_consumption': total_consumption
                    })
                    
                    total_engine_fuel_consumption += total_consumption
                    logger.debug(f"发动机 {engine_number} 总耗油量: {total_consumption}")
            
            # 计算总燃油消耗
            total_fuel_consumption = total_start_fuel - total_end_fuel
            logger.info(f"总燃油消耗: {total_fuel_consumption} kg")
            
            # 低油量监测（全过程）
            low_fuel_events = []
            tank_info_dict = {tank['tank_name']: tank for tank in tank_info}
            
            for tank_name, tank in tank_info_dict.items():
                # 检查是否有任何时刻油量低于阈值
                low_fuel_mask = tank['fuel_data'] < FUEL_CONFIG['LOW_FUEL_THRESHOLD']
                if low_fuel_mask.any():
                    logger.debug(f"{tank_name} 检测到低油量事件")
                    # 找到所有低于200kg的时间点
                    low_fuel_times = df_selected.loc[low_fuel_mask, [col for col in df_selected.columns if GENERAL_COLUMNS['FLIGHT_TIME'] in col][0]]
                    low_fuel_values = tank['fuel_data'][low_fuel_mask]
                    
                    # 将连续的时间点合并为时间段
                    time_periods = merge_continuous_time_periods(
                        low_fuel_times, 
                        low_fuel_values, 
                        FUEL_CONFIG['CONTINUOUS_TIME_THRESHOLD'])
                    
                    # 添加低油量事件，将min_value重命名为min_fuel
                    for period in time_periods:
                        low_fuel_events.append({
                            'tank_name': tank_name,
                            'start_time': period['start_time'],
                            'end_time': period['end_time'],
                            'min_fuel': period.get('min_value', 0)
                        })
            
            # 油箱不平衡监测（比较各油箱油量差异）
            imbalance_fuel_events = []
            tank_names = list(processed_tank_data.keys())
            if len(tank_names) >= 2:
                logger.debug(f"检测油箱间不平衡，涉及油箱: {tank_names}")
                # 计算所有油箱之间的油量差异
                for i in range(len(tank_names)):
                    for j in range(i+1, len(tank_names)):
                        tank1_name = tank_names[i]
                        tank2_name = tank_names[j]
                        tank1_data = processed_tank_data[tank1_name]
                        tank2_data = processed_tank_data[tank2_name]
                        
                        # 计算油量差异
                        diff = abs(tank1_data - tank2_data)
                        
                        # 检查是否有差异超过阈值的情况
                        imbalance_mask = diff > FUEL_CONFIG['IMBALANCE_THRESHOLD']
                        if imbalance_mask.any():
                            logger.debug(f"检测到 {tank1_name} 和 {tank2_name} 之间存在不平衡")
                            # 找到所有不平衡的时间点
                            imbalance_times = df_selected.loc[imbalance_mask, [col for col in df_selected.columns if GENERAL_COLUMNS['FLIGHT_TIME'] in col][0]]
                            imbalance_values = diff[imbalance_mask]
                            
                            # 将连续的时间点合并为时间段
                            time_periods = merge_continuous_time_periods(
                                imbalance_times, 
                                imbalance_values, 
                                FUEL_CONFIG['CONTINUOUS_TIME_THRESHOLD'])
                            
                            # 添加不平衡事件，将max_value重命名为max_diff
                            for period in time_periods:
                                imbalance_fuel_events.append({
                                    'tank1_name': tank1_name,
                                    'tank2_name': tank2_name,
                                    'start_time': period['start_time'],
                                    'end_time': period['end_time'],
                                    'max_diff': period.get('max_value', 0)
                                })
            
            # 组装最终结果
            fuel_result.update({
                'has_fuel_info': True,
                'fuel_tanks': tank_info,
                'engine_fuel_consumptions': engine_fuel_consumption_info,
                'total_fuel_consumption': total_fuel_consumption,
                'total_engine_fuel_consumption': total_engine_fuel_consumption,
                'start_time': df_selected[[col for col in df_selected.columns if GENERAL_COLUMNS['FLIGHT_TIME'] in col][0]].iloc[0] if len(df_selected) > 0 else None,
                'end_time': df_selected[[col for col in df_selected.columns if GENERAL_COLUMNS['FLIGHT_TIME'] in col][0]].iloc[-1] if len(df_selected) > 0 else None,
                'low_fuel_events': low_fuel_events,
                'imbalance_fuel_events': imbalance_fuel_events
            })
            
            logger.info("完成燃油系统数据分析")
            return fuel_result
        except Exception as e:
            logger.error(f"分析燃油系统数据时出错: {str(e)}", exc_info=True)
            return {
                'type': 'fuel',
                'has_fuel_info': False,
                'fuel_tanks': [],
                'total_fuel_consumption': None,
                'start_time': None,
                'end_time': None,
                'warnings': [],
                'low_fuel_events': [],
                'imbalance_fuel_events': [],
                'errors': [f"分析燃油系统数据时出错: {str(e)}"]
            }
    
    def generate_text(self, fuel_data: Dict[str, Any]) -> str:
        """生成燃油系统分析结果文本
        
        Args:
            fuel_data (dict): 燃油系统分析数据
            
        Returns:
            str: 格式化的文本结果
        """
        try:
            result = []
            
            # 检查是否有错误
            if 'errors' in fuel_data and fuel_data['errors']:
                result.extend(fuel_data['errors'])
                return "\n".join(result)
            
            # 检查是否有燃油信息
            if not fuel_data['has_fuel_info']:
                result.append("未找到燃油系统相关信息")
                return "\n".join(result)
            
            # 添加标题标记 (使用Markdown标题格式)
            result.append("### 燃油系统分析结果")
            
            # 添加燃油消耗信息（注意：这行不应该被居中显示）
            result.append(f"总燃油消耗: {fuel_data['total_fuel_consumption']:.2f} kg")
            
            # 添加合并后的油箱和发动机耗油量信息表格 (使用Markdown表格格式)
            if fuel_data['fuel_tanks']:
                result.append("")
                # 创建一个映射，将发动机编号映射到其总耗油量
                engine_fuel_map = {}
                if fuel_data['engine_fuel_consumptions']:
                    for engine in fuel_data['engine_fuel_consumptions']:
                        engine_fuel_map[engine['engine_name']] = engine['total_consumption']
                
                # 表头包含油箱信息和对应的发动机耗油量
                result.append("| 油箱编号 | 初始燃油(kg) | 最终燃油(kg) | 消耗燃油(kg) | 温度变化(°C) | 发动机编号 | 发动机耗油量(kg) |")
                # 添加列宽定义行，使所有列等宽
                result.append("| :::14.3::: | :::14.3::: | :::14.3::: | :::14.3::: | :::14.3::: | :::14.3::: | :::14.3::: |")
                result.append("|----------|--------------|--------------|--------------|--------------|------------|------------------|")
                
                # 定义油箱到发动机的映射关系
                tank_to_engine_map = {
                    "Ⅰ号": "1发",
                    "Ⅱ号": "2发",
                    "Ⅲ号": "3发",
                    "Ⅳ号": "4发",
                    "1号": "1发",
                    "2号": "2发",
                    "3号": "3发",
                    "4号": "4发"
                }
                
                # 计算总消耗燃油量、初始燃油总量和最终燃油总量
                total_consumption = 0.0
                total_start_fuel = 0.0
                total_end_fuel = 0.0
                total_engine_consumption = 0.0
                
                for tank in fuel_data['fuel_tanks']:
                    # 如果有温度数据，显示温度信息
                    temp_change = "无温度数据"
                    if tank['temperature_data'] is not None and len(tank['temperature_data']) > 0:
                        start_temp = tank['temperature_data'].iloc[0]
                        end_temp = tank['temperature_data'].iloc[-1]
                        temp_change = f"{start_temp:.2f} -> {end_temp:.2f}"
                    
                    # 尝试关联对应的发动机编号和耗油量
                    engine_id = "无"
                    engine_consumption = 0.0
                    
                    # 根据油箱编号查找对应的发动机
                    if tank['tank_name'] in tank_to_engine_map:
                        engine_name = tank_to_engine_map[tank['tank_name']]
                        if engine_name in engine_fuel_map:
                            engine_id = engine_name
                            engine_consumption = engine_fuel_map[engine_name]
                    
                    # 累加各项数据
                    total_consumption += tank['consumption']
                    total_start_fuel += tank['start_fuel']
                    total_end_fuel += tank['end_fuel']
                    total_engine_consumption += engine_consumption
                    
                    # 添加表格行
                    engine_consumption_str = f"{engine_consumption:.2f}" if engine_consumption > 0 else "无"
                    result.append(f"| {tank['tank_name']} | {tank['start_fuel']:.2f} | {tank['end_fuel']:.2f} | {tank['consumption']:.2f} | {temp_change} | {engine_id} | {engine_consumption_str} |")
                
                # 添加求和行，使用 "-" 填充非数值列
                result.append(f"| 合计 | {total_start_fuel:.2f} | {total_end_fuel:.2f} | {total_consumption:.2f} | - | - | {total_engine_consumption:.2f} |")
            # 如果没有油箱信息但是有发动机耗油量信息，单独显示发动机信息
            elif fuel_data['engine_fuel_consumptions']:
                result.append("")
                result.append("| 发动机编号 | 总耗油量(kg) |")
                # 添加列宽定义行，使所有列等宽
                result.append("| :::50::: | :::50::: |")
                result.append("|----------|-------------|")
                
                # 计算总消耗燃油量
                total_engine_consumption = 0.0
                for engine in fuel_data['engine_fuel_consumptions']:
                    result.append(f"| {engine['engine_name']} | {engine['total_consumption']:.2f} |")
                    total_engine_consumption += engine['total_consumption']
                
                # 添加求和行
                result.append(f"| 合计 | {total_engine_consumption:.2f} |")
            return "\n".join(result)
        except Exception as e:
            logging.error(f"生成燃油系统分析文本时出错: {str(e)}")
            return f"生成燃油系统分析文本时出错: {str(e)}"