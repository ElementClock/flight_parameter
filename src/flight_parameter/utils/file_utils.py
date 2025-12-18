"""
文件工具模块
"""

import os
import chardet
from typing import Optional, List
import logging
from io import BytesIO
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("reportlab库未安装，PDF生成功能不可用")


def detect_encoding(file_path: str, encodings: List[str] = None) -> str:
    """
    检测文件编码
    
    Args:
        file_path (str): 文件路径
        encodings (List[str], optional): 尝试的编码列表
        
    Returns:
        str: 检测到的编码
    """
    try:
        # 如果提供了编码列表，先尝试这些编码
        if encodings:
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        f.read(1024)  # 只读取一部分内容测试编码
                    return encoding
                except UnicodeDecodeError:
                    continue
        
        # 使用chardet库检测编码
        with open(file_path, 'rb') as f:
            raw_data = f.read(1024)  # 只读取一部分内容以提高性能
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            if encoding is None:
                return 'utf-8'  # 默认编码
            return encoding
    except Exception:
        # 默认返回utf-8
        return 'utf-8'


def read_csv_file(file_path: str, encoding: Optional[str] = None) -> str:
    """
    读取CSV文件内容
    
    Args:
        file_path (str): 文件路径
        encoding (str, optional): 文件编码
        
    Returns:
        str: 文件内容
    """
    if encoding is None:
        encoding = detect_encoding(file_path)
        
    try:
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            return f.read()
    except UnicodeDecodeError:
        # 如果指定编码失败，尝试其他常见编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc, errors='ignore') as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        # 所有编码都失败，抛出异常
        raise


def is_safe_path(base_path: str, user_path: str) -> bool:
    """
    检查路径是否安全，防止路径遍历攻击
    
    Args:
        base_path (str): 基础路径
        user_path (str): 用户提供的路径
        
    Returns:
        bool: 路径是否安全
    """
    try:
        # 规范化路径
        normalized_user_path = os.path.normpath(user_path)
        # 获取绝对路径
        abs_user_path = os.path.abspath(normalized_user_path)
        # 检查是否在基础路径内
        return abs_user_path.startswith(base_path)
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename (str): 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    # 定义非法字符
    illegal_chars = '<>:"/\\|?*'
    # 替换非法字符
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    return filename


def save_as_pdf(output_path: str, content: str):
    """
    将内容保存为PDF文件
    
    Args:
        output_path (str): 输出文件路径
        content (str): 要保存的内容
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("缺少PDF生成库，请安装reportlab")
    
    try:
        # 创建PDF文档
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # 处理内容，按段落分割
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                p = Paragraph(para.strip().replace('\n', '<br/>'), styles['Normal'])
                story.append(p)
        
        # 构建PDF
        doc.build(story)
    except Exception as e:
        logging.error(f"保存PDF时出错: {str(e)}")
        raise


def remove_format_markers(text: str) -> str:
    """
    移除文本中的格式标记
    
    Args:
        text (str): 包含格式标记的文本
        
    Returns:
        str: 移除格式标记后的纯文本
    """
    # 移除常见的格式标记
    formatted_text = text.replace('[BOLD]', '').replace('[/BOLD]', '')
    formatted_text = formatted_text.replace('[ITALIC]', '').replace('[/ITALIC]', '')
    formatted_text = formatted_text.replace('[UNDERLINE]', '').replace('[/UNDERLINE]', '')
    return formatted_text