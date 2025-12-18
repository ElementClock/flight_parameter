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
import markdown
from ..utils.html_utils import HTMLGenerator
from ..resources.styles.style_definitions import (
    GLOBAL_CSS,
    TABLE_CELL_BASE_STYLE,
    TABLE_HEADER_BASE_STYLE,
    ALIGN_LEFT,
    ALIGN_CENTER,
    ALIGN_RIGHT,
    ALIGN_LEFT_HEADER,
    ALIGN_CENTER_HEADER,
    ALIGN_RIGHT_HEADER,
    TABLE_STYLE_FIXED,
    TABLE_STYLE_AUTO,
    EMPTY_LINE_STYLE,
    SMALL_EMPTY_LINE_STYLE,
    ERROR_FALLBACK_STYLE
)


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

    def update_data_choice(self, choices):
        """更新数据选择下拉菜单选项
        
        Args:
            choices (list): 新的选项列表
        """
        try:
            self.data_choice.Clear()
            for choice in choices:
                self.data_choice.Append(choice)
            if choices:
                self.data_choice.SetSelection(0)
        except Exception as e:
            logging.error(f"更新数据选择下拉菜单时出错: {str(e)}")


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
            # 创建HTML生成器实例
            generator = HTMLGenerator()
            
            # 创建文档
            doc = generator.create_document("")
            
            # 添加默认CSS样式
            # generator.add_css(GLOBAL_CSS)
            
            # 处理Markdown标题 (# 标题)
            lines = text.split('\n')
            i = 0
            html_parts = []
            while i < len(lines):
                line = lines[i]
                # 处理Markdown一级标题 (### 标题)
                if line.startswith('### '):
                    # 添加标题
                    title_text = line[4:]  # 去掉 "### "
                    html_parts.append(f'<h3 style="text-align: center;">{title_text}</h3>')
                # 处理Markdown五级标题 (##### 标题)
                elif line.startswith('##### '):
                    # 添加标题
                    title_text = line[6:]  # 去掉 "##### "
                    html_parts.append(f'<h5 style="text-align: center;">{title_text}</h5>')
                # 处理加粗文本 (**文本**)
                elif '**' in line and '|' not in line:
                    # 简单处理加粗文本
                    clean_line = line.replace('**', '<strong>')
                    clean_line = clean_line.replace('</strong><strong>', '')
                    html_parts.append(f'<p>{clean_line}</p>')
                # 处理表格
                elif '|' in line and line.count('|') >= 3 and not line.startswith('#'):
                    # 开始处理表格
                    table_lines = []
                    # 收集连续的表格行
                    while i < len(lines) and '|' in lines[i] and lines[i].count('|') >= 3 and not lines[i].startswith('#'):
                        table_lines.append(lines[i])
                        i += 1
                    i -= 1  # 回退一步，因为主循环还会增加i
                    
                    # 解析表格
                    if len(table_lines) >= 2:  # 至少要有表头和分隔行
                        # 检查是否有自定义列宽设置
                        has_custom_widths = ':::' in table_lines[1]
                        
                        # 移除宽度定义行
                        if has_custom_widths:
                            table_lines.pop(1)
                        
                        # 处理表头
                        header_cells = [cell.strip() for cell in table_lines[0].split('|')]
                        # 移除首尾的空字符串
                        if header_cells[0] == '':
                            header_cells = header_cells[1:]
                        if header_cells and header_cells[-1] == '':
                            header_cells = header_cells[:-1]
                        
                        # 处理表头中的加粗标记
                        formatted_headers = []
                        for cell in header_cells:
                            formatted_cell = cell.replace('**', '<strong>')
                            formatted_cell = formatted_cell.replace('</strong><strong>', '')
                            formatted_headers.append(formatted_cell)
                        
                        # 开始创建表格HTML
                        table_html = '<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">'
                        
                        # 添加表头
                        table_html += '<thead><tr>'
                        for header in formatted_headers:
                            table_html += f'<th style="background-color: #f2f2f2; font-weight: bold;">{header}</th>'
                        table_html += '</tr></thead><tbody>'
                        
                        # 确定数据起始索引
                        data_start_index = 1  # 默认从索引1开始（跳过表头）
                        
                        # 检查第二行是否为分隔行（只包含-和|字符）
                        if len(table_lines) > 1:
                            separator_line = table_lines[1].strip()
                            if all(c in '|-' for c in separator_line):
                                # 这是一个分隔行，需要跳过
                                data_start_index = 2
                        
                        # 处理数据行
                        for row_idx in range(data_start_index, len(table_lines)):
                            row_line = table_lines[row_idx]
                            row_cells = [cell.strip() for cell in row_line.split('|')]
                            # 移除首尾的空字符串
                            if row_cells[0] == '':
                                row_cells = row_cells[1:]
                            if row_cells and row_cells[-1] == '':
                                row_cells = row_cells[:-1]
                            
                            # 处理单元格中的加粗标记和颜色标记
                            formatted_cells = []
                            for cell in row_cells:
                                # 处理加粗文本
                                formatted_cell = cell.replace('**', '<strong>')
                                formatted_cell = formatted_cell.replace('</strong><strong>', '')
                                
                                # 处理颜色标记
                                if '警告级' in formatted_cell:
                                    formatted_cell = formatted_cell.replace('警告级', '<span style="color:red;font-weight:bold;">警告级</span>')
                                elif '戒备级' in formatted_cell:
                                    formatted_cell = formatted_cell.replace('戒备级', '<span style="color:#FFBF00;font-weight:bold;">戒备级</span>')
                                elif '提示级' in formatted_cell:
                                    formatted_cell = formatted_cell.replace('提示级', '<span style="color:blue;font-weight:bold;">提示级</span>')
                            
                                formatted_cells.append(formatted_cell)
                            
                            # 添加表格行
                            table_html += '<tr>'
                            for cell in formatted_cells:
                                table_html += f'<td style="text-align: center;">{cell}</td>'
                            table_html += '</tr>'
                        
                        table_html += '</tbody></table>'
                        html_parts.append(table_html)
                    else:
                        # 不符合表格格式，当作普通文本处理
                        html_parts.append(f'<p>{line}</p>')
                else:
                    # 处理普通文本行
                    if line.strip():  # 只有非空行才添加
                        html_parts.append(f'<p>{line}</p>')
                    else:
                        # 空行添加空白div
                        html_parts.append('<div style="height: 10px;"></div>')
                i += 1
            
            # 组合所有HTML部分
            content = '\n'.join(html_parts)
            
            # 返回生成的HTML
            return generator.create_document(content)
        except Exception as e:
            logging.error(f"转换自定义标记为HTML时出错: {str(e)}")
            # 出错时回退到原来的实现
            return f"<html><body><p>转换错误: {str(e)}</p><pre>{text}</pre></body></html>"
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