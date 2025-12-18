#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
电源系统报告生成器
================

专门负责将电源系统分析结果转换为文本格式的类。
"""

import logging
from typing import Dict, Any

from ..config import POWER_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class PowerReportGenerator:
    """电源系统报告生成器类
    
    该类专门负责将电源系统分析结果转换为文本格式，严格遵守单一职责原则。
    """
    
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
            if not power_data.get('has_power_info', False):
                result.append("未找到电源系统相关信息")
                return "\n".join(result)
            
            # 添加标题标记 (使用Markdown标题格式)
            result.append("### 电源系统分析结果")
            
            # 添加警告信息
            if 'warnings' in power_data and power_data['warnings']:
                for warning in power_data['warnings']:
                    result.append(f"**警告: {warning}**")
            
            # 添加直流发电机电压和电流信息 (使用Markdown表格格式)
            if power_data.get('dc_generators'):
                # 创建表格形式的输出
                result.append("")
                result.append("| 直流发电机 | 电压平均值(V) | 电压最大值(V) | 电流平均值(A) | 电流最大值(A) | 负载状态(≤3200A) |")
                # 添加列宽定义行，使所有列等宽
                result.append("| :::16.7::: | :::16.7::: | :::16.7::: | :::16.7::: | :::16.7::: | :::16.7::: |")
                
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
                        if generator['max_current'] > POWER_CONFIG['DC_GENERATOR_LOAD_THRESHOLD']:
                            load_status = "**False(超限)**"
                        else:
                            load_status = "True"
                    
                    # 提取编号
                    gen_num = generator['generator_id'].replace("号直流发电机", "")
                    
                    result.append(f"| {gen_num}号 | {avg_v} | {max_v} | {avg_a} | {max_a} | {load_status} |")
            else:
                result.append("未找到直流发电机电压电流数据")
            
            # 添加交流发电机电压和电流信息 (使用Markdown表格格式)
            if power_data.get('ac_generators'):
                result.append("")
                result.append("| 交流发电机 | 电压平均值(V) | 电压最大值(V) | 电流平均值(A) | 电流最大值(A) | 负载状态(≤400A) |")
                # 添加列宽定义行，使所有列等宽
                result.append("| :::16.7::: | :::16.7::: | :::16.7::: | :::16.7::: | :::16.7::: | :::16.7::: |")
                
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
                        if generator['max_current'] > POWER_CONFIG['AC_GENERATOR_LOAD_THRESHOLD']:
                            load_status = "**False(超限)**"
                        else:
                            load_status = "True"
                    
                    # 提取编号
                    gen_num = generator['generator_id'].replace("号交流发电机", "")
                    
                    result.append(f"| {gen_num}号 | {avg_v} | {max_v} | {avg_a} | {max_a} | {load_status} |")
            else:
                result.append("未找到交流发电机电压电流数据")
            
            # 添加汇流条电压和电流信息 (使用Markdown表格格式)
            if power_data.get('bus_bars'):
                result.append("")
                result.append("| 汇流条 | 电压平均值(V) | 电压最大值(V) | 电流平均值(A) | 电流最大值(A) |")
                result.append("| :::16.7::: | :::16.7::: | :::16.7::: | :::16.7::: | :::16.7::: |")
                
                for bus in power_data['bus_bars']:
                    # 电压信息
                    avg_v = f"{bus['avg_voltage']:.2f}" if bus['avg_voltage'] is not None else "N/A"
                    max_v = f"{bus['max_voltage']:.2f}" if bus['max_voltage'] is not None else "N/A"
                    
                    # 电流信息
                    avg_a = f"{bus['avg_current']:.2f}" if bus['avg_current'] is not None else "N/A"
                    max_a = f"{bus['max_current']:.2f}" if bus['max_current'] is not None else "N/A"
                    
                    bus_name = bus.get('bus_id', bus.get('bus_name', '')).replace("汇流条", "")
                    
                    result.append(f"| {bus_name} | {avg_v} | {max_v} | {avg_a} | {max_a} |")
            else:
                result.append("未找到汇流条电压电流数据")
            
            return "\n".join(result)
        except Exception as e:
            logging.error(f"生成电源系统分析文本时出错: {str(e)}")
            return f"生成电源系统分析文本时出错: {str(e)}"