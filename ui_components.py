#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI组件模块
==========

定义应用程序的用户界面组件，包括侧边栏、内容区域和右侧边栏等。
"""

import logging
from abc import ABC, abstractmethod

import wx
import wx.html as html

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class UIComponent(ABC):
    """UI组件抽象基类"""
    
    def __init__(self, parent):
        self.parent = parent
        self.panel = None
    
    @abstractmethod
    def create(self):
        """创建UI组件的抽象方法"""
        pass


class ButtonFactory:
    """按钮工厂类"""
    
    @staticmethod
    def create_buttons(parent, button_configs, basic_width, basic_height):
        """创建按钮列表
        
        Args:
            parent: 父窗口
            button_configs: 按钮配置列表
            basic_width: 基础宽度
            basic_height: 基础高度
            
        Returns:
            list: 按钮列表
        """
        buttons = []
        for label, event_handler in button_configs:
            button = wx.Button(parent, label=label)
            button.SetMinSize((basic_width, basic_height * 1.5))
            button.SetMaxSize((basic_width, basic_height * 1.5))

            # 如果提供了事件处理函数，则绑定事件
            if event_handler:
                button.Bind(wx.EVT_BUTTON, event_handler)

            buttons.append(button)
        return buttons


class SidebarPanel(wx.Panel):
    """侧边栏面板类"""
    
    def __init__(self, parent, on_load_data, on_save_data, on_save_analysis, 
                 on_clear_analysis, on_clear_data, on_quick_save, on_separator):
        """初始化侧边栏面板
        
        Args:
            parent: 父窗口
            on_load_data: 加载数据事件处理函数
            on_save_data: 保存数据事件处理函数
            on_save_analysis: 保存分析事件处理函数
            on_clear_analysis: 清除分析事件处理函数
            on_clear_data: 清除数据事件处理函数
            on_quick_save: 快捷保存事件处理函数
            on_separator: 分隔符事件处理函数
        """
        try:
            super().__init__(parent)
            self.data_choice = None
            self.progress_bar = None
            self.progress_text = None
            self.button_factory = ButtonFactory()
            self.create_sidebar(on_load_data, on_save_data, on_save_analysis, 
                               on_clear_analysis, on_clear_data, on_quick_save, on_separator)
        except Exception as e:
            logging.error(f"初始化侧边栏面板时出错: {str(e)}")
            raise e
    
    def create_sidebar(self, on_load_data, on_save_data, on_save_analysis, 
                       on_clear_analysis, on_clear_data, on_quick_save, on_separator):
        """创建侧边栏区域
        
        Args:
            on_load_data: 加载数据事件处理函数
            on_save_data: 保存数据事件处理函数
            on_save_analysis: 保存分析事件处理函数
            on_clear_analysis: 清除分析事件处理函数
            on_clear_data: 清除数据事件处理函数
            on_quick_save: 快捷保存事件处理函数
            on_separator: 分隔符事件处理函数
        """
        try:
            sidebar_sizer = wx.BoxSizer(wx.VERTICAL)

            # 定义基础尺寸单位，根据屏幕尺寸动态计算
            screen_width, screen_height = wx.GetDisplaySize()
            # 修改基础尺寸参数
            basic_width = int(screen_width * 0.1)
            basic_height = int(screen_height * 0.02)

            # 创建标题标签
            logo_label = wx.StaticText(self, label="选择导出模式", style=wx.ALIGN_CENTER)
            font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            logo_label.SetFont(font)
            # 设置标签最小尺寸，确保在窗口缩小时仍可见
            logo_label.SetMinSize((basic_width, basic_height))
            sidebar_sizer.Add(logo_label, 0, wx.ALL | wx.EXPAND, 10)

            # 创建数据选择下拉菜单
            self.data_choice = wx.Choice(self, choices=[])
            self.data_choice.SetMinSize((basic_width, basic_height * 1.5))
            self.data_choice.SetMaxSize((basic_width, basic_height * 1.5))
            # 注意：事件绑定将在主框架中完成
            data_choice_sizer = wx.BoxSizer(wx.HORIZONTAL)
            data_choice_sizer.AddSpacer(20)  # 左边距
            data_choice_sizer.Add(self.data_choice, 1, wx.TOP | wx.BOTTOM, 5)  # 上下边距
            data_choice_sizer.AddSpacer(0)  # 右边距
            sidebar_sizer.Add(data_choice_sizer, 0, wx.EXPAND)

            # 创建按钮布局管理器
            button_sizer = wx.BoxSizer(wx.VERTICAL)

            # 创建按钮
            buttons_config = [
                ("加载数据", on_load_data),
                ("保存数据", on_save_data),
                ("保存分析", on_save_analysis),
                ("清除分析", on_clear_analysis),
                ("清除数据", on_clear_data),
                ("快捷保存", on_quick_save),
                ("批量处理", on_separator),  # 将"///"改为"批量处理"
            ]
            
            buttons = self.button_factory.create_buttons(self, buttons_config, basic_width, basic_height)

            # 添加按钮到布局，不伸缩，居中显示
            for button in buttons:
                button_sizer.Add(button, 0, wx.ALL | wx.CENTER, 5)

            # 添加按钮布局到侧边栏布局，设置合适的比例和最小尺寸
            # 确保按钮区域在窗口缩小时不会被过度压缩
            sidebar_sizer.Add(button_sizer, 1, wx.ALL | wx.EXPAND, 5)

            # 创建进度显示区域 - 放在最底部
            progress_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # 进度文本
            self.progress_text = wx.StaticText(self, label="就绪")
            progress_sizer.Add(self.progress_text, 0, wx.ALL | wx.EXPAND, 5)
            
            # 进度条
            self.progress_bar = wx.Gauge(self, range=100, size=(basic_width, basic_height))
            self.progress_bar.Hide()  # 默认隐藏进度条
            progress_sizer.Add(self.progress_bar, 0, wx.ALL | wx.EXPAND, 5)
            
            sidebar_sizer.Add(progress_sizer, 0, wx.EXPAND)

            # 设置侧边栏面板的布局管理器
            self.SetSizer(sidebar_sizer)

            # 手动计算并设置最小尺寸，确保所有按钮可见
            # 先调用Layout让Sizer计算布局
            sidebar_sizer.Layout()
            # 获取内容所需最小尺寸
            min_size = sidebar_sizer.GetMinSize()
            # 设置侧边栏面板的最小尺寸
            self.SetMinSize(min_size)

            # 可选：手动调整最终最小尺寸
            min_size = sidebar_sizer.GetMinSize()
            # 增加额外的宽高（单位：像素）
            min_size.width += 20
            min_size.height += basic_height * 4
            self.SetMinSize(min_size)
        except Exception as e:
            logging.error(f"创建侧边栏区域时出错: {str(e)}")
            raise e
        
    def show_progress(self, show=True):
        """显示或隐藏进度条"""
        try:
            if show:
                self.progress_bar.Show()
            else:
                self.progress_bar.Hide()
                self.progress_text.SetLabel("就绪")
            self.Layout()
        except Exception as e:
            logging.error(f"显示或隐藏进度条时出错: {str(e)}")
        
    def update_progress(self, value, message=""):
        """更新进度条和进度文本
        
        Args:
            value (int): 进度值(0-100)
            message (str): 进度消息
        """
        try:
            if message:
                self.progress_text.SetLabel(message)
            self.progress_bar.SetValue(value)
            self.Refresh()
            wx.Yield()  # 确保UI更新
        except Exception as e:
            logging.error(f"更新进度条和进度文本时出错: {str(e)}")


class RightSidebarPanel(wx.Panel):
    """右侧边栏面板类"""
    
    def __init__(self, parent):
        """初始化右侧边栏面板
        
        Args:
            parent: 父窗口
        """
        try:
            super().__init__(parent)
            self.create_right_sidebar()
            self.Hide()  # 默认隐藏
        except Exception as e:
            logging.error(f"初始化右侧边栏面板时出错: {str(e)}")
            raise e
        
    def create_right_sidebar(self):
        """创建右侧边栏区域"""
        try:
            right_sidebar_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # 定义基础尺寸单位，与左侧边栏保持一致
            screen_width, screen_height = wx.GetDisplaySize()
            basic_width = int(screen_width * 0.1)
            basic_height = int(screen_height * 0.02)
            
            # 创建标题
            title = wx.StaticText(self, label="工具面板", style=wx.ALIGN_CENTER)
            font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            title.SetFont(font)
            title.SetMinSize((basic_width, basic_height))
            right_sidebar_sizer.Add(title, 0, wx.ALL | wx.EXPAND, 10)
            
            # 添加航路点绘制按钮
            self.route_visualization_button = wx.Button(self, label="航路点绘制")
            self.route_visualization_button.SetMinSize((basic_width, basic_height * 1.5))
            self.route_visualization_button.SetMaxSize((basic_width, basic_height * 1.5))
            right_sidebar_sizer.Add(self.route_visualization_button, 0, wx.ALL | wx.CENTER, 5)
            
            # 添加一些示例内容
            content_text = wx.StaticText(self, label="这里应该设置一些按钮", style=wx.ALIGN_CENTER)
            right_sidebar_sizer.Add(content_text, 0, wx.ALL | wx.EXPAND, 10)
            
            # 设置布局
            self.SetSizer(right_sidebar_sizer)
            
            # 设置最小尺寸，与左侧边栏保持一致
            right_sidebar_sizer.Layout()
            min_size = right_sidebar_sizer.GetMinSize()
            # 增加额外宽度和高度（单位：像素），与左侧边栏保持一致
            min_size.width += 20
            min_size.height += basic_height * 4
            self.SetMinSize(min_size)
        except Exception as e:
            logging.error(f"创建右侧边栏区域时出错: {str(e)}")
            raise e


class ContentPanel(wx.Panel):
    """内容区域面板类"""
    
    def __init__(self, parent):
        """初始化内容区域面板
        
        Args:
            parent: 父窗口
        """
        try:
            super().__init__(parent)
            self.html_window = None
            self.toggle_button = None
            self.create_content_area()
        except Exception as e:
            logging.error(f"初始化内容区域面板时出错: {str(e)}")
            raise e
    
    def create_content_area(self):
        """创建主内容区域"""
        try:
            content_sizer = wx.BoxSizer(wx.VERTICAL)

            # 定义基础尺寸单位
            screen_width, screen_height = wx.GetDisplaySize()
            basic_width = int(screen_width * 0.1)
            basic_height = int(screen_height * 0.02)

            # 创建结果区域标题的水平布局
            title_sizer = wx.BoxSizer(wx.HORIZONTAL)
            
            # 创建结果区域标题
            logo_msg_box = wx.StaticText(self, label="数据导出结果", style=wx.ALIGN_CENTER)
            # 设置字体为等宽字体，便于显示格式化数据
            font = wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            logo_msg_box.SetFont(font)
            # 设置最小尺寸确保可见性
            logo_msg_box.SetMinSize((basic_width, basic_height))
            
            # 创建切换右侧边栏显示的按钮，使用右箭头表示面板当前处于收起状态
            self.toggle_button = wx.Button(self, label="▶", size=(30, -1))
            self.toggle_button.SetMinSize((30, basic_height))
            
            # 添加控件到标题布局
            title_sizer.Add(logo_msg_box, 1, wx.ALIGN_CENTER_VERTICAL)
            title_sizer.Add(self.toggle_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
            
            # 添加标题布局到内容布局
            content_sizer.Add(title_sizer, 0, wx.ALL | wx.EXPAND, 10)

            # 创建HTML显示窗口，用于显示导出结果
            self.html_window = html.HtmlWindow(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
            # 文本框占据剩余空间
            content_sizer.Add(self.html_window, 1, wx.ALL | wx.EXPAND, 5)
            # 设置内容区域最小尺寸
            content_sizer.SetMinSize((3 * basic_width, 10 * basic_height))

            # 设置内容面板的布局管理器
            self.SetSizer(content_sizer)
        except Exception as e:
            logging.error(f"创建主内容区域时出错: {str(e)}")
            raise e
    
    def set_formatted_text(self, text):
        """设置格式化的文本内容
        
        Args:
            text (str): 要显示的文本内容
        """
        try:
            # 将自定义标记转换为HTML标记
            html_text = self.convert_custom_markup_to_html(text)
            # 在HTML窗口中显示内容
            self.html_window.SetPage(html_text)
        except Exception as e:
            # 出现异常时显示原始文本
            logging.error(f"设置格式化文本时出错: {str(e)}")
            self.html_window.SetPage(f"<html>显示文本时出错: {str(e)}<br>原始文本:<br>{text}</html>")
            
    def convert_custom_markup_to_html(self, text):
        """将自定义标记转换为HTML标记
        
        Args:
            text (str): 包含自定义标记的文本
            
        Returns:
            str: 转换为HTML格式的文本
        """
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
            
            # 处理段前段后间距标记
            html_content = html_content.replace('[[PARA_MARGIN]]', '<p style="margin: 1em 0;">')
            html_content = html_content.replace('[[/PARA_MARGIN]]', '</p>')
            
            # 处理专业标题标记 - 只保留段前1行间距，取消段后1行间距
            html_content = html_content.replace('[[TITLE]]', '<br><h3 style="margin: 0; text-align: center; font-weight: bold;">')
            html_content = html_content.replace('[[/TITLE]]', '</h3><br>')
            
            # 处理告警级别标题标记 - 只保留段前1行间距，取消段后1行间距
            html_content = html_content.replace('[[LEVEL_TITLE]]', '<br><h5 style="margin: 0; text-align: center; font-weight: bold;">')
            html_content = html_content.replace('[[/LEVEL_TITLE]]', '</h5><br>')
            
            # 处理居中对齐标记
            html_content = html_content.replace('[[CENTER]]', '<p style="text-align: center;">')
            html_content = html_content.replace('[[/CENTER]]', '</p>')
            
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

            # 总是返回完整的HTML结构，确保正确渲染
            # 添加默认的正文样式，确保正文内容左对齐且与其他内容区分
            return f'<html><body style="font-family: Consolas, \'Courier New\', monospace; text-align: left;">{html_content}</body></html>'
        except Exception as e:
            logging.error(f"转换自定义标记为HTML时出错: {str(e)}")
            return f'<html><body style="font-family: Consolas, \'Courier New\', monospace;"><pre>{text}</pre></body></html>'

    def get_plain_text(self):
        """获取纯文本内容（去除所有格式标记）
        
        Returns:
            str: 纯文本内容
        """
        try:
            # 获取当前显示的文本内容
            text = self.html_window.ToText()
            return text if text else ""
        except Exception as e:
            logging.error(f"获取纯文本时出错: {str(e)}")
            return ""
            
    def GetValue(self):
        """兼容旧接口的方法，用于获取文本内容
        
        Returns:
            str: 纯文本内容
        """
        return self.get_plain_text()

    def SetValue(self, text):
        """兼容旧接口的方法，用于设置文本内容
        
        Args:
            text (str): 要显示的文本内容
        """
        self.set_formatted_text(text)
