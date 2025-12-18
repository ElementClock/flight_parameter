#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
运行飞行参数分析工具
==================

这个脚本用于启动飞行参数分析工具应用程序。
"""

import sys
import os

# 将src目录添加到Python路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from flight_parameter.core.app import main

if __name__ == "__main__":
    main()