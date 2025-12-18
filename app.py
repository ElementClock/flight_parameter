#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
飞行参数分析工具主程序
====================

这是飞行参数分析工具的主程序入口。
"""

import sys
import os

# 将src目录添加到Python路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flight_parameter import main

if __name__ == "__main__":
    main()