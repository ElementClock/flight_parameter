#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
电源系统分析模块
===============

分析电源系统数据，包括发电机、电池状态等关键参数。
"""

import logging
import re
from typing import Dict, Any, List

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


class PowerAnalysis(AnalysisInterface):
    """电源系统分析类"""
    
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
            # 匹配直流发电机电压列，如"1号直流发电机电压"、"2号直流发电机电压"等
            dc_voltage_pattern = re.compile(r'(\d)号直流发电机(?:输出)?电压')
            dc_current_pattern = re.compile(r'(\d)号直流发电机(?:输出)?电流')
            
            # 匹配交流发电机电压列，如"1号交流发电机电压"、"2号交流发电机电压"等
            ac_voltage_pattern = re.compile(r'(\d)号交流发电机(?:输出)?电压')
            ac_current_pattern = re.compile(r'(\d)号交流发电机(?:输出)?电流')
            
            # 匹配汇流条列，如"左汇流条电压"、"右汇流条电流"等
            bus_voltage_pattern = re.compile(r'(.+?)汇流条电压')
            bus_current_pattern = re.compile(r'(.+?)汇流条电流')
            
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
            selected_columns = ['飞行时间']
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
                        generator_info['start_voltage'] = voltage_data.iloc[0] if len(voltage_data) > 0 else None
                        generator_info['end_voltage'] = voltage_data.iloc[-1] if len(voltage_data) > 0 else None
                        generator_info['avg_voltage'] = voltage_data.mean() if len(voltage_data) > 0 else None
                        generator_info['max_voltage'] = voltage_data.max() if len(voltage_data) > 0 else None
                        generator_info['min_voltage'] = voltage_data.min() if len(voltage_data) > 0 else None
                    
                    if has_current and current_col in df_selected.columns:
                        current_data = df_selected[current_col]
                        generator_info['start_current'] = current_data.iloc[0] if len(current_data) > 0 else None
                        generator_info['end_current'] = current_data.iloc[-1] if len(current_data) > 0 else None
                        generator_info['avg_current'] = current_data.mean() if len(current_data) > 0 else None
                        generator_info['max_current'] = current_data.max() if len(current_data) > 0 else None
                        generator_info['min_current'] = current_data.min() if len(current_data) > 0 else None
                    
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
                        generator_info['start_voltage'] = voltage_data.iloc[0] if len(voltage_data) > 0 else None
                        generator_info['end_voltage'] = voltage_data.iloc[-1] if len(voltage_data) > 0 else None
                        generator_info['avg_voltage'] = voltage_data.mean() if len(voltage_data) > 0 else None
                        generator_info['max_voltage'] = voltage_data.max() if len(voltage_data) > 0 else None
                        generator_info['min_voltage'] = voltage_data.min() if len(voltage_data) > 0 else None
                    
                    if has_current and current_col in df_selected.columns:
                        current_data = df_selected[current_col]
                        generator_info['start_current'] = current_data.iloc[0] if len(current_data) > 0 else None
                        generator_info['end_current'] = current_data.iloc[-1] if len(current_data) > 0 else None
                        generator_info['avg_current'] = current_data.mean() if len(current_data) > 0 else None
                        generator_info['max_current'] = current_data.max() if len(current_data) > 0 else None
                        generator_info['min_current'] = current_data.min() if len(current_data) > 0 else None
                    
                    ac_generator_info.append(generator_info)
            
            # 分析汇流条数据
            bus_bar_info = []
            # 收集所有汇流条名称
            bus_names = set()
            for col in bus_voltage_columns + bus_current_columns:
                match = bus_voltage_pattern.search(col) or bus_current_pattern.search(col)
                if match:
                    bus_names.add(match.group(1))
                    
            for bus_name in sorted(bus_names):
                # 查找电压列和电流列
                voltage_col = None
                current_col = None
                
                # 查找电压列
                for col in bus_voltage_columns:
                    if f"{bus_name}汇流条" in col:
                        voltage_col = col
                        break
                        
                # 查找电流列
                for col in bus_current_columns:
                    if f"{bus_name}汇流条" in col:
                        current_col = col
                        break
                
                # 检查是否存在这些列
                has_voltage = voltage_col is not None
                has_current = current_col is not None
                
                if has_voltage or has_current:
                    bus_info = {
                        'bus_name': f"{bus_name}汇流条",
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
                        bus_info['start_voltage'] = voltage_data.iloc[0] if len(voltage_data) > 0 else None
                        bus_info['end_voltage'] = voltage_data.iloc[-1] if len(voltage_data) > 0 else None
                        bus_info['avg_voltage'] = voltage_data.mean() if len(voltage_data) > 0 else None
                        bus_info['max_voltage'] = voltage_data.max() if len(voltage_data) > 0 else None
                        bus_info['min_voltage'] = voltage_data.min() if len(voltage_data) > 0 else None
                    
                    if has_current and current_col in df_selected.columns:
                        current_data = df_selected[current_col]
                        bus_info['start_current'] = current_data.iloc[0] if len(current_data) > 0 else None
                        bus_info['end_current'] = current_data.iloc[-1] if len(current_data) > 0 else None
                        bus_info['avg_current'] = current_data.mean() if len(current_data) > 0 else None
                        bus_info['max_current'] = current_data.max() if len(current_data) > 0 else None
                        bus_info['min_current'] = current_data.min() if len(current_data) > 0 else None
                            
                    bus_bar_info.append(bus_info)
            
            # 填充返回数据
            power_result['has_power_info'] = bool(dc_generator_info or ac_generator_info or bus_bar_info)
            power_result['dc_generators'] = dc_generator_info
            power_result['ac_generators'] = ac_generator_info
            power_result['bus_bars'] = bus_bar_info
            power_result['start_time'] = df_selected['飞行时间'].iloc[0] if not df_selected.empty and '飞行时间' in df_selected.columns else None
            power_result['end_time'] = df_selected['飞行时间'].iloc[-1] if not df_selected.empty and '飞行时间' in df_selected.columns else None
            
            return power_result
        except Exception as e:
            logging.error(f"分析电源系统数据时出错: {str(e)}")
            return {
                'type': 'power',
                'errors': [f"分析电源系统数据时出错: {str(e)}"],
                'has_power_info': False,
                'dc_generators': [],
                'ac_generators': [],
                'bus_bars': [],
                'start_time': None,
                'end_time': None,
                'warnings': []
            }
    
    def generate_text(self, power_data: Dict[str, Any]) -> str:
        """生成电源系统分析结果文本
        
        Args:
            power_data (dict): 电源系统分析数据
            
        Returns:
            str: 格式化的文本结果
        """
        try:
            result = []
            
            # 检查是否有错误信息
            if 'errors' in power_data and power_data['errors']:
                result.extend(power_data['errors'])
                return "\n".join(result)
            
            # 检查是否有电源信息
            if not power_data['has_power_info']:
                result.append("未找到电源系统相关信息")
                return "\n".join(result)
            
            # 添加标题标记
            result.append("[[TITLE]]电源系统分析结果[[/TITLE]]")
            
            # 添加警告信息
            if 'warnings' in power_data and power_data['warnings']:
                for warning in power_data['warnings']:
                    result.append(f"[[AMBER]]警告: {warning}[[/AMBER]]")
            
            # 添加直流发电机电压和电流信息
            if power_data['dc_generators']:
                # 创建表格形式的输出
                result.append("")
                result.append("|-直流发电机|电压平均值(V)|电压最大值(V)|电流平均值(A)|电流最大值(A)|负载状态(≤3200A)-|")
                
                for generator in power_data['dc_generators']:
                    # 电压信息
                    avg_v = f"{generator['avg_voltage']:.2f}" if generator['avg_voltage'] is not None else "N/A"
                    max_v = f"{generator['max_voltage']:.2f}" if generator['max_voltage'] is not None else "N/A"
                    
                    # 电流信息
                    avg_a = f"{generator['avg_current']:.2f}" if generator['avg_current'] is not None else "N/A"
                    max_a = f"{generator['max_current']:.2f}" if generator['max_current'] is not None else "N/A"
                    
                    # 负载状态（基于最大电流是否超限）
                    load_status = "N/A"
                    if generator['max_current'] is not None:
                        if generator['max_current'] > 3200:
                            load_status = "[[RED]]False(超限)[[/RED]]"
                        else:
                            load_status = "True"
                    
                    # 提取编号
                    gen_num = generator['generator_id'].replace("号直流发电机", "")
                    
                    result.append(f"|{gen_num}号|{avg_v}|{max_v}|{avg_a}|{max_a}|{load_status}|")
                result.append("|-|--|--|--|--|--|-|")
            else:
                result.append("未找到直流发电机电压电流数据")
            
            # 添加交流发电机电压和电流信息
            if power_data['ac_generators']:
                result.append("")
                result.append("|-交流发电机|电压平均值(V)|电压最大值(V)|电流平均值(A)|电流最大值(A)|负载状态(≤400A)-|")
                
                for generator in power_data['ac_generators']:
                    # 电压信息
                    avg_v = f"{generator['avg_voltage']:.2f}" if generator['avg_voltage'] is not None else "N/A"
                    max_v = f"{generator['max_voltage']:.2f}" if generator['max_voltage'] is not None else "N/A"
                    
                    # 电流信息
                    avg_a = f"{generator['avg_current']:.2f}" if generator['avg_current'] is not None else "N/A"
                    max_a = f"{generator['max_current']:.2f}" if generator['max_current'] is not None else "N/A"
                    
                    # 负载状态（基于最大电流是否超限）
                    load_status = "N/A"
                    if generator['max_current'] is not None:
                        if generator['max_current'] > 400:
                            load_status = "[[RED]]False(超限)[[/RED]]"
                        else:
                            load_status = "True"
                    
                    # 提取编号
                    gen_num = generator['generator_id'].replace("号交流发电机", "")
                    
                    result.append(f"|{gen_num}号|{avg_v}|{max_v}|{avg_a}|{max_a}|{load_status}|")
                result.append("|-|--|--|--|--|--|-|")
            else:
                result.append("未找到交流发电机电压电流数据")
            
            # 添加汇流条电压和电流信息
            if power_data['bus_bars']:
                result.append("")
                result.append("|-汇流条|电压平均值(V)|电压最大值(V)|电流平均值(A)|电流最大值(A)-|")
                
                for bus in power_data['bus_bars']:
                    # 电压信息
                    avg_v = f"{bus['avg_voltage']:.2f}" if bus['avg_voltage'] is not None else "N/A"
                    max_v = f"{bus['max_voltage']:.2f}" if bus['max_voltage'] is not None else "N/A"
                    
                    # 电流信息
                    avg_a = f"{bus['avg_current']:.2f}" if bus['avg_current'] is not None else "N/A"
                    max_a = f"{bus['max_current']:.2f}" if bus['max_current'] is not None else "N/A"
                    
                    bus_name = bus['bus_name'].replace("汇流条", "")
                    
                    result.append(f"|{bus_name}|{avg_v}|{max_v}|{avg_a}|{max_a}|")
                result.append("|-|--|--|--|--|-|")
            else:
                result.append("未找到汇流条电压电流数据")
            
            return "\n".join(result)
        except Exception as e:
            logging.error(f"生成电源系统分析文本时出错: {str(e)}")
            return f"生成电源系统分析文本时出错: {str(e)}"