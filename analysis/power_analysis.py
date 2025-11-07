#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
电源系统分析模块
===============

分析电源系统数据，包括直流发电机、交流发电机和汇流条等关键参数。
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


def analyze_power(df):
    """
    分析电源系统数据
    
    Args:
        df (pandas.DataFrame): 包含电源系统数据的DataFrame
        
    Returns:
        dict: 电源系统分析结果
    """
    try:
        # 初始化返回数据
        power_result = {
            'type': 'power',
            'has_power_info': False,
            'dc_generators': [],  # 1-8号直流发电机
            'ac_generators': [],  # 1-4号交流发电机
            'bus_bars': [],       # 汇流条信息
            'start_time': None,
            'end_time': None,
            'warnings': [],
            'errors': []
        }
        
        # 查找电源相关列
        # 根据用户提供的信息，匹配直流发电机列，如"1号直流发电机电压"、"2号直流发电机电流"等
        dc_voltage_pattern = re.compile(r'(\d)号直流发电机(?:输出)?电压')
        dc_current_pattern = re.compile(r'(\d)号直流发电机(?:输出)?电流')
        dc_power_pattern = re.compile(r'(\d)号直流发电机(?:输出)?功率')
        
        # 根据用户提供的信息，匹配交流发电机列，如"1号交流发电机电压"、"2号交流发电机电流"等
        ac_voltage_pattern = re.compile(r'(\d)号交流发电机(?:输出)?电压')
        ac_current_pattern = re.compile(r'(\d)号交流发电机(?:输出)?电流')
        ac_power_pattern = re.compile(r'(\d)号交流发电机(?:输出)?功率')
        
        # 匹配汇流条列，如"左汇流条电压"、"右汇流条电流"等
        bus_voltage_pattern = re.compile(r'(.+?)汇流条电压')
        bus_current_pattern = re.compile(r'(.+?)汇流条电流')
        
        # 提取相关列
        dc_voltage_columns = [col for col in df.columns if dc_voltage_pattern.search(col)]
        dc_current_columns = [col for col in df.columns if dc_current_pattern.search(col)]
        dc_power_columns = [col for col in df.columns if dc_power_pattern.search(col)]
        
        ac_voltage_columns = [col for col in df.columns if ac_voltage_pattern.search(col)]
        ac_current_columns = [col for col in df.columns if ac_current_pattern.search(col)]
        ac_power_columns = [col for col in df.columns if ac_power_pattern.search(col)]
        
        bus_voltage_columns = [col for col in df.columns if bus_voltage_pattern.search(col)]
        bus_current_columns = [col for col in df.columns if bus_current_pattern.search(col)]
        
        # 调试信息 - 打印找到的列
        logging.info(f"找到的直流发电机电压列: {dc_voltage_columns}")
        logging.info(f"找到的直流发电机电流列: {dc_current_columns}")
        logging.info(f"找到的直流发电机功率列: {dc_power_columns}")
        logging.info(f"找到的交流发电机电压列: {ac_voltage_columns}")
        logging.info(f"找到的交流发电机电流列: {ac_current_columns}")
        logging.info(f"找到的交流发电机功率列: {ac_power_columns}")
        logging.info(f"找到的汇流条电压列: {bus_voltage_columns}")
        logging.info(f"找到的汇流条电流列: {bus_current_columns}")
        
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
        if dc_power_columns:
            selected_columns.extend(dc_power_columns)
        if ac_voltage_columns:
            selected_columns.extend(ac_voltage_columns)
        if ac_current_columns:
            selected_columns.extend(ac_current_columns)
        if ac_power_columns:
            selected_columns.extend(ac_power_columns)
        if bus_voltage_columns:
            selected_columns.extend(bus_voltage_columns)
        if bus_current_columns:
            selected_columns.extend(bus_current_columns)
            
        df_selected = df[selected_columns].copy()
        
        # 调试信息 - 打印df_selected的列名
        logging.info(f"df_selected的列名: {list(df_selected.columns)}")
        
        # 分析直流发电机数据
        dc_generator_info = []
        # 首先收集所有直流发电机编号
        dc_gen_numbers = set()
        for col in dc_voltage_columns + dc_current_columns + dc_power_columns:
            match = dc_voltage_pattern.search(col) or dc_current_pattern.search(col) or dc_power_pattern.search(col)
            if match:
                dc_gen_numbers.add(int(match.group(1)))
        
        logging.info(f"找到的直流发电机编号: {sorted(dc_gen_numbers)}")
        
        for i in sorted(dc_gen_numbers):  # 使用实际找到的发电机编号
            # 构造可能的列名并查找实际存在的列
            voltage_col = None
            current_col = None
            power_col = None
            
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
                    
            # 查找功率列
            for col in dc_power_columns:
                if f"{i}号直流发电机" in col:
                    power_col = col
                    break
            
            # 检查是否存在这些列
            has_voltage = voltage_col is not None
            has_current = current_col is not None
            has_power = power_col is not None
            
            logging.info(f"发电机 {i}: 电压列={voltage_col}, 电流列={current_col}, 功率列={power_col}")
            
            if has_voltage or has_current or has_power:
                generator_info = {
                    'generator_id': f"{i}号直流发电机",
                    'voltage_data': df_selected[voltage_col] if has_voltage else None,
                    'current_data': df_selected[current_col] if has_current else None,
                    'power_data': df_selected[power_col] if has_power else None,
                    'start_voltage': None,
                    'end_voltage': None,
                    'avg_voltage': None,
                    'max_voltage': None,
                    'min_voltage': None,
                    'start_current': None,
                    'end_current': None,
                    'avg_current': None,
                    'max_current': None,
                    'min_current': None,
                    'start_power': None,
                    'end_power': None,
                    'avg_power': None,
                    'max_power': None,
                    'min_power': None
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
                    
                if has_power and power_col in df_selected.columns:
                    power_data = df_selected[power_col]
                    generator_info['start_power'] = power_data.iloc[0] if len(power_data) > 0 else None
                    generator_info['end_power'] = power_data.iloc[-1] if len(power_data) > 0 else None
                    generator_info['avg_power'] = power_data.mean() if len(power_data) > 0 else None
                    generator_info['max_power'] = power_data.max() if len(power_data) > 0 else None
                    generator_info['min_power'] = power_data.min() if len(power_data) > 0 else None
                
                dc_generator_info.append(generator_info)
        
        # 分析交流发电机数据
        ac_generator_info = []
        # 首先收集所有交流发电机编号
        ac_gen_numbers = set()
        for col in ac_voltage_columns + ac_current_columns + ac_power_columns:
            match = ac_voltage_pattern.search(col) or ac_current_pattern.search(col) or ac_power_pattern.search(col)
            if match:
                ac_gen_numbers.add(int(match.group(1)))
                
        logging.info(f"找到的交流发电机编号: {sorted(ac_gen_numbers)}")
        
        for i in sorted(ac_gen_numbers):  # 使用实际找到的发电机编号
            # 构造可能的列名并查找实际存在的列
            voltage_col = None
            current_col = None
            power_col = None
            
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
                    
            # 查找功率列
            for col in ac_power_columns:
                if f"{i}号交流发电机" in col:
                    power_col = col
                    break
            
            # 检查是否存在这些列
            has_voltage = voltage_col is not None
            has_current = current_col is not None
            has_power = power_col is not None
            
            logging.info(f"发电机 {i}: 电压列={voltage_col}, 电流列={current_col}, 功率列={power_col}")
            
            if has_voltage or has_current or has_power:
                generator_info = {
                    'generator_id': f"{i}号交流发电机",
                    'voltage_data': df_selected[voltage_col] if has_voltage else None,
                    'current_data': df_selected[current_col] if has_current else None,
                    'power_data': df_selected[power_col] if has_power else None,
                    'start_voltage': None,
                    'end_voltage': None,
                    'avg_voltage': None,
                    'max_voltage': None,
                    'min_voltage': None,
                    'start_current': None,
                    'end_current': None,
                    'avg_current': None,
                    'max_current': None,
                    'min_current': None,
                    'start_power': None,
                    'end_power': None,
                    'avg_power': None,
                    'max_power': None,
                    'min_power': None
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
                    # 添加调试信息，检查电流数据的一些统计信息
                    logging.info(f"发电机 {i} 电流数据统计: 长度={len(current_data)}, 非空值数量={current_data.count()}, 平均值={current_data.mean() if len(current_data) > 0 else 'N/A'}")
                    logging.info(f"发电机 {i} 电流数据前5个值: {current_data.head() if len(current_data) > 0 else 'N/A'}")
                    
                    generator_info['start_current'] = current_data.iloc[0] if len(current_data) > 0 else None
                    generator_info['end_current'] = current_data.iloc[-1] if len(current_data) > 0 else None
                    generator_info['avg_current'] = current_data.mean() if len(current_data) > 0 else None
                    generator_info['max_current'] = current_data.max() if len(current_data) > 0 else None
                    generator_info['min_current'] = current_data.min() if len(current_data) > 0 else None
                    
                if has_power and power_col in df_selected.columns:
                    power_data = df_selected[power_col]
                    generator_info['start_power'] = power_data.iloc[0] if len(power_data) > 0 else None
                    generator_info['end_power'] = power_data.iloc[-1] if len(power_data) > 0 else None
                    generator_info['avg_power'] = power_data.mean() if len(power_data) > 0 else None
                    generator_info['max_power'] = power_data.max() if len(power_data) > 0 else None
                    generator_info['min_power'] = power_data.min() if len(power_data) > 0 else None
                
                ac_generator_info.append(generator_info)
        
        # 分析汇流条数据
        bus_bar_info = []
        # 收集所有汇流条名称
        bus_names = set()
        for col in bus_voltage_columns + bus_current_columns:
            match = bus_voltage_pattern.search(col) or bus_current_pattern.search(col)
            if match:
                bus_names.add(match.group(1))
                
        logging.info(f"找到的汇流条名称: {sorted(bus_names)}")
        
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
            
            logging.info(f"汇流条 {bus_name}: 电压列={voltage_col}, 电流列={current_col}")
            
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
        
        # 调试信息
        logging.info(f"找到 {len(dc_generator_info)} 个直流发电机")
        logging.info(f"找到 {len(ac_generator_info)} 个交流发电机")
        logging.info(f"找到 {len(bus_bar_info)} 个汇流条")
        
        # 清理临时数据以释放内存
        del df_selected
        
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


def generate_power_text_with_markers(power_data):
    """生成带标识符的电源系统分析文本输出
    
    Args:
        power_data (dict): 包含电源系统分析结果的字典，可能包含错误信息
        
    Returns:
        str: 格式化的文本结果，包含错误信息或正常分析结果
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
        
        # 使用标识符标记标题行
        title = "[[BOLD]]电源系统分析结果[[/BOLD]]"
        formatted_title = title.center(100, '-')
        result.append(formatted_title)
        
        # 添加警告信息
        if 'warnings' in power_data and power_data['warnings']:
            for warning in power_data['warnings']:
                result.append(f"[[AMBER]]警告: {warning}[[/AMBER]]")
        
        # 添加直流发电机信息
        if power_data['dc_generators']:
            # 创建表格形式的输出
            result.append(" 直流发电机信息:")
            result.append("  编号    电压平均值(V)   电压最大值(V)   电流平均值(A)   电流最大值(A)   负载状态(≤3200A)")
            result.append("  ----------------------------------------------------------------------------")
            
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
                
                result.append(f"  {gen_num:>2}号    {avg_v:>10}      {max_v:>10}      {avg_a:>10}      {max_a:>10}        {load_status:>8}")
        else:
            result.append(" 未找到直流发电机数据 ")
        
        # 添加交流发电机信息
        if power_data['ac_generators']:
            result.append("")
            result.append(" 交流发电机信息:")
            result.append("  编号    电压平均值(V)   电压最大值(V)   电流平均值(A)   电流最大值(A)   负载状态(≤400A)")
            result.append("  ----------------------------------------------------------------------------")
            
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
                
                result.append(f"  {gen_num:>2}号    {avg_v:>10}      {max_v:>10}      {avg_a:>10}      {max_a:>10}        {load_status:>8}")
        else:
            result.append(" 未找到交流发电机数据 ")
        
        # 添加汇流条信息
        if power_data['bus_bars']:
            result.append("")
            result.append(" 汇流条信息:")
            result.append("  名称                  电压平均值(V)   电压最大值(V)   电流平均值(A)   电流最大值(A)")
            result.append("  ----------------------------------------------------------------------")
            
            for bus in power_data['bus_bars']:
                # 电压信息
                avg_v = f"{bus['avg_voltage']:.2f}" if bus['avg_voltage'] is not None else "N/A"
                max_v = f"{bus['max_voltage']:.2f}" if bus['max_voltage'] is not None else "N/A"
                
                # 电流信息
                avg_a = f"{bus['avg_current']:.2f}" if bus['avg_current'] is not None else "N/A"
                max_a = f"{bus['max_current']:.2f}" if bus['max_current'] is not None else "N/A"
                
                bus_name = bus['bus_name'].replace("汇流条", "")
                
                result.append(f"  {bus_name:<18}  {avg_v:>10}      {max_v:>10}      {avg_a:>10}      {max_a:>10}")
        else:
            result.append(" 未找到汇流条数据 ")
        
        return "\n".join(result)
    except Exception as e:
        logging.error(f"生成电源系统分析文本时出错: {str(e)}")
        return f"生成电源系统分析文本时出错: {str(e)}"
