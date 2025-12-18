#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CAS分析报告生成模块
=================

专门负责将CAS分析结果转换为文本报告格式。
"""

import logging
import os
from typing import Dict, Any

import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class CasReportGenerator:
    """CAS报告生成器类
    
    该类专门负责将CAS分析结果转换为文本报告，严格遵守单一职责原则。
    """
    
    def generate_text(self, cas_data: Dict[str, Any]) -> str:
        """生成带标识符的CAS分析文本输出
        
        Args:
            cas_data (dict): CAS分析数据
            
        Returns:
            str: 格式化的文本结果
        """
        try:
            result = []
            
            # 检查错误情况
            if cas_data['is_empty']:
                result.append("输入的 DataFrame 为空，请检查数据源")
                return "\n".join(result)
            if cas_data['missing_time_column']:
                result.append("缺少 '飞行时间' 列，请检查数据源")
                return "\n".join(result)
            if cas_data['no_alarm_columns']:
                result.append("没有找到告警相关的列，请检查数据源")
                return "\n".join(result)
            if 'errors' in cas_data:
                result.append("CAS分析过程中出错:")
                result.extend(cas_data['errors'])
                return "\n".join(result)

            # 检查告警数据
            if not cas_data['alarms']:
                result.append("没有发现告警")
                return "\n".join(result)

            # 添加标题标记 (使用Markdown标题格式)
            result.append("### CAS告警分析结果")

            # 读取告警等级信息
            alarm_levels = self.load_alarm_levels()
            
            # 按告警级别分组
            grouped_alarms = self.group_alarms_by_level(cas_data['alarms'], alarm_levels)
            
            # 创建一个包含所有告警的列表，并添加告警级别信息
            all_alarms_with_levels = []
            
            # 按级别顺序处理告警
            level_order = ['警告级', '戒备级', '提示级', '状态级', '未知级别']
            for level in level_order:
                if level in grouped_alarms and grouped_alarms[level]:
                    for alarm in grouped_alarms[level]:
                        alarm_copy = alarm.copy()
                        alarm_copy['level'] = level
                        all_alarms_with_levels.append(alarm_copy)
            
            # 如果有告警，则显示在一个表格中
            if all_alarms_with_levels:
                # 添加表格标记 (使用Markdown表格格式)
                result.append("| 告警名称 | 时间 | 持续时间 | 告警级别 |")
                # 添加列宽定义行，设置告警名称:时间:持续时间:告警级别 = 4:3:2:1的比例
                result.append("| :::40::: | :::30::: | :::20::: | :::10::: |")
                result.append("|----------|------|----------|----------|")
                
                # 遍历所有告警数据
                for alarm in all_alarms_with_levels:
                    # 提取当前行的告警信息
                    alarm_name = alarm['name']
                    start_time = alarm['start_time']
                    end_time = alarm['end_time']
                    duration = alarm['duration']
                    level = alarm['level']
                    
                    # 根据告警级别设置颜色（使用内联样式，因为CSS类在wx.html.HtmlWindow中可能不生效）
                    if level == '警告级':
                        level_html = '警告级'  # 现在在UI组件中处理颜色
                    elif level == '戒备级':
                        level_html = '戒备级'
                    elif level == '提示级':
                        level_html = '提示级'
                    else:
                        level_html = level
                    
                    # 添加表格行
                    time_range = f"{start_time}-{end_time}"
                    result.append(f"| {alarm_name} | {time_range} | {duration} | {level_html} |")

            return "\n".join(result)
        except Exception as e:
            logging.error(f"格式化CAS输出时出错: {str(e)}")
            return f"格式化CAS输出时出错: {str(e)}"
    
    def load_alarm_levels(self):
        """加载告警级别信息
        
        Returns:
            dict: 告警ID到告警级别的映射字典
        """
        try:
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cas_level_path = os.path.join(project_root, 'cas', 'cas_level.csv')
            
            # 读取CSV文件
            df = pd.read_csv(cas_level_path, header=0)
            
            # 提取C列(编号)和G列(告警等级)
            # 注意：pandas默认0索引，C列是第2列(索引为2)，G列是第6列(索引为6)
            alarm_levels = {}
            # 使用向量化操作替代iterrows
            for idx in range(len(df)):
                # 忽略大小写进行匹配
                alarm_id = str(df.iloc[idx, 2]).strip().lower() if pd.notna(df.iloc[idx, 2]) else None
                alarm_level = df.iloc[idx, 6] if pd.notna(df.iloc[idx, 6]) else None
                
                if alarm_id and alarm_level:
                    alarm_levels[alarm_id] = alarm_level
                    
            return alarm_levels
        except FileNotFoundError:
            logging.error(f"告警级别文件未找到: {cas_level_path}")
            return {}
        except Exception as e:
            logging.error(f"加载告警级别信息时出错: {e}")
            return {}

    def group_alarms_by_level(self, alarms, alarm_levels):
        """根据告警级别对告警进行分组
        
        Args:
            alarms (list): 告警列表
            alarm_levels (dict): 告警ID到告警级别的映射字典
            
        Returns:
            dict: 按告警级别分组的告警字典
        """
        try:
            grouped = {
                '警告级': [],
                '戒备级': [],
                '提示级': [],
                '状态级': [],
                '未知级别': []
            }
            
            # 遍历所有告警级别定义
            for alarm_id, level in alarm_levels.items():
                # 对于每个告警级别，检查所有告警项
                for alarm in alarms:
                    alarm_name = alarm['name']
                    # 如果alarm_levels中的ID在告警名称中，则将该告警归类到对应级别
                    if alarm_id.lower() in alarm_name.lower():
                        grouped[level].append(alarm)
            
            # 将未匹配到级别的告警归类到'未知级别'
            # 先找出已匹配的告警
            matched_alarms = []
            for level_alarms in grouped.values():
                matched_alarms.extend(level_alarms)
            
            # 将未匹配的告警添加到'未知级别'
            for alarm in alarms:
                if alarm not in matched_alarms:
                    grouped['未知级别'].append(alarm)
            
            return grouped
        except Exception as e:
            logging.error(f"告警分组时出错: {str(e)}")
            return {}