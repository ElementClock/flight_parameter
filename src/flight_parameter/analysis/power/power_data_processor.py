#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
电源系统数据分析核心模块
======================

专门负责电源系统数据的分析处理，不涉及文本生成。
"""

import logging
import re
from typing import Dict, Any, List

import pandas as pd

from ..utils import safe_get_statistic
from ..config import POWER_CONFIG
from ..column_config import POWER_COLUMNS, GENERAL_COLUMNS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class PowerDataProcessor:
    """电源系统数据处理器类
    
    该类专门负责电源系统数据的分析处理，严格遵守单一职责原则。
    """
    
    def analyze(self, df, **kwargs) -> Dict[str, Any]:
        """
        分析电源系统数据
        
        Args:
            df (pandas.DataFrame): 包含电源系统数据的DataFrame
            **kwargs: 其他参数
            
        Returns:
            dict: 电源系统分析结果
        """
        try:
            # 初始化返回数据
            power_result = {
                'type': 'power',
                'has_power_info': False,
                'dc_generators': [],  # 直流发电机
                'ac_generators': [],  # 交流发电机
                'bus_bars': [],       # 汇流条信息
                'start_time': None,
                'end_time': None,
                'warnings': [],
                'errors': []
            }
            
            # 查找电源相关列
            # 使用配置文件中的模式匹配直流发电机电压列，如"1号直流发电机电压"、"2号直流发电机电压"等
            dc_voltage_pattern = re.compile(POWER_COLUMNS['DC_VOLTAGE'])
            dc_current_pattern = re.compile(POWER_COLUMNS['DC_CURRENT'])
            
            # 使用配置文件中的模式匹配交流发电机电压列，如"1号交流发电机电压"、"2号交流发电机电压"等
            ac_voltage_pattern = re.compile(POWER_COLUMNS['AC_VOLTAGE'])
            ac_current_pattern = re.compile(POWER_COLUMNS['AC_CURRENT'])
            
            # 使用配置文件中的模式匹配汇流条列，如"左汇流条电压"、"右汇流条电流"等
            bus_voltage_pattern = re.compile(POWER_COLUMNS['BUS_VOLTAGE'])
            bus_current_pattern = re.compile(POWER_COLUMNS['BUS_CURRENT'])
            
            # 提取相关列
            dc_voltage_columns = [col for col in df.columns if dc_voltage_pattern.search(col)]
            dc_current_columns = [col for col in df.columns if dc_current_pattern.search(col)]
            
            ac_voltage_columns = [col for col in df.columns if ac_voltage_pattern.search(col)]
            ac_current_columns = [col for col in df.columns if ac_current_pattern.search(col)]
            
            bus_voltage_columns = [col for col in df.columns if bus_voltage_pattern.search(col)]
            bus_current_columns = [col for col in df.columns if bus_current_pattern.search(col)]
            
            # 检查是否有电源数据
            if not any([dc_voltage_columns, ac_voltage_columns, bus_voltage_columns]):
                power_result['errors'] = ["未找到电源系统相关数据列"]
                return power_result
                
            # 优化内存使用：只选择需要的列进行处理
            selected_columns = [col for col in df.columns if GENERAL_COLUMNS['FLIGHT_TIME'] in col]
            if dc_voltage_columns:
                selected_columns.extend(dc_voltage_columns)
            if dc_current_columns:
                selected_columns.extend(dc_current_columns)
            if ac_voltage_columns:
                selected_columns.extend(ac_voltage_columns)
            if ac_current_columns:
                selected_columns.extend(ac_current_columns)
            if bus_voltage_columns:
                selected_columns.extend(bus_voltage_columns)
            if bus_current_columns:
                selected_columns.extend(bus_current_columns)
                
            df_selected = df[selected_columns].copy()
            
            # 分析直流发电机数据
            dc_generator_info = []
            # 首先收集所有直流发电机编号
            dc_gen_numbers = set()
            for col in dc_voltage_columns + dc_current_columns:
                match = dc_voltage_pattern.search(col) or dc_current_pattern.search(col)
                if match:
                    dc_gen_numbers.add(int(match.group(1)))
            
            for i in sorted(dc_gen_numbers):  # 使用实际找到的发电机编号
                # 构造可能的列名并查找实际存在的列
                voltage_col = None
                current_col = None
                
                # 查找电压列
                for col in dc_voltage_columns:
                    if f"{i}号直流发电机" in col:
                        voltage_col = col
                        break
                        
                # 查找电流列
                for col in dc_current_columns:
                    if f"{i}号直流发电机" in col:
                        current_col = col
                        break
                
                # 检查是否存在这些列
                has_voltage = voltage_col is not None
                has_current = current_col is not None
                
                if has_voltage or has_current:
                    generator_info = {
                        'generator_id': f"{i}号直流发电机",
                        'voltage_data': df_selected[voltage_col] if has_voltage else None,
                        'current_data': df_selected[current_col] if has_current else None,
                        'start_voltage': None,
                        'end_voltage': None,
                        'avg_voltage': None,
                        'max_voltage': None,
                        'min_voltage': None,
                        'start_current': None,
                        'end_current': None,
                        'avg_current': None,
                        'max_current': None,
                        'min_current': None
                    }
                    
                    # 计算统计数据
                    if has_voltage and voltage_col in df_selected.columns:
                        voltage_data = df_selected[voltage_col]
                        generator_info['start_voltage'] = safe_get_statistic(voltage_data, 'first')
                        generator_info['end_voltage'] = safe_get_statistic(voltage_data, 'last')
                        generator_info['avg_voltage'] = safe_get_statistic(voltage_data, 'mean')
                        generator_info['max_voltage'] = safe_get_statistic(voltage_data, 'max')
                        generator_info['min_voltage'] = safe_get_statistic(voltage_data, 'min')
                    
                    if has_current and current_col in df_selected.columns:
                        current_data = df_selected[current_col]
                        generator_info['start_current'] = safe_get_statistic(current_data, 'first')
                        generator_info['end_current'] = safe_get_statistic(current_data, 'last')
                        generator_info['avg_current'] = safe_get_statistic(current_data, 'mean')
                        generator_info['max_current'] = safe_get_statistic(current_data, 'max')
                        generator_info['min_current'] = safe_get_statistic(current_data, 'min')
                    
                    dc_generator_info.append(generator_info)
            
            # 分析交流发电机数据
            ac_generator_info = []
            # 首先收集所有交流发电机编号
            ac_gen_numbers = set()
            for col in ac_voltage_columns + ac_current_columns:
                match = ac_voltage_pattern.search(col) or ac_current_pattern.search(col)
                if match:
                    ac_gen_numbers.add(int(match.group(1)))
                    
            for i in sorted(ac_gen_numbers):  # 使用实际找到的发电机编号
                # 构造可能的列名并查找实际存在的列
                voltage_col = None
                current_col = None
                
                # 查找电压列
                for col in ac_voltage_columns:
                    if f"{i}号交流发电机" in col:
                        voltage_col = col
                        break
                        
                # 查找电流列
                for col in ac_current_columns:
                    if f"{i}号交流发电机" in col:
                        current_col = col
                        break
                
                # 检查是否存在这些列
                has_voltage = voltage_col is not None
                has_current = current_col is not None
                
                if has_voltage or has_current:
                    generator_info = {
                        'generator_id': f"{i}号交流发电机",
                        'voltage_data': df_selected[voltage_col] if has_voltage else None,
                        'current_data': df_selected[current_col] if has_current else None,
                        'start_voltage': None,
                        'end_voltage': None,
                        'avg_voltage': None,
                        'max_voltage': None,
                        'min_voltage': None,
                        'start_current': None,
                        'end_current': None,
                        'avg_current': None,
                        'max_current': None,
                        'min_current': None
                    }
                    
                    # 计算统计数据
                    if has_voltage and voltage_col in df_selected.columns:
                        voltage_data = df_selected[voltage_col]
                        generator_info['start_voltage'] = safe_get_statistic(voltage_data, 'first')
                        generator_info['end_voltage'] = safe_get_statistic(voltage_data, 'last')
                        generator_info['avg_voltage'] = safe_get_statistic(voltage_data, 'mean')
                        generator_info['max_voltage'] = safe_get_statistic(voltage_data, 'max')
                        generator_info['min_voltage'] = safe_get_statistic(voltage_data, 'min')
                    
                    if has_current and current_col in df_selected.columns:
                        current_data = df_selected[current_col]
                        generator_info['start_current'] = safe_get_statistic(current_data, 'first')
                        generator_info['end_current'] = safe_get_statistic(current_data, 'last')
                        generator_info['avg_current'] = safe_get_statistic(current_data, 'mean')
                        generator_info['max_current'] = safe_get_statistic(current_data, 'max')
                        generator_info['min_current'] = safe_get_statistic(current_data, 'min')
                    
                    ac_generator_info.append(generator_info)
            
            # 分析汇流条数据
            bus_bar_info = []
            # 收集所有汇流条编号
            bus_numbers = set()
            for col in bus_voltage_columns + bus_current_columns:
                match = bus_voltage_pattern.search(col) or bus_current_pattern.search(col)
                if match:
                    bus_numbers.add(match.group(1))
            
            for bus_name in sorted(bus_numbers):
                # 构造可能的列名并查找实际存在的列
                voltage_col = None
                current_col = None
                
                # 查找电压列
                for col in bus_voltage_columns:
                    if bus_name in col:
                        voltage_col = col
                        break
                        
                # 查找电流列
                for col in bus_current_columns:
                    if bus_name in col:
                        current_col = col
                        break
                
                # 检查是否存在这些列
                has_voltage = voltage_col is not None
                has_current = current_col is not None
                
                if has_voltage or has_current:
                    bus_info = {
                        'bus_id': bus_name,
                        'voltage_data': df_selected[voltage_col] if has_voltage else None,
                        'current_data': df_selected[current_col] if has_current else None,
                        'start_voltage': None,
                        'end_voltage': None,
                        'avg_voltage': None,
                        'max_voltage': None,
                        'min_voltage': None,
                        'start_current': None,
                        'end_current': None,
                        'avg_current': None,
                        'max_current': None,
                        'min_current': None
                    }
                    
                    # 计算统计数据
                    if has_voltage and voltage_col in df_selected.columns:
                        voltage_data = df_selected[voltage_col]
                        bus_info['start_voltage'] = safe_get_statistic(voltage_data, 'first')
                        bus_info['end_voltage'] = safe_get_statistic(voltage_data, 'last')
                        bus_info['avg_voltage'] = safe_get_statistic(voltage_data, 'mean')
                        bus_info['max_voltage'] = safe_get_statistic(voltage_data, 'max')
                        bus_info['min_voltage'] = safe_get_statistic(voltage_data, 'min')
                    
                    if has_current and current_col in df_selected.columns:
                        current_data = df_selected[current_col]
                        bus_info['start_current'] = safe_get_statistic(current_data, 'first')
                        bus_info['end_current'] = safe_get_statistic(current_data, 'last')
                        bus_info['avg_current'] = safe_get_statistic(current_data, 'mean')
                        bus_info['max_current'] = safe_get_statistic(current_data, 'max')
                        bus_info['min_current'] = safe_get_statistic(current_data, 'min')
                    
                    bus_bar_info.append(bus_info)
            
            # 设置返回结果
            power_result.update({
                'has_power_info': True,
                'dc_generators': dc_generator_info,
                'ac_generators': ac_generator_info,
                'bus_bars': bus_bar_info,
                'start_time': df_selected.iloc[0, 0] if len(df_selected) > 0 else None,
                'end_time': df_selected.iloc[-1, 0] if len(df_selected) > 0 else None
            })
            
            return power_result
        except Exception as e:
            logging.error(f"分析电源系统数据时出错: {str(e)}", exc_info=True)
            return {
                'type': 'power',
                'has_power_info': False,
                'dc_generators': [],
                'ac_generators': [],
                'bus_bars': [],
                'start_time': None,
                'end_time': None,
                'warnings': [],
                'errors': [f"分析电源系统数据时出错: {str(e)}"]
            }