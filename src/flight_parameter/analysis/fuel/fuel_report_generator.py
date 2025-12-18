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
            
            # 合并显示油箱和发动机信息在一个表格中（列合并）
            if fuel_data.get('fuel_tanks') or fuel_data.get('engine_fuel_consumptions'):
                result.append(f"\n燃油系统总消耗: {fuel_data.get('total_fuel_consumption', 0):.1f} kg")
                result.append("| 油箱编号 | 初始油量(kg) | 最终油量(kg) | 消耗油量(kg) | 对应发动机编号 | 发动机总耗油量(kg) |")
                result.append("|----------|--------------|--------------|--------------|----------------|------------------|")
                
                # 获取油箱和发动机数据
                tanks = fuel_data.get('fuel_tanks', [])
                engines = fuel_data.get('engine_fuel_consumptions', [])
                
                # 确定需要显示的行数（油箱和发动机数量的最大值）
                max_rows = max(len(tanks), len(engines))
                
                # 逐行合并显示油箱和发动机信息
                total_start_fuel = 0
                total_end_fuel = 0
                total_tank_consumption = 0
                total_engine_consumption = 0
                
                for i in range(max_rows):
                    # 油箱信息
                    tank_info = ""
                    start_fuel = ""
                    end_fuel = ""
                    tank_consumption = ""
                    
                    if i < len(tanks):
                        tank = tanks[i]
                        tank_info = tank.get('tank_name', '未知')
                        start_fuel = f"{tank.get('start_fuel', 0):.1f}"
                        end_fuel = f"{tank.get('end_fuel', 0):.1f}"
                        tank_consumption = f"{tank.get('consumption', 0):.1f}"
                        
                        total_start_fuel += tank.get('start_fuel', 0)
                        total_end_fuel += tank.get('end_fuel', 0)
                        total_tank_consumption += tank.get('consumption', 0)
                    
                    # 发动机信息
                    engine_info = ""
                    engine_consumption = ""
                    
                    if i < len(engines):
                        engine = engines[i]
                        engine_info = engine.get('engine_name', '未知')
                        engine_consumption = f"{engine.get('total_consumption', 0):.1f}"
                        
                        total_engine_consumption += engine.get('total_consumption', 0)
                    
                    # 输出合并后的行
                    result.append(f"| {tank_info} | {start_fuel} | {end_fuel} | {tank_consumption} | {engine_info} | {engine_consumption} |")
                
                # 添加总计行
                result.append(f"| **总计** | **{total_start_fuel:.1f}** | **{total_end_fuel:.1f}** | **{total_tank_consumption:.1f}** | **-** | **{total_engine_consumption:.1f}** |")

            
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