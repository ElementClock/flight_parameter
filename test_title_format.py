#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试标题格式化显示
"""

test_content = """这是标题前的内容

[[CENTER]][[BOLD]]动力分析结果[[/BOLD]][[/CENTER]]

这是标题后的内容，应该在新的一行显示

|-列1|列2|列3-|
|数据1|数据2|数据3|
|数据4|数据5|数据6|
|-|--|--|-|

这是表格后的内容"""

def convert_custom_markup_to_html(text):
    """模拟UI组件中的HTML转换函数"""
    try:
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
                                    # 处理单元格内的颜色标记
                                    formatted_cell = cell.strip()
                                    formatted_cell = formatted_cell.replace('[[RED]]', '<span style="color:red;">')
                                    formatted_cell = formatted_cell.replace('[[/RED]]', '</span>')
                                    formatted_cell = formatted_cell.replace('[[AMBER]]', '<span style="color:#FFBF00; font-weight:bold;">')
                                    formatted_cell = formatted_cell.replace('[[/AMBER]]', '</span>')
                                    formatted_cell = formatted_cell.replace('[[BOLD]]', '<span style="font-weight:bold;">')
                                    formatted_cell = formatted_cell.replace('[[/BOLD]]', '</span>')
                                    html_lines.append(f'<td>{formatted_cell}</td>')
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
        
        # 处理居中对齐标记
        html_content = html_content.replace('[[CENTER]]', '<div style="text-align: center;">')
        html_content = html_content.replace('[[/CENTER]]', '</div>')
        
        # 处理段前段后间距标记
        html_content = html_content.replace('[[PARA_MARGIN]]', '<p style="margin: 1em 0;">')
        html_content = html_content.replace('[[/PARA_MARGIN]]', '</p>')
        
        # 处理标题段前段后换行
        html_content = html_content.replace('\n[[CENTER]]', '\n<div style="margin: 1em 0; text-align: center;">')
        html_content = html_content.replace('[[/CENTER]]\n', '</div>\n')
        
        # 处理非表格中的颜色标记
        # 逐一处理各种颜色标记，确保只替换一对标记
        # 检查是否包含需要红色渲染的文本
        while '[[RED]]' in html_content and '[/RED]]' in html_content:
            # 应用红色格式
            html_content = html_content.replace('[[RED]]', '<span style="color:red;">', 1)
            html_content = html_content.replace('[[/RED]]', '</span>', 1)
            
        # 检查是否包含需要黄色渲染的文本
        while '[[YELLOW]]' in html_content and '[[/YELLOW]]' in html_content:
            # 应用黄色格式
            html_content = html_content.replace('[[YELLOW]]', '<span style="color:yellow;">', 1)
            html_content = html_content.replace('[[/YELLOW]]', '</span>', 1)
            
        # 检查是否包含需要琥珀色渲染的文本
        while '[[AMBER]]' in html_content and '[[/AMBER]]' in html_content:
            # 应用琥珀色格式
            html_content = html_content.replace('[[AMBER]]', '<span style="color:#FFBF00; font-weight:bold;">', 1)
            html_content = html_content.replace('[[/AMBER]]', '</span>', 1)
            
        # 检查是否包含需要蓝色渲染的文本
        while '[[BLUE]]' in html_content and '[[/BLUE]]' in html_content:
            # 应用蓝色格式
            html_content = html_content.replace('[[BLUE]]', '<span style="color:blue; font-weight:bold;">', 1)
            html_content = html_content.replace('[[/BLUE]]', '</span>', 1)
            
        # 检查是否包含需要加粗的标题行
        while '[[BOLD]]' in html_content and '[[/BOLD]]' in html_content:
            # 应用加粗格式
            html_content = html_content.replace('[[BOLD]]', '<span style="font-weight:bold;">', 1)
            html_content = html_content.replace('[[/BOLD]]', '</span>', 1)

        # 使用<pre>标签包装内容以保留所有空白字符和换行符（仅对非表格内容）
        if '<table' in html_content:
            # 如果包含表格，则不使用<pre>标签
            return f'<html><body style="font-family: Consolas, \'Courier New\', monospace;">{html_content}</body></html>'
        else:
            # 如果不包含表格，则使用<pre>标签保持格式
            return f'<html><body style="font-family: Consolas, \'Courier New\', monospace;"><pre>{html_content}</pre></body></html>'
    except Exception as e:
        return f'<html><body style="font-family: Consolas, \'Courier New\', monospace;"><pre>{text}</pre></body></html>'

# 测试转换函数
html_result = convert_custom_markup_to_html(test_content)
print("转换后的HTML:")
print(html_result)

# 将结果保存到文件中以便查看
with open("test_output.html", "w", encoding="utf-8") as f:
    f.write(html_result)

print("\nHTML结果已保存到 test_output.html 文件中，请在浏览器中打开查看效果。")