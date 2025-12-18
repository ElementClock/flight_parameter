#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据分析主模块
==============

飞行数据主分析流程，协调各个子分析模块完成完整的数据分析任务。
"""

import logging
import os
from datetime import timedelta
from typing import Callable, Optional

import pandas as pd

# 项目模块导入
from analysis.analysis_interface import AnalysisResult
from analysis.plugin_manager import PluginManager, PluginConfig
from analysis.engines.engine_analysis import EngineAnalysis
from analysis.fuel.fuel_analysis import FuelAnalysis
from analysis.power.power_analysis import PowerAnalysis
from analysis.cas.cas_analysis import CasAnalysis

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class DataAnalyzer:
    """数据分析师类，用于协调各种分析模块"""
    
    def __init__(self):
        """初始化数据分析师"""
        # 创建插件管理器
        self.plugin_manager = PluginManager()
        
        # 注册插件及配置
        engine_config = PluginConfig("engine", priority=40)
        fuel_config = PluginConfig("fuel", priority=30)
        power_config = PluginConfig("power", priority=20)
        cas_config = PluginConfig("cas", priority=10, dependencies=["engine"])
        
        self.plugin_manager.register_plugin("engine", EngineAnalysis(), engine_config)
        self.plugin_manager.register_plugin("fuel", FuelAnalysis(), fuel_config)
        self.plugin_manager.register_plugin("power", PowerAnalysis(), power_config)
        self.plugin_manager.register_plugin("cas", CasAnalysis(), cas_config)
    
    def analyze(self, df, progress_callback: Optional[Callable] = None):
        """分析飞行数据主函数
        
        Args:
            df (pandas.DataFrame): 飞行数据
            progress_callback (callable): 进度更新回调函数
            
        Returns:
            AnalysisResult: 包含分析结果的对象
        """
        try:
            if progress_callback:
                progress_callback(10, "正在转换飞行时间...")
            df = self.convert_flight_time(df)
            
            if progress_callback:
                progress_callback(30, "正在转换列名...")
            df = self.convert_flight_name(df)
            
            # 使用插件管理器执行所有分析
            if progress_callback:
                progress_callback(50, "正在分析数据...")
            analysis_results = self.plugin_manager.execute_analysis(df)
            
            # 生成带标识符的文本输出
            if progress_callback:
                progress_callback(90, "正在生成分析报告...")
            reports = self.plugin_manager.generate_reports(analysis_results)
            
            # 将所有结果封装到AnalysisResult对象中
            result = AnalysisResult(
                text_engine=reports.get('engine', ''),
                text_fuel=reports.get('fuel', ''),
                text_power=reports.get('power', ''),
                text_cas=reports.get('cas', ''),
                engine_start_time=analysis_results.get('engine', {}).get('takeoff_start_time'),
                engine_end_time=analysis_results.get('engine', {}).get('takeoff_end_time'),
                df=df,
                engine_data=analysis_results.get('engine', {}),
                fuel_data=analysis_results.get('fuel', {}),
                power_data=analysis_results.get('power', {}),
                cas_data=analysis_results.get('cas', {})
            )
            
            if progress_callback:
                progress_callback(100, "分析完成")
                
            return result
        except Exception as e:
            logging.error(f"分析飞行数据时出错: {str(e)}")
            # 返回一个包含错误信息的AnalysisResult对象
            return AnalysisResult(
                errors=[f"分析飞行数据时出错: {str(e)}"]
            )
    
    def convert_flight_time(self, df):
        """
        将飞参数据中的时间列转换为标准的北京时间格式
        
        修改说明：
        - 获取第4、5、6列数据
        - 第4列为日期数据（格式：2025/10/13 或 25-10-13）
        - 第5列为标识符数据（1为可信，0为不可信）
        - 第6列为时间数据（格式：1:01:55）
        - 只保留标识符为1的可信数据
        - 合并日期和时间数据转换为datetime对象
        - 将飞行时间列移动到第一列
        
        参数:
            df (pandas.DataFrame): 包含飞参数据的DataFrame
            
        返回:
            pandas.DataFrame: 时间列已转换并移动到第一列的DataFrame
        """
        try:
            # 获取第4、5、6列的列名
            date_column, flag_column, time_column = self._get_time_column_names(df)
            
            # 过滤标识符为1的可信数据
            df_filtered = self._filter_reliable_data(df, flag_column)
            
            if df_filtered.empty:
                logging.warning("过滤后没有可信数据")
                return df
                
            # 解析日期列
            parsed_dates = self._parse_date_column(df_filtered, date_column)
            
            # 将日期和时间数据合并为完整的日期时间字符串
            # 格式: 2025/10/13 1:01:55
            datetime_combined = parsed_dates.astype(str) + ' ' + df_filtered[time_column].astype(str)
            
            # 转换为datetime对象，支持标准日期时间格式
            df_filtered['_datetime'] = pd.to_datetime(datetime_combined, errors='coerce')
            
            # 将时间转换为北京时间(UTC+8)
            df_filtered['_datetime'] = df_filtered['_datetime'] + timedelta(hours=8)
            
            # 更新原数据列
            df_filtered[date_column] = df_filtered['_datetime']
            
            # 删除临时列和不再需要的标识符、时间列
            df_filtered.rename(columns={date_column: '飞行时间'}, inplace=True)
            if '_datetime' in df_filtered.columns:
                df_filtered.drop(['_datetime'], axis=1, inplace=True)
            if flag_column in df_filtered.columns:
                df_filtered.drop([flag_column], axis=1, inplace=True)
            if time_column in df_filtered.columns and time_column != '飞行时间':
                df_filtered.drop([time_column], axis=1, inplace=True)
            
            # 将"飞行时间"列移动到第一列
            if '飞行时间' in df_filtered.columns:
                flight_time_col = df_filtered.pop('飞行时间')
                # 使用pd.concat替代insert以避免DataFrame碎片化警告
                df_filtered = pd.concat([flight_time_col, df_filtered], axis=1)
            
            return df_filtered
        except Exception as e:
            logging.error(f"转换飞行时间时出错: {e}")
            return df
    
    def _get_time_column_names(self, df):
        """获取时间相关列的列名
        
        Args:
            df (pandas.DataFrame): 包含飞参数据的DataFrame
            
        Returns:
            tuple: (date_col, flag_col, time_col) 日期列、标识符列和时间列的列名
        """
        if len(df.columns) < 6:
            # 如果列数不足，尝试查找时间相关的列
            time_columns = [col for col in df.columns if '时间' in col or '日期' in col]
            if len(time_columns) >= 3:
                date_column = time_columns[0]
                flag_column = time_columns[1] 
                time_column = time_columns[2]
            else:
                # 如果找不到足够的时间列，直接返回原始数据
                # 抛出异常或返回默认值
                raise ValueError("无法找到足够的时间相关列")
        else:
            date_column = df.columns[3]    # 第4列：日期数据
            flag_column = df.columns[4]    # 第5列：标识符数据
            time_column = df.columns[5]    # 第6列：时间数据
            
        return date_column, flag_column, time_column
    
    def _filter_reliable_data(self, df, flag_column):
        """过滤标识符为1的可信数据
        
        Args:
            df (pandas.DataFrame): 原始数据
            flag_column (str): 标识符列名
            
        Returns:
            pandas.DataFrame: 过滤后的数据
        """
        if flag_column in df.columns:
            return df[df[flag_column] == 1].copy()
        else:
            return df.copy()
    
    def _parse_date_column(self, df_filtered, date_column):
        """解析日期列
        
        Args:
            df_filtered (pandas.DataFrame): 过滤后的数据
            date_column (str): 日期列名
            
        Returns:
            pandas.Series: 解析后的日期数据
        """
        sample_date = str(df_filtered[date_column].iloc[0]) if not df_filtered.empty else ""
        parsed_dates = None
        
        # 根据字符长度判断日期格式
        # 通过检查样本日期的长度来推测日期格式类型
        if len(sample_date) >= 10:  # "2025/10/13" 格式，长度至少为10
            # 尝试使用 %Y/%m/%d 格式解析（年份为四位数）
            try:
                parsed_dates = pd.to_datetime(df_filtered[date_column], format='%Y/%m/%d', errors='coerce')
                # 检查是否成功解析了大部分数据
                # 如果超过一半无法解析，则认为此格式不匹配，重置为None继续尝试其他格式
                if parsed_dates.isna().sum() / len(parsed_dates) > 0.5:  # 如果超过一半无法解析
                    parsed_dates = None  # 重置，尝试其他格式
            except Exception:
                parsed_dates = None
                
        elif len(sample_date) >= 8 and len(sample_date) < 10:  # "25-10-13" 格式，长度通常为8
            # 尝试使用 %y-%m-%d 格式解析（年份为两位数）
            try:
                parsed_dates = pd.to_datetime(df_filtered[date_column], format='%y-%m-%d', errors='coerce')
                # 检查是否成功解析了大部分数据
                # 如果超过一半无法解析，则认为此格式不匹配，重置为None继续尝试其他格式
                if parsed_dates.isna().sum() / len(parsed_dates) > 0.5:  # 如果超过一半无法解析
                    parsed_dates = None  # 重置，尝试其他格式
            except Exception:
                parsed_dates = None
        
        # 如果基于长度的判断失败，则尝试其他方法
        if parsed_dates is None:
            # 尝试自动解析，pandas会自动尝试多种常见格式
            parsed_dates = pd.to_datetime(df_filtered[date_column], errors='coerce')
            
            # 如果自动解析失败较多（超过50%数据无法解析），则尝试指定格式进行精确解析
            if not df_filtered.empty and parsed_dates.isna().sum() / len(parsed_dates) > 0.5:
                # 尝试 %Y/%m/%d 格式
                try:
                    parsed_dates_y = pd.to_datetime(df_filtered[date_column], format='%Y/%m/%d', errors='coerce')
                    # 如果这种格式解析效果更好（缺失值更少），则使用
                    if parsed_dates_y.isna().sum() < parsed_dates.isna().sum():
                        parsed_dates = parsed_dates_y
                except Exception:
                    pass
                    
                # 尝试 %y-%m-%d 格式
                try:
                    parsed_dates_yy = pd.to_datetime(df_filtered[date_column], format='%y-%m-%d', errors='coerce')
                    # 如果这种格式解析效果更好（缺失值更少），则使用
                    if parsed_dates_yy.isna().sum() < parsed_dates.isna().sum():
                        parsed_dates = parsed_dates_yy
                except Exception:
                    pass
                    
        return parsed_dates
        
    def convert_flight_name(self, df):
        """转换飞行数据列名
        
        Args:
            df (pandas.DataFrame): 飞行数据
            
        Returns:
            pandas.DataFrame: 列名已转换的DataFrame
        """
        try:
            # 优化内存使用：创建新的DataFrame而不是修改原数据
            df_new = df.copy()
            
            # 定义替换规则字典
            replacement_rules = self._get_replacement_rules()
            
            # 创建列名映射字典
            column_mapping = self._create_column_mapping(df_new, replacement_rules)
            
            # 重命名列
            df_new = df_new.rename(columns=column_mapping)
            
            return df_new
        except Exception as e:
            logging.error(f"转换飞行数据列名时出错: {e}")
            return df
    
    def _get_replacement_rules(self):
        """获取列名替换规则字典
        
        Returns:
            dict: 替换规则字典
        """
        return {
            'ATA345_GNSU1全球卫星定位系统': '全球卫星定位系统1',
            'ATA345_GNSU2全球卫星定位系统': '全球卫星定位系统2',
            'ATA345_SMU短报文': '短报文',
            'ATA342_AHRU航姿基准系统': '航姿基准系统',
            'ATA341_ADRU1大气数据系统': '大气数据系统1',
            'ATA341_ADRU2大气数据系统': '大气数据系统2',
            'ATA341_ADRU3大气数据系统': '大气数据系统3',
            'ATA344_IRU1惯性基准系统': '惯性基准系统',
            'ATA344_IRU2惯性基准系统': '惯性基准系统',
            'ATA317_FMCC1飞行管理系统': '飞行管理系统1',
            'ATA317_FMCC2飞行管理系统': '飞行管理系统2',
            'ATA316_IDU1显示控制系统': '显示控制系统',
            'ATA344_RA1无线电高度表': '无线电高度表1',
            'ATA344_RA2无线电高度表': '无线电高度表2',
            'ATA344_RPU气象雷达': '气象雷达',
            'ATA341_ISI备份仪表': '备份仪表',
            'ATA315_CAS1显示告警系统': '显示告警系统',
            'ATA344_LIU_C1波段L综合系统': '波段L综合系统1',
            'ATA344_LIU_C2波段L综合系统': '波段L综合系统2',
            'ATA238_RIU1无线电接口单元': '无线电接口单元1',
            'ATA238_RIU2无线电接口单元': '无线电接口单元2',
            'ATA314_RDC1机电信息采集系统': '机电信息采集系统1',
            'ATA314_RDC2机电信息采集系统': '机电信息采集系统2',
            'ATA314_RDC3机电信息采集系统': '机电信息采集系统3',
            'ATA314_RDC4机电信息采集系统': '机电信息采集系统4',
            'ATA314_RDC5机电信息采集系统': '机电信息采集系统5',
            'ATA314_RDC6机电信息采集系统': '机电信息采集系统6',
            'ATA314_RDC7机电信息采集系统': '机电信息采集系统7',
            'ATA314_RDC8机电信息采集系统': '机电信息采集系统8',
            'ATA314_CPDC1机电信息采集': '机电信息采集',
            'ATA36气源系统': '气源系统',
            'ATA21空调系统': '空调系统',
            'ATA21_CPC1座舱压力系统': '座舱压力系统',
            'ATA21_CPSU座舱压力系统': '座舱压力系统',
            'ATA22_AFCC自动飞行系统': '自动飞行系统',
            'ATA22_AFCP自动飞行系统': '自动飞行系统',
            'ATA24_L_PDU左电源系统': '左电源系统',
            'ATA24_R_PDU右电源系统': '右电源系统',
            'ATA26_HKH17A防火系统': '防火系统',
            'ATA279_CAB1主飞控系统': '主飞控系统1',
            'ATA279_CAB2主飞控系统': '主飞控系统2',
            'ATA279_CAB3主飞控系统': '主飞控系统3',
            'ATA275_FECU1襟翼控制系统': '襟翼控制系统1',
            'ATA275_FECU2襟翼控制系统': '襟翼控制系统2',
            'ATA28_FQC燃油系统': '燃油系统',
            'ATA28_FQC燃油系统': '燃油系统',
            'ATA324_BCU刹车控制系统': '刹车控制系统',
            'ATA293_HECU液压电控系统': '液压电控系统',
            'ATA325_SCU前轮转弯系统': '前轮转弯系统',
            'ATA30_TBDI_TIMER防冰和除雨': '防冰和除雨',
            'ATA30_WTC1防冰和除雨': '防冰和除雨',
            'ATA30_PR_PHC防冰和除雨': '防冰和除雨',
            'ATA52_KZQ舱门系统': '舱门系统',
            'ATA25_WATERCU设备用具': '设备用具',
            'ATA32_PDCU1起落架系统': '起落架系统',
            'ATA48_FTC灭火任务系统': '灭火任务系统',
            'ATA48_FECC灭火任务系统': '灭火任务系统',
            'ATA344_SAVMU环境感知与视频管理系统': '环境感知与视频管理系统',
            'ATA42_NCPP1综合处理系统': '综合处理系统1',
            'ATA42_NCPP2综合处理系统': '综合处理系统2',
            'ATA42_HM_GPM1综合处理系统': '综合处理系统3',
            'ATA313_FDR飞参系统': '飞参系统',
            'ATA313_TACE飞参系统': '飞参系统',
            'ATA313_QAR飞参系统': '飞参系统',
            'ATA73_EUC燃油系统': '燃油系统'
        }
    
    def _create_column_mapping(self, df, replacement_rules):
        """创建列名映射字典
        
        Args:
            df (pandas.DataFrame): 数据框
            replacement_rules (dict): 替换规则字典
            
        Returns:
            dict: 列名映射字典
        """
        column_mapping = {}
        for old_name in df.columns:
            new_name = old_name
            for pattern, replacement in replacement_rules.items():
                if pattern in old_name:
                    new_name = old_name.replace(pattern, replacement)
                    break
            column_mapping[old_name] = new_name
        return column_mapping