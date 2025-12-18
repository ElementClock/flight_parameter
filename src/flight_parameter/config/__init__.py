"""
配置模块初始化文件
"""

# 导出配置相关的常量和设置
from ..analysis.config import (
    ENGINE_CONFIG,
    FUEL_CONFIG, 
    POWER_CONFIG,
    CAS_CONFIG
)

__all__ = [
    'ENGINE_CONFIG',
    'FUEL_CONFIG',
    'POWER_CONFIG', 
    'CAS_CONFIG'
]