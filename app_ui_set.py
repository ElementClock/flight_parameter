import ctypes
import os
import sys

import wx
import pandas as pd
from analysis.analysis_data import analysis_data


class AppFrame(wx.Frame):
    """应用程序主窗口类"""

    def __init__(self, parent=None, title="i森超级定制款"):
        """初始化应用程序窗口"""
        # 启用高DPI支持，确保在高分辨率屏幕上正确显示
        if hasattr(wx, 'EnableHighDPIAware'):
            wx.EnableHighDPIAware()
        try:
            # 2表示PerMonitorV2，支持每个监视器的DPI设置
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except AttributeError:
            pass

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
            self.SetIcon(wx.Icon(icon_path, wx.BITMAP_TYPE_ICO))

        # 创建主面板
        self.panel = wx.Panel(self)

        # 创建UI界面
        self.create_ui()

        # 设置窗口最小尺寸，防止用户将窗口缩得太小
        min_size = self.main_sizer.GetMinSize()
        self.SetMinSize(min_size)

        # 绑定窗口关闭事件
        # self.Bind(wx.EVT_CLOSE, self.on_close)

    def create_ui(self):
        """创建用户界面"""
        # 创建主布局管理器，采用水平布局
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 创建侧边栏面板和内容面板
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

    def create_buttons_batch(self, parent, button_configs, basic_width, basic_height):
        """
        批量创建按钮的辅助方法
        
        :param parent: 按钮的父容器
        :param button_configs: 按钮配置列表，每个元素为 (label, event_handler) 元组
        :param basic_width: 按钮基础宽度
        :param basic_height: 按钮基础高度
        :return: 按钮列表
        """
        buttons = []
        for label, event_handler in button_configs:
            button = wx.Button(parent, label=label)
            button.SetMinSize((basic_width, basic_height * 1.5))
            button.SetMaxSize((basic_width, basic_height * 1.5))

            # 如果提供了事件处理函数，则绑定事件
            if event_handler:
                button.Bind(wx.EVT_BUTTON, event_handler)

            buttons.append(button)
        return buttons

    def create_sidebar(self):
        """创建侧边栏区域"""
        # 为侧边栏创建独立面板，便于管理和布局
        self.sidebar_panel = wx.Panel(self.panel)
        sidebar_sizer = wx.BoxSizer(wx.VERTICAL)

        # 定义基础尺寸单位，根据屏幕尺寸动态计算
        screen_width, screen_height = wx.GetDisplaySize()
        # 修改基础尺寸参数
        basic_width = int(screen_width * 0.1)
        basic_height = int(screen_height * 0.02)

        # 创建标题标签
        logo_label = wx.StaticText(self.sidebar_panel, label="选择导出模式", style=wx.ALIGN_CENTER)
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        logo_label.SetFont(font)
        # 设置标签最小尺寸，确保在窗口缩小时仍可见
        logo_label.SetMinSize((basic_width, basic_height))
        sidebar_sizer.Add(logo_label, 0, wx.ALL | wx.EXPAND, 10)

        # 创建按钮布局管理器
        button_sizer = wx.BoxSizer(wx.VERTICAL)

        # 使用批量创建方法创建按钮
        button_configs = [
            ("加载数据", self.load_data),
            ("选择数据", self.single_button_event_1),
            ("保存数据", self.single_button_event_1),
            ("保存分析", self.single_button_event_1),
            ("清除分析", self.single_button_event_1),
            ("/", self.single_button_event_1),
            ("/", self.single_button_event_1),
            ("/", self.single_button_event_1),
        ]

        buttons = self.create_buttons_batch(self.sidebar_panel, button_configs, basic_width, basic_height)

        # 添加按钮到布局，不伸缩，居中显示
        for button in buttons:
            button_sizer.Add(button, 0, wx.ALL | wx.CENTER, 5)

        # 添加按钮布局到侧边栏布局，设置合适的比例和最小尺寸
        # 确保按钮区域在窗口缩小时不会被过度压缩
        sidebar_sizer.Add(button_sizer, 1, wx.ALL | wx.EXPAND, 5)

        # 设置侧边栏面板的布局管理器
        self.sidebar_panel.SetSizer(sidebar_sizer)

        # 手动计算并设置最小尺寸，确保所有按钮可见
        # 先调用Layout让Sizer计算布局
        sidebar_sizer.Layout()
        # 获取内容所需最小尺寸
        min_size = sidebar_sizer.GetMinSize()
        # 设置侧边栏面板的最小尺寸
        self.sidebar_panel.SetMinSize(min_size)

        # 可选：手动调整最终最小尺寸
        min_size = sidebar_sizer.GetMinSize()
        # 增加额外的宽高（单位：像素）
        min_size.width += 20
        min_size.height += basic_height * 4
        self.sidebar_panel.SetMinSize(min_size)

    def create_content_area(self):
        """创建主内容区域"""
        # 为主要内容区域创建独立面板
        self.content_panel = wx.Panel(self.panel)
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        # 定义基础尺寸单位
        screen_width, screen_height = wx.GetDisplaySize()
        basic_width = int(screen_width * 0.1)
        basic_height = int(screen_height * 0.02)

        # 创建结果区域标题
        logo_msg_box = wx.StaticText(self.content_panel, label="数据导出结果", style=wx.ALIGN_CENTER)
        # 设置字体为等宽字体，便于显示格式化数据
        font = wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        logo_msg_box.SetFont(font)
        # 设置最小尺寸确保可见性
        logo_msg_box.SetMinSize((basic_width, basic_height))
        content_sizer.Add(logo_msg_box, 0, wx.ALL | wx.EXPAND, 10)

        # 创建文本显示框，用于显示导出结果
        self.textbox = wx.TextCtrl(self.content_panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
        # 文本框占据剩余空间
        content_sizer.Add(self.textbox, 1, wx.ALL | wx.EXPAND, 5)
        # 设置内容区域最小尺寸
        content_sizer.SetMinSize((3 * basic_width, 10 * basic_height))

        # 设置内容面板的布局管理器
        self.content_panel.SetSizer(content_sizer)

    def single_button_event_1(self, event):
        """处理单个文件导出按钮点击事件"""
        # 提交任务到线程池
        pass

    def load_data(self, event):
        """加载CSV数据文件"""
        with wx.FileDialog(
                self,
                message="选择CSV文件",
                wildcard="CSV文件 (*.csv)|*.csv",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            try:
                # 尝试多种编码方式
                encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
                self.df = None
                last_error = None

                for encoding in encodings:
                    try:
                        self.df = pd.read_csv(pathname, encoding=encoding)
                        self.analysis_result, self.df = analysis_data(self.df)
                        # 新信息追加到原有信息之后
                        current_value = self.textbox.GetValue()
                        self.textbox.SetValue(
                            current_value + f"成功加载文件({encoding}编码): {pathname}\n"
                                            f"本次文件解析结果如下：\n {self.analysis_result}\n")
                        break
                    except UnicodeDecodeError as e:
                        last_error = e
                        continue
                    except Exception as e:
                        raise e

                if self.df is None:
                    raise last_error

            except Exception as e:
                wx.MessageBox(f"无法读取文件 '{pathname}': {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
                self.textbox.SetValue(f"加载文件失败: {str(e)}")

    def on_close(self, event):
        """处理窗口关闭事件"""
        # 如果存在数据框，则在关闭时自动保存
        if hasattr(self, 'df') and self.df is not None:
            try:
                # 保存为UTF-8 with BOM格式
                self.df.to_csv('auto_saved_data.csv', encoding='utf-8-sig', index=False)
                self.textbox.SetValue("数据已自动保存至 auto_saved_data.csv (UTF-8 SIG格式)")
            except Exception as e:
                self.textbox.SetValue(f"保存数据时出错: {str(e)}")
        
        # 销毁窗口
        self.Destroy()


def calculate_window_geometry():
    """计算窗口初始位置和大小"""
    screen_width, screen_height = wx.GetDisplaySize()

    # 使用相对比例而非绝对像素，确保在不同分辨率屏幕上都有合适的大小
    window_width = int(screen_width * 0.6)
    window_height = int(screen_height * 0.6)
    # 使得初始窗口居中
    app_init_x = (screen_width - window_width) // 2
    app_init_y = (screen_height - window_height) // 2
    return window_width, window_height, app_init_x, app_init_y


if __name__ == "__main__":
    # 创建应用程序实例
    app = wx.App()
    # 创建并显示主窗口
    frame = AppFrame()
    frame.Show()
    # 启动事件循环
    app.MainLoop()