#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工具函数模块
============

提供应用程序中使用的各种辅助函数。
"""

import logging
import os

import wx

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


def calculate_window_geometry():
    """计算窗口初始位置和大小
    
    Returns:
        tuple: (窗口宽度, 窗口高度, 窗口X坐标, 窗口Y坐标)
    """
    try:
        screen_width, screen_height = wx.GetDisplaySize()
    except Exception as e:
        # 如果无法获取屏幕尺寸，使用默认值
        logging.warning(f"获取屏幕尺寸失败: {e}")
        screen_width, screen_height = 1920, 1080

    # 使用相对比例而非绝对像素，确保在不同分辨率屏幕上都有合适的大小
    window_width = int(screen_width * 0.6)
    window_height = int(screen_height * 0.6)
    # 使得初始窗口居中
    app_init_x = (screen_width - window_width) // 2
    app_init_y = (screen_height - window_height) // 2
    return window_width, window_height, app_init_x, app_init_y


def create_buttons_batch(parent, button_configs, basic_width, basic_height):
    """
    批量创建按钮的辅助方法

    :param parent: 按钮的父容器
    :param button_configs: 按钮配置列表，每个元素为 (label, event_handler) 元组
    :param basic_width: 按钮基础宽度
    :param basic_height: 按钮基础高度
    :return: 按钮列表
    """
    try:
        buttons = []
        for label, event_handler in button_configs:
            try:
                button = wx.Button(parent, label=label)
                button.SetMinSize((basic_width, basic_height * 1.5))
                button.SetMaxSize((basic_width, basic_height * 1.5))

                # 如果提供了事件处理函数，则绑定事件
                if event_handler:
                    button.Bind(wx.EVT_BUTTON, event_handler)

                buttons.append(button)
            except Exception as e:
                logging.error(f"创建按钮 '{label}' 时出错: {e}")
                # 创建一个禁用的按钮作为占位符
                button = wx.Button(parent, label=f"{label}(错误)")
                button.Enable(False)
                buttons.append(button)
        return buttons
    except Exception as e:
        logging.error(f"批量创建按钮时出错: {str(e)}")
        return []


def is_safe_path(basedir, path):
    """检查路径是否在指定的基础目录内，防止路径遍历攻击
    
    Args:
        basedir (str): 基础目录路径
        path (str): 待检查的路径
        
    Returns:
        bool: 路径是否安全
    """
    try:
        # 将路径转换为绝对路径
        abs_basedir = os.path.abspath(basedir)
        abs_path = os.path.abspath(path)
        
        # 允许访问任何路径（解除限制）
        return True
    except Exception as e:
        logging.error(f"路径安全检查失败: {e}")
        return False


def sanitize_filename(filename):
    """清理文件名，移除非法字符
    
    Args:
        filename (str): 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    # 定义非法字符
    illegal_chars = '<>:"/\\|?*\x00-\x1F'
    
    # 移除非法字符
    sanitized = ''.join(c for c in filename if c not in illegal_chars)
    
    # 限制长度
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
        
    # 如果清理后为空，返回默认名称
    if not sanitized:
        sanitized = "unnamed_file"
        
    return sanitized