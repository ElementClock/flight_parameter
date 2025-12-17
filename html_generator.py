#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTML生成器模块
==============

提供更强大和灵活的HTML生成功能，用于替代简单的字符串拼接方式。
使用dominate库来生成结构化的HTML内容。
"""

import logging
from typing import List, Dict, Any, Optional

try:
    import dominate
    from dominate import tags as dtags
    from dominate.util import raw
except ImportError:
    logging.error("缺少dominate库，请安装：pip install dominate")
    raise

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class HTMLGenerator:
    """HTML生成器类
    
    使用dominate库生成结构化的HTML内容，提供比字符串拼接更可靠和灵活的方式。
    """
    
    def __init__(self):
        """初始化HTML生成器"""
        self.doc = None
        self.current_table = None
        self.current_table_head = None
        self.current_table_body = None
    
    def create_document(self, title: str = "") -> dominate.document:
        """创建一个新的HTML文档
        
        Args:
            title (str): 文档标题
            
        Returns:
            dominate.document: HTML文档对象
        """
        self.doc = dominate.document(title=title)
        return self.doc
    
    def add_css(self, css_content: str):
        """添加CSS样式到文档
        
        Args:
            css_content (str): CSS样式内容
        """
        if self.doc is None:
            raise ValueError("请先创建文档")
            
        with self.doc.head:
            dtags.style(raw(css_content))
    
    def add_title(self, text: str, level: int = 3, center: bool = True):
        """添加标题
        
        Args:
            text (str): 标题文本
            level (int): 标题级别 (1-6)
            center (bool): 是否居中显示
        """
        if self.doc is None:
            raise ValueError("请先创建文档")
            
        # 根据级别选择合适的标题标签
        title_tags = {
            1: dtags.h1,
            2: dtags.h2,
            3: dtags.h3,
            4: dtags.h4,
            5: dtags.h5,
            6: dtags.h6
        }
        
        title_tag = title_tags.get(level, dtags.h3)
        
        with self.doc:
            attrs = {}
            if center:
                attrs['style'] = 'text-align: center; margin: 1em 0;'
                
            title_tag(text, **attrs)
    
    def start_table(self, style: str = "", css_class: str = ""):
        """开始创建表格
        
        Args:
            style (str): 表格样式
            css_class (str): 表格CSS类名
        """
        if self.doc is None:
            raise ValueError("请先创建文档")
            
        with self.doc:
            attrs = {}
            if style:
                attrs['style'] = style
            if css_class:
                attrs['cls'] = css_class
                
            self.current_table = dtags.table(**attrs)
            self.current_table_head = None
            self.current_table_body = None
    
    def add_table_header(self, headers: List[str], widths: Optional[List[float]] = None, align: str = "center"):
        """添加表格头部
        
        Args:
            headers (List[str]): 表头列表
            widths (Optional[List[float]]): 列宽度百分比列表
            align (str): 对齐方式 ("left", "center", "right")
        """
        if self.current_table is None:
            raise ValueError("请先开始创建表格")
            
        with self.current_table:
            self.current_table_head = dtags.thead()
            with self.current_table_head:
                with dtags.tr():
                    for i, header in enumerate(headers):
                        attrs = {'style': f'background-color: #f2f2f2; word-wrap: break-word; text-align: {align};'}
                        if widths and i < len(widths) and widths[i] is not None:
                            attrs['style'] += f' width: {widths[i]}%;'
                            
                        dtags.th(header, **attrs)
    
    def start_table_body(self):
        """开始表格主体部分"""
        if self.current_table is None:
            raise ValueError("请先开始创建表格")
            
        with self.current_table:
            self.current_table_body = dtags.tbody()
    
    def add_table_row(self, cells: List[str], align: str = "center"):
        """添加表格行
        
        Args:
            cells (List[str]): 单元格内容列表
            align (str): 对齐方式 ("left", "center", "right")
        """
        if self.current_table_body is None:
            raise ValueError("请先开始表格主体部分")
            
        with self.current_table_body:
            with dtags.tr():
                for cell in cells:
                    dtags.td(cell, style=f"word-wrap: break-word; text-align: {align};")
    
    def end_table(self):
        """结束表格创建"""
        if self.doc is None:
            raise ValueError("请先创建文档")
            
        with self.doc:
            self.current_table = None
            self.current_table_head = None
            self.current_table_body = None
    
    def add_paragraph(self, text: str, style: str = ""):
        """添加段落
        
        Args:
            text (str): 段落文本
            style (str): 段落样式
        """
        if self.doc is None:
            raise ValueError("请先创建文档")
            
        with self.doc:
            attrs = {}
            if style:
                attrs['style'] = style
            dtags.p(text, **attrs)
    
    def add_raw_html(self, html_content: str):
        """添加原始HTML内容
        
        Args:
            html_content (str): HTML内容
        """
        if self.doc is None:
            raise ValueError("请先创建文档")
            
        with self.doc:
            raw(html_content)
    
    def get_html(self) -> str:
        """获取生成的HTML内容
        
        Returns:
            str: HTML内容字符串
        """
        if self.doc is None:
            raise ValueError("请先创建文档")
            
        return str(self.doc)
    
    def convert_markdown_table_to_html(self, markdown_table: str) -> str:
        """将Markdown表格转换为HTML表格
        
        Args:
            markdown_table (str): Markdown表格字符串
            
        Returns:
            str: HTML表格字符串
        """
        lines = markdown_table.strip().split('\n')
        if len(lines) < 2:
            return markdown_table
            
        # 解析表头
        header_line = lines[0]
        headers = [cell.strip() for cell in header_line.split('|') if cell.strip()]
        
        # 检查是否有自定义宽度定义行
        has_custom_widths = len(lines) > 1 and ':::' in lines[1]
        widths = None
        
        if has_custom_widths:
            # 解析自定义宽度
            width_line = lines[1]
            width_parts = [part.strip() for part in width_line.split('|') if part.strip()]
            widths = []
            for part in width_parts:
                if part.startswith(':::') and part.endswith(':::'):
                    try:
                        width_percent = float(part[3:-3])
                        widths.append(width_percent)
                    except ValueError:
                        widths.append(None)
                else:
                    widths.append(None)
            # 移除宽度定义行
            lines.pop(1)
        
        # 创建HTML文档
        temp_doc = dominate.document()
        with temp_doc:
            # 使用 table-layout: fixed 强制按比例显示
            table_style = 'width: 100%; table-layout: fixed; border-collapse: collapse;' if has_custom_widths else \
                         'width: 100%; table-layout: auto; border-collapse: collapse;'
            with dtags.table(style=table_style, border="1", cellspacing="0", cellpadding="3"):
                # 表头
                with dtags.thead():
                    with dtags.tr():
                        for i, header in enumerate(headers):
                            style_attrs = 'background-color: #f2f2f2; word-wrap: break-word;'
                            if has_custom_widths and widths and i < len(widths) and widths[i] is not None:
                                style_attrs += f' width: {widths[i]}%;'
                            dtags.th(header, style=style_attrs)
                
                # 表体
                with dtags.tbody():
                    # 从第二行开始处理数据行（如果有宽度定义行，则实际上是第三行开始）
                    start_index = 2 if not has_custom_widths else 1
                    for line in lines[start_index:]:
                        cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                        if cells:  # 只处理非空行
                            with dtags.tr():
                                for cell in cells:
                                    dtags.td(cell, style="word-wrap: break-word;")
        
        return str(temp_doc)


# 使用示例
if __name__ == "__main__":
    # 创建HTML生成器实例
    generator = HTMLGenerator()
    
    # 创建文档
    doc = generator.create_document("测试文档")
    
    # 添加CSS样式
    generator.add_css("""
        body {
            font-family: Consolas, 'Courier New', monospace;
            font-size: 14px;
        }
        table {
            margin: 1em 0;
        }
    """)
    
    # 添加标题
    generator.add_title("测试标题", level=3)
    
    # 添加表格
    generator.start_table(style="width: 100%; border-collapse: collapse;", css_class="test-table")
    generator.add_table_header(["列1", "列2", "列3"], widths=[40, 30, 30])
    generator.start_table_body()
    generator.add_table_row(["数据1", "数据2", "数据3"])
    generator.add_table_row(["数据4", "数据5", "数据6"])
    generator.end_table()
    
    # 添加段落
    generator.add_paragraph("这是一个测试段落。")
    
    # 输出生成的HTML
    print(generator.get_html())