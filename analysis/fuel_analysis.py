#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
燃油系统分析模块
===============

分析燃油系统数据，包括燃油消耗、油箱状态等关键参数。
"""

import logging
import re

import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


def analyze_fuel(df):
    """
    分析燃油系统数据
    
    Args:
        df (pandas.DataFrame): 包含燃油系统数据的DataFrame
        
    Returns:
        dict: 燃油系统分析结果
    """
    try:
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
        # 匹配燃油油箱列，如"Ⅰ号油箱油量"、"Ⅱ号油箱油量"等
        fuel_tank_pattern = re.compile(r'([ⅠⅡⅢⅣ])号油箱油量')
        fuel_temp_pattern = re.compile(r'([ⅠⅡⅢⅣ])号油箱燃油温度')
        engine_fuel_consumption_pattern = re.compile(r'(\d)发总耗量')
        
        # 提取燃油油量、温度和发动机耗油量列
        fuel_tank_columns = [col for col in df.columns if fuel_tank_pattern.search(col)]
        fuel_temp_columns = [col for col in df.columns if fuel_temp_pattern.search(col)]
        engine_fuel_consumption_columns = [col for col in df.columns if engine_fuel_consumption_pattern.search(col)]
        
        # 检查是否有燃油数据
        if not fuel_tank_columns and not engine_fuel_consumption_columns:
            fuel_result['errors'] = ["未找到燃油系统相关数据列"]
            return fuel_result
            
        # 优化内存使用：只选择需要的列进行处理
        selected_columns = ['飞行时间']
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
                high_diff_mask = max_diff > 20
                if high_diff_mask.any():
                    warning_msg = f"{tank_number}号油箱传感器间存在差异过高的情况 ({(high_diff_mask.sum())} 个时间点差异超过20)"
                    fuel_result['warnings'].append(warning_msg)
                
                # 计算平均值
                processed_tank_data[tank_number] = tank_data_df.mean(axis=1)
        
        # 分析各油箱数据
        tank_info = []
        total_start_fuel = 0
        total_end_fuel = 0
        
        for tank_number, fuel_data in processed_tank_data.items():
            # 获取初始和最终燃油量
            start_fuel = fuel_data.iloc[0] if len(fuel_data) > 0 else 0
            end_fuel = fuel_data.iloc[-1] if len(fuel_data) > 0 else 0
            consumption = start_fuel - end_fuel
            
            # 获取温度数据（如果存在）
            temp_data = None
            temp_col_name = f"{tank_number}号油箱燃油温度"
            if temp_col_name in df_selected.columns:
                temp_data = df_selected[temp_col_name]
            
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
        
        # 计算总燃油消耗
        total_fuel_consumption = total_start_fuel - total_end_fuel
        
        # 低油量监测（全过程）
        low_fuel_events = []
        tank_info_dict = {tank['tank_name']: tank for tank in tank_info}
        
        for tank_name, tank in tank_info_dict.items():
            # 检查是否有任何时刻油量低于200kg
            low_fuel_mask = tank['fuel_data'] < 200
            if low_fuel_mask.any():
                # 找到所有低于200kg的时间点
                low_fuel_times = df_selected.loc[low_fuel_mask, '飞行时间']
                low_fuel_values = tank['fuel_data'][low_fuel_mask]
                
                # 将连续的时间点合并为时间段
                time_periods = []
                if len(low_fuel_times) > 0:
                    # 初始化第一个时间段
                    start_time = low_fuel_times.iloc[0]
                    end_time = low_fuel_times.iloc[0]
                    min_fuel = low_fuel_values.iloc[0]
                    
                    # 遍历所有低油量时间点
                    for i in range(1, len(low_fuel_times)):
                        current_time = low_fuel_times.iloc[i]
                        current_fuel = low_fuel_values.iloc[i]
                        
                        # 检查是否与前一个时间点连续（时间差不超过1秒）
                        time_diff = (current_time - low_fuel_times.iloc[i-1]).total_seconds()
                        if time_diff <= 1.0:
                            # 更新结束时间和最小油量
                            end_time = current_time
                            min_fuel = min(min_fuel, current_fuel)
                        else:
                            # 结束当前时间段并开始新时间段
                            time_periods.append({
                                'start_time': start_time,
                                'end_time': end_time,
                                'min_fuel': min_fuel
                            })
                            start_time = current_time
                            end_time = current_time
                            min_fuel = current_fuel
                    
                    # 添加最后一个时间段
                    time_periods.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'min_fuel': min_fuel
                    })
                
                low_fuel_events.append({
                    'tank_name': tank_name,
                    'times': low_fuel_times.tolist(),
                    'values': low_fuel_values.tolist(),
                    'count': len(low_fuel_times),
                    'time_periods': time_periods
                })
        
        # 不平衡油量监测（全过程）
        imbalance_fuel_events = []
        # 查找1号和2号油箱（左侧）以及3号和4号油箱（右侧）
        tank_1 = tank_info_dict.get("Ⅰ号")
        tank_2 = tank_info_dict.get("Ⅱ号")
        tank_3 = tank_info_dict.get("Ⅲ号")
        tank_4 = tank_info_dict.get("Ⅳ号")
        
        if tank_1 and tank_2 and tank_3 and tank_4:
            # 计算两侧油量
            left_side_fuel = tank_1['fuel_data'] + tank_2['fuel_data']
            right_side_fuel = tank_3['fuel_data'] + tank_4['fuel_data']
            
            # 检查不平衡情况
            fuel_difference = abs(left_side_fuel - right_side_fuel)
            imbalance_mask = fuel_difference > 100
            
            if imbalance_mask.any():
                # 找到所有不平衡的时间点
                imbalance_times = df_selected.loc[imbalance_mask, '飞行时间']
                difference_values = fuel_difference[imbalance_mask]
                
                # 将连续的时间点合并为时间段
                time_periods = []
                if len(imbalance_times) > 0:
                    # 初始化第一个时间段
                    start_time = imbalance_times.iloc[0]
                    end_time = imbalance_times.iloc[0]
                    max_difference = difference_values.iloc[0]
                    
                    # 遍历所有不平衡时间点
                    for i in range(1, len(imbalance_times)):
                        current_time = imbalance_times.iloc[i]
                        current_difference = difference_values.iloc[i]
                        
                        # 检查是否与前一个时间点连续（时间差不超过1秒，假设数据是每秒记录一次）
                        time_diff = (current_time - imbalance_times.iloc[i-1]).total_seconds()
                        if time_diff <= 1.0:
                            # 更新结束时间和最大差异
                            end_time = current_time
                            max_difference = max(max_difference, current_difference)
                        else:
                            # 结束当前时间段并开始新时间段
                            time_periods.append({
                                'start_time': start_time,
                                'end_time': end_time,
                                'max_difference': max_difference
                            })
                            start_time = current_time
                            end_time = current_time
                            max_difference = current_difference
                    
                    # 添加最后一个时间段
                    time_periods.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'max_difference': max_difference
                    })
                
                imbalance_fuel_events.append({
                    'times': imbalance_times.tolist(),
                    'differences': difference_values.tolist(),
                    'count': len(imbalance_times),
                    'time_periods': time_periods
                })
        
        # 填充返回数据
        fuel_result['has_fuel_info'] = bool(tank_info)
        fuel_result['fuel_tanks'] = tank_info
        fuel_result['engine_fuel_consumptions'] = engine_fuel_consumption_info
        fuel_result['total_fuel_consumption'] = total_fuel_consumption
        fuel_result['total_engine_fuel_consumption'] = total_engine_fuel_consumption
        fuel_result['start_time'] = df_selected['飞行时间'].iloc[0] if not df_selected.empty and '飞行时间' in df_selected.columns else None
        fuel_result['end_time'] = df_selected['飞行时间'].iloc[-1] if not df_selected.empty and '飞行时间' in df_selected.columns else None
        fuel_result['low_fuel_events'] = low_fuel_events
        fuel_result['imbalance_fuel_events'] = imbalance_fuel_events
        
        # 清理临时数据以释放内存
        del df_selected
        
        return fuel_result
    except Exception as e:
        logging.error(f"分析燃油系统数据时出错: {str(e)}")
        return {
            'type': 'fuel',
            'errors': [f"分析燃油系统数据时出错: {str(e)}"],
            'has_fuel_info': False,
            'fuel_tanks': [],
            'engine_fuel_consumptions': [],
            'total_fuel_consumption': None,
            'total_engine_fuel_consumption': None,
            'start_time': None,
            'end_time': None,
            'warnings': [],
            'low_fuel_events': [],
            'imbalance_fuel_events': []
        }


def generate_fuel_text_with_markers(fuel_data):
    """生成带标识符的燃油系统分析文本输出
    
    Args:
        fuel_data (dict): 包含燃油系统分析结果的字典，可能包含错误信息
        
    Returns:
        str: 格式化的文本结果，包含错误信息或正常分析结果
    """
    try:
        result = []
        
        # 检查是否有错误信息
        if 'errors' in fuel_data and fuel_data['errors']:
            result.extend(fuel_data['errors'])
            return "\n".join(result)
        
        # 检查是否有燃油信息
        if not fuel_data['has_fuel_info']:
            result.append("未找到燃油系统相关信息")
            return "\n".join(result)
        
        # 使用标识符标记标题行
        title = "[[BOLD]]燃油系统分析结果[[/BOLD]]"
        formatted_title = title.center(100, '-')
        result.append(formatted_title)
        
        # 添加警告信息
        if 'warnings' in fuel_data and fuel_data['warnings']:
            for warning in fuel_data['warnings']:
                result.append(f"[[AMBER]]警告: {warning}[[/AMBER]]")
        
        # 添加低油量事件信息
        if 'low_fuel_events' in fuel_data and fuel_data['low_fuel_events']:
            for event in fuel_data['low_fuel_events']:
                result.append(f"  {event['tank_name']}油箱本次飞行累计 {event['count']} s油量低于200kg，最低油量为 {min(event['values']):.2f} kg")
                
                # 如果有时间段信息，添加详细的时间段
                if 'time_periods' in event and event['time_periods']:
                    result.append("    低油量时间段详情:")
                    for period in event['time_periods']:
                        if period['start_time'] == period['end_time']:
                            result.append(f"      - {period['start_time'].strftime('%H:%M:%S')} : 最低油量 {period['min_fuel']:.2f} kg")
                        else:
                            result.append(f"      - {period['start_time'].strftime('%H:%M:%S')} ~ {period['end_time'].strftime('%H:%M:%S')} : 最低油量 {period['min_fuel']:.2f} kg")
        
        # 添加不平衡油量事件信息
        if 'imbalance_fuel_events' in fuel_data and fuel_data['imbalance_fuel_events']:
            for event in fuel_data['imbalance_fuel_events']:
                result.append(f"  本次飞行不平衡油量累计 {event['count']} s，最大差异为 {max(event['differences']):.2f} kg")
                
                # 如果有时间段信息，添加详细的时间段
                if 'time_periods' in event and event['time_periods']:
                    result.append("    不平衡时间段详情:")
                    for period in event['time_periods']:
                        if period['start_time'] == period['end_time']:
                            result.append(f"      - {period['start_time'].strftime('%H:%M:%S')} : 差异 {period['max_difference']:.2f} kg")
                        else:
                            result.append(f"      - {period['start_time'].strftime('%H:%M:%S')} ~ {period['end_time'].strftime('%H:%M:%S')} : 最大差异 {period['max_difference']:.2f} kg")
        
        # 添加总燃油消耗信息
        if fuel_data['total_fuel_consumption'] is not None:
            result.append(f" 油箱总燃油消耗量: {fuel_data['total_fuel_consumption']:.2f} kg ")
        
        # 添加发动机总耗油量信息
        if fuel_data['total_engine_fuel_consumption'] is not None:
            result.append(f" 发动机总耗油量: {fuel_data['total_engine_fuel_consumption']:.2f} kg ")
        
        # 添加各油箱信息
        if fuel_data['fuel_tanks']:
            result.append(" 各油箱燃油情况: ")
            for tank in fuel_data['fuel_tanks']:
                result.append(f"  {tank['tank_name']}油箱 - 初始燃油: {tank['start_fuel']:.2f} kg, "
                             f"最终燃油: {tank['end_fuel']:.2f} kg, 消耗燃油: {tank['consumption']:.2f} kg")
                
                # 如果有温度数据，显示温度信息
                if tank['temperature_data'] is not None:
                    start_temp = tank['temperature_data'].iloc[0] if len(tank['temperature_data']) > 0 else 0
                    end_temp = tank['temperature_data'].iloc[-1] if len(tank['temperature_data']) > 0 else 0
                    result.append(f"    温度变化: {start_temp:.2f} °C -> {end_temp:.2f} °C")
        
        # 添加发动机耗油量信息
        if fuel_data['engine_fuel_consumptions']:
            result.append(" 各发动机耗油量: ")
            for engine in fuel_data['engine_fuel_consumptions']:
                result.append(f"  {engine['engine_name']} - 总耗油量: {engine['total_consumption']:.2f} kg")
        
        return "\n".join(result)
    except Exception as e:
        logging.error(f"生成燃油系统分析文本时出错: {str(e)}")
        return f"生成燃油系统分析文本时出错: {str(e)}"