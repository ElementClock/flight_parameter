#!/usr/bin/env python3
# -*- coding: utf-8 -*-

test_content = """这是标题前的内容
[[TITLE]]动力分析结果[[/TITLE]]
这是标题后的内容

|-列1|列2|列3-|
|数据1|数据2|数据3|
|数据4|数据5|数据6|
|-|--|--|-|

这是表格后的内容"""

def debug_convert_custom_markup_to_html(text):
    """调试版本的HTML转换函数"""
    print("原始文本:")
    print(repr(text))
    
    html_content = text
    
    # 处理表格标记
    if '|-' in html_content and '-|' in html_content:
        lines = html_content.split('\n')
        html_lines = []
        in_table = False
        table_rows = []
        
        for line in lines:
            if '|-' in line and '-|' in line:
                # 表格开始或结束标记
                if not in_table:
                    # 开始表格
                    in_table = True
                    table_rows = []
                    # 提取表头
                    header_line = line.replace('|-', '').replace('-|', '').strip()
                    if header_line:
                        table_rows.append(header_line.split('|'))
                else:
                    # 结束表格
                    in_table = False
                    # 生成HTML表格
                    if table_rows:
                        html_lines.append('<table border="1" cellspacing="0" cellpadding="3">')
                        # 表头
                        if len(table_rows) > 0:
                            html_lines.append('<tr>')
                            for cell in table_rows[0]:
                                html_lines.append(f'<th>{cell.strip()}</th>')
                            html_lines.append('</tr>')
                        # 数据行
                        for row in table_rows[1:]:
                            html_lines.append('<tr>')
                            for cell in row:
                                html_lines.append(f'<td>{cell.strip()}</td>')
                            html_lines.append('</tr>')
                        html_lines.append('</table>')
            elif in_table:
                # 表格中的行
                row_data = line.strip().split('|')
                # 移除首尾的空字符串（由于分割造成的）
                if row_data[0] == '':
                    row_data = row_data[1:]
                if row_data and row_data[-1] == '':
                    row_data = row_data[:-1]
                table_rows.append(row_data)
            else:
                # 非表格行
                html_lines.append(line)
        
        html_content = '\n'.join(html_lines)
        print("\n处理表格后:")
        print(repr(html_content))
    
    # 处理专业标题标记
    html_content = html_content.replace('[[TITLE]]', '<div style="display: block; margin: 1em 0; text-align: center; font-weight: bold;">')
    html_content = html_content.replace('[[/TITLE]]', '</div>')
    print("\n处理标题后:")
    print(repr(html_content))
    
    # 总是返回完整的HTML结构，确保正确渲染
    result = f'<html><body style="font-family: Consolas, \'Courier New\', monospace;">{html_content}</body></html>'
    print("\n最终HTML:")
    print(result)
    return result

# 测试转换函数
html_result = debug_convert_custom_markup_to_html(test_content)