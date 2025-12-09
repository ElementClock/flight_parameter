#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
插件管理器单元测试
"""

import unittest
import pandas as pd
from datetime import datetime, timedelta
from analysis.plugin_manager import PluginManager, PluginConfig
from analysis.analysis_interface import AnalysisInterface


class MockAnalysisPlugin(AnalysisInterface):
    """模拟分析插件用于测试"""
    
    def __init__(self, name="mock"):
        self._name = name
    
    def get_name(self) -> str:
        return self._name
    
    def analyze(self, df, **kwargs) -> dict:
        return {"plugin": self._name, "result": "analyzed"}
    
    def generate_text(self, analysis_data: dict) -> str:
        return f"Report from {self._name}"


class TestPluginManager(unittest.TestCase):
    """插件管理器测试类"""

    def setUp(self):
        """测试前准备"""
        self.plugin_manager = PluginManager()
        self.mock_plugin1 = MockAnalysisPlugin("mock1")
        self.mock_plugin2 = MockAnalysisPlugin("mock2")

    def test_register_plugin(self):
        """测试插件注册"""
        self.plugin_manager.register_plugin("mock1", self.mock_plugin1)
        
        # 检查插件是否注册成功
        self.assertIn("mock1", self.plugin_manager.get_plugins())
        self.assertEqual(self.plugin_manager.get_plugin("mock1"), self.mock_plugin1)

    def test_unregister_plugin(self):
        """测试插件注销"""
        self.plugin_manager.register_plugin("mock1", self.mock_plugin1)
        self.plugin_manager.unregister_plugin("mock1")
        
        # 检查插件是否注销成功
        self.assertNotIn("mock1", self.plugin_manager.get_plugins())

    def test_plugin_config(self):
        """测试插件配置"""
        config = PluginConfig("mock1", enabled=True, priority=10, dependencies=["dep1"])
        self.plugin_manager.register_plugin("mock1", self.mock_plugin1, config)
        
        # 检查配置是否正确设置
        self.assertEqual(self.plugin_manager.plugin_configs["mock1"].priority, 10)
        self.assertEqual(self.plugin_manager.plugin_configs["mock1"].dependencies, ["dep1"])

    def test_plugin_order(self):
        """测试插件执行顺序"""
        config1 = PluginConfig("mock1", priority=10)
        config2 = PluginConfig("mock2", priority=20)
        
        self.plugin_manager.register_plugin("mock1", self.mock_plugin1, config1)
        self.plugin_manager.register_plugin("mock2", self.mock_plugin2, config2)
        
        # 检查插件是否按照优先级排序
        order = self.plugin_manager.get_plugin_order()
        self.assertEqual(order, ["mock2", "mock1"])  # 高优先级在前

    def test_execute_analysis(self):
        """测试执行分析"""
        self.plugin_manager.register_plugin("mock1", self.mock_plugin1)
        self.plugin_manager.register_plugin("mock2", self.mock_plugin2)
        
        # 创建模拟数据
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
        
        # 执行分析
        results = self.plugin_manager.execute_analysis(df)
        
        # 检查结果
        self.assertIn("mock1", results)
        self.assertIn("mock2", results)
        self.assertEqual(results["mock1"]["plugin"], "mock1")
        self.assertEqual(results["mock2"]["plugin"], "mock2")

    def test_generate_reports(self):
        """测试生成报告"""
        self.plugin_manager.register_plugin("mock1", self.mock_plugin1)
        self.plugin_manager.register_plugin("mock2", self.mock_plugin2)
        
        # 模拟分析数据
        analysis_data = {
            "mock1": {"plugin": "mock1", "result": "analyzed"},
            "mock2": {"plugin": "mock2", "result": "analyzed"}
        }
        
        # 生成报告
        reports = self.plugin_manager.generate_reports(analysis_data)
        
        # 检查报告
        self.assertIn("mock1", reports)
        self.assertIn("mock2", reports)
        self.assertIn("Report from mock1", reports["mock1"])
        self.assertIn("Report from mock2", reports["mock2"])

    def test_enable_disable_plugin(self):
        """测试启用/禁用插件"""
        config1 = PluginConfig("mock1", enabled=True)
        config2 = PluginConfig("mock2", enabled=False)
        
        self.plugin_manager.register_plugin("mock1", self.mock_plugin1, config1)
        self.plugin_manager.register_plugin("mock2", self.mock_plugin2, config2)
        
        # 检查初始状态
        order = self.plugin_manager.get_plugin_order()
        self.assertIn("mock1", order)
        self.assertNotIn("mock2", order)
        
        # 启用插件2
        self.plugin_manager.enable_plugin("mock2", True)
        order = self.plugin_manager.get_plugin_order()
        self.assertIn("mock1", order)
        self.assertIn("mock2", order)
        
        # 禁用插件1
        self.plugin_manager.enable_plugin("mock1", False)
        order = self.plugin_manager.get_plugin_order()
        self.assertNotIn("mock1", order)
        self.assertIn("mock2", order)


if __name__ == '__main__':
    unittest.main()