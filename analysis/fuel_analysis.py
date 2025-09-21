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
            'warnings': []
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
                'temperature_data': temp_data
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
        
        # 填充返回数据
        fuel_result['has_fuel_info'] = bool(tank_info)
        fuel_result['fuel_tanks'] = tank_info
        fuel_result['engine_fuel_consumptions'] = engine_fuel_consumption_info
        fuel_result['total_fuel_consumption'] = total_fuel_consumption
        fuel_result['total_engine_fuel_consumption'] = total_engine_fuel_consumption
        fuel_result['start_time'] = df_selected['飞行时间'].iloc[0] if not df_selected.empty and '飞行时间' in df_selected.columns else None
        fuel_result['end_time'] = df_selected['飞行时间'].iloc[-1] if not df_selected.empty and '飞行时间' in df_selected.columns else None
        
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
            'warnings': []
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