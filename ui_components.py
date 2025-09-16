import wx


class SidebarPanel(wx.Panel):
    """侧边栏面板类"""
    
    def __init__(self, parent, on_load_data, on_save_data, on_save_analysis, 
                 on_clear_analysis, on_clear_data, on_quick_save, on_separator):
        super().__init__(parent)
        self.data_choice = None
        self.create_sidebar(on_load_data, on_save_data, on_save_analysis, 
                           on_clear_analysis, on_clear_data, on_quick_save, on_separator)
    
    def create_sidebar(self, on_load_data, on_save_data, on_save_analysis, 
                       on_clear_analysis, on_clear_data, on_quick_save, on_separator):
        """创建侧边栏区域"""
        sidebar_sizer = wx.BoxSizer(wx.VERTICAL)

        # 定义基础尺寸单位，根据屏幕尺寸动态计算
        screen_width, screen_height = wx.GetDisplaySize()
        # 修改基础尺寸参数
        basic_width = int(screen_width * 0.1)
        basic_height = int(screen_height * 0.02)

        # 创建标题标签
        logo_label = wx.StaticText(self, label="选择导出模式", style=wx.ALIGN_CENTER)
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        logo_label.SetFont(font)
        # 设置标签最小尺寸，确保在窗口缩小时仍可见
        logo_label.SetMinSize((basic_width, basic_height))
        sidebar_sizer.Add(logo_label, 0, wx.ALL | wx.EXPAND, 10)

        # 创建数据选择下拉菜单
        self.data_choice = wx.Choice(self, choices=[])
        self.data_choice.SetMinSize((basic_width, basic_height * 1.5))
        self.data_choice.SetMaxSize((basic_width, basic_height * 1.5))
        # 注意：事件绑定将在主框架中完成
        data_choice_sizer = wx.BoxSizer(wx.HORIZONTAL)
        data_choice_sizer.AddSpacer(20)  # 左边距
        data_choice_sizer.Add(self.data_choice, 1, wx.TOP | wx.BOTTOM, 5)  # 上下边距
        data_choice_sizer.AddSpacer(0)  # 右边距
        sidebar_sizer.Add(data_choice_sizer, 0, wx.EXPAND)

        # 创建按钮布局管理器
        button_sizer = wx.BoxSizer(wx.VERTICAL)

        # 创建按钮
        buttons_config = [
            ("加载数据", on_load_data),
            ("保存数据", on_save_data),
            ("保存分析", on_save_analysis),
            ("清除分析", on_clear_analysis),
            ("清除数据", on_clear_data),
            ("快捷保存", on_quick_save),
            ("/", on_separator),
        ]
        
        buttons = []
        for label, event_handler in buttons_config:
            button = wx.Button(self, label=label)
            button.SetMinSize((basic_width, basic_height * 1.5))
            button.SetMaxSize((basic_width, basic_height * 1.5))

            # 如果提供了事件处理函数，则绑定事件
            if event_handler:
                button.Bind(wx.EVT_BUTTON, event_handler)

            buttons.append(button)

        # 添加按钮到布局，不伸缩，居中显示
        for button in buttons:
            button_sizer.Add(button, 0, wx.ALL | wx.CENTER, 5)

        # 添加按钮布局到侧边栏布局，设置合适的比例和最小尺寸
        # 确保按钮区域在窗口缩小时不会被过度压缩
        sidebar_sizer.Add(button_sizer, 1, wx.ALL | wx.EXPAND, 5)

        # 设置侧边栏面板的布局管理器
        self.SetSizer(sidebar_sizer)

        # 手动计算并设置最小尺寸，确保所有按钮可见
        # 先调用Layout让Sizer计算布局
        sidebar_sizer.Layout()
        # 获取内容所需最小尺寸
        min_size = sidebar_sizer.GetMinSize()
        # 设置侧边栏面板的最小尺寸
        self.SetMinSize(min_size)

        # 可选：手动调整最终最小尺寸
        min_size = sidebar_sizer.GetMinSize()
        # 增加额外的宽高（单位：像素）
        min_size.width += 20
        min_size.height += basic_height * 4
        self.SetMinSize(min_size)


class ContentPanel(wx.Panel):
    """内容区域面板类"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.textbox = None
        self.create_content_area()
    
    def create_content_area(self):
        """创建主内容区域"""
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        # 定义基础尺寸单位
        screen_width, screen_height = wx.GetDisplaySize()
        basic_width = int(screen_width * 0.1)
        basic_height = int(screen_height * 0.02)

        # 创建结果区域标题
        logo_msg_box = wx.StaticText(self, label="数据导出结果", style=wx.ALIGN_CENTER)
        # 设置字体为等宽字体，便于显示格式化数据
        font = wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        logo_msg_box.SetFont(font)
        # 设置最小尺寸确保可见性
        logo_msg_box.SetMinSize((basic_width, basic_height))
        content_sizer.Add(logo_msg_box, 0, wx.ALL | wx.EXPAND, 10)

        # 创建文本显示框，用于显示导出结果
        self.textbox = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
        # 文本框占据剩余空间
        content_sizer.Add(self.textbox, 1, wx.ALL | wx.EXPAND, 5)
        # 设置内容区域最小尺寸
        content_sizer.SetMinSize((3 * basic_width, 10 * basic_height))

        # 设置内容面板的布局管理器
        self.SetSizer(content_sizer)