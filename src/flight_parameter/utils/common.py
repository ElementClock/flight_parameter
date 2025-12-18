#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
公共工具函数模块
==============

包含在整个项目中重复使用的工具函数，避免代码重复。
"""

import logging
import os


def save_as_pdf(pathname, analysis_result):
    """将分析结果保存为PDF文件
    
    Args:
        pathname (str): 保存路径
        analysis_result (str): 分析结果文本
    """
    try:
        import markdown
        from weasyprint import HTML, CSS
        
        # 将自定义标记转换为HTML
        html_text = _convert_custom_markup_to_html_for_export(analysis_result)
        
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
        plain_text = remove_format_markers(analysis_result)
        with open(pathname.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
            f.write(plain_text)
    except Exception as e:
        # 如果PDF生成失败，则回退到文本格式
        logging.warning(f"PDF生成失败: {str(e)}，回退到文本格式")
        plain_text = remove_format_markers(analysis_result)
        with open(pathname.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
            f.write(plain_text)


def remove_format_markers(text):
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


def detect_encoding(filepath, encodings=['utf-8', 'gbk', 'gb2312', 'latin1']):
    """检测文件编码
    
    Args:
        filepath (str): 文件路径
        encodings (list): 尝试的编码列表
        
    Returns:
        str: 检测到的文件编码
        
    Raises:
        Exception: 当无法确定文件编码时抛出异常
    """
    # 检查路径安全性
    if not is_safe_path(os.getcwd(), filepath):
        raise ValueError(f"不允许访问的文件路径: {filepath}")
        
    # 读取文件的前几行进行测试
    # 逐个尝试不同的编码方式，一旦成功读取就返回该编码
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                f.read(1024)  # 读取前1024个字符
            logging.info(f"使用 {encoding} 编码成功读取文件头部")
            return encoding
        except UnicodeDecodeError:
            logging.warning(f"使用 {encoding} 编码读取文件失败")
            continue
        except Exception as e:
            logging.warning(f"使用 {encoding} 编码读取文件时出现其他错误: {str(e)}")
            continue
    raise Exception(f"无法确定文件 {filepath} 的编码")


def is_safe_path(base_path, target_path):
    """检查目标路径是否在基础路径内，防止路径遍历攻击
    
    Args:
        base_path (str): 基础路径
        target_path (str): 目标路径
        
    Returns:
        bool: 如果目标路径在基础路径内返回True，否则返回False
    """
    try:
        base_path = os.path.abspath(base_path)
        target_path = os.path.abspath(target_path)
        return target_path.startswith(base_path)
    except Exception:
        return False


def _convert_custom_markup_to_html_for_export(text):
    """将自定义标记转换为HTML标记用于导出
    
    Args:
        text (str): 包含自定义标记的文本
        
    Returns:
        str: 转换为HTML格式的文本
    """
    try:
        # 导入必要的模块
        from html_generator import HTMLGenerator
        from styles import (
            GLOBAL_CSS, 
            TABLE_STYLE_FIXED,
            TABLE_STYLE_AUTO,
            SMALL_EMPTY_LINE_STYLE
        )
        
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


__all__ = [
    'save_as_pdf',
    'remove_format_markers',
    'detect_encoding',
    'is_safe_path'
]