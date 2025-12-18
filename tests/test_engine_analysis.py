#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
发动机分析模块单元测试
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flight_parameter.analysis.engines.engine_analysis import EngineAnalysis


class TestEngineAnalysis(unittest.TestCase):
    """发动机分析模块测试类"""

    def setUp(self):
        """测试前准备"""
        self.engine_analysis = EngineAnalysis()
        # 创建模拟数据
        self.sample_data = self._create_sample_data()

    def _create_sample_data(self):
        """创建模拟飞行数据"""
        # 创建时间序列
        start_time = datetime(2023, 1, 1, 10, 0, 0)
        time_points = [start_time + timedelta(seconds=i) for i in range(100)]
        
        # 创建发动机转速数据（1号发动机）
        # 模拟发动机启动和关车过程
        rpm_1_data = [0] * 20 + [80] * 60 + [0] * 20  # 前20秒和后20秒为0，中间60秒为80
        
        # 创建发动机转速数据（2号发动机）
        rpm_2_data = [0] * 30 + [85] * 40 + [0] * 30  # 前30秒和后30秒为0，中间40秒为85
        
        # 构建DataFrame
        data = {
            '飞行时间': time_points,
            '1号发动机转速': rpm_1_data,
            '2号发动机转速': rpm_2_data
        }
        
        return pd.DataFrame(data)

    def test_analyze_normal_case(self):
        """测试正常情况下的分析"""
        result = self.engine_analysis.analyze(self.sample_data)
        
        # 检查返回结果的基本结构（更新以匹配新接口）
        self.assertIn('has_takeoff_info', result)
        self.assertIn('takeoff_info', result)
        
        # 检查是否检测到发动机启动信息
        self.assertTrue(result['has_takeoff_info'])
        
        # 检查发动机信息
        self.assertEqual(len(result['takeoff_info']), 4)  # 应该有4个发动机的信息
        
        # 检查1号发动机的启动信息
        engine_1_info = result['takeoff_info'][0]  # 第一个应该是1号发动机
        self.assertEqual(engine_1_info['engine_id'], 1)
        self.assertGreater(len(engine_1_info['start_times']), 0)
        self.assertGreater(len(engine_1_info['end_times']), 0)

    def test_analyze_missing_time_column(self):
        """测试缺少时间列的情况"""
        # 移除时间列
        data_no_time = self.sample_data.drop('飞行时间', axis=1)
        result = self.engine_analysis.analyze(data_no_time)
        
        # 应该返回错误信息
        self.assertIn('errors', result)
        self.assertIsInstance(result['errors'], list)

    def test_analyze_missing_rpm_columns(self):
        """测试缺少发动机转速列的情况"""
        # 只保留时间列
        data_only_time = self.sample_data[['飞行时间']].copy()
        result = self.engine_analysis.analyze(data_only_time)
        
        # 应该返回错误信息
        self.assertIn('errors', result)
        self.assertIsInstance(result['errors'], list)

    def test_generate_text_normal_case(self):
        """测试正常情况下的文本生成"""
        analysis_result = self.engine_analysis.analyze(self.sample_data)
        text_result = self.engine_analysis.generate_text(analysis_result)
        
        # 检查是否包含关键信息
        self.assertIn('动力分析结果', text_result)
        self.assertIn('开关车时间', text_result)
        self.assertIn('首次开车时间', text_result)

    def test_generate_text_with_errors(self):
        """测试包含错误信息的文本生成"""
        error_result = {'errors': ['测试错误信息']}
        text_result = self.engine_analysis.generate_text(error_result)
        
        # 检查是否包含错误信息
        self.assertIn('测试错误信息', text_result)

    def test_find_engine_takeoff_info(self):
        """测试发动机启动信息查找功能"""
        takeoff_info = self.engine_analysis._find_engine_takeoff_info(
            self.sample_data, '飞行时间')
        
        # 检查返回结果
        self.assertIsInstance(takeoff_info, list)
        self.assertEqual(len(takeoff_info), 4)  # 应该有4个发动机的信息
        
        # 检查每个发动机的信息结构
        for info in takeoff_info:
            self.assertIn('engine_id', info)
            self.assertIn('start_times', info)
            self.assertIn('end_times', info)
            self.assertIn('restart_times', info)


if __name__ == '__main__':
    unittest.main()