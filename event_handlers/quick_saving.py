#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快捷保存事件处理器
==============

处理应用程序中的快捷保存事件。
"""

import logging
import os
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import wx

from .base import BaseEventHandler, MAX_WORKERS
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


class QuickSaveHandler(BaseEventHandler):
    """快捷保存事件处理器"""
    
    def __init__(self, app_frame):
        super().__init__(app_frame)
        # 创建线程池
        self.executor = ThreadPoolExecutor(max_workers=1)
        
    def handle(self, event):
        """处理单个文件导出按钮点击事件"""
        try:
            # 获取当前选中的数据容器
            current_container = self.app_frame.data_manager.get_current_data()
            
            if not current_container:
                wx.MessageBox("暂无数据可保存", "提示", wx.OK | wx.ICON_INFORMATION)
                return
            
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
            
            # 生成文件名
            from datetime import datetime
            import os
            
            # 获取原始文件的目录，如果有的话
            if hasattr(current_container, 'original_path') and current_container.original_path:
                save_directory = os.path.dirname(current_container.original_path)
            else:
                # 如果没有原始路径信息，则保存到当前工作目录
                save_directory = os.getcwd()
            
            # 使用飞行数据中的时间作为文件时间部分，而不是系统当前时间
            flight_time = None
            # 尝试从发动机数据获取时间
            if (hasattr(current_container, 'engine_data') and 
                current_container.engine_data):
                flight_time = current_container.engine_data.get('takeoff_start_time')
            
            # 如果发动机数据中没有时间，尝试从数据帧获取
            if flight_time is None and hasattr(current_container, 'df') and current_container.df is not None:
                if '飞行时间' in current_container.df.columns and len(current_container.df) > 0:
                    flight_time = current_container.df['飞行时间'].iloc[0]
            
            # 如果仍然没有时间数据，则使用当前时间
            if flight_time is not None:
                current_time = flight_time.strftime("%Y%m%d")
            else:
                current_time = datetime.now().strftime("%Y%m%d")
                
            default_filename_base = f"{identifier}{current_time}"
            
            # 创建保存数据和分析结果的默认路径
            default_data_filename = f"{default_filename_base}.csv"
            default_analysis_filename = f"{default_filename_base}_分析.pdf"  # 更改为PDF格式
            
            # 构建完整路径
            default_data_path = os.path.join(save_directory, default_data_filename)
            default_analysis_path = os.path.join(save_directory, default_analysis_filename)
            
            try:
                # 检查路径安全性
                if not is_safe_path(os.getcwd(), default_data_path) or not is_safe_path(os.getcwd(), default_analysis_path):
                    wx.MessageBox("不允许保存到指定路径", "错误", wx.OK | wx.ICON_ERROR)
                    return
                
                # 清理文件名
                data_dir = os.path.dirname(default_data_path)
                data_filename = sanitize_filename(os.path.basename(default_data_path))
                default_data_path = os.path.join(data_dir, data_filename)
                
                analysis_dir = os.path.dirname(default_analysis_path)
                analysis_filename = sanitize_filename(os.path.basename(default_analysis_path))
                default_analysis_path = os.path.join(analysis_dir, analysis_filename)
                
                # 使用线程池处理保存操作，避免阻塞UI
                future = self.executor.submit(self._save_files, current_container, default_data_path, default_analysis_path)
                # 注册回调函数处理结果
                future.add_done_callback(self._on_save_complete)
                
                # 显示正在保存的消息
                self.app_frame.content_panel.set_formatted_text("正在保存文件，请稍候...")
                self.app_frame.sidebar_panel.show_progress(True)
                self.app_frame.sidebar_panel.update_progress(50, "正在保存文件...")
                
            except Exception as e:
                logging.error(f"快捷保存时出错: {str(e)}")
                wx.MessageBox(f"快捷保存时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
                
        except Exception as e:
            logging.error(f"处理快捷保存按钮点击事件时出错: {str(e)}")
            wx.MessageBox(f"快捷保存时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            
    def _save_files(self, current_container, data_path, analysis_path):
        """在后台线程中保存文件"""
        try:
            # 保存数据文件
            current_container.df.to_csv(data_path, encoding='utf-8-sig', index=False)
            
            # 保存分析结果为PDF文件
            analysis_result = current_container.get_analysis_result()
            self._save_as_pdf(analysis_path, analysis_result)
            return data_path, analysis_path
        except Exception as e:
            logging.error(f"保存文件时出错: {str(e)}")
            raise e
    
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
            
    def _on_save_complete(self, future):
        """保存完成回调"""
        try:
            data_path, analysis_path = future.result()
            
            # 在UI线程中更新界面
            wx.CallAfter(self._update_ui_after_saving, data_path, analysis_path)
        except Exception as e:
            logging.error(f"处理保存完成回调时出错: {str(e)}")
            wx.CallAfter(
                self._update_ui_after_saving, 
                None, 
                None, 
                f"保存文件时出错: {str(e)}"
            )
            
    def _update_ui_after_saving(self, data_path, analysis_path, error=None):
        """在UI线程中更新界面"""
        try:
            self.app_frame.sidebar_panel.show_progress(False)
            
            if error:
                wx.MessageBox(error, "错误", wx.OK | wx.ICON_ERROR)
                self.app_frame.content_panel.set_formatted_text(f"保存失败: {error}")
            else:
                # 检查是否回退到了TXT格式
                actual_analysis_path = analysis_path
                if not os.path.exists(analysis_path) and os.path.exists(analysis_path.replace('.pdf', '.txt')):
                    actual_analysis_path = analysis_path.replace('.pdf', '.txt')
                    message = f"快捷保存完成！\n注意：由于系统缺少PDF生成组件，分析结果已保存为TXT格式。\n\n数据文件已保存至: {data_path}\n分析结果已保存至: {actual_analysis_path}"
                else:
                    message = f"快捷保存完成！\n\n数据文件已保存至: {data_path}\n分析结果已保存至: {actual_analysis_path}"
                self.app_frame.content_panel.set_formatted_text(message)
                wx.MessageBox(message, "保存成功", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            logging.error(f"更新界面时出错: {str(e)}")