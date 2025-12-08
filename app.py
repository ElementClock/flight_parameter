#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
飞行参数分析工具主程序
====================

飞行参数分析工具是一个专为航空工程技术人员和飞行数据分析人员设计的桌面应用程序，
用于快速处理和分析飞行数据并生成专业报告。

主要功能:
- 数据加载与管理：支持CSV格式文件多文件加载，自动识别编码（UTF-8、GBK等）
- 发动机参数分析：识别启动/关车时间、转速变化、点火状态、起飞时间段
- CAS告警分析：识别告警时间段、类型及持续时间统计
- 结果展示与交互：图形化界面实时显示结果，支持多文件切换查看
- 数据导出功能：可将分析结果保存为文本文件，原始数据导出为CSV
- 用户体验优化：高DPI适配、自适应窗口、多线程防卡顿、友好错误提示
"""

import ctypes
import logging
import os
import sys
from abc import ABC, abstractmethod

import wx

# 项目模块导入
from data_manager import DataManager
from event_handlers import EventHandlers
from ui_components import SidebarPanel, ContentPanel, RightSidebarPanel
from utils import calculate_window_geometry

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class UIFactory(ABC):
    """UI工厂抽象基类"""
    
    @abstractmethod
    def create_sidebar(self, parent, event_handlers):
        pass
    
    @abstractmethod
    def create_content_area(self, parent):
        pass
    
    @abstractmethod
    def create_right_sidebar(self, parent):
        pass


class DefaultUIFactory(UIFactory):
    """默认UI工厂实现"""
    
    def create_sidebar(self, parent, event_handlers):
        """创建侧边栏区域"""
        return SidebarPanel(
            parent,
            on_load_data=event_handlers.load_data,
            on_save_data=event_handlers.save_current_data,
            on_save_analysis=event_handlers.save_analysis,
            on_clear_analysis=event_handlers.remove_analysis,
            on_clear_data=event_handlers.remove_current_data,
            on_quick_save=event_handlers.single_button_event_1,
            on_separator=event_handlers.single_button_event_1
        )
    
    def create_content_area(self, parent):
        """创建主内容区域"""
        return ContentPanel(parent)
    
    def create_right_sidebar(self, parent):
        """创建右侧边栏区域"""
        return RightSidebarPanel(parent)


class AppFrame(wx.Frame):
    """应用程序主窗口类"""

    # 展开模式：0=向内展开(压缩内容区域)，1=向外展开(窗口扩展)
    EXPAND_MODE = 0

    def __init__(self, parent=None, title="飞行参数分析工具", ui_factory=None):
        """初始化应用程序窗口
        
        Args:
            parent: 父窗口，默认为None
            title: 窗口标题，默认为"飞行参数分析工具"
            ui_factory: UI工厂实例，用于创建UI组件
        """
        try:
            # 启用高DPI支持，确保在高分辨率屏幕上正确显示
            if hasattr(wx, 'EnableHighDPIAware'):
                wx.EnableHighDPIAware()
            try:
                # 2表示PerMonitorV2，支持每个监视器的DPI设置
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except (AttributeError, OSError) as e:
                # 在不支持PerMonitorV2的系统上降级处理
                logging.warning(f"设置高DPI感知失败: {e}")

            # 自动按比例获取窗口大小
            width, height, app_init_x, app_init_y = calculate_window_geometry()
            # 初始化窗口
            super().__init__(parent, title=title, size=(width, height), pos=(app_init_x, app_init_y))

            # 获取打包后的资源路径
            if getattr(sys, 'frozen', False):
                # 如果是打包后的可执行文件
                base_path = sys._MEIPASS
            else:
                # 如果是源代码运行
                base_path = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_path, 'app_icon.ico')

            # 设置应用程序图标
            if os.path.exists(icon_path):
                try:
                    self.SetIcon(wx.Icon(icon_path, wx.BITMAP_TYPE_ICO))
                except Exception as e:
                    logging.warning(f"设置图标失败: {e}")
            else:
                logging.warning(f"图标文件未找到: {icon_path}")

            # 创建主面板
            self.panel = wx.Panel(self)

            # 创建数据管理器
            self.data_manager = DataManager()

            # 创建事件处理器
            self.event_handlers = EventHandlers(self)

            # 设置UI工厂
            self.ui_factory = ui_factory or DefaultUIFactory()

            # 创建UI界面
            self.create_ui()

            # 设置窗口最小尺寸，防止用户将窗口缩得太小
            min_size = self.main_sizer.GetMinSize()
            self.SetMinSize(min_size)

            # 绑定窗口关闭事件
            self.Bind(wx.EVT_CLOSE, self.event_handlers.on_close)
        except Exception as e:
            logging.error(f"初始化应用程序窗口时出错: {str(e)}")
            raise e

    def create_ui(self):
        """创建用户界面"""
        try:
            # 创建主布局管理器，采用水平布局
            self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)

            # 创建侧边栏面板和内容区域
            self.create_sidebar()
            self.create_content_area()
            self.create_right_sidebar()

            # 将侧边栏、内容区域和右侧边栏添加到主布局
            # 侧边栏不伸缩（proportion=0），内容区域占据剩余空间（proportion=1）
            self.main_sizer.Add(self.sidebar_panel, 0, wx.EXPAND)
            self.main_sizer.Add(self.content_panel, 1, wx.EXPAND)
            self.main_sizer.Add(self.right_sidebar_panel, 0, wx.EXPAND)

            # 设置主面板的布局管理器
            self.panel.SetSizer(self.main_sizer)
            # 调整窗口大小以适应内容
            self.main_sizer.Fit(self.panel)
            
            # 绑定鼠标滚轮事件以自定义滚动速度
            self.content_panel.textbox.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)

            # 计算右侧边栏的宽度
            self.right_sidebar_panel.Show()  # 临时显示以计算尺寸
            self.main_sizer.Layout()
            self.right_sidebar_width = self.right_sidebar_panel.GetSize().width
            self.right_sidebar_panel.Hide()  # 恢复隐藏状态
            self.main_sizer.Layout()
            
            # 初始化按钮标签
            self.update_toggle_button_label()
        except Exception as e:
            logging.error(f"创建用户界面时出错: {str(e)}")
            raise e

    def create_sidebar(self):
        """创建侧边栏区域"""
        try:
            # 使用工厂创建侧边栏
            self.sidebar_panel = self.ui_factory.create_sidebar(self.panel, self.event_handlers)
            
            # 绑定数据选择事件
            self.sidebar_panel.data_choice.Bind(wx.EVT_CHOICE, self.event_handlers.on_data_choice)
        except Exception as e:
            logging.error(f"创建侧边栏区域时出错: {str(e)}")
            raise e

    def create_content_area(self):
        """创建主内容区域"""
        try:
            # 使用工厂创建内容区域
            self.content_panel = self.ui_factory.create_content_area(self.panel)
            
            # 绑定切换按钮事件
            self.content_panel.toggle_button.Bind(wx.EVT_BUTTON, self.on_toggle_right_sidebar)
            
            # 初始化按钮标签
            self.update_toggle_button_label()
        except Exception as e:
            logging.error(f"创建主内容区域时出错: {str(e)}")
            raise e

    def create_right_sidebar(self):
        """创建右侧边栏区域"""
        try:
            # 使用工厂创建右侧边栏
            self.right_sidebar_panel = self.ui_factory.create_right_sidebar(self.panel)
            
            # 绑定航路点绘制按钮事件
            self.right_sidebar_panel.route_visualization_button.Bind(
                wx.EVT_BUTTON, 
                self.event_handlers.on_route_visualization
            )
            
            self.right_sidebar_panel.Hide()  # 默认隐藏右侧边栏
        except Exception as e:
            logging.error(f"创建右侧边栏区域时出错: {str(e)}")
            raise e
        
    def update_toggle_button_label(self):
        """根据当前状态和展开模式更新按钮标签"""
        try:
            # 确保右侧边栏面板已创建
            if not hasattr(self, 'right_sidebar_panel'):
                return
                
            is_shown = self.right_sidebar_panel.IsShown()
            
            if self.EXPAND_MODE == 0:  # 向内展开
                if is_shown:
                    # 面板已显示，点击将收起（向右箭头）
                    self.content_panel.toggle_button.SetLabel("▶")
                else:
                    # 面板已隐藏，点击将展开（向左箭头）
                    self.content_panel.toggle_button.SetLabel("◀")
            else:  # 向外展开
                if is_shown:
                    # 面板已显示，点击将收起（向左箭头）
                    self.content_panel.toggle_button.SetLabel("◀")
                else:
                    # 面板已隐藏，点击将展开（向右箭头）
                    self.content_panel.toggle_button.SetLabel("▶")
        except Exception as e:
            logging.error(f"更新切换按钮标签时出错: {str(e)}")
        
    def on_toggle_right_sidebar(self, event):
        """切换右侧边栏显示状态"""
        try:
            if self.right_sidebar_panel.IsShown():
                # 隐藏右侧边栏
                self.right_sidebar_panel.Hide()
                
                if self.EXPAND_MODE == 1:  # 向外展开模式
                    # 恢复到基础窗口尺寸
                    current_size = self.GetSize()
                    new_width = current_size.width - self.right_sidebar_width
                    self.SetSize((new_width, current_size.height))
            else:
                # 显示右侧边栏
                self.right_sidebar_panel.Show()
                
                if self.EXPAND_MODE == 1:  # 向外展开模式
                    # 增加窗口宽度以容纳右侧边栏
                    current_size = self.GetSize()
                    new_width = current_size.width + self.right_sidebar_width
                    self.SetSize((new_width, current_size.height))
            
            # 更新按钮标签
            self.update_toggle_button_label()
            
            # 重新布局
            self.main_sizer.Layout()
        except Exception as e:
            logging.error(f"切换右侧边栏显示状态时出错: {str(e)}")
    
    def on_mouse_wheel(self, event):
        """处理鼠标滚轮事件以调整滚动速度"""
        try:
            # 获取滚动方向和系统默认滚动增量
            wheel_rotation = event.GetWheelRotation()
            wheel_delta = event.GetWheelDelta()
            
            # 防止除零错误并计算滚动行数
            if wheel_delta == 0:
                event.Skip()
                return
                
            # 计算要滚动的行数，将默认的3行滚动速度加倍到6行
            scroll_lines = int(6 * wheel_rotation / wheel_delta)
            
            # 只有当需要滚动时才执行
            if scroll_lines != 0:
                # 使用ScrollLines进行行数滚动
                self.content_panel.textbox.ScrollLines(-scroll_lines)
            
            # 跳过事件以便其他处理器也能处理
            event.Skip()
        except Exception as e:
            logging.error(f"处理鼠标滚轮事件时出错: {str(e)}")
            event.Skip()


def main():
    """主函数，创建并运行应用程序"""
    try:
        # 创建应用程序实例
        app = wx.App(clearSigInt=True)  # clearSigInt=True可以更好地处理信号
        # 创建并显示主窗口
        frame = AppFrame()
        frame.Show()
        # 启动事件循环
        app.MainLoop()
    except Exception as e:
        logging.error(f"运行应用程序时出错: {str(e)}")
        print(f"运行应用程序时出错: {str(e)}")


if __name__ == "__main__":
    main()