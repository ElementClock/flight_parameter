#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
发动机分析模块
==============

分析飞行数据中的发动机相关信息，包括发动机启动和关车时间、转速变化、点火状态等。

功能特性：
---------
1. 自动识别发动机启动和关车时间点
2. 检测发动机转速变化情况
3. 分析发动机点火状态
4. 识别发动机起飞状态时间段
5. 检测发动机重启事件

使用方法：
--------
>>> analyzer = EngineAnalysis()
>>> result = analyzer.analyze(dataframe)
>>> text_report = analyzer.generate_text(result)

注意事项：
--------
- 输入数据必须包含飞行时间和发动机转速列
- 发动机转速单位为百分比（0-100）
- 发动机启动阈值为10%，关车阈值为10%
"""

import logging
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime

from ..analysis_interface import AnalysisInterface
from ..logger import get_analysis_logger, log_step
from ..config import ENGINE_CONFIG

# 获取日志记录器
logger = get_analysis_logger(__name__)


class EngineAnalysis(AnalysisInterface):
    """发动机分析类
    
    该类提供了完整的发动机数据分析功能，包括数据解析、特征提取和报告生成。
    
    属性：
    ------
    无
    
    方法：
    -----
    analyze(df, **kwargs) -> Dict[str, Any]
        分析发动机数据
    _find_engine_takeoff_info(df, time_column) -> List[Dict[str, Any]]
        查找发动机启动和关车时间信息
    generate_text(engine_data: Dict[str, Any]) -> str
        生成带标识符的发动机分析文本输出
    """
    
    def get_name(self) -> str:
        """获取分析器名称
        
        Returns:
            str: 分析器名称
        """
        return "engine"
    
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

            # 检查是否存在必要的列 - 使用更灵活的方式查找发动机转速列
            time_columns = [col for col in df.columns if '飞行时间' in col]
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
            
            # 查找所有发动机转速列
            engine_rpm_columns = [col for col in df.columns if '发动机' in col and '转速' in col]
            logger.debug(f"找到发动机转速列: {engine_rpm_columns}")
            
            # 遍历找到的发动机列
            for i, rpm_column in enumerate(engine_rpm_columns):
                logger.debug(f"处理发动机列: {rpm_column}")
                # 从列名中提取发动机编号
                # 使用正则表达式更精确地提取发动机编号，参考燃油专业的做法
                import re
                engine_id = None
                
                # 查找类似"发动机1"、"#1"、"1号发动机"这样的模式
                patterns = [
                    r'发动机[#\s]*([1-4])(?!\d)',  # 匹配"发动机1"、"发动机 1"、"发动机#1"，但不匹配"发动机11"
                    r'([1-4])[#\s]*发动机(?!\d)',   # 匹配"1#发动机"、"1 发动机"，但不匹配"11发动机"
                    r'#([1-4])(?!\d)',              # 匹配"#1"，但不匹配"#11"
                    r'(?<![0-9])([1-4])号(?!\d)',   # 匹配"1号"，但不匹配"11号"
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, rpm_column)
                    if match:
                        engine_id = int(match.group(1))
                        logger.debug(f"通过模式 {pattern} 提取到发动机编号: {engine_id}")
                        break
                
                # 如果没有找到明确的编号模式，则使用索引作为备用方案
                if engine_id is None:
                    engine_id = i + 1  # 使用索引作为默认编号，确保不会重复
                    logger.debug(f"未找到明确编号，使用默认编号: {engine_id}")
                
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
            
            # 确保有指定数量的发动机信息（即使某些发动机没有数据）
            # 先收集已存在的发动机ID
            existing_engine_ids = {info['engine_id'] for info in engines_info}
            
            # 补充缺失的发动机信息
            engine_range = ENGINE_CONFIG['ENGINE_NUMBER_RANGE']
            for engine_id in range(engine_range[0], engine_range[1] + 1):
                if engine_id not in existing_engine_ids:
                    engines_info.append({
                        'engine_id': engine_id,
                        'start_times': [],
                        'end_times': [],
                        'restart_times': []
                    })
            
            # 按发动机编号排序
            engines_info.sort(key=lambda x: x['engine_id'])
            
            # 确保发动机编号唯一性，如果有重复则重新分配编号
            seen_ids = set()
            for info in engines_info:
                original_id = info['engine_id']
                if original_id in seen_ids:
                    # 如果编号重复，寻找下一个可用编号
                    new_id = 1
                    while new_id in seen_ids:
                        new_id += 1
                    info['engine_id'] = new_id
                    logger.warning(f"发动机编号重复，将 {original_id} 重分配为 {new_id}")
                seen_ids.add(info['engine_id'])
            
            # 再次按发动机编号排序
            engines_info.sort(key=lambda x: x['engine_id'])
            
            logger.info(f"完成查找发动机启停信息，共处理 {len(engines_info)} 个发动机")
            return engines_info
        except Exception as e:
            logger.error(f"查找发动机启动信息时出错: {str(e)}", exc_info=True)
            return []
    
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