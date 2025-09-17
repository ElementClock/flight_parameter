import wx
import wx.richtext as rt


class SidebarPanel(wx.Panel):
    """侧边栏面板类"""
    
    def __init__(self, parent, on_load_data, on_save_data, on_save_analysis, 
                 on_clear_analysis, on_clear_data, on_quick_save, on_separator):
        """初始化侧边栏面板
        
        Args:
            parent: 父窗口
            on_load_data: 加载数据事件处理函数
            on_save_data: 保存数据事件处理函数
            on_save_analysis: 保存分析事件处理函数
            on_clear_analysis: 清除分析事件处理函数
            on_clear_data: 清除数据事件处理函数
            on_quick_save: 快捷保存事件处理函数
            on_separator: 分隔符事件处理函数
        """
        super().__init__(parent)
        self.data_choice = None
        self.create_sidebar(on_load_data, on_save_data, on_save_analysis, 
                           on_clear_analysis, on_clear_data, on_quick_save, on_separator)
    
    def create_sidebar(self, on_load_data, on_save_data, on_save_analysis, 
                       on_clear_analysis, on_clear_data, on_quick_save, on_separator):
        """创建侧边栏区域
        
        Args:
            on_load_data: 加载数据事件处理函数
            on_save_data: 保存数据事件处理函数
            on_save_analysis: 保存分析事件处理函数
            on_clear_analysis: 清除分析事件处理函数
            on_clear_data: 清除数据事件处理函数
            on_quick_save: 快捷保存事件处理函数
            on_separator: 分隔符事件处理函数
        """
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
            ("///", on_separator),
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


class RightSidebarPanel(wx.Panel):
    """右侧边栏面板类"""
    
    def __init__(self, parent):
        """初始化右侧边栏面板
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.create_right_sidebar()
        self.Hide()  # 默认隐藏
        
    def create_right_sidebar(self):
        """创建右侧边栏区域"""
        right_sidebar_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 定义基础尺寸单位
        screen_width, screen_height = wx.GetDisplaySize()
        basic_width = int(screen_width * 0.1)
        basic_height = int(screen_height * 0.02)
        
        # 创建标题
        title = wx.StaticText(self, label="工具面板")
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(font)
        title.SetMinSize((basic_width, basic_height))
        right_sidebar_sizer.Add(title, 0, wx.ALL | wx.CENTER, 10)
        
        # 添加一些示例内容
        content_text = wx.StaticText(self, label="这是右侧工具面板\n您可以在这里放置\n额外的工具和选项")
        right_sidebar_sizer.Add(content_text, 0, wx.ALL | wx.CENTER, 10)
        
        # 设置布局
        self.SetSizer(right_sidebar_sizer)
        
        # 设置固定的最小尺寸
        self.SetMinSize((200, -1))


class ContentPanel(wx.Panel):
    """内容区域面板类"""
    
    def __init__(self, parent):
        """初始化内容区域面板
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.textbox = None
        self.toggle_button = None
        self.create_content_area()
    
    def create_content_area(self):
        """创建主内容区域"""
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        # 定义基础尺寸单位
        screen_width, screen_height = wx.GetDisplaySize()
        basic_width = int(screen_width * 0.1)
        basic_height = int(screen_height * 0.02)

        # 创建结果区域标题的水平布局
        title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 创建结果区域标题
        logo_msg_box = wx.StaticText(self, label="数据导出结果", style=wx.ALIGN_CENTER)
        # 设置字体为等宽字体，便于显示格式化数据
        font = wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        logo_msg_box.SetFont(font)
        # 设置最小尺寸确保可见性
        logo_msg_box.SetMinSize((basic_width, basic_height))
        
        # 创建切换右侧边栏显示的按钮，使用右箭头表示面板当前处于收起状态
        self.toggle_button = wx.Button(self, label="▶", size=(30, -1))
        self.toggle_button.SetMinSize((30, basic_height))
        
        # 添加控件到标题布局
        title_sizer.Add(logo_msg_box, 1, wx.ALIGN_CENTER_VERTICAL)
        title_sizer.Add(self.toggle_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        
        # 添加标题布局到内容布局
        content_sizer.Add(title_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # 创建富文本显示框，用于显示导出结果
        self.textbox = rt.RichTextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
        # 文本框占据剩余空间
        content_sizer.Add(self.textbox, 1, wx.ALL | wx.EXPAND, 5)
        # 设置内容区域最小尺寸
        content_sizer.SetMinSize((3 * basic_width, 10 * basic_height))

        # 设置内容面板的布局管理器
        self.SetSizer(content_sizer)
    
    def set_formatted_text(self, text):
        """设置格式化的文本内容
        
        Args:
            text (str): 要显示的文本内容
        """
        try:
            # 清空现有内容
            self.textbox.Clear()
            
            # 按行处理文本
            lines = text.split('\n')
            for line in lines:
                # 检查是否为需要红色渲染的文本
                if '[[RED]]' in line and '[[/RED]]' in line:
                    # 提取纯文本（去除标记）
                    clean_line = line.replace('[[RED]]', '').replace('[[/RED]]', '')
                    # 应用红色格式
                    self.textbox.BeginTextColour(wx.RED)
                    self.textbox.WriteText(clean_line + '\n')
                    self.textbox.EndTextColour()
                # 检查是否为需要黄色渲染的文本
                elif '[[YELLOW]]' in line and '[[/YELLOW]]' in line:
                    # 提取纯文本（去除标记）
                    clean_line = line.replace('[[YELLOW]]', '').replace('[[/YELLOW]]', '')
                    # 应用黄色格式
                    self.textbox.BeginTextColour(wx.YELLOW)
                    self.textbox.WriteText(clean_line + '\n')
                    self.textbox.EndTextColour()
                # 检查是否为需要琥珀色渲染的文本
                elif '[[AMBER]]' in line and '[[/AMBER]]' in line:
                    # 提取纯文本（去除标记）
                    clean_line = line.replace('[[AMBER]]', '').replace('[[/AMBER]]', '')
                    # 应用深橙色格式 (RGB: 255, 140, 0)
                    amber_color = wx.Colour(255, 140, 0)
                    self.textbox.BeginTextColour(amber_color)
                    self.textbox.BeginBold()
                    self.textbox.WriteText(clean_line + '\n')
                    self.textbox.EndBold()
                    self.textbox.EndTextColour()
                # 检查是否为需要蓝色渲染的文本
                elif '[[BLUE]]' in line and '[[/BLUE]]' in line:
                    # 提取纯文本（去除标记）
                    clean_line = line.replace('[[BLUE]]', '').replace('[[/BLUE]]', '')
                    # 应用蓝色格式
                    self.textbox.BeginTextColour(wx.BLUE)
                    self.textbox.BeginBold()
                    self.textbox.WriteText(clean_line + '\n')
                    self.textbox.EndBold()
                    self.textbox.EndTextColour()
                # 检查是否为需要加粗的标题行
                elif '[[BOLD]]' in line and '[[/BOLD]]' in line:
                    # 提取纯文本标题（去除标记）
                    clean_line = line.replace('[[BOLD]]', '').replace('[[/BOLD]]', '')
                    # 应用加粗格式
                    self.textbox.BeginBold()
                    self.textbox.WriteText(clean_line + '\n')
                    self.textbox.EndBold()
                else:
                    # 普通文本
                    self.textbox.WriteText(line + '\n')
        except Exception as e:
            # 出现异常时显示原始文本
            self.textbox.Clear()
            self.textbox.WriteText(f"显示文本时出错: {str(e)}\n原始文本:\n{text}")