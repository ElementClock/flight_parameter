import wx


def calculate_window_geometry():
    """计算窗口初始位置和大小
    
    Returns:
        tuple: (窗口宽度, 窗口高度, 窗口X坐标, 窗口Y坐标)
    """
    try:
        screen_width, screen_height = wx.GetDisplaySize()
    except Exception as e:
        # 如果无法获取屏幕尺寸，使用默认值
        print(f"获取屏幕尺寸失败: {e}")
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
            print(f"创建按钮 '{label}' 时出错: {e}")
            # 创建一个禁用的按钮作为占位符
            button = wx.Button(parent, label=f"{label}(错误)")
            button.Enable(False)
            buttons.append(button)
    return buttons