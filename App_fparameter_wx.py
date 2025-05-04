import ctypes
import json
import os
import sys
import time

import pandas as pd
import wx

import func_fparameter as ffp


def calculate_window_geometry():
    import wx
    # 启用高DPI支持
    if hasattr(wx, 'EnableHighDPIAware'):
        wx.EnableHighDPIAware()
    # 设置进程DPI感知级别（适用于Windows）
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # 2表示PerMonitorV2，支持每个监视器的DPI设置
    except AttributeError:
        pass
    screen_width, screen_height = wx.GetDisplaySize()
    user32 = ctypes.windll.user32
    real_screen_width = user32.GetSystemMetrics(0)
    real_dpi = real_screen_width // screen_width
    window_width = 1800
    window_height = 1200
    x = ((screen_width // 2) - (window_width // 2)) * real_dpi
    y = ((screen_height // 2) - (window_height // 2)) * real_dpi * 0.75
    return window_width, window_height, int(x), int(y)


class AppFrame(wx.Frame):
    def __init__(self, parent=None, title="飞行数据快速处理"):
        width, height, x, y = calculate_window_geometry()
        super().__init__(parent, title=title, size=(width, height), pos=(x, y))
        self.df_idx = None
        # 设置窗口最小和最大尺寸，使其固定不变
        self.SetMinSize((width, height))
        self.SetMaxSize((width, height))

        # 获取打包后的资源路径
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'app_icon.ico')

        # 设置图标
        if os.path.exists(icon_path):
            self.SetIcon(wx.Icon(icon_path, wx.BITMAP_TYPE_ICO))

        # 创建主面板
        self.panel = wx.Panel(self)

        # 侧边栏布局
        sidebar_sizer = wx.BoxSizer(wx.VERTICAL)
        logo_label = wx.StaticText(self.panel, label="选择导出模式", style=wx.ALIGN_CENTER)
        font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        logo_label.SetFont(font)
        sidebar_sizer.Add(logo_label, 0, wx.ALL | wx.EXPAND, 20)

        # 替换按钮部分的代码如下：
        button_sizer = wx.BoxSizer(wx.VERTICAL)  # 改为垂直布局

        self.sidebar_button_1 = wx.Button(self.panel, label="单个文件导出")
        self.sidebar_button_1.Bind(wx.EVT_BUTTON, self.single_button_event)
        button_sizer.Add(self.sidebar_button_1, 0, wx.ALL | wx.EXPAND, 5)

        self.sidebar_button_2 = wx.Button(self.panel, label="多个文件导出")
        self.sidebar_button_2.Bind(wx.EVT_BUTTON, self.multi_button_event)
        button_sizer.Add(self.sidebar_button_2, 0, wx.ALL | wx.EXPAND, 5)

        self.sidebar_button_del_msg = wx.Button(self.panel, label="重置信息")
        self.sidebar_button_del_msg.Bind(wx.EVT_BUTTON, self.del_button_event)
        button_sizer.Add(self.sidebar_button_del_msg, 0, wx.ALL | wx.EXPAND, 5)

        self.copy_result_button = wx.Button(self.panel, label="复制信息")
        self.copy_result_button.Bind(wx.EVT_BUTTON, self.copy_result_to_clipboard)
        button_sizer.Add(self.copy_result_button, 0, wx.ALL | wx.EXPAND, 5)

        self.toggle_all_button = wx.Button(self.panel, label="全选/取消全选")
        self.toggle_all_button.Bind(wx.EVT_BUTTON, self.toggle_all_checkboxes)
        button_sizer.Add(self.toggle_all_button, 0, wx.ALL | wx.EXPAND, 5)

        sidebar_sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # 数据源多选框
        self.checkbox_vars = []
        self.checkboxes = []
        options = ["全球卫星定位系统", "短报文", "航姿基准系统", "大气数据系统", "惯性基准系统", "飞行管理系统",
                   "显示控制系统", "无线电高度表", "气象雷达", "备份仪表", "飞参系统", "燃油系统", "灭火任务系统",
                   "环境感知与视频管理系统", "综合处理系统", "显示告警系统", "综合自动调谐系统",
                   "机电信息采集系统", "波段L综合系统", "设备用具", "防冰和除雨", "空调系统", "座舱压力系统",
                   "防火系统", "起落架系统", "舱门系统", "电源系统", "主飞控系统", "襟翼控制系统", "刹车控制系统",
                   "液压电控系统", "前轮转弯系统", "自动飞行系统", "自定义"]
        num_columns = 2
        checkbox_sizer = wx.FlexGridSizer(rows=len(options) // num_columns, cols=num_columns, vgap=2, hgap=5)
        for option in options:
            var = wx.CheckBox(self.panel, label=option)
            if option == "自定义":
                font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
                var.SetFont(font)
            checkbox_sizer.Add(var, 0, wx.ALL | wx.ALIGN_LEFT, 5)
            self.checkbox_vars.append(var)
            self.checkboxes.append(var)
        sidebar_sizer.Add(checkbox_sizer, 1, wx.ALL | wx.EXPAND, 10)

        # 结果显示区域
        result_sizer = wx.BoxSizer(wx.VERTICAL)
        logo_msg_box = wx.StaticText(self.panel, label="数据导出结果", style=wx.ALIGN_CENTER)
        font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        logo_msg_box.SetFont(font)
        result_sizer.Add(logo_msg_box, 0, wx.ALL | wx.EXPAND, 20)

        self.textbox = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
        result_sizer.Add(self.textbox, 1, wx.ALL | wx.EXPAND, 10)

        # 主布局
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(sidebar_sizer, 0, wx.ALL | wx.EXPAND, 0)
        main_sizer.Add(result_sizer, 1, wx.ALL | wx.EXPAND, 0)

        self.panel.SetSizer(main_sizer)

        # 加载上次配置状态
        self.load_checkbox_states()

        # 拦截窗口关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def get_df_idx(self):
        """
        根据自定义选项的勾选情况获取 df_idx
        自定义和勾选是冲突的，只能自定义或者勾选
        """
        custom_checked = self.checkbox_vars[-1].GetValue()
        if custom_checked:  # 如果自定义选项被选中，则从自定义文件读取 df_idx
            file_path = 'init_flight_parameter.csv'
            if not os.path.exists(file_path):
                self.update_result("错误", "请新建文件init_flight_parameter.csv，并配置抽引参数")
                return None
            try:
                self.df_idx = pd.read_csv(file_path)
            except pd.errors.ParserError:
                self.update_result("错误", f"无法正确解析文件 {file_path}，请检查文件格式。")
                return None
            except Exception as e:
                self.update_result("错误", f"读取文件 {file_path} 时发生未知错误: {e}")
                return None
        else:
            selected_systems = [var.GetValue() for var in self.checkbox_vars[:-1]]
            options = ["全球卫星定位系统", "短报文", "航姿基准系统", "大气数据系统", "惯性基准系统", "飞行管理系统",
                       "显示控制系统", "无线电高度表", "气象雷达", "备份仪表", "飞参系统", "燃油系统", "灭火任务系统",
                       "环境感知与视频管理系统", "综合处理系统", "显示告警系统", "综合自动调谐系统",
                       "机电信息采集系统", "波段L综合系统", "设备用具", "防冰和除雨", "空调系统", "座舱压力系统",
                       "防火系统", "起落架系统", "舱门系统", "电源系统", "主飞控系统", "襟翼控制系统", "刹车控制系统",
                       "液压电控系统", "前轮转弯系统", "自动飞行系统"]
            data = {
                'system': options,
                'selected': selected_systems
            }
            self.df_idx = pd.DataFrame(data)

        return self.df_idx

    def single_button_event(self, event):
        start_time = time.time()
        df_idx = self.get_df_idx()
        if df_idx is None:
            return
        try:
            df, text_analyze = ffp.single_abstract(df_idx)
            self.update_result(f"数据提取完成，耗时: {time.time() - start_time:.2f}秒", text_analyze)
        except Exception as e:
            self.update_result("错误", str(e))

    def multi_button_event(self, event):
        df_idx = self.get_df_idx()
        if df_idx is None:
            return
        start_time = time.time()
        try:
            ffp.multi_abstract_parallel(df_idx)
            self.update_result("批量处理完成", f"所有文件已成功处理，耗时: {time.time() - start_time:.2f}秒")
        except Exception as e:
            self.update_result("错误", str(e))

    def update_result(self, title, content):
        # 追加新内容到文本框末尾
        self.textbox.AppendText(f"【{title}】\n\n{content}\n\n")

    def del_button_event(self, event):
        """删除导出文本框内容"""
        self.textbox.Clear()

    def load_checkbox_states(self):
        """加载数据源框配置"""
        if os.path.exists('checkbox_states.json'):
            with open('checkbox_states.json', 'r') as f:
                states = json.load(f)
                for i, var in enumerate(self.checkbox_vars):
                    if i < len(states):
                        # 将字符串转换为布尔值
                        state = bool(states[i])
                        var.SetValue(state)

    def save_checkbox_states(self):
        """保存数据源框配置"""
        states = [var.GetValue() for var in self.checkbox_vars]
        with open('checkbox_states.json', 'w') as f:
            json.dump(states, f)

    def on_close(self, event):
        self.save_checkbox_states()
        self.Destroy()

    def toggle_all_checkboxes(self, event):
        """切换所有复选框的选中状态，排除最后一个“自定义”选项"""
        # 检查除“自定义”外的所有复选框是否都已选中
        all_checked = all(var.GetValue() for var in self.checkbox_vars[:-1])
        # 切换除“自定义”外的所有复选框的状态
        for var in self.checkbox_vars[:-1]:
            var.SetValue(not all_checked)

    def copy_result_to_clipboard(self, event):
        """将数据导出结果框内的文字复制到剪贴板"""
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(self.textbox.GetValue()))
            wx.TheClipboard.Close()
        else:
            self.update_result("错误", "无法打开剪贴板")


if __name__ == "__main__":
    app = wx.App()
    frame = AppFrame()
    frame.Show()
    app.MainLoop()
