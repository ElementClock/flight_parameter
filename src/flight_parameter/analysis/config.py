#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分析模块配置参数
==============

定义分析模块中使用的所有可配置参数，避免硬编码。
"""

# 发动机分析配置
ENGINE_CONFIG = {
    # 发动机启动阈值(RPM)
    'START_THRESHOLD': 10,
    
    # 发动机重启时间间隔阈值(秒)
    'RESTART_INTERVAL_THRESHOLD': 300,
    
    # 发动机编号范围
    'ENGINE_NUMBER_RANGE': (1, 4)
}

# 燃油分析配置
FUEL_CONFIG = {
    # 传感器间差异阈值(kg)
    'SENSOR_DIFFERENCE_THRESHOLD': 20,
    
    # 低油量阈值(kg)
    'LOW_FUEL_THRESHOLD': 200,
    
    # 油箱不平衡阈值(kg)
    'IMBALANCE_THRESHOLD': 100,
    
    # 连续时间判断阈值(秒)
    'CONTINUOUS_TIME_THRESHOLD': 1.0
}

# 电源分析配置
POWER_CONFIG = {
    # 直流发电机负载阈值(A)
    'DC_GENERATOR_LOAD_THRESHOLD': 3200,
    
    # 交流发电机负载阈值(A)
    'AC_GENERATOR_LOAD_THRESHOLD': 400
}

# CAS分析配置
CAS_CONFIG = {
    # 告警连续性判断时间间隔阈值(秒)
    'ALARM_CONTINUITY_THRESHOLD': 1.0
}