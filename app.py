#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
飞行参数分析工具主程序（兼容旧版）
==============================

这是为了保持向后兼容性的主程序入口。
"""

import sys
import os

# 将src目录添加到Python路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flight_parameter.core.app import main

if __name__ == "__main__":
    main()