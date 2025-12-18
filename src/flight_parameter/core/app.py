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
import random
from abc import ABC, abstractmethod

import wx

# 项目模块导入
from .data_manager import DataManager
from ..event_handlers import EventHandlers
from ..ui.components import SidebarPanel, ContentPanel, RightSidebarPanel
from ..utils.system_utils import calculate_window_geometry

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class AppTitleManager:
    """应用程序标题管理器"""
    
    def __init__(self):
        """初始化标题管理器"""
        # 定义标题选项列表，便于添加新内容
        self.title_options = [
            "哈基元说：曼波波波，哈基米沃南北绿豆，阿西嘎呀压库乃龙，哈，呵哈，呵哈，呵哈，呵哈，哈基米起床，呵哈，呵啊，呵，呵啊，呵啊，呵哈，嘿，叮咚咚，曼波波波，哈基米沃南北绿豆，阿西嘎呀压库乃龙",
            "哈基元说：哈基米南北路多~阿西噶阿西~阿西噶哈雅酷奶农~哈基米哈基~哈基米南北路多~阿西哈雅酷奶农~哈基米曼波雅噗雅噗~有特有特哦吗哈基米曼波~哈基米南北路多~阿西噶哈雅酷奶农~马吉利哇哈亚曼波",
            "哈基元说：别问我兜里有什么，不是南北绿豆，就是没唱完的曼波小调～",
            "哈基元说：别催我别催我，再唱一遍 “南北绿豆”，脚步自然就快起来啦！",
            "哈基元说：我立志当曼波节奏大师，天天在家练打节拍，结果把楼下的大爷吵得上来投诉，还非要跟我讨教 “哈基 哈基” 的唱法～"
        ]
        
        # 彩蛋标题及其出现概率 (标题, 概率)
        # 概率为0-1之间的浮点数，例如0.1表示10%的概率
        self.easter_egg_title = "哈基元说：我的歌单里没有慢歌，毕竟可爱是不能减速的！"
        self.easter_egg_base_probability = 0.03  # 初始概率
        self.easter_egg_current_probability = self.easter_egg_base_probability  # 当前概率
        self.easter_egg_consecutive_misses = 0  # 连续未出现次数
    
    def get_random_title(self):
        """获取随机标题"""
        # 检查是否触发彩蛋标题
        if self._should_show_easter_egg():
            return self._get_easter_egg_title()
        else:
            self._update_easter_egg_probability()
            
        # 返回普通标题
        return self._get_random_regular_title()
    
    def _should_show_easter_egg(self):
        """检查是否应该显示彩蛋标题
        
        Returns:
            bool: 如果应该显示彩蛋标题返回True，否则返回False
        """
        return self.easter_egg_title and random.random() < self.easter_egg_current_probability
    
    def _get_easter_egg_title(self):
        """获取彩蛋标题并重置相关计数器
        
        Returns:
            str: 彩蛋标题
        """
        # 彩蛋标题被选中，重置连续未出现次数和当前概率
        self.easter_egg_consecutive_misses = 0
        self.easter_egg_current_probability = self.easter_egg_base_probability
        return self.easter_egg_title
    
    def _update_easter_egg_probability(self):
        """更新彩蛋标题出现概率"""
        # 只有在彩蛋未被选中的情况下才增加连续未出现次数并调整概率
        if self.easter_egg_title:
            # 彩蛋未被选中，增加连续未出现次数，并提高下次出现概率
            self.easter_egg_consecutive_misses += 1
            # 每次未出现，概率增加初始概率的值，但不超过0.5
            self.easter_egg_current_probability = min(
                self.easter_egg_base_probability + 
                self.easter_egg_consecutive_misses * self.easter_egg_base_probability,
                0.5
            )
    
    def _get_random_regular_title(self):
        """获取随机的常规标题
        
        Returns:
            str: 随机选择的常规标题
        """
        return random.choice(self.title_options)
    
    def add_title_option(self, title):
        """添加新的标题选项
        
        Args:
            title (str): 要添加的标题
        """
        if title not in self.title_options:
            self.title_options.append(title)
    
    def set_easter_egg(self, title, probability):
        """设置彩蛋标题和出现概率
        
        Args:
            title (str): 彩蛋标题
            probability (float): 出现概率，0-1之间，例如0.1表示10%
        """
        self.easter_egg_title = title
        self.easter_egg_base_probability = max(0.0, min(1.0, probability))  # 限制在0-1之间
        self.easter_egg_current_probability = self.easter_egg_base_probability  # 重置当前概率
        self.easter_egg_consecutive_misses = 0  # 重置连续未出现次数
    
    def get_all_titles(self):
        """获取所有标题选项"""
        return self.title_options.copy()


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
            on_separator=event_handlers.batch_process  # 将"///"按钮绑定到批量处理功能
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

    def __init__(self, parent=None, title=None, ui_factory=None):
        """初始化应用程序窗口
        
        Args:
            parent: 父窗口，默认为None
            title: 窗口标题，如果为None则随机生成
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

            # 创建标题管理器
            self.title_manager = AppTitleManager()
            
            # 如果没有提供标题，则随机生成一个
            if title is None:
                title = self.title_manager.get_random_title()

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
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, 'resources', 'icons', 'app_icon.ico')

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
            self.content_panel.html_window.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)

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
                self.content_panel.html_window.ScrollLines(-scroll_lines)
            
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