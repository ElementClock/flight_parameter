"""
HTML工具模块
"""

import logging
from typing import Dict, Any


class HTMLGenerator:
    """HTML生成器类"""
    
    def __init__(self):
        """初始化HTML生成器"""
        self.css_styles = self._get_default_css()
        self.content = ""
        
    def _get_default_css(self) -> str:
        """获取默认CSS样式"""
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
        
    def generate_html(self, content: str, title: str = "分析结果") -> str:
        """
        生成完整的HTML页面
        
        Args:
            content (str): HTML内容
            title (str): 页面标题
            
        Returns:
            str: 完整的HTML页面
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            {self.css_styles}
        </head>
        <body>
            <div class="analysis-result">
                {content}
            </div>
        </body>
        </html>
        """
        
    def create_document(self, content: str = "", title: str = "分析结果") -> str:
        """
        创建HTML文档
        
        Args:
            content (str): HTML内容
            title (str): 页面标题
            
        Returns:
            str: 完整的HTML文档
        """
        return self.generate_html(content, title)
        
    def escape_html(self, text: str) -> str:
        """
        转义HTML特殊字符
        
        Args:
            text (str): 原始文本
            
        Returns:
            str: 转义后的文本
        """
        if not isinstance(text, str):
            text = str(text)
            
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#39;",
            ">": "&gt;",
            "<": "&lt;",
        }
        
        return "".join(html_escape_table.get(c, c) for c in text)