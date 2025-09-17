import ctypes
import os
import sys

import wx
from analysis.analysis_data import analysis_data

from ui_components import SidebarPanel, ContentPanel
from data_manager import DataManager
from event_handlers import EventHandlers
from utils import calculate_window_geometry


class AppFrame(wx.Frame):
    """应用程序主窗口类"""

    def __init__(self, parent=None, title="i森超级定制款"):
        """初始化应用程序窗口
        
        Args:
            parent: 父窗口，默认为None
            title: 窗口标题，默认为"i森超级定制款"
        """
        # 启用高DPI支持，确保在高分辨率屏幕上正确显示
        if hasattr(wx, 'EnableHighDPIAware'):
            wx.EnableHighDPIAware()
        try:
            # 2表示PerMonitorV2，支持每个监视器的DPI设置
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError) as e:
            # 在不支持PerMonitorV2的系统上降级处理
            print(f"设置高DPI感知失败: {e}")

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
                print(f"设置图标失败: {e}")
        else:
            print(f"图标文件未找到: {icon_path}")

        # 创建主面板
        self.panel = wx.Panel(self)

        # 创建数据管理器
        self.data_manager = DataManager()

        # 创建事件处理器
        self.event_handlers = EventHandlers(self)

        # 创建UI界面
        self.create_ui()

        # 设置窗口最小尺寸，防止用户将窗口缩得太小
        min_size = self.main_sizer.GetMinSize()
        self.SetMinSize(min_size)

        # 绑定窗口关闭事件
        self.Bind(wx.EVT_CLOSE, self.event_handlers.on_close)

    def create_ui(self):
        """创建用户界面"""
        # 创建主布局管理器，采用水平布局
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 创建侧边栏面板和内容区域
        self.create_sidebar()
        self.create_content_area()

        # 将侧边栏和内容区域添加到主布局
        # 侧边栏不伸缩（proportion=0），内容区域占据剩余空间（proportion=1）
        self.main_sizer.Add(self.sidebar_panel, 0, wx.EXPAND)
        self.main_sizer.Add(self.content_panel, 1, wx.EXPAND)

        # 设置主面板的布局管理器
        self.panel.SetSizer(self.main_sizer)
        # 调整窗口大小以适应内容
        self.main_sizer.Fit(self.panel)
        
        # 绑定鼠标滚轮事件以自定义滚动速度
        self.content_panel.textbox.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)

    def create_sidebar(self):
        """创建侧边栏区域"""
        # 为侧边栏创建独立面板，便于管理和布局
        self.sidebar_panel = SidebarPanel(
            self.panel,
            on_load_data=self.event_handlers.load_data,
            on_save_data=self.event_handlers.save_current_data,
            on_save_analysis=self.event_handlers.save_analysis,
            on_clear_analysis=self.event_handlers.remove_analysis,
            on_clear_data=self.event_handlers.remove_current_data,
            on_quick_save=self.event_handlers.single_button_event_1,
            on_separator=self.event_handlers.single_button_event_1
        )
        
        # 绑定数据选择事件
        self.sidebar_panel.data_choice.Bind(wx.EVT_CHOICE, self.event_handlers.on_data_choice)

    def create_content_area(self):
        """创建主内容区域"""
        # 为主要内容区域创建独立面板
        self.content_panel = ContentPanel(self.panel)
    
    def on_mouse_wheel(self, event):
        """处理鼠标滚轮事件以调整滚动速度"""
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


def main():
    """主函数，创建并运行应用程序"""
    # 创建应用程序实例
    app = wx.App(clearSigInt=True)  # clearSigInt=True可以更好地处理信号
    # 创建并显示主窗口
    frame = AppFrame()
    frame.Show()
    # 启动事件循环
    app.MainLoop()


if __name__ == "__main__":
    main()