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
    # 这里可以添加实际的转换逻辑
    # 目前只是简单示例
    return text


__all__ = [
    'save_as_pdf',
    'remove_format_markers',
    'detect_encoding',
    'is_safe_path'
]