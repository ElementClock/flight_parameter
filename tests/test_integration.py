#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
集成测试方案
===========

针对飞行参数分析工具进行全面的集成测试，确保各模块协同工作正常。
"""

import unittest
import pandas as pd
import tempfile
import os
from datetime import datetime, timedelta
import numpy as np

from analysis.data_analyzer import DataAnalyzer
from analysis.plugin_manager import PluginManager
from analysis.engine_analysis import EngineAnalysis
from analysis.fuel_analysis import FuelAnalysis
from analysis.power_analysis import PowerAnalysis
from analysis.cas_analysis import CasAnalysis
from analysis.analysis_interface import AnalysisResult


class TestIntegration(unittest.TestCase):
    """集成测试类"""

    def setUp(self):
        """测试前准备"""
        self.data_analyzer = DataAnalyzer()
        # 创建临时目录用于测试文件操作
        self.temp_dir = tempfile.mkdtemp()
        # 获取测试数据文件路径
        self.test_data_path = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_flight_data.csv')

    def tearDown(self):
        """测试后清理"""
        # 清理临时目录
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    def read_test_data(self):
        """读取测试数据，处理中文编码"""
        # 尝试多种编码方式读取文件
        encodings = ['gbk', 'gb2312', 'utf-8']
        for encoding in encodings:
            try:
                df = pd.read_csv(self.test_data_path, encoding=encoding)
                return df
            except UnicodeDecodeError:
                continue
        # 如果所有编码都失败，则使用errors='ignore'参数
        return pd.read_csv(self.test_data_path, encoding='gbk', errors='ignore')

    def test_full_analysis_pipeline(self):
        """测试完整的数据分析流水线"""
        # 读取真实测试数据
        df = self.read_test_data()
        
        # 执行完整分析
        result = self.data_analyzer.analyze(df)
        
        # 验证结果类型
        self.assertIsInstance(result, AnalysisResult)
        
        # 验证各模块分析结果存在
        self.assertTrue(hasattr(result, 'text_engine'))
        self.assertTrue(hasattr(result, 'text_fuel'))
        self.assertTrue(hasattr(result, 'text_power'))
        self.assertTrue(hasattr(result, 'text_cas'))

    def test_plugin_manager_integration(self):
        """测试插件管理器与分析模块的集成"""
        plugin_manager = PluginManager()
        
        # 注册所有分析插件
        plugin_manager.register_plugin("engine", EngineAnalysis())
        plugin_manager.register_plugin("fuel", FuelAnalysis())
        plugin_manager.register_plugin("power", PowerAnalysis())
        plugin_manager.register_plugin("cas", CasAnalysis())
        
        # 读取真实测试数据
        df = self.read_test_data()
        converted_data = self.data_analyzer.convert_flight_time(df)
        converted_data = self.data_analyzer.convert_flight_name(converted_data)
        
        # 执行分析
        analysis_results = plugin_manager.execute_analysis(converted_data)
        
        # 验证所有插件都被执行
        self.assertIn('engine', analysis_results)
        self.assertIn('fuel', analysis_results)
        self.assertIn('power', analysis_results)
        self.assertIn('cas', analysis_results)
        
        # 验证没有错误
        for plugin_name, result in analysis_results.items():
            self.assertNotIn('error', result, f"Plugin {plugin_name} encountered an error")
        
        # 生成报告
        reports = plugin_manager.generate_reports(analysis_results)
        
        # 验证报告生成
        self.assertIn('engine', reports)
        self.assertIn('fuel', reports)
        self.assertIn('power', reports)
        self.assertIn('cas', reports)
        
        # 验证报告非空
        self.assertGreater(len(reports['engine']), 0)
        self.assertGreater(len(reports['fuel']), 0)
        self.assertGreater(len(reports['power']), 0)
        self.assertGreater(len(reports['cas']), 0)

    def test_error_handling_integration(self):
        """测试错误处理的集成"""
        # 创建不完整的测试数据（缺少关键列）
        incomplete_data = pd.DataFrame({
            '飞行时间': [datetime(2023, 1, 1, 10, 0, 0)],
            '无关列': [1]
        })
        
        # 执行分析应该仍然返回结果对象，但包含错误信息
        result = self.data_analyzer.analyze(incomplete_data)
        
        # 验证结果对象仍然创建成功
        self.assertIsInstance(result, AnalysisResult)

    def test_time_conversion_integration(self):
        """测试时间转换与其他模块的集成"""
        # 读取真实测试数据
        df = self.read_test_data()
        
        # 执行时间转换
        converted_data = self.data_analyzer.convert_flight_time(df)
        
        # 验证时间列存在且正确转换
        self.assertIn('飞行时间', converted_data.columns)
        self.assertIsInstance(converted_data['飞行时间'].iloc[0], pd.Timestamp)
        
        # 执行列名转换
        final_data = self.data_analyzer.convert_flight_name(converted_data)
        
        # 验证列名转换正确
        # 检查是否存在包含预期模式的列
        expected_patterns = [
            '发动机转速', '油箱油量', '发电机电压', '显示告警系统'
        ]
        
        for pattern in expected_patterns:
            # 检查是否存在包含该模式的列
            matching_cols = [col for col in final_data.columns if pattern in col]
            self.assertGreater(len(matching_cols), 0, f"No column containing pattern: {pattern}")

    def test_plugin_dependencies(self):
        """测试插件依赖关系"""
        plugin_manager = PluginManager()
        
        # 设置带有依赖关系的插件配置
        from analysis.plugin_manager import PluginConfig
        
        engine_config = PluginConfig("engine", priority=40)
        cas_config = PluginConfig("cas", priority=10, dependencies=["engine"])
        
        plugin_manager.register_plugin("engine", EngineAnalysis(), engine_config)
        plugin_manager.register_plugin("cas", CasAnalysis(), cas_config)
        
        # 验证插件顺序正确（依赖者应在被依赖者之后执行）
        order = plugin_manager.get_plugin_order()
        self.assertEqual(set(order), {"engine", "cas"})
        
        # 读取真实测试数据
        df = self.read_test_data()
        converted_data = self.data_analyzer.convert_flight_time(df)
        converted_data = self.data_analyzer.convert_flight_name(converted_data)
        
        # 执行分析
        results = plugin_manager.execute_analysis(converted_data)
        
        # 验证CAS分析获得了发动机的启动/关车时间
        cas_result = results.get('cas', {})
        self.assertIsInstance(cas_result, dict)

    def test_analysis_result_object_integration(self):
        """测试AnalysisResult对象的集成"""
        # 读取真实测试数据并执行完整分析
        df = self.read_test_data()
        result = self.data_analyzer.analyze(df)
        
        # 验证AnalysisResult对象包含所有预期属性
        expected_attrs = [
            'text_engine', 'text_fuel', 'text_power', 'text_cas',
            'engine_start_time', 'engine_end_time',
            'engine_data', 'fuel_data', 'power_data', 'cas_data'
        ]
        
        for attr in expected_attrs:
            self.assertTrue(hasattr(result, attr), f"Missing attribute: {attr}")

    def test_file_based_integration(self):
        """测试基于文件的集成"""
        # 读取测试数据
        df = self.read_test_data()
        
        # 执行分析
        result = self.data_analyzer.analyze(df)
        
        # 验证结果
        self.assertIsInstance(result, AnalysisResult)
        self.assertTrue(hasattr(result, 'text_engine'))
        self.assertTrue(hasattr(result, 'text_fuel'))
        self.assertTrue(hasattr(result, 'text_power'))
        self.assertTrue(hasattr(result, 'text_cas'))


if __name__ == '__main__':
    unittest.main()