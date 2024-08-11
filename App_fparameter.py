import ctypes
import os
import sys
from tkinter import messagebox

import customtkinter
import pandas as pd

import func_fparameter as ffp


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("飞行数据快速处理")
        if os.path.exists('init_flight_parameter.csv'):
            df_idx = pd.read_csv('init_flight_parameter.csv')
            # 将df_idx作为实例变量保存
            self.df_idx = df_idx
        else:
            # 如果文件不存在，创建一个新的空DataFrame
            messagebox.showinfo("文件缺失", "请新建文件init_flight_parameter.csv，并配置抽引参数")
            sys.exit()
        # 获取屏幕的宽度和高度
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        user32 = ctypes.windll.user32
        real_screen_width = user32.GetSystemMetrics(0)
        # real_screen_height = user32.GetSystemMetrics(1)
        # 由于geometry 大小为缩放后的像素大小，位置为真实像素位置，因此需要计算dpi恢复真实位置
        real_dpi = real_screen_width // screen_width
        window_width = 500  # 窗口长度 系统DPI缩放后的值
        window_height = 309  # 窗口高度
        x = ((screen_width // 2) - (window_width // 2)) * real_dpi
        y = ((screen_height // 2) - (window_height // 2)) * real_dpi * 0.75  # 向上偏一点更好看
        self.geometry(f'{window_width}x{window_height}+{int(x)}+{int(y)}')
        self.resizable(False, False)
        # 设置侧边栏
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=1, sticky="nsew")  # row span指定跨域多少行
        self.grid_columnconfigure(0, weight=0)
        # 设置侧边栏标题
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="选择导出模式",
                                                 font=customtkinter.CTkFont(size=15, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        # 侧边栏内按钮
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, command=self.single_button_event1,
                                                        text="单个文件导出")
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, command=self.multi_button_event2,
                                                        text="多个文件导出")
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)

    def single_button_event1(self):
        ffp.single_abstract(self.df_idx)

    def multi_button_event2(self):
        ffp.multi_abstract(self.df_idx)


if __name__ == "__main__":
    app = App()
    app.mainloop()
