#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置模块单元测试
"""

import unittest
from analysis.config import ENGINE_CONFIG, FUEL_CONFIG, POWER_CONFIG, CAS_CONFIG


class TestConfig(unittest.TestCase):
    """配置模块测试类"""

    def test_engine_config(self):
        """测试发动机配置"""
        self.assertIn('START_THRESHOLD', ENGINE_CONFIG)
        self.assertIn('RESTART_INTERVAL_THRESHOLD', ENGINE_CONFIG)
        self.assertIn('ENGINE_NUMBER_RANGE', ENGINE_CONFIG)
        
        self.assertIsInstance(ENGINE_CONFIG['START_THRESHOLD'], (int, float))
        self.assertIsInstance(ENGINE_CONFIG['RESTART_INTERVAL_THRESHOLD'], (int, float))
        self.assertIsInstance(ENGINE_CONFIG['ENGINE_NUMBER_RANGE'], tuple)
        self.assertEqual(len(ENGINE_CONFIG['ENGINE_NUMBER_RANGE']), 2)

    def test_fuel_config(self):
        """测试燃油配置"""
        self.assertIn('SENSOR_DIFFERENCE_THRESHOLD', FUEL_CONFIG)
        self.assertIn('LOW_FUEL_THRESHOLD', FUEL_CONFIG)
        self.assertIn('IMBALANCE_THRESHOLD', FUEL_CONFIG)
        self.assertIn('CONTINUOUS_TIME_THRESHOLD', FUEL_CONFIG)
        
        self.assertIsInstance(FUEL_CONFIG['SENSOR_DIFFERENCE_THRESHOLD'], (int, float))
        self.assertIsInstance(FUEL_CONFIG['LOW_FUEL_THRESHOLD'], (int, float))
        self.assertIsInstance(FUEL_CONFIG['IMBALANCE_THRESHOLD'], (int, float))
        self.assertIsInstance(FUEL_CONFIG['CONTINUOUS_TIME_THRESHOLD'], (int, float))

    def test_power_config(self):
        """测试电源配置"""
        self.assertIn('DC_GENERATOR_LOAD_THRESHOLD', POWER_CONFIG)
        self.assertIn('AC_GENERATOR_LOAD_THRESHOLD', POWER_CONFIG)
        
        self.assertIsInstance(POWER_CONFIG['DC_GENERATOR_LOAD_THRESHOLD'], (int, float))
        self.assertIsInstance(POWER_CONFIG['AC_GENERATOR_LOAD_THRESHOLD'], (int, float))

    def test_cas_config(self):
        """测试CAS配置"""
        self.assertIn('ALARM_CONTINUITY_THRESHOLD', CAS_CONFIG)
        
        self.assertIsInstance(CAS_CONFIG['ALARM_CONTINUITY_THRESHOLD'], (int, float))


if __name__ == '__main__':
    unittest.main()