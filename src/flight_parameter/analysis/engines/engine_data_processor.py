#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
发动机数据分析核心模块
====================

专门负责发动机数据的分析处理，不涉及文本生成。
"""

import logging
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime

from ..logger import get_analysis_logger, log_step
from ..config import ENGINE_CONFIG
from ..column_config import ENGINE_COLUMNS, GENERAL_COLUMNS

# 获取日志记录器
logger = get_analysis_logger(__name__)


class EngineDataProcessor:
    """发动机数据处理器类
    
    该类专门负责发动机数据的分析处理，严格遵守单一职责原则。
    """
    
    @log_step("发动机数据分析")
    def analyze(self, df, **kwargs) -> Dict[str, Any]:
        """分析发动机数据
        
        Args:
            df (pandas.DataFrame): 飞行数据
            **kwargs: 其他参数，包括可能由其他分析模块传递的参数
            
        Returns:
            dict: 发动机分析结果，包含以下键值：
                - type: 'engine' 字符串
                - has_takeoff_info: 是否有发动机启动信息
                - takeoff_info: 发动机启停信息列表
                - start_time: 数据起始时间
                - end_time: 数据结束时间
                - takeoff_start_time: 发动机首次启动时间
                - takeoff_end_time: 发动机最后关车时间
                - errors: 错误信息列表（如果有的话）
        """
        try:
            logger.info(f"开始分析发动机数据，数据形状: {df.shape if hasattr(df, 'shape') else '未知'}")
            result = {}

            # 检查是否存在必要的列 - 使用配置文件中的模式查找列
            time_columns = [col for col in df.columns if GENERAL_COLUMNS['FLIGHT_TIME'] in col]
            engine_rpm_columns = [col for col in df.columns if '发动机' in col and '转速' in col]
            
            logger.debug(f"找到时间列: {time_columns}")
            logger.debug(f"找到发动机转速列: {engine_rpm_columns}")
            
            if not time_columns:
                logger.warning("缺少时间列")
                result['errors'] = ["缺少时间列"]
                return result
                
            if not engine_rpm_columns:
                logger.warning("缺少发动机转速列")
                result['errors'] = ["缺少发动机转速列"]
                return result

            time_column = time_columns[0]  # 使用第一个找到的时间列
            logger.info(f"使用时间列: {time_column}")

            # 获取时间范围
            result['start_time'] = df[time_column].min()
            result['end_time'] = df[time_column].max()
            logger.info(f"数据时间范围: {result['start_time']} 到 {result['end_time']}")

            # 查找发动机启动和关车时间
            logger.info("开始查找发动机启停信息")
            result['takeoff_info'] = self._find_engine_takeoff_info(df, time_column)
            logger.info(f"找到 {len(result['takeoff_info'])} 个发动机的信息")
            
            # 检查是否有任何发动机启动信息
            result['has_takeoff_info'] = any(len(info['start_times']) > 0 for info in result['takeoff_info'])
            
            # 如果有发动机启动信息，则获取第一次启动和最后一次关车时间
            if result['has_takeoff_info']:
                all_start_times = []
                all_end_times = []
                
                for info in result['takeoff_info']:
                    if info['start_times']:
                        all_start_times.extend(info['start_times'])
                    if info['end_times']:
                        all_end_times.extend(info['end_times'])
                
                if all_start_times:
                    result['takeoff_start_time'] = min(all_start_times)
                if all_end_times:
                    result['takeoff_end_time'] = max(all_end_times)
                
                logger.info(f"发动机启动时间: {result['takeoff_start_time']}")
                logger.info(f"发动机关车时间: {result['takeoff_end_time']}")

            logger.info("完成发动机数据分析")
            return result
        except Exception as e:
            logger.error(f"分析发动机数据时出错: {str(e)}", exc_info=True)
            return {
                'type': 'engine',
                'has_takeoff_info': False,
                'takeoff_info': [],
                'start_time': None,
                'end_time': None,
                'takeoff_start_time': None,
                'takeoff_end_time': None,
                'errors': [f"分析发动机数据时出错: {str(e)}"]
            }
    
    @log_step("查找发动机启停信息")
    def _find_engine_takeoff_info(self, df, time_column) -> List[Dict[str, Any]]:
        """查找发动机启动和关车时间信息
        
        Args:
            df (pandas.DataFrame): 飞行数据
            time_column (str): 时间列名
            
        Returns:
            list: 发动机启动和关车时间信息列表，每个元素包含：
                - engine_id: 发动机编号
                - start_times: 启动时间列表
                - end_times: 关车时间列表
                - restart_times: 重启时间列表
        """
        try:
            logger.info("开始查找发动机启停信息")
            engines_info = []
            
            # 查找所有发动机转速列，使用配置文件中的模式
            import re
            rpm_pattern = re.compile(ENGINE_COLUMNS['RPM'])
            engine_rpm_columns = [col for col in df.columns if rpm_pattern.search(col)]
            
            logger.debug(f"找到发动机转速列: {engine_rpm_columns}")
            
            # 遍历找到的发动机列
            for rpm_column in engine_rpm_columns:
                logger.debug(f"处理发动机列: {rpm_column}")
                # 从列名中提取发动机编号
                match = rpm_pattern.search(rpm_column)
                if match:
                    engine_id = int(match.group(1))
                else:
                    # 如果没有匹配，默认使用1作为发动机编号
                    engine_id = 1
                
                # 获取RPM数据
                rpm_series = df[rpm_column]
                time_series = df[time_column]
                
                logger.debug(f"发动机 {engine_id} RPM数据点数: {len(rpm_series)}")
                
                # 查找发动机启动和关车时间点
                start_times = []
                end_times = []
                restart_times = []
                
                # 判断发动机是否启动的阈值（假设RPM大于阈值表示启动）
                threshold = ENGINE_CONFIG['START_THRESHOLD']
                is_running = False
                
                # 遍历数据查找启动和关车时间点
                for rpm, time in zip(rpm_series, time_series):
                    # 检查是否为有效数值
                    if pd.isna(rpm):
                        continue
                    
                    # 如果发动机之前未启动且当前RPM超过阈值，则认为启动
                    if not is_running and rpm > threshold:
                        start_times.append(time)
                        is_running = True
                        logger.debug(f"发动机 {engine_id} 启动: {time}")
                    # 如果发动机之前已启动且当前RPM低于阈值，则认为关车
                    elif is_running and rpm <= threshold:
                        end_times.append(time)
                        is_running = False
                        logger.debug(f"发动机 {engine_id} 关车: {time}")
                
                # 查找重启时间（在运行过程中短暂停止后再次启动）
                if len(start_times) > 1:
                    logger.debug(f"发动机 {engine_id} 有 {len(start_times)} 次启动，检查重启情况")
                    for k in range(1, len(start_times)):
                        # 如果两次启动之间的时间间隔较短，认为是重启而不是完全关车
                        if (start_times[k] - start_times[k-1]).total_seconds() < ENGINE_CONFIG['RESTART_INTERVAL_THRESHOLD']:  # 5分钟内
                            restart_times.append(start_times[k])
                            logger.debug(f"发动机 {engine_id} 重启: {start_times[k]}")
                
                engines_info.append({
                    'engine_id': engine_id,
                    'start_times': start_times,
                    'end_times': end_times,
                    'restart_times': restart_times
                })
                
                logger.info(f"发动机 {engine_id} 启动次数: {len(start_times)}, 关车次数: {len(end_times)}, 重启次数: {len(restart_times)}")
            
            # 按发动机编号排序
            engines_info.sort(key=lambda x: x['engine_id'])
            
            logger.info(f"完成查找发动机启停信息，共处理 {len(engines_info)} 个发动机")
            return engines_info
        except Exception as e:
            logger.error(f"查找发动机启动信息时出错: {str(e)}", exc_info=True)
            return []