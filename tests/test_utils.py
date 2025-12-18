#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工具模块单元测试
"""

import unittest
import pandas as pd
from datetime import datetime, timedelta
from analysis.utils import merge_continuous_time_periods, format_exception, safe_get_statistic


class TestUtils(unittest.TestCase):
    """工具模块测试类"""

    def setUp(self):
        """测试前准备"""
        # 创建测试时间序列
        start_time = datetime(2023, 1, 1, 10, 0, 0)
        self.time_points = pd.Series([
            start_time + timedelta(seconds=i) for i in range(10)
        ])
        
        # 创建测试值序列
        self.value_points = pd.Series([i for i in range(10)])

    def test_merge_continuous_time_periods_basic(self):
        """测试基本的时间段合并功能"""
        # 测试空序列
        result = merge_continuous_time_periods(pd.Series([]))
        self.assertEqual(result, [])
        
        # 测试单个时间点
        single_time = pd.Series([self.time_points.iloc[0]])
        result = merge_continuous_time_periods(single_time)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['start_time'], self.time_points.iloc[0])
        self.assertEqual(result[0]['end_time'], self.time_points.iloc[0])

    def test_merge_continuous_time_periods_with_gaps(self):
        """测试带间隙的时间段合并"""
        # 创建带间隙的时间序列
        gapped_times = pd.Series([
            self.time_points.iloc[0],
            self.time_points.iloc[1],
            self.time_points.iloc[5],  # 间隙
            self.time_points.iloc[6],
        ])
        
        result = merge_continuous_time_periods(gapped_times, time_threshold=1.5)
        # 应该分成两个时间段
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['start_time'], self.time_points.iloc[0])
        self.assertEqual(result[0]['end_time'], self.time_points.iloc[1])
        self.assertEqual(result[1]['start_time'], self.time_points.iloc[5])
        self.assertEqual(result[1]['end_time'], self.time_points.iloc[6])

    def test_merge_continuous_time_periods_with_values(self):
        """测试带值的时间段合并"""
        # 创建带间隙的时间序列和值序列
        gapped_times = pd.Series([
            self.time_points.iloc[0],
            self.time_points.iloc[1],
            self.time_points.iloc[5],  # 间隙
            self.time_points.iloc[6],
        ])
        
        gapped_values = pd.Series([10, 20, 100, 110])
        
        result = merge_continuous_time_periods(gapped_times, gapped_values, time_threshold=1.5)
        # 应该分成两个时间段
        self.assertEqual(len(result), 2)
        self.assertIn('min_value', result[0])
        self.assertIn('max_value', result[0])
        self.assertIn('min_value', result[1])
        self.assertIn('max_value', result[1])

    def test_format_exception(self):
        """测试异常格式化功能"""
        # 测试无上下文的异常
        try:
            raise ValueError("测试错误")
        except Exception as e:
            result = format_exception(e)
            self.assertEqual(result, "测试错误")
        
        # 测试带上下文的异常
        try:
            raise ValueError("测试错误")
        except Exception as e:
            result = format_exception(e, "测试上下文")
            self.assertEqual(result, "测试上下文: 测试错误")

    def test_safe_get_statistic(self):
        """测试安全获取统计值功能"""
        # 测试空序列
        empty_series = pd.Series([])
        result = safe_get_statistic(empty_series, 'mean')
        self.assertIsNone(result)
        
        # 测试正常序列的各种统计
        test_series = pd.Series([1, 2, 3, 4, 5])
        
        mean_result = safe_get_statistic(test_series, 'mean')
        self.assertEqual(mean_result, 3.0)
        
        min_result = safe_get_statistic(test_series, 'min')
        self.assertEqual(min_result, 1)
        
        max_result = safe_get_statistic(test_series, 'max')
        self.assertEqual(max_result, 5)
        
        first_result = safe_get_statistic(test_series, 'first')
        self.assertEqual(first_result, 1)
        
        last_result = safe_get_statistic(test_series, 'last')
        self.assertEqual(last_result, 5)
        
        # 测试无效统计类型
        invalid_result = safe_get_statistic(test_series, 'invalid')
        self.assertIsNone(invalid_result)


if __name__ == '__main__':
    unittest.main()