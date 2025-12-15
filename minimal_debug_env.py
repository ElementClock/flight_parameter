#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
最小可复现调试环境 - 数据导出框文本格式调试
=================================================

此脚本提供了一个最小的可运行环境，用于调试数据导出框内的输出文本格式。
目标是能够独立测试和调试UI组件中的文本格式化功能。
"""

import wx
import wx.html as html


class DebugFrame(wx.Frame):
    """调试窗口类"""
    
    def __init__(self):
        super().__init__(None, title="数据导出框文本格式调试环境", size=(800, 600))
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建控件
        title = wx.StaticText(panel, label="数据导出结果调试")
        font = wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(font)
        
        # 创建HTML显示窗口
        self.html_window = html.HtmlWindow(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
        
        # 创建按钮
        test_button = wx.Button(panel, label="测试格式化文本")
        test_button.Bind(wx.EVT_BUTTON, self.on_test_format)
        
        clear_button = wx.Button(panel, label="清除")
        clear_button.Bind(wx.EVT_BUTTON, self.on_clear)
        
        # 布局
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(test_button, 0, wx.ALL, 5)
        button_sizer.Add(clear_button, 0, wx.ALL, 5)
        
        sizer.Add(title, 0, wx.ALL | wx.CENTER, 5)
        sizer.Add(self.html_window, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 5)
        
        panel.SetSizer(sizer)
        
    def on_test_format(self, event):
        """测试格式化文本"""
        # 示例输入数据
        sample_text = self.get_sample_text()
        self.set_formatted_text(sample_text)
        # 打印部分HTML内容用于调试
        html_text = self.convert_custom_markup_to_html(sample_text)
        print("部分HTML内容（前500字符）:")
        print(html_text[:500])
        
    def on_clear(self, event):
        """清除显示内容"""
        self.html_window.SetPage("")
        
    def get_sample_text(self):
        """获取示例文本"""
        return """[[TITLE]]动力分析结果[[/TITLE]]

这是普通文本内容，用于测试基本显示效果。

[[LEVEL_TITLE]]发动机参数表[[/LEVEL_TITLE]]
|-参数名称|数值|单位-|
|转速|5200|RPM|
|温度|980|°C|
|压力|1.2|MPa|
|-|--|--|-|

[[PARA_MARGIN]]这段文字应该有段落间距。[[/PARA_MARGIN]]

[[CENTER]][[BOLD]]警告信息[[/BOLD]][[/CENTER]]

[[RED]]重要提醒：这是红色文本，表示关键信息。[[/RED]]

[[AMBER]]注意：这是琥珀色文本，表示需要注意的信息。[[/AMBER]]

[[BLUE]]提示：这是蓝色文本，表示一般提示信息。[[/BLUE]]

[[TITLE]]燃油系统分析结果[[/TITLE]]

总燃油消耗: 1250.50 kg

[[CENTER]]|-油箱编号|初始燃油(kg)|最终燃油(kg)|消耗燃油(kg)|温度变化(°C)-|[[/CENTER]]
|Ⅰ号|1000.00|800.00|200.00|25.00 -> 22.00|
|Ⅱ号|950.00|750.50|199.50|24.50 -> 21.80|
|-|--|--|--|--|-|

[[TITLE]]CAS告警分析结果[[/TITLE]]

|-[[LEVEL_TITLE]]警告级[[/LEVEL_TITLE]]-|
|-告警名称|时间|持续时间-|
|发动机超温告警|10:25:30-10:26:45|1 分钟 15 秒|
|燃油低压告警|11:15:20-11:15:25|5 秒|
|-|--|--|-|

|-[[LEVEL_TITLE]]提示级[[/LEVEL_TITLE]]-|
|-告警名称|时间|持续时间-|
|座舱高度高|10:45:10-10:46:30|1 分钟 20 秒|
|-|--|--|-|

[[TITLE]]电源系统分析结果[[/TITLE]]

[[CENTER]]|-直流发电机|电压平均值(V)|电压最大值(V)|电流平均값(A)|电流最大值(A)|负载状态(≤3200A)-|[[/CENTER]]
|1号|28.50|29.20|1650.30|3100.20|True|
|2号|28.40|29.10|1780.50|3250.80|[[RED]]False(超限)[[/RED]]|
|-|--|--|--|--|--|-|

[[CENTER]]|-交流发电机|电压平均值(V)|电压最大值(V)|电流平均값(A)|电流最大值(A)|负载状态(≤400A)-|[[/CENTER]]
|1号|115.00|118.50|250.30|380.20|True|
|2号|114.80|119.20|260.50|420.80|[[RED]]False(超限)[[/RED]]|
|-|--|--|--|--|--|-|
"""
        
    def set_formatted_text(self, text):
        """设置格式化的文本内容
        
        Args:
            text (str): 要显示的文本内容
        """
        # 将自定义标记转换为HTML标记
        html_text = self.convert_custom_markup_to_html(text)
        # 在HTML窗口中显示内容
        self.html_window.SetPage(html_text)
            
    def convert_custom_markup_to_html(self, text):
        """将自定义标记转换为HTML标记
        
        Args:
            text (str): 包含自定义标记的文本
            
        Returns:
            str: 转换为HTML格式的文本
        """
        # 定义样式库
        styles = {
            'title': 'margin: 0.3em 0; text-align: center; font-weight: bold;',
            'level_title': 'margin: 0.3em 0; text-align: center; font-weight: bold;',
            'paragraph': 'margin: 0.3em 0;',
            'center': 'text-align: center;',
            'bold': 'font-weight: bold;',
            'red': 'color: red;',
            'amber': 'color: #FFBF00; font-weight: bold;',
            'blue': 'color: blue; font-weight: bold;',
            'yellow': 'color: yellow;'
        }
        
        html_content = text
        
        # 处理表格标记
        if '|-' in html_content and '-|' in html_content:
            lines = html_content.split('\n')
            html_lines = []
            in_table = False
            table_rows = []
            table_needs_center_alignment = False  # 表格是否需要居中对齐
            
            for line in lines:
                # 检查表格是否需要居中对齐
                if '|-' in line and '-|' in line:
                    # 检查表头是否有居中对齐标记
                    stripped_line = line.replace('|-', '').replace('-|', '').strip()
                    if stripped_line and '[[CENTER]]' in stripped_line:
                        table_needs_center_alignment = True
                
                if '|-' in line and '-|' in line:
                    # 表格开始或结束标记
                    if not in_table:
                        # 开始表格
                        in_table = True
                        table_rows = []
                        # 提取表头
                        header_line = line.replace('|-', '').replace('-|', '').strip()
                        if header_line:
                            # 移除居中标记（如果有的话）
                            header_line = header_line.replace('[[CENTER]]', '').replace('[[/CENTER]]', '')
                            table_rows.append(header_line.split('|'))
                    else:
                        # 结束表格
                        in_table = False
                        # 生成HTML表格，设置宽度100%并使用fixed布局使列宽相等
                        if table_rows:
                            # 根据需要决定是否添加居中对齐
                            alignment_style = styles['center'] if table_needs_center_alignment else ""
                            html_lines.append(f'<table style="width: 100%; table-layout: fixed; {alignment_style}" border="1" cellspacing="0" cellpadding="3">')
                            # 表头
                            if len(table_rows) > 0:
                                # 检查是否是特殊表头（LEVEL_TITLE）
                                first_row = table_rows[0]
                                if len(first_row) == 1 and '[[LEVEL_TITLE]]' in first_row[0]:
                                    # 这是一个特殊表头，横跨所有列
                                    level_title_content = first_row[0].replace('[[LEVEL_TITLE]]', '').replace('[[/LEVEL_TITLE]]', '')
                                    html_lines.append(f'<tr><th colspan="100%" style="{styles["level_title"]}">{level_title_content}</th></tr>')
                                    # 从第二行开始处理正常的表头
                                    if len(table_rows) > 1:
                                        html_lines.append('<tr>')
                                        for cell in table_rows[1]:
                                            html_lines.append(f'<th style="word-wrap: break-word;">{cell.strip()}</th>')
                                        html_lines.append('</tr>')
                                        # 处理数据行（从第三行开始）
                                        for row in table_rows[2:]:
                                            html_lines.append('<tr>')
                                            for cell in row:
                                                # 处理单元格内的颜色标记
                                                formatted_cell = cell.strip()
                                                formatted_cell = formatted_cell.replace('[[RED]]', f'<span style="{styles["red"]}">')
                                                formatted_cell = formatted_cell.replace('[[/RED]]', '</span>')
                                                formatted_cell = formatted_cell.replace('[[AMBER]]', f'<span style="{styles["amber"]}">')
                                                formatted_cell = formatted_cell.replace('[[/AMBER]]', '</span>')
                                                formatted_cell = formatted_cell.replace('[[BOLD]]', f'<span style="{styles["bold"]}">')
                                                formatted_cell = formatted_cell.replace('[[/BOLD]]', '</span>')
                                                html_lines.append(f'<td style="word-wrap: break-word;">{formatted_cell}</td>')
                                            html_lines.append('</tr>')
                                else:
                                    # 正常的表头处理
                                    html_lines.append('<tr>')
                                    for cell in table_rows[0]:
                                        html_lines.append(f'<th style="word-wrap: break-word;">{cell.strip()}</th>')
                                    html_lines.append('</tr>')
                                    # 数据行
                                    for row in table_rows[1:]:
                                        html_lines.append('<tr>')
                                        for cell in row:
                                            # 处理单元格内的颜色标记
                                            formatted_cell = cell.strip()
                                            formatted_cell = formatted_cell.replace('[[RED]]', f'<span style="{styles["red"]}">')
                                            formatted_cell = formatted_cell.replace('[[/RED]]', '</span>')
                                            formatted_cell = formatted_cell.replace('[[AMBER]]', f'<span style="{styles["amber"]}">')
                                            formatted_cell = formatted_cell.replace('[[/AMBER]]', '</span>')
                                            formatted_cell = formatted_cell.replace('[[BOLD]]', f'<span style="{styles["bold"]}">')
                                            formatted_cell = formatted_cell.replace('[[/BOLD]]', '</span>')
                                            html_lines.append(f'<td style="word-wrap: break-word;">{formatted_cell}</td>')
                                        html_lines.append('</tr>')
                            html_lines.append('</table>')
                            # 在表格后添加一行空白行
                            html_lines.append('<div style="height: 0.3em;"></div>')
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
        
        # 处理段前段后间距标记
        html_content = html_content.replace('[[PARA_MARGIN]]', f'<p style="{styles["paragraph"]}">')
        html_content = html_content.replace('[[/PARA_MARGIN]]', '</p>')
        
        # 处理专业标题标记 - 使用<h2>标签确保独立显示
        html_content = html_content.replace('[[TITLE]]', f'<h2 style="{styles["title"]}">')
        html_content = html_content.replace('[[/TITLE]]', '</h2>')
        
        # 处理告警级别标题标记 - 使用<h3>标签确保独立显示
        html_content = html_content.replace('[[LEVEL_TITLE]]', f'<h3 style="{styles["level_title"]}">')
        html_content = html_content.replace('[[/LEVEL_TITLE]]', '</h3>')
        
        # 处理居中对齐标记
        html_content = html_content.replace('[[CENTER]]', f'<p style="{styles["center"]}">')
        html_content = html_content.replace('[[/CENTER]]', '</p>')
        
        # 处理非表格中的颜色标记
        # 逐一处理各种颜色标记，确保只替换一对标记
        # 检查是否包含需要红色渲染的文本
        while '[[RED]]' in html_content and '[/RED]]' in html_content:
            # 应用红色格式
            html_content = html_content.replace('[[RED]]', f'<span style="{styles["red"]}">', 1)
            html_content = html_content.replace('[[/RED]]', '</span>', 1)
            
        # 检查是否包含需要黄色渲染的文本
        while '[[YELLOW]]' in html_content and '[[/YELLOW]]' in html_content:
            # 应用黄色格式
            html_content = html_content.replace('[[YELLOW]]', f'<span style="{styles["yellow"]}">', 1)
            html_content = html_content.replace('[[/YELLOW]]', '</span>', 1)
            
        # 检查是否包含需要琥珀色渲染的文本
        while '[[AMBER]]' in html_content and '[[/AMBER]]' in html_content:
            # 应用琥珀色格式
            html_content = html_content.replace('[[AMBER]]', f'<span style="{styles["amber"]}">', 1)
            html_content = html_content.replace('[[/AMBER]]', '</span>', 1)
            
        # 检查是否包含需要蓝色渲染的文本
        while '[[BLUE]]' in html_content and '[[/BLUE]]' in html_content:
            # 应用蓝色格式
            html_content = html_content.replace('[[BLUE]]', f'<span style="{styles["blue"]}">', 1)
            html_content = html_content.replace('[[/BLUE]]', '</span>', 1)
            
        # 检查是否包含需要加粗的标题行
        while '[[BOLD]]' in html_content and '[[/BOLD]]' in html_content:
            # 应用加粗格式
            html_content = html_content.replace('[[BOLD]]', f'<span style="{styles["bold"]}">', 1)
            html_content = html_content.replace('[[/BOLD]]', '</span>', 1)

        # 总是返回完整的HTML结构，确保正确渲染
        # 添加默认的正文样式，确保正文内容左对齐且与其他内容区分
        return f'<html><body style="font-family: Consolas, \'Courier New\', monospace; text-align: left; line-height: 1.2;">{html_content}</body></html>'


class DebugApp(wx.App):
    """调试应用程序类"""
    
    def OnInit(self):
        frame = DebugFrame()
        frame.Show()
        return True


def main():
    """主函数"""
    print("启动数据导出框文本格式调试环境...")
    print("问题描述:")
    print("  当前项目中，数据导出框使用自定义标记语言来格式化文本显示。")
    print("  这些标记包括标题、表格、颜色等，需要正确转换为HTML以便在HtmlWindow中显示。")
    print("  目标是调试这些格式转换逻辑，确保文本正确显示。")
    print("\n预期输出示例:")
    print("  - 标题应居中显示且加粗")
    print("  - 表格应正确渲染，带有边框")
    print("  - 不同颜色的文本应正确显示对应颜色")
    print("  - 居中文本应居中显示")
    print("\n简化输入数据:")
    print("  使用包含各种标记的示例文本进行测试")
    
    app = DebugApp()
    app.MainLoop()


if __name__ == '__main__':
    main()