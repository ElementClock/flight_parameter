#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分析结果样式调试器
==================

这是一个独立的调试工具，用于快速测试和调试飞行参数分析结果的样式显示效果。
通过使用真实的测试数据文件，可以直接查看各种样式在UI中的表现效果。

使用方法:
1. 运行此脚本: python analysis_result_style_debugger.py
2. 在弹出的窗口中查看各种分析结果的样式效果
3. 修改样式相关代码后重新运行以查看效果变化
"""

import wx
import wx.html as html
import pandas as pd
from datetime import datetime
import sys
import os
import json
import hashlib
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis.data_analyzer import DataAnalyzer
from data_manager import DataContainer
from html_generator import HTMLGenerator
from styles import (
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


class StyleDebuggerFrame(wx.Frame):
    """样式调试窗口类"""
    
    def __init__(self):
        super().__init__(None, title="分析结果样式调试器", size=(1000, 700))
        self.cache_file = "analysis_result_cache.json"
        self.init_ui()
        self.load_or_generate_analysis_result()
        
    def init_ui(self):
        """初始化用户界面"""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建标题
        title = wx.StaticText(panel, label="分析结果样式调试器")
        font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(font)
        sizer.Add(title, 0, wx.ALL | wx.CENTER, 10)
        
        # 创建说明文本
        description = wx.StaticText(panel, label="此工具用于调试各种分析结果的样式显示效果")
        sizer.Add(description, 0, wx.ALL | wx.CENTER, 5)
        
        # 创建按钮区域
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.test_all_button = wx.Button(panel, label="显示全部分析结果")
        self.test_all_button.Bind(wx.EVT_BUTTON, self.on_test_all)
        button_sizer.Add(self.test_all_button, 0, wx.ALL, 5)
        
        self.test_engine_button = wx.Button(panel, label="显示发动机分析结果")
        self.test_engine_button.Bind(wx.EVT_BUTTON, self.on_test_engine)
        button_sizer.Add(self.test_engine_button, 0, wx.ALL, 5)
        
        self.test_fuel_button = wx.Button(panel, label="显示燃油分析结果")
        self.test_fuel_button.Bind(wx.EVT_BUTTON, self.on_test_fuel)
        button_sizer.Add(self.test_fuel_button, 0, wx.ALL, 5)
        
        self.test_power_button = wx.Button(panel, label="显示电源分析结果")
        self.test_power_button.Bind(wx.EVT_BUTTON, self.on_test_power)
        button_sizer.Add(self.test_power_button, 0, wx.ALL, 5)
        
        self.test_cas_button = wx.Button(panel, label="显示CAS分析结果")
        self.test_cas_button.Bind(wx.EVT_BUTTON, self.on_test_cas)
        button_sizer.Add(self.test_cas_button, 0, wx.ALL, 5)
        
        self.clear_button = wx.Button(panel, label="清空")
        self.clear_button.Bind(wx.EVT_BUTTON, self.on_clear)
        button_sizer.Add(self.clear_button, 0, wx.ALL, 5)
        
        # 添加重新加载按钮
        self.reload_button = wx.Button(panel, label="重新加载数据")
        self.reload_button.Bind(wx.EVT_BUTTON, self.on_reload)
        button_sizer.Add(self.reload_button, 0, wx.ALL, 5)
        
        # 添加导出按钮
        self.export_button = wx.Button(panel, label="导出HTML")
        self.export_button.Bind(wx.EVT_BUTTON, self.on_export)
        button_sizer.Add(self.export_button, 0, wx.ALL, 5)
        
        sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 5)
        
        # 创建HTML显示窗口
        self.html_window = html.HtmlWindow(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
        sizer.Add(self.html_window, 1, wx.ALL | wx.EXPAND, 10)
        
        panel.SetSizer(sizer)
        
    def load_or_generate_analysis_result(self):
        """加载或生成分析结果"""
        # 查找测试数据文件
        test_data_paths = [
            "test_data/20250930050159_00_001_Phy.csv",
            "20250930050159_00_001_Phy.csv",
            "../test_data/20250930050159_00_001_Phy.csv"
        ]
        
        data_file_path = None
        for path in test_data_paths:
            if os.path.exists(path):
                data_file_path = path
                break
                
        if data_file_path is None:
            # 如果找不到测试数据文件，创建模拟数据
            wx.MessageBox("未找到测试数据文件 20250930050159_00_001_Phy.csv，将使用模拟数据", "警告", wx.OK | wx.ICON_WARNING)
            self.generate_sample_data()
            return
            
        # 检查缓存
        if self.is_cache_valid(data_file_path):
            try:
                self.load_from_cache()
                wx.MessageBox("已从缓存加载分析结果", "信息", wx.OK | wx.ICON_INFORMATION)
                return
            except Exception as e:
                logging.error(f"加载缓存失败: {e}")
        
        # 加载并分析数据
        try:
            # 读取真实的测试数据文件
            self.sample_df = pd.read_csv(data_file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                self.sample_df = pd.read_csv(data_file_path, encoding='gbk')
            except UnicodeDecodeError:
                self.sample_df = pd.read_csv(data_file_path, encoding='latin1')
        
        # 创建数据容器
        self.data_container = DataContainer(self.sample_df, "20250930050159_00_001_Phy.csv")
        
        # 进行分析
        analyzer = DataAnalyzer()
        self.analysis_result = analyzer.analyze(self.sample_df)
        
        # 将分析结果存储到数据容器中
        self.data_container.analysis_result = self.format_analysis_result(self.analysis_result)
        
        # 保存到缓存
        self.save_to_cache(data_file_path)
        
        wx.MessageBox(f"成功加载并分析测试数据文件: {data_file_path}", "信息", wx.OK | wx.ICON_INFORMATION)
        
    def is_cache_valid(self, data_file_path):
        """检查缓存是否有效"""
        if not os.path.exists(self.cache_file):
            return False
            
        if not os.path.exists(data_file_path):
            return False
            
        try:
            # 检查文件修改时间
            cache_mtime = os.path.getmtime(self.cache_file)
            data_mtime = os.path.getmtime(data_file_path)
            
            if data_mtime > cache_mtime:
                return False
                
            # 检查缓存内容
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # 检查是否包含必要的字段
            required_fields = ['data_file', 'analysis_results']
            for field in required_fields:
                if field not in cache_data:
                    return False
                    
            return True
        except Exception as e:
            logging.error(f"检查缓存有效性时出错: {e}")
            return False
        
    def load_from_cache(self):
        """从缓存加载分析结果"""
        with open(self.cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            
        # 重建分析结果对象
        self.analysis_result = type('AnalysisResult', (), {})()
        analysis_results = cache_data['analysis_results']
        
        # 恢复各个分析结果
        self.analysis_result.text_engine = analysis_results.get('text_engine', '')
        self.analysis_result.text_fuel = analysis_results.get('text_fuel', '')
        self.analysis_result.text_power = analysis_results.get('text_power', '')
        self.analysis_result.text_cas = analysis_results.get('text_cas', '')
        
        # 创建数据容器
        self.data_container = DataContainer(None, "20250930050159_00_001_Phy.csv")
        self.data_container.analysis_result = self.format_analysis_result(self.analysis_result)
        
    def save_to_cache(self, data_file_path):
        """保存分析结果到缓存"""
        # 准备缓存数据
        cache_data = {
            'data_file': data_file_path,
            'data_file_mtime': os.path.getmtime(data_file_path),
            'analysis_results': {
                'text_engine': getattr(self.analysis_result, 'text_engine', ''),
                'text_fuel': getattr(self.analysis_result, 'text_fuel', ''),
                'text_power': getattr(self.analysis_result, 'text_power', ''),
                'text_cas': getattr(self.analysis_result, 'text_cas', '')
            }
        }
        
        # 保存到文件
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
    def generate_sample_data(self):
        """生成示例数据用于测试（当真实数据不可用时）"""
        # 创建示例数据框
        data = {
            '飞行时间': pd.date_range(start='2025-09-30 05:01:00', periods=100, freq='S'),
            '发动机1转速': [6000 + i*10 for i in range(100)],
            '发动机1温度': [800 + i for i in range(100)],
            '燃油箱1油量': [1000 - i*5 for i in range(100)],
            '电源汇流条1电压': [28.0 + i*0.1 for i in range(100)],
            '显示告警系统1': ['无' for _ in range(100)]
        }
        
        # 在某些时间点添加告警
        for i in range(20, 25):
            data['显示告警系统1'][i] = '发动机超温'
            
        for i in range(50, 55):
            data['显示告警系统1'][i] = '燃油低压'
        
        self.sample_df = pd.DataFrame(data)
        
        # 创建数据容器
        self.data_container = DataContainer(self.sample_df, "20250930050159_00_001_Phy.csv")
        
        # 进行分析
        analyzer = DataAnalyzer()
        self.analysis_result = analyzer.analyze(self.sample_df)
        
        # 将分析结果存储到数据容器中
        self.data_container.analysis_result = self.format_analysis_result(self.analysis_result)
        
    def format_analysis_result(self, analysis_result):
        """格式化分析结果"""
        text_parts = []
        
        # 添加各个分析模块的结果
        if hasattr(analysis_result, 'text_engine') and analysis_result.text_engine:
            text_parts.append(analysis_result.text_engine)
        if hasattr(analysis_result, 'text_fuel') and analysis_result.text_fuel:
            text_parts.append(analysis_result.text_fuel)
        if hasattr(analysis_result, 'text_power') and analysis_result.text_power:
            text_parts.append(analysis_result.text_power)
        if hasattr(analysis_result, 'text_cas') and analysis_result.text_cas:
            text_parts.append(analysis_result.text_cas)
            
        return "\n\n".join(text_parts) if text_parts else "无分析结果"
        
    def on_test_all(self, event):
        """显示全部分析结果"""
        self.display_result(self.data_container.analysis_result)
        
    def on_test_engine(self, event):
        """显示发动机分析结果"""
        result = getattr(self.analysis_result, 'text_engine', '无发动机分析结果')
        self.display_result(result)
        
    def on_test_fuel(self, event):
        """显示燃油分析结果"""
        result = getattr(self.analysis_result, 'text_fuel', '无燃油分析结果')
        self.display_result(result)
        
    def on_test_power(self, event):
        """显示电源分析结果"""
        result = getattr(self.analysis_result, 'text_power', '无电源分析结果')
        self.display_result(result)
        
    def on_test_cas(self, event):
        """显示CAS分析结果"""
        result = getattr(self.analysis_result, 'text_cas', '无CAS分析结果')
        self.display_result(result)
        
    def on_clear(self, event):
        """清空显示内容"""
        self.html_window.SetPage("")
        
    def on_reload(self, event):
        """重新加载数据"""
        # 删除缓存文件
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
            
        # 重新加载数据
        self.load_or_generate_analysis_result()
        
    def on_export(self, event):
        """导出当前显示内容为HTML文件"""
        try:
            # 获取当前显示的HTML内容
            html_content = self.html_window.GetOpenedPage() or self.html_window.GetParser().GetInnerXml()
            
            # 如果无法获取内容，则使用ToText方法获取文本
            if not html_content:
                html_content = self.html_window.ToText()
                # 如果是纯文本，包装成完整的HTML
                if html_content and not html_content.strip().startswith('<'):
                    html_content = f"<html><body>{html_content}</body></html>"
            
            # 打开文件保存对话框
            with wx.FileDialog(
                self,
                message="保存HTML文件",
                wildcard="HTML文件 (*.html)|*.html",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            ) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return
                    
                pathname = fileDialog.GetPath()
                
                # 保存HTML内容到文件
                with open(pathname, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                    
                wx.MessageBox(f"已成功导出到: {pathname}", "导出成功", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            logging.error(f"导出HTML时出错: {e}")
            wx.MessageBox(f"导出失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
        
    def display_result(self, text):
        """显示结果文本"""
        # 这里使用与ui_components.py中相同的转换逻辑
        html_text = self.convert_custom_markup_to_html(text)
        self.html_window.SetPage(html_text)
        
    def convert_custom_markup_to_html(self, text):
        """将自定义标记转换为HTML标记（与ui_components.py中相同）"""
        try:
            # 创建HTML生成器实例
            generator = HTMLGenerator()
            
            # 创建文档
            doc = generator.create_document()
            
            # 添加默认CSS样式
            generator.add_css(GLOBAL_CSS)
            
            # 处理Markdown标题 (# 标题)
            lines = text.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i]
                # 处理Markdown一级标题 (### 标题)
                if line.startswith('### '):
                    generator.add_title(line[4:], level=3, center=True)
                # 处理Markdown五级标题 (##### 标题)
                elif line.startswith('##### '):
                    generator.add_title(line[6:], level=5, center=True)
                # 处理加粗文本 (**文本**)
                elif '**' in line and not '|' in line:
                    # 简单处理加粗文本，后续可以增强
                    clean_line = line.replace('**', '<strong>')
                    clean_line = clean_line.replace('</strong><strong>', '')
                    generator.add_paragraph(clean_line)
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
                        widths = None
                        
                        if has_custom_widths:
                            # 解析自定义列宽
                            width_line = table_lines[1]
                            widths = []
                            width_parts = width_line.split('|')
                            # 移除首尾的空字符串
                            if width_parts[0] == '':
                                width_parts = width_parts[1:]
                            if width_parts and width_parts[-1] == '':
                                width_parts = width_parts[:-1]
                            
                            for part in width_parts:
                                part = part.strip()
                                if part.startswith(':::') and part.endswith(':::'):
                                    try:
                                        width_percent = float(part[3:-3])
                                        widths.append(width_percent)
                                    except ValueError:
                                        widths.append(None)
                                else:
                                    widths.append(None)
                            
                            # 移除宽度定义行
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
                        
                        # 开始创建表格
                        table_style = TABLE_STYLE_FIXED if has_custom_widths else TABLE_STYLE_AUTO
                        generator.start_table(style=table_style, css_class="analysis-table")
                        generator.add_table_header(formatted_headers, widths)
                        generator.start_table_body()
                        
                        # 确定数据起始索引
                        data_start_index = 1  # 默认从索引1开始（跳过表头）
                        
                        # 检查第二行是否为分隔行（只包含-和|字符）
                        if len(table_lines) > 1:
                            separator_line = table_lines[1].strip()
                            if all(c in '|-' for c in separator_line):
                                # 这是一个分隔行，需要跳过
                                data_start_index = 2
                            elif has_custom_widths:
                                # 这是宽度定义行，已经在前面移除了，所以数据从索引1开始
                                data_start_index = 1
                            else:
                                # 这是数据行，数据从索引1开始
                                data_start_index = 1
                        
                        # 检查是否是CAS告警表格（第一列应该是"告警名称"）
                        is_cas_table = len(header_cells) >= 3 and header_cells[0] == "告警名称" and header_cells[1] == "时间" and header_cells[2] == "持续时间"
                        
                        # 处理数据行
                        for row_idx in range(data_start_index, len(table_lines)):
                            row_line = table_lines[row_idx]
                            row_cells = [cell.strip() for cell in row_line.split('|')]
                            # 移除首尾的空字符串
                            if row_cells[0] == '':
                                row_cells = row_cells[1:]
                            if row_cells and row_cells[-1] == '':
                                row_cells = row_cells[:-1]
                            
                            # 处理单元格中的加粗标记
                            formatted_cells = []
                            for cell in row_cells:
                                formatted_cell = cell.replace('**', '<strong>')
                                formatted_cell = formatted_cell.replace('</strong><strong>', '')
                                formatted_cells.append(formatted_cell)
                            
                            # 对于CAS告警表格，第一列（告警名称）左对齐，其余居中对齐
                            if is_cas_table:
                                generator.add_table_row(formatted_cells, "left")
                            else:
                                generator.add_table_row(formatted_cells, "center")
                        
                        generator.end_table()
                        
                        # 在表格后添加一行空白
                        generator.add_raw_html(EMPTY_LINE_STYLE)
                    else:
                        # 不符合表格格式，当作普通文本处理
                        generator.add_paragraph(line)
                else:
                    # 处理普通文本行
                    if line.strip():  # 只有非空行才添加
                        generator.add_paragraph(line)
                    else:
                        # 空行添加空白div
                        generator.add_raw_html(SMALL_EMPTY_LINE_STYLE)
                i += 1
            
            # 返回生成的HTML
            return generator.get_html()
        except Exception as e:
            logging.error(f"转换自定义标记为HTML时出错: {str(e)}")
            # 出错时回退到原来的实现
            return ERROR_FALLBACK_STYLE.format(text=text)


class StyleDebuggerApp(wx.App):
    """样式调试应用程序类"""
    
    def OnInit(self):
        frame = StyleDebuggerFrame()
        frame.Show()
        return True


def main():
    """主函数"""
    print("启动分析结果样式调试器...")
    print("此工具用于调试飞行参数分析结果的样式显示效果")
    print("\n功能说明:")
    print("  - 显示全部分析结果: 显示所有专业的分析结果")
    print("  - 显示各专业结果: 单独显示某一专业的分析结果")
    print("  - 清空: 清除当前显示内容")
    print("  - 重新加载数据: 强制重新加载并分析数据（忽略缓存）")
    print("  - 导出HTML: 将当前显示内容导出为HTML文件")
    
    app = StyleDebuggerApp()
    app.MainLoop()


if __name__ == '__main__':
    main()