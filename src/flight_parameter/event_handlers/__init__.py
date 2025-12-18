#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
事件处理器包
==============

处理应用程序中的各种事件，包括数据加载、保存、分析等操作。
使用线程池管理并发任务，确保UI响应性。
"""

# 导入基础类和常量
from .base import BaseEventHandler, MAX_WORKERS, CHUNK_SIZE, MIN_PROCESSING_TIME_THRESHOLD, FILE_READ_BUFFER_SIZE

# 导入所有事件处理器
from .route_visualization import RouteVisualizationHandler
from .data_loading import DataLoaderHandler
from .data_saving import DataSaveHandler
from .analysis_saving import AnalysisSaveHandler
from .data_clearing import DataClearHandler
from .analysis_clearing import AnalysisClearHandler
from .quick_saving import QuickSaveHandler
from .batch_processing import BatchProcessHandler
from .data_selection import DataChoiceHandler
from .closing import CloseHandler

import logging
import wx
from wx import ID_CANCEL, NOT_FOUND

class EventHandlers:
    """事件处理类"""
    
    def __init__(self, app_frame):
        """初始化事件处理器
        
        Args:
            app_frame: 应用程序主窗口实例
        """
        try:
            self.app_frame = app_frame
            
            # 创建各类专门的事件处理器
            self.route_visualization_handler = RouteVisualizationHandler(app_frame)
            self.data_loader_handler = DataLoaderHandler(app_frame)
            self.data_save_handler = DataSaveHandler(app_frame)
            self.analysis_save_handler = AnalysisSaveHandler(app_frame)
            self.data_clear_handler = DataClearHandler(app_frame)
            self.analysis_clear_handler = AnalysisClearHandler(app_frame)
            self.quick_save_handler = QuickSaveHandler(app_frame)
            self.batch_process_handler = BatchProcessHandler(app_frame)  # 添加批量处理处理器
            self.data_choice_handler = DataChoiceHandler(app_frame)
            self.close_handler = CloseHandler(app_frame)
        except Exception as e:
            logging.error(f"初始化事件处理器时出错: {str(e)}")
            raise e
    
    def on_route_visualization(self, event):
        """处理航路点绘制按钮点击事件"""
        self.route_visualization_handler.handle(event)
    
    def load_data(self, event):
        """加载CSV数据文件"""
        self.data_loader_handler.handle(event)
    
    def save_current_data(self, event):
        """保存当前选中的数据"""
        self.data_save_handler.handle(event)
    
    def save_analysis(self, event):
        """保存分析结果"""
        self.analysis_save_handler.handle(event)
    
    def remove_current_data(self, event):
        """清除当前选中的数据"""
        self.data_clear_handler.handle(event)
    
    def remove_analysis(self, event):
        """清除分析数据框信息"""
        self.analysis_clear_handler.handle(event)
    
    def single_button_event_1(self, event):
        """处理单个文件导出按钮点击事件"""
        self.quick_save_handler.handle(event)
    
    def batch_process(self, event):
        """处理批量处理按钮点击事件"""
        self.batch_process_handler.handle(event)
    
    def on_data_choice(self, event):
        """处理数据选择变化事件"""
        self.data_choice_handler.handle(event)
    
    def on_close(self, event):
        """处理窗口关闭事件"""
        self.close_handler.handle(event)

__all__ = [
    'BaseEventHandler',
    'RouteVisualizationHandler', 
    'DataLoaderHandler',
    'DataSaveHandler',
    'AnalysisSaveHandler',
    'DataClearHandler',
    'AnalysisClearHandler',
    'QuickSaveHandler',
    'BatchProcessHandler',
    'DataChoiceHandler',
    'CloseHandler',
    'MAX_WORKERS',
    'CHUNK_SIZE',
    'MIN_PROCESSING_TIME_THRESHOLD',
    'FILE_READ_BUFFER_SIZE'
]