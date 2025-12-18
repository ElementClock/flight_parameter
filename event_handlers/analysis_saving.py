#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分析结果保存事件处理器
==============

处理应用程序中的分析结果保存事件。
"""

import logging
import os
import re
from datetime import datetime

import wx

from .base import BaseEventHandler
from html_generator import HTMLGenerator
from styles import GLOBAL_CSS, TABLE_STYLE_FIXED, TABLE_STYLE_AUTO, SMALL_EMPTY_LINE_STYLE
from utils import is_safe_path, sanitize_filename

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class AnalysisSaveHandler(BaseEventHandler):
    """分析结果保存事件处理器"""
    
    def handle(self, event):
        """保存分析结果"""
        try:
            current_container = self.app_frame.data_manager.get_current_data()
            if current_container:
                # 确定文件标识符 (F: 飞行架次, D: 地面试车, N: 未开车)
                identifier = "N"  # 默认为未开车
                if (hasattr(current_container, 'engine_data') and 
                    current_container.engine_data and 
                    current_container.engine_data.get('has_takeoff_info')):
                    # 检查是否有起飞信息来判断是飞行还是地面试验
                    start_time = current_container.engine_data.get('takeoff_start_time')
                    end_time = current_container.engine_data.get('takeoff_end_time')
                    
                    # 如果有明确的开关车时间，则认为是地面试验开车
                    if start_time and end_time:
                        identifier = "D"
                        
                        # 进一步检查是否是飞行架次（简单判断：持续时间超过一定阈值）
                        try:
                            duration = end_time - start_time
                            # 如果发动机运行时间超过10分钟，认为是飞行架次
                            if duration.total_seconds() > 600:
                                identifier = "F"
                        except:
                            pass
                
                # 生成默认文件名
                import os
                
                # 使用当前时间作为文件时间部分
                current_time = datetime.now().strftime("%Y%m%d")
                default_filename_base = f"{identifier}{current_time}"
                default_analysis_filename = f"{default_filename_base}_分析.pdf"  # 更改为PDF扩展名
                
                # 获取原始文件的目录，如果有的话
                if hasattr(current_container, 'original_path') and current_container.original_path:
                    save_directory = os.path.dirname(current_container.original_path)
                else:
                    # 如果没有原始路径信息，则保存到当前工作目录
                    save_directory = os.getcwd()
                
                # 构建完整默认路径
                default_analysis_path = os.path.join(save_directory, default_analysis_filename)
                
                with wx.FileDialog(
                    self.app_frame,
                    message="保存分析结果",
                    defaultFile=default_analysis_path,  # 预填充默认文件名和路径
                    wildcard="PDF文件 (*.pdf)|*.pdf|Markdown文件 (*.md)|*.md|文本文件 (*.txt)|*.txt",
                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                ) as fileDialog:
                    if fileDialog.ShowModal() == wx.ID_CANCEL:
                        return

                    pathname = fileDialog.GetPath()
                    
                    # 检查路径安全性
                    if not is_safe_path(os.getcwd(), pathname):
                        wx.MessageBox("不允许保存到指定路径", "错误", wx.OK | wx.ICON_ERROR)
                        return
                    
                    # 清理文件名
                    dir_name = os.path.dirname(pathname)
                    file_name = sanitize_filename(os.path.basename(pathname))
                    pathname = os.path.join(dir_name, file_name)
                    
                    # 确保目录存在
                    os.makedirs(os.path.dirname(pathname) or '.', exist_ok=True)
                    
                    try:
                        # 获取当前数据容器中的分析结果
                        analysis_result = current_container.get_analysis_result()
                        
                        # 根据文件扩展名决定保存格式
                        if pathname.endswith('.pdf'):
                            self._save_as_pdf(pathname, analysis_result)
                        elif pathname.endswith('.md'):
                            self._save_as_markdown(pathname, analysis_result)
                        else:  # 默认为文本格式
                            if not pathname.endswith('.txt'):
                                pathname += '.txt'
                            # 从当前数据容器中获取分析结果，并去除格式标记
                            plain_text = self.remove_format_markers(analysis_result)
                            with open(pathname, 'w', encoding='utf-8') as f:
                                f.write(plain_text)
                        
                        self.app_frame.content_panel.set_formatted_text(f"分析结果已保存至: {pathname}")
                    except Exception as e:
                        logging.error(f"保存分析结果时出错: {str(e)}")
                        wx.MessageBox(f"保存文件时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            else:
                wx.MessageBox("暂无分析数据可保存", "提示", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            logging.error(f"保存分析结果时出错: {str(e)}")
            wx.MessageBox(f"保存分析结果时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            
    def _save_as_pdf(self, pathname, analysis_result):
        """将分析结果保存为PDF文件
        
        Args:
            pathname (str): 保存路径
            analysis_result (str): 分析结果文本
        """
        try:
            import markdown
            from weasyprint import HTML, CSS
            
            # 将自定义标记转换为HTML
            html_text = self._convert_custom_markup_to_html_for_export(analysis_result)
            
            # 使用markdown转换为HTML
            html = markdown.markdown(html_text)
            
            # 添加基本样式
            css = CSS(string='''
                body { font-family: "Microsoft YaHei", sans-serif; }
                h3 { text-align: center; margin: 1em 0; }
                table { border-collapse: collapse; width: 100%; margin: 1em 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .red { color: red; }
                .amber { color: #FFBF00; font-weight: bold; }
                .bold { font-weight: bold; }
            ''')
            
            # 生成PDF
            HTML(string=html).write_pdf(pathname, stylesheets=[css])
        except ImportError as e:
            # 如果缺少依赖库，则回退到文本格式
            logging.warning(f"缺少PDF生成库: {str(e)}，回退到文本格式")
            plain_text = self.remove_format_markers(analysis_result)
            with open(pathname.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
                f.write(plain_text)
        except Exception as e:
            # 如果PDF生成失败，则回退到文本格式
            logging.warning(f"PDF生成失败: {str(e)}，回退到文本格式")
            plain_text = self.remove_format_markers(analysis_result)
            with open(pathname.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
                f.write(plain_text)
                
    def remove_format_markers(self, text):
        """移除文本中的格式标记
        
        Args:
            text (str): 包含格式标记的文本
            
        Returns:
            str: 移除格式标记后的纯文本
        """
        try:
            import re
            # 移除所有格式标记，如 **文本**
            clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            # 移除标题标记
            clean_text = clean_text.replace('### ', '').replace('##### ', '')
            return clean_text
        except Exception as e:
            logging.error(f"移除格式标记时出错: {str(e)}")
            return text
            
    def _save_as_markdown(self, pathname, analysis_result):
        """将分析结果保存为Markdown文件
        
        Args:
            pathname (str): 保存路径
            analysis_result (str): 分析结果文本
        """
        try:
            # 将自定义标记转换为Markdown
            markdown_text = self._convert_custom_markup_to_markdown(analysis_result)
            
            with open(pathname, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
        except Exception as e:
            logging.error(f"保存Markdown时出错: {str(e)}")
            raise e
            
    def _convert_custom_markup_to_html_for_export(self, text):
        """将自定义标记转换为HTML标记用于导出
        
        Args:
            text (str): 包含自定义标记的文本
            
        Returns:
            str: 转换为HTML格式的文本
        """
        try:
            # 创建HTML生成器实例
            generator = HTMLGenerator()
            
            # 创建文档
            doc = generator.create_document()
            
            # 添加默认CSS样式
            generator.add_css(GLOBAL_CSS)
            
            # 处理表格标记
            lines = text.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i]
                # 处理表格
                if line.startswith('|') and line.endswith('|') and line.count('|') >= 3:
                    # 开始处理表格
                    table_lines = []
                    # 收集连续的表格行
                    while i < len(lines) and lines[i].startswith('|') and lines[i].endswith('|') and lines[i].count('|') >= 3:
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
                        generator.start_table(style=table_style, css_class="export-table")
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
                    else:
                        # 不符合表格格式，当作普通文本处理
                        generator.add_paragraph(line)
                # 处理标题
                elif line.startswith('### '):
                    generator.add_title(line[4:], level=3)
                elif line.startswith('##### '):
                    generator.add_title(line[6:], level=5)
                # 处理加粗文本
                elif '**' in line:
                    # 简单处理加粗文本，后续可以增强
                    clean_line = line.replace('**', '<strong>')
                    clean_line = clean_line.replace('</strong><strong>', '')
                    generator.add_paragraph(clean_line)
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
            return text
            
    def _convert_custom_markup_to_markdown(self, text):
        """将自定义标记转换为Markdown标记
        
        Args:
            text (str): 包含自定义标记的文本
            
        Returns:
            str: 转换为Markdown格式的文本
        """
        try:
            # 对于已经是Markdown格式的文本，直接返回
            return text
        except Exception as e:
            logging.error(f"转换自定义标记为Markdown时出错: {str(e)}")
            return text