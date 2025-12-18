#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据分析主模块
==============

飞行数据主分析流程，协调各个子分析模块完成完整的数据分析任务。
"""

import logging
from typing import Callable, Optional

import pandas as pd

# 项目模块导入
from .analysis_interface import AnalysisResult
from .plugin_manager import PluginManager, PluginConfig
from .engines.engine_analysis import EngineAnalysis
from .fuel.fuel_analysis import FuelAnalysis
from .power.power_analysis import PowerAnalysis
from .cas.cas_analysis import CasAnalysis
from .time_processor import convert_flight_time
from .column_processor import convert_flight_name

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
            df = convert_flight_time(df)
            
            if progress_callback:
                progress_callback(30, "正在转换列名...")
            df = convert_flight_name(df)
            
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
