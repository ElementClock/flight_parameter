#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据分析主模块单元测试
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from analysis.data_analyzer import DataAnalyzer


class TestDataAnalyzer(unittest.TestCase):
    """数据分析主模块测试类"""

    def setUp(self):
        """测试前准备"""
        self.data_analyzer = DataAnalyzer()
        self.sample_data = self._create_sample_data()

    def _create_sample_data(self):
        """创建模拟飞行数据"""
        # 创建时间序列
        start_time = datetime(2023, 1, 1, 10, 0, 0)
        time_points = [start_time + timedelta(seconds=i) for i in range(100)]
        
        # 创建发动机转速数据
        rpm_1_data = [0] * 20 + [80] * 60 + [0] * 20
        rpm_2_data = [0] * 30 + [85] * 40 + [0] * 30
        
        # 创建燃油数据
        fuel_tank_1_data = [1000 - i*2 for i in range(100)]  # 燃油逐渐减少
        fuel_tank_2_data = [800 - i*1.5 for i in range(100)]
        
        # 创建电源数据
        dc_voltage_data = [28.0 + np.random.normal(0, 0.5) for _ in range(100)]  # 直流电压
        ac_voltage_data = [115.0 + np.random.normal(0, 2.0) for _ in range(100)]  # 交流电压
        
        # 创建CAS告警数据
        cas_data = [0] * 50 + [1] * 10 + [0] * 40  # 中间有一段告警
        
        # 构建DataFrame
        data = {
            '飞行时间': time_points,
            '1号发动机转速': rpm_1_data,
            '2号发动机转速': rpm_2_data,
            'Ⅰ号油箱油量': fuel_tank_1_data,
            'Ⅱ号油箱油量': fuel_tank_2_data,
            '1号直流发电机电压': dc_voltage_data,
            '1号交流发电机电压': ac_voltage_data,
            '显示告警系统': cas_data
        }
        
        return pd.DataFrame(data)

    def test_convert_flight_time(self):
        """测试飞行时间转换功能"""
        converted_data = self.data_analyzer.convert_flight_time(self.sample_data)
        
        # 检查是否成功转换
        self.assertIn('飞行时间', converted_data.columns)
        # 由于测试数据中没有标识符列，所以不会进行UTC+8转换，仍为原始时间
        self.assertEqual(converted_data['飞行时间'].iloc[0].hour, 10)

    def test_convert_flight_name(self):
        """测试飞行数据列名转换功能"""
        # 创建包含原始命名的数据
        data_with_original_names = self.sample_data.copy()
        data_with_original_names.rename(columns={
            '1号发动机转速': 'ATA344_IRU1惯性基准系统1号发动机转速'
        }, inplace=True)
        
        converted_data = self.data_analyzer.convert_flight_name(data_with_original_names)
        
        # 检查是否成功转换
        self.assertIn('惯性基准系统1号发动机转速', converted_data.columns)

    def test_analyze(self):
        """测试完整的数据分析功能"""
        result = self.data_analyzer.analyze(self.sample_data)
        
        # 检查返回结果的基本结构
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'text_engine'))
        self.assertTrue(hasattr(result, 'text_fuel'))
        self.assertTrue(hasattr(result, 'text_power'))
        self.assertTrue(hasattr(result, 'text_cas'))

    def test_analyze_with_progress_callback(self):
        """测试带进度回调的数据分析功能"""
        progress_updates = []
        
        def progress_callback(value, message):
            progress_updates.append((value, message))
        
        result = self.data_analyzer.analyze(self.sample_data, progress_callback)
        
        # 检查进度更新
        self.assertGreater(len(progress_updates), 0)
        self.assertEqual(progress_updates[-1][0], 100)  # 最后应该是100%
        self.assertEqual(progress_updates[-1][1], "分析完成")


if __name__ == '__main__':
    unittest.main()