#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
发动机分析报告生成模块
====================

专门负责将发动机分析结果转换为文本报告格式。
"""

import logging
from typing import Dict, Any

from ..logger import get_analysis_logger

# 获取日志记录器
logger = get_analysis_logger(__name__)


class EngineReportGenerator:
    """发动机报告生成器类
    
    该类专门负责将发动机分析结果转换为文本报告，严格遵守单一职责原则。
    """
    
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
                # 添加标题标记 (使用Markdown标题格式)
                result.append("### 动力分析结果")
                
                if engine_data.get('takeoff_start_time') and engine_data.get('takeoff_end_time'):
                    gap_time = engine_data['takeoff_end_time'] - engine_data['takeoff_start_time']
                    result.append(f"开关车时间为：{engine_data['takeoff_start_time']}-{engine_data['takeoff_end_time']}，耗时：{gap_time}")
                
                # 添加发动机启动信息表格 (使用Markdown表格格式)
                result.append("| 发动机编号 | 首次开车时间 | 关车时间 | 重启次数 | 重启时间点 |")
                result.append("|------------|--------------|----------|----------|------------|")
                for info in engine_data['takeoff_info']:
                    if info['start_times']:
                        # 获取首次开车时间
                        start_time = info['start_times'][0]
                        
                        # 获取最后一次关车时间（如果有）
                        end_time = "无"
                        if info['end_times']:
                            end_time = info['end_times'][-1]
                        
                        # 获取重启信息
                        restart_count = len(info.get('restart_times', []))
                        restart_times_str = "无"
                        if info.get('restart_times'):
                            restart_times_str = ", ".join([str(t) for t in info['restart_times']])
                        
                        # 添加表格行
                        result.append(f"| {info['engine_id']} | {start_time} | {end_time} | {restart_count} | {restart_times_str} |")
            # 新增逻辑：当所有发动机都未启动时，说明分析时间范围并提示无开车记录
            else:
                if engine_data.get('start_time') and engine_data.get('end_time'):
                    result.append(f"本文件时间为： {engine_data['start_time']} 到 {engine_data['end_time']}")
                    result.append("本次数据分析：飞机未启动发动机，请检查数据")
            
            return "\n".join(result)
        except Exception as e:
            logger.error(f"生成发动机分析文本时出错: {str(e)}")
            return f"生成发动机分析文本时出错: {str(e)}"