"""
飞行参数分析工具
================

这是一个用于分析飞行参数数据并生成专业报告的工具。

主要功能:
- 数据加载与管理：支持CSV格式文件多文件加载，自动识别编码
- 发动机参数分析：识别启动/关车时间、转速变化、点火状态等
- CAS告警分析：识别告警时间段、类型及持续时间统计
- 燃油系统分析：分析燃油消耗、油箱状态等关键参数
- 电源系统分析：分析发电机、电池状态等关键参数
- 结果展示与交互：图形化界面实时显示结果，支持多文件切换查看
- 数据导出功能：可将分析结果保存为文本文件，原始数据导出为CSV
"""

# 版本信息
__version__ = "2.0.0"

# 核心功能导入
from .core.app import main
from .core.data_manager import DataManager
from .analysis import (
    DataAnalyzer,
    EngineAnalysis,
    FuelAnalysis,
    PowerAnalysis,
    CasAnalysis
)

__all__ = [
    'main',
    'DataManager',
    'DataAnalyzer',
    'EngineAnalysis',
    'FuelAnalysis',
    'PowerAnalysis',
    'CasAnalysis'
]