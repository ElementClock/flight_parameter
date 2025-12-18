#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志模块单元测试
"""

import unittest
import logging
from analysis.logger import get_analysis_logger, log_execution, log_step


class TestLogger(unittest.TestCase):
    """日志模块测试类"""

    def test_get_analysis_logger(self):
        """测试获取分析日志记录器功能"""
        logger1 = get_analysis_logger("test_module1")
        logger2 = get_analysis_logger("test_module2")
        logger3 = get_analysis_logger("test_module1")  # 同名
        
        # 检查返回的是Logger实例
        self.assertIsInstance(logger1, logging.Logger)
        self.assertIsInstance(logger2, logging.Logger)
        
        # 检查同名logger是同一个实例
        self.assertIs(logger1, logger3)
        
        # 检查logger名称
        self.assertEqual(logger1.name, "test_module1")
        self.assertEqual(logger2.name, "test_module2")

    def test_log_execution_decorator(self):
        """测试执行日志装饰器"""
        @log_execution
        def test_function():
            return "success"
        
        # 执行函数，应该正常返回
        result = test_function()
        self.assertEqual(result, "success")

    def test_log_execution_decorator_with_exception(self):
        """测试执行日志装饰器处理异常"""
        @log_execution
        def failing_function():
            raise ValueError("测试异常")
        
        # 执行应该抛出异常
        with self.assertRaises(ValueError):
            failing_function()

    def test_log_step_decorator(self):
        """测试步骤日志装饰器"""
        @log_step("测试步骤")
        def test_function():
            return "success"
        
        # 执行函数，应该正常返回
        result = test_function()
        self.assertEqual(result, "success")

    def test_log_step_decorator_with_exception(self):
        """测试步骤日志装饰器处理异常"""
        @log_step("测试步骤")
        def failing_function():
            raise RuntimeError("测试运行时错误")
        
        # 执行应该抛出异常
        with self.assertRaises(RuntimeError):
            failing_function()


if __name__ == '__main__':
    unittest.main()