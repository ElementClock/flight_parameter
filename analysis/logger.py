#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分析模块日志工具
==============

提供统一的日志配置和工具函数，用于分析模块中的日志记录。
"""

import logging
import functools
from typing import Callable, Any


def get_analysis_logger(name: str) -> logging.Logger:
    """获取分析模块专用的日志记录器
    
    Args:
        name (str): 日志记录器名称，通常使用模块名
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 如果记录器已经有处理器，直接返回
    if logger.handlers:
        return logger
    
    # 设置日志级别
    logger.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到记录器
    logger.addHandler(console_handler)
    
    return logger


def log_execution(func: Callable) -> Callable:
    """装饰器：记录函数执行过程
    
    Args:
        func (Callable): 被装饰的函数
        
    Returns:
        Callable: 装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        logger = get_analysis_logger(func.__module__)
        logger.info(f"开始执行 {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"完成执行 {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"执行 {func.__name__} 时发生错误: {str(e)}")
            raise
    return wrapper


def log_step(step_name: str) -> Callable:
    """装饰器：记录分析步骤
    
    Args:
        step_name (str): 步骤名称
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_analysis_logger(func.__module__)
            logger.info(f"开始步骤: {step_name}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"完成步骤: {step_name}")
                return result
            except Exception as e:
                logger.error(f"步骤 {step_name} 发生错误: {str(e)}")
                raise
        return wrapper
    return decorator