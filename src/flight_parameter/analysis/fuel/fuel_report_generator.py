#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
燃油系统分析报告生成模块
======================

专门负责将燃油系统分析结果转换为文本报告格式。
"""

import logging
from typing import Dict, Any

from ..logger import get_analysis_logger

# 获取日志记录器
logger = get_analysis_logger(__name__)


class FuelReportGenerator:
    """燃油系统报告生成器类
    
    该类专门负责将燃油系统分析结果转换为文本报告，严格遵守单一职责原则。
    """
    
    def generate_text(self, fuel_data: Dict[str, Any]) -> str:
        """生成燃油系统分析的文本报告
        
        Args:
            fuel_data (dict): 燃油系统分析结果数据
            
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
            if not fuel_data.get('has_fuel_info', False):
                result.append("未找到燃油系统相关数据")
                return "\n".join(result)
            
            # 添加标题
            result.append("### 燃油系统分析结果")
            
            # 添加油箱信息
            if fuel_data.get('fuel_tanks'):
                result.append("\n#### 油箱状态信息")
                result.append("| 油箱编号 | 初始油量(kg) | 最终油量(kg) | 消耗油量(kg) |")
                result.append("|----------|--------------|--------------|--------------|")
                
                total_start_fuel = 0
                total_end_fuel = 0
                total_consumption = 0
                
                for tank in fuel_data['fuel_tanks']:
                    start_fuel = tank.get('start_fuel', 0)
                    end_fuel = tank.get('end_fuel', 0)
                    consumption = tank.get('consumption', 0)
                    
                    result.append(f"| {tank.get('tank_name', '未知')} | {start_fuel:.1f} | {end_fuel:.1f} | {consumption:.1f} |")
                    
                    total_start_fuel += start_fuel
                    total_end_fuel += end_fuel
                    total_consumption += consumption
                
                # 添加总计行
                result.append(f"| **总计** | **{total_start_fuel:.1f}** | **{total_end_fuel:.1f}** | **{total_consumption:.1f}** |")
            
            # 添加发动机耗油信息
            if fuel_data.get('engine_fuel_consumptions'):
                result.append("\n#### 发动机耗油信息")
                result.append("| 发动机编号 | 总耗油量(kg) |")
                result.append("|------------|--------------|")
                
                total_engine_consumption = 0
                for engine in fuel_data['engine_fuel_consumptions']:
                    consumption = engine.get('total_consumption', 0)
                    result.append(f"| {engine.get('engine_name', '未知')} | {consumption:.1f} |")
                    total_engine_consumption += consumption
                
                result.append(f"| **总计** | **{total_engine_consumption:.1f}** |")
                result.append(f"\n燃油系统总消耗: {fuel_data.get('total_fuel_consumption', 0):.1f} kg")
            
            # 添加低油量告警
            if fuel_data.get('low_fuel_events'):
                result.append("\n#### 低油量告警")
                result.append("| 油箱编号 | 开始时间 | 结束时间 | 最低油量(kg) |")
                result.append("|----------|----------|----------|--------------|")
                
                for event in fuel_data['low_fuel_events']:
                    start_time = event.get('start_time', '').strftime('%H:%M:%S') if event.get('start_time') else ''
                    end_time = event.get('end_time', '').strftime('%H:%M:%S') if event.get('end_time') else ''
                    min_fuel = event.get('min_fuel', 0)
                    result.append(f"| {event.get('tank_name', '未知')} | {start_time} | {end_time} | {min_fuel:.1f} |")
            
            # 添加油箱不平衡告警
            if fuel_data.get('imbalance_fuel_events'):
                result.append("\n#### 油箱不平衡告警")
                result.append("| 油箱对比 | 开始时间 | 结束时间 | 最大差异(kg) |")
                result.append("|----------|----------|----------|--------------|")
                
                for event in fuel_data['imbalance_fuel_events']:
                    start_time = event.get('start_time', '').strftime('%H:%M:%S') if event.get('start_time') else ''
                    end_time = event.get('end_time', '').strftime('%H:%M:%S') if event.get('end_time') else ''
                    max_diff = event.get('max_difference', 0)
                    tank1 = event.get('tank1_name', '未知1')
                    tank2 = event.get('tank2_name', '未知2')
                    result.append(f"| {tank1} vs {tank2} | {start_time} | {end_time} | {max_diff:.1f} |")
            
            # 添加警告信息
            if fuel_data.get('warnings'):
                result.append("\n#### 警告信息")
                for warning in fuel_data['warnings']:
                    result.append(f"- {warning}")
            
            return "\n".join(result)
        except Exception as e:
            logger.error(f"生成燃油系统分析文本时出错: {str(e)}")
            return f"生成燃油系统分析文本时出错: {str(e)}"