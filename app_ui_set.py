import os
import sys
import ctypes
import wx


class AppFrame(wx.Frame):
    def __init__(self, parent=None, title="i森超级定制款"):
        # 自动按比例获取窗口大小
        width, height, app_init_x, app_init_y = calculate_window_geometry()
        # 初始化窗口
        super().__init__(parent, title=title, size=(width, height), pos=(app_init_x, app_init_y))
        # 获取打包后的资源路径
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'app_icon.ico')

        # 设置图标
        if os.path.exists(icon_path):
            self.SetIcon(wx.Icon(icon_path, wx.BITMAP_TYPE_ICO))
        # 使用相对字体大小
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        # 创建主面板
        self.panel = wx.Panel(self)

        # 创建布局管理器
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)  # 水平布局
        sidebar_sizer = wx.BoxSizer(wx.VERTICAL)
        button_sizer = wx.BoxSizer(wx.VERTICAL)  # 改为垂直布局



        # 创建一个静态文本控件，并设置字体
        logo_label = wx.StaticText(self.panel, label="选择导出模式", style=wx.ALIGN_CENTER)
        logo_label.SetFont(font)

        # 创建按钮
        self.sidebar_button_1 = wx.Button(self.panel, label="单个文件导出")
        self.sidebar_button_1.Bind(wx.EVT_BUTTON, self.single_button_event)
        button_sizer.Add(self.sidebar_button_1, 0, wx.ALL | wx.EXPAND, 20)

        # 结果显示区域
        result_sizer = wx.BoxSizer(wx.VERTICAL)
        logo_msg_box = wx.StaticText(self.panel, label="数据导出结果", style=wx.ALIGN_CENTER)
        # 设置字体为等宽字体
        font = wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        logo_msg_box.SetFont(font)
        result_sizer.Add(logo_msg_box, 0, wx.ALL | wx.EXPAND, 20)

        self.textbox = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
        result_sizer.Add(self.textbox, 1, wx.ALL | wx.EXPAND, 10)


        # 给sidebar_sizer添加部件
        sidebar_sizer.Add(logo_label, 0, wx.ALL | wx.EXPAND, 10)
        sidebar_sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 10)
        # 主布局添加sidebar_sizer
        main_sizer.Add(sidebar_sizer, 0, wx.ALL | wx.EXPAND, 10)
        main_sizer.Add(result_sizer, 1, wx.ALL | wx.EXPAND, 0)

        # 使面板内的控件按照该布局管理器的规则进行排列
        self.panel.SetSizer(main_sizer)
        # 强制面板重新计算并应用布局，确保控件按照新设置的布局管理器正确显示位置和大小
        self.panel.Layout()

    def single_button_event(self, event):
        # 提交任务到线程池
        pass







def calculate_window_geometry():
    # 启用高DPI支持
    if hasattr(wx, 'EnableHighDPIAware'):
        wx.EnableHighDPIAware()
    # 设置进程DPI感知级别（适用于Windows）
    try:
        # 2表示PerMonitorV2，支持每个监视器的DPI设置
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except AttributeError:
        pass
    screen_width, screen_height = wx.GetDisplaySize()
    user32 = ctypes.windll.user32
    real_screen_width = user32.GetSystemMetrics(0)
    real_dpi = real_screen_width // screen_width

    # 使用相对比例而非绝对像素
    window_width = int(screen_width * 0.6)
    window_height = int(screen_height * 0.6)
    # 使得初始窗口居中
    app_init_x = (screen_width - window_width) // 2
    app_init_y = (screen_height - window_height) // 2
    return window_width, window_height, app_init_x, app_init_y




if __name__ == "__main__":
    app = wx.App()
    frame = AppFrame()
    frame.Show()
    app.MainLoop()