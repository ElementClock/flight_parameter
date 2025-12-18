#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
样式配置模块
============

定义应用程序中使用的统一样式配置，避免在多个文件中重复定义样式。
"""

# 全局CSS样式
GLOBAL_CSS = """
body {
    font-family: Consolas, 'Courier New', monospace;
    font-size: 14px;
    text-align: left;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
}

th, td {
    padding: 3px;
    word-wrap: break-word;
}

th {
    background-color: #f2f2f2;
}

h1, h2, h3, h4, h5, h6 {
    margin: 1em 0;
    text-align: center;
}

h3 {
    font-weight: bold;
}

h5 {
    font-weight: bold;
}

/* 告警级别颜色定义 */
.alarm-warning {
    color: red;
    font-weight: bold;
}

.alarm-caution {
    color: #FFBF00;
    font-weight: bold;
}

.alarm-advisory {
    color: blue;
    font-weight: bold;
}
"""

# 表格相关样式
TABLE_STYLE_BASE = "width: 100%; border-collapse: collapse;"
TABLE_STYLE_FIXED = "width: 100%; table-layout: fixed; border-collapse: collapse;"
TABLE_STYLE_AUTO = "width: 100%; table-layout: auto; border-collapse: collapse;"

# 基础单元格样式
TABLE_CELL_BASE_STYLE = "word-wrap: break-word;"
TABLE_HEADER_BASE_STYLE = "background-color: #f2f2f2; word-wrap: break-word;"

# 表格对齐方式样式（包含基础样式）
ALIGN_LEFT = TABLE_CELL_BASE_STYLE + " text-align: left;"
ALIGN_CENTER = TABLE_CELL_BASE_STYLE + " text-align: center;"
ALIGN_RIGHT = TABLE_CELL_BASE_STYLE + " text-align: right;"

# 表格头部对齐方式样式（包含背景色）
ALIGN_LEFT_HEADER = TABLE_HEADER_BASE_STYLE + " text-align: left;"
ALIGN_CENTER_HEADER = TABLE_HEADER_BASE_STYLE + " text-align: center;"
ALIGN_RIGHT_HEADER = TABLE_HEADER_BASE_STYLE + " text-align: right;"

# 空白行样式
EMPTY_LINE_STYLE = '<div style="height: 1em;"></div>'
SMALL_EMPTY_LINE_STYLE = '<div style="height: 0.5em;"></div>'

# 错误处理样式
ERROR_FALLBACK_STYLE = '<html><body style="font-family: Consolas, \'Courier New\', monospace;"><pre>{text}</pre></body></html>'