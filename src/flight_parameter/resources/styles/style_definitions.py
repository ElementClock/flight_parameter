"""
样式定义模块
"""

def get_css_styles():
    """获取CSS样式定义"""
    return """
    <style>
    body {
        font-family: "Microsoft YaHei", Arial, sans-serif;
        margin: 20px;
        background-color: #f0f0f0;
    }
    .analysis-result {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1, h2, h3 {
        color: #333;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 10px 0;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    th {
        background-color: #f2f2f2;
        font-weight: bold;
    }
    .warning {
        color: #ff6600;
        font-weight: bold;
    }
    .error {
        color: #ff0000;
        font-weight: bold;
    }
    .success {
        color: #00aa00;
        font-weight: bold;
    }
    </style>
    """

# 全局CSS样式
GLOBAL_CSS = get_css_styles()

# 表格单元格基础样式
TABLE_CELL_BASE_STYLE = "border: 1px solid #ddd; padding: 8px; text-align: left;"
TABLE_HEADER_BASE_STYLE = "background-color: #f2f2f2; font-weight: bold; border: 1px solid #ddd; padding: 8px; text-align: left;"

# 文本对齐样式
ALIGN_LEFT = "text-align: left;"
ALIGN_CENTER = "text-align: center;"
ALIGN_RIGHT = "text-align: right;"

# 表头对齐样式
ALIGN_LEFT_HEADER = "text-align: left; font-weight: bold;"
ALIGN_CENTER_HEADER = "text-align: center; font-weight: bold;"
ALIGN_RIGHT_HEADER = "text-align: right; font-weight: bold;"

# 表格样式
TABLE_STYLE_FIXED = "table-layout: fixed;"
TABLE_STYLE_AUTO = "table-layout: auto;"

# 空行样式
EMPTY_LINE_STYLE = "height: 20px;"
SMALL_EMPTY_LINE_STYLE = "height: 10px;"

# 错误回退样式
ERROR_FALLBACK_STYLE = "color: #ff0000; font-weight: bold;"