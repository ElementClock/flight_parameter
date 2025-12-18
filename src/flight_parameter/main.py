#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
飞行参数分析工具主入口
====================

这是飞行参数分析工具的主入口文件，用于启动应用程序。
"""

import sys
import os

# 将src目录添加到Python路径中，确保可以正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flight_parameter.core.app import main

if __name__ == "__main__":
    main()