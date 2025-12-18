#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据列名配置文件
================

定义各种数据列的匹配模式，便于统一管理和维护。
"""

# 发动机相关列名配置
ENGINE_COLUMNS = {
    'RPM': r'(\d)发发动机转速',  # 发动机转速
    'TEMPERATURE': r'(\d)发排气温度',  # 发动机排气温度
    'PRESSURE': r'(\d)发滑油压力',  # 发动机滑油压力
    'OIL_TEMPERATURE': r'(\d)发滑油温度'  # 发动机滑油温度
}

# 燃油系统相关列名配置
FUEL_COLUMNS = {
    'TANK_LEVEL': r'([ⅠⅡⅢⅣ])号油箱油量',  # 油箱油量
    'TANK_TEMPERATURE': r'([ⅠⅡⅢⅣ])号油箱燃油温度',  # 油箱燃油温度
    'ENGINE_CONSUMPTION': r'(\d)发总耗量'  # 发动机总耗油量
}

# CAS告警系统相关列名配置
CAS_COLUMNS = {
    'ALARM': r'显示告警系统'  # CAS告警
}

# 电源系统相关列名配置
POWER_COLUMNS = {
    'DC_VOLTAGE': r'(\d)号直流发电机(?:输出)?电压',  # 直流发电机电压
    'DC_CURRENT': r'(\d)号直流发电机(?:输出)?电流',  # 直流发电机电流
    'AC_VOLTAGE': r'(\d)号交流发电机(?:输出)?电压',  # 交流发电机电压
    'AC_CURRENT': r'(\d)号交流发电机(?:输出)?电流',  # 交流发电机电流
    'BUS_VOLTAGE': r'(.+?)汇流条电压',  # 汇流条电压
    'BUS_CURRENT': r'(.+?)汇流条电流'  # 汇流条电流
}

# 通用列名配置
GENERAL_COLUMNS = {
    'FLIGHT_TIME': r'飞行时间'  # 飞行时间
}