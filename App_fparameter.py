import ctypes
import json
import os
import sys
import time
from tkinter import messagebox

import customtkinter
import pandas as pd

import func_fparameter as ffp


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        # 设置窗口图标
        icon_path = 'app_icon.ico'
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        else:
            print(f"图标文件 {icon_path} 未找到。")

        self.df_idx = None

        """主窗口配置"""
        self.title("飞行数据快速处理")
        # 获取屏幕的宽度和高度
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        user32 = ctypes.windll.user32
        real_screen_width = user32.GetSystemMetrics(0)
        # 由于geometry 大小为缩放后的像素大小，位置为真实像素位置，因此需要计算dpi恢复真实位置
        real_dpi = real_screen_width // screen_width
        window_width = 1000  # 窗口长度 系统DPI缩放后的值
        window_height = 618  # 窗口高度
        x = ((screen_width // 2) - (window_width // 2)) * real_dpi
        y = ((screen_height // 2) - (window_height // 2)) * real_dpi * 0.75  # 向上偏一点更好看
        self.geometry(f'{window_width}x{window_height}+{int(x)}+{int(y)}')
        self.resizable(False, False)

        """侧边栏布局"""
        self.sidebar_frame = customtkinter.CTkFrame(self, width=300)
        self.sidebar_frame.pack(side="left", fill="y")

        self.logo_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="选择导出模式",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        self.logo_label.pack(pady=20, padx=20)

        self.create_sidebar_buttons()
        self.create_data_sources()

        """结果显示区域"""
        self.result_frame = customtkinter.CTkFrame(self)
        self.result_frame.pack(side="right", fill="both", expand=True)

        self.logo_msg_box = customtkinter.CTkLabel(
            self.result_frame,
            text="数据导出结果",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        self.logo_msg_box.pack(pady=20, padx=20)

        self.textbox = customtkinter.CTkTextbox(
            self.result_frame,
            wrap="word",
            font=customtkinter.CTkFont(size=12)
        )
        self.textbox.pack(fill="both", expand=True, padx=20, pady=10)

        # 加载上次配置状态
        self.load_checkbox_states()
        # 拦截窗口关闭事件，在窗口关闭之前执行自定义的操作
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_sidebar_buttons(self):
        """创建侧边栏按钮"""
        button_frame = customtkinter.CTkFrame(self.sidebar_frame)
        button_frame.pack(pady=10, padx=20, fill="x")

        self.sidebar_button_1 = customtkinter.CTkButton(
            button_frame,
            text="单个文件导出",
            command=self.single_button_event,
            width=80  # 适当调整按钮宽度
        )
        self.sidebar_button_1.grid(row=0, column=0, padx=5, sticky="ew")

        self.sidebar_button_2 = customtkinter.CTkButton(
            button_frame,
            text="多个文件导出",
            command=self.multi_button_event,
            width=80  # 适当调整按钮宽度
        )
        self.sidebar_button_2.grid(row=0, column=1, padx=5, sticky="ew")

        self.sidebar_button_del_msg = customtkinter.CTkButton(
            button_frame,
            text="重置信息框",
            command=self.del_button_event,
            width=80  # 适当调整按钮宽度
        )
        self.sidebar_button_del_msg.grid(row=0, column=2, padx=5, sticky="ew")

        # 让列均匀分配空间
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

    def create_data_sources(self):
        """创建数据源多选框"""
        # 使用普通的 CTkFrame 代替 CTkScrollableFrame
        self.scrollable_frame = customtkinter.CTkFrame(
            self.sidebar_frame,
            width=250,
            height=300  # 保持固定高度
        )
        self.scrollable_frame.pack(pady=10, padx=20, fill="both")

        self.checkbox_vars = []
        self.checkboxes = []

        # 直接使用列表来存储选项，保证顺序
        self.options = ["全球卫星定位系统", "短报文", "航姿基准系统", "大气数据系统", "惯性基准系统", "飞行管理系统",
                        "显示控制系统", "无线电高度表", "气象雷达", "备份仪表", "飞参系统", "燃油系统", "灭火任务系统",
                        "环境感知与视频管理系统", "综合处理系统", "显示告警系统", "综合自动调谐系统",
                        "机电信息采集系统", "波段L综合系统", "设备用具", "防冰和除雨", "空调系统", "座舱压力系统",
                        "防火系统", "起落架系统", "舱门系统", "电源系统", "主飞控系统", "襟翼控制系统", "刹车控制系统",
                        "液压电控系统", "前轮转弯系统", "自动飞行系统", "自定义"]

        num_columns = 2
        for i, option in enumerate(self.options):
            var = customtkinter.StringVar(value="off")
            if option == "自定义":
                checkbox = customtkinter.CTkCheckBox(
                    self.scrollable_frame,
                    text=option,
                    variable=var,
                    onvalue="on",
                    offvalue="off",
                    font=customtkinter.CTkFont(family="微软雅黑", size=12, weight="bold")
                )
            else:
                checkbox = customtkinter.CTkCheckBox(
                    self.scrollable_frame,
                    text=option,
                    variable=var,
                    onvalue="on",
                    offvalue="off",
                    font=customtkinter.CTkFont(size=12)
                )
            row = i // num_columns
            col = i % num_columns
            checkbox.grid(row=row, column=col, padx=5, pady=2, sticky="w")
            self.checkbox_vars.append(var)
            self.checkboxes.append(checkbox)

    def get_df_idx(self):
        """根据自定义选项的勾选情况获取 df_idx"""
        custom_checked = self.checkbox_vars[-1].get() == "on"
        if custom_checked:
            file_path = 'init_flight_parameter.csv'
            if not os.path.exists(file_path):
                messagebox.showinfo("文件缺失", "请新建文件init_flight_parameter.csv，并配置抽引参数")
                # 更友好地退出程序
                self.destroy()
                return None
            try:
                self.df_idx = pd.read_csv(file_path)
            except pd.errors.ParserError:
                messagebox.showerror("文件解析错误", f"无法正确解析文件 {file_path}，请检查文件格式。")
                self.destroy()
                return None
            except Exception as e:
                messagebox.showerror("未知错误", f"读取文件 {file_path} 时发生未知错误: {e}")
                self.destroy()
                return None
        else:
            selected_systems = [var.get() == "on" for var in self.checkbox_vars[:-1]]
            data = {
                'system': self.options[:-1],
                'selected': selected_systems
            }
            self.df_idx = pd.DataFrame(data)

        return self.df_idx

    def single_button_event(self):
        start_time = time.time()
        df_idx = self.get_df_idx()
        try:
            df, text_analyze = ffp.single_abstract(df_idx)
            self.update_result(f"数据提取完成，耗时: {time.time() - start_time:.2f}秒", text_analyze)
        except Exception as e:
            self.update_result("错误", str(e))

    def multi_button_event(self):
        df_idx = self.get_df_idx()
        try:
            ffp.multi_abstract(df_idx)
            self.update_result("批量处理完成", "所有文件已成功处理")
        except Exception as e:
            self.update_result("错误", str(e))

    def update_result(self, title, content):
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", f"【{title}】\n\n{content}")

    def del_button_event(self):
        """删除导出文本框内容"""
        self.textbox.delete("1.0", "end")

    def load_checkbox_states(self):
        """加载数据源框配置"""
        if os.path.exists('checkbox_states.json'):
            with open('checkbox_states.json', 'r') as f:
                states = json.load(f)
                for i, var in enumerate(self.checkbox_vars):
                    if i < len(states):
                        var.set(states[i])

    def save_checkbox_states(self):
        """保存数据源框配置"""
        states = [var.get() for var in self.checkbox_vars]
        with open('checkbox_states.json', 'w') as f:
            json.dump(states, f)

    def on_close(self):
        self.save_checkbox_states()
        self.destroy()


if __name__ == "__main__":
    customtkinter.set_appearance_mode("light")
    customtkinter.set_default_color_theme("blue")
    app = App()
    app.mainloop()
