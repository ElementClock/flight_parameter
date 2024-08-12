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
        if os.path.exists('init_flight_parameter.csv'):
            df_idx = pd.read_csv('init_flight_parameter.csv')
            # 将df_idx作为实例变量保存
            self.df_idx = df_idx
        else:
            # 如果文件不存在，创建一个新的空DataFrame
            messagebox.showinfo("文件缺失", "请新建文件init_flight_parameter.csv，并配置抽引参数")
            sys.exit()
        """"主窗口"""
        self.title("飞行数据快速处理")
        # 获取屏幕的宽度和高度
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        user32 = ctypes.windll.user32
        real_screen_width = user32.GetSystemMetrics(0)
        # real_screen_height = user32.GetSystemMetrics(1)
        # 由于geometry 大小为缩放后的像素大小，位置为真实像素位置，因此需要计算dpi恢复真实位置
        real_dpi = real_screen_width // screen_width
        window_width = 1000  # 窗口长度 系统DPI缩放后的值
        window_height = 618  # 窗口高度
        x = ((screen_width // 2) - (window_width // 2)) * real_dpi
        y = ((screen_height // 2) - (window_height // 2)) * real_dpi * 0.75  # 向上偏一点更好看
        self.geometry(f'{window_width}x{window_height}+{int(x)}+{int(y)}')
        self.resizable(False, False)
        """部件创建"""
        # 设置侧边栏
        self.sidebar_frame = customtkinter.CTkFrame(self, corner_radius=0)
        # 设置侧边栏标题
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="选择导出模式",
                                                 font=customtkinter.CTkFont(size=15, weight="bold"))
        # 侧边栏内按钮
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, command=self.single_button_event,
                                                        text="单个文件导出")
        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, command=self.multi_button_event,
                                                        text="多个文件导出")
        self.sidebar_button_del_msg = customtkinter.CTkButton(self.sidebar_frame, command=self.del_button_event,
                                                              text="重置信息框")
        # 文本框
        self.textbox = customtkinter.CTkTextbox(self, width=280)
        self.logo_msg_box = customtkinter.CTkLabel(self, text="数据分析结果",
                                                   font=customtkinter.CTkFont(size=15, weight="bold"))

        """部件外观"""
        # row行 column列 row span跨行 sticky网格单元格内对齐和扩展 padx=(20, 0)：这个参数是一个元组，指定了控件在水平方向上的内边距
        # 第一列部件
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.logo_label.grid(row=0, column=0, padx=0, pady=(20, 10))
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
        self.sidebar_button_del_msg.grid(row=3, column=0, padx=20, pady=10)
        # 第二列部件
        self.logo_msg_box.grid(row=0, column=1, padx=0, pady=(20, 10))
        self.textbox.grid(row=1, column=1, rowspan=2, padx=(20, 20), pady=(10, 10), sticky="nsew")

        """布局权重"""
        self.grid_rowconfigure(1, weight=1)  # 行配置 index行号，weight权重
        self.grid_columnconfigure(1, weight=1)  # 列配置 index列号，weight权重

    def single_button_event(self):
        df, text_analyze, = ffp.single_abstract(self.df_idx)
        # 使用 "1.0" 作为插入文本的起始位置，这表示从文本框的第1行第0列开始插入内容。
        self.textbox.insert("1.0", text_analyze)
        return

    def multi_button_event(self):
        ffp.multi_abstract(self.df_idx)
        return

    def del_button_event(self):
        # 清空现有内容 使用 "1.0" 作为插入文本的起始位置，这表示从文本框的第1行第0列开始插入内容。
        self.textbox.delete("1.0", customtkinter.END)
        return


if __name__ == "__main__":
    app = App()
    app.mainloop()
