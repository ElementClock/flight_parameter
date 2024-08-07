import pandas as pd
import tkinter as tk
import glob
import os
import sys
from tkinter import filedialog
from tkinter import messagebox




def extract_flight_parameter(df_original, df_idx):
    # 提取需要参数并修改名称
    columns_to_extract = df_idx.iloc[:, 0].tolist()
    df = df_original[columns_to_extract]
    new_column_names = df_idx['简化参数名'].tolist()
    df.columns = new_column_names
    # 格林威治标准时间转为北京时间
    df_time = df.loc[:, ('飞行日期', '飞行时间')]
    df_time.loc[:, '飞行日期'] = df_time['飞行日期'].apply(lambda x: f'20{x[:2]}-{x[3:5]}-{x[6:]}')
    df_time.loc[:, 'UTC时间'] = pd.to_datetime(df_time['飞行日期'] + ' ' + df_time['飞行时间'])
    df_time.loc[:, '北京时间'] = df_time['UTC时间'] + pd.Timedelta(hours=8)
    df.loc[:, '飞行日期'] = pd.to_datetime(df_time['北京时间']).dt.date
    df.loc[:, '飞行时间'] = pd.to_datetime(df_time['北京时间']).dt.time
    return df


def center_window(root, width, height):
    # 绘制居中窗口
    screen_width = root.winfo_screenwidth()  # 获取屏幕宽度和高度
    screen_height = root.winfo_screenheight()
    # 计算x和y坐标，使窗口居中
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 3) - (height // 3)
    # 设置窗口位置和大小
    root.geometry(f'{width}x{height}+{int(x)}+{int(y)}')


def on_button_click_1():
    # 选择单个文件导出
    root.withdraw()
    f_path = filedialog.askopenfilename()
    df_original = pd.read_csv(f_path, encoding='gbk')
    # 数据提取
    df = extract_flight_parameter(df_original, df_idx)
    out_path = f_path[:-15] + '(数据提取).csv'
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    # quit()
    root.destroy()


def on_button_click_2():
    # 批量文件导出
    root.withdraw()  # 隐藏Tkinter窗口
    # 弹出文件夹选择对话框
    folder_path = filedialog.askdirectory()  # 返回选定的文件夹路径
    # 定义匹配规则
    pattern = '*_00_001_Phy.csv'
    # 使用glob找到所有匹配的文件
    matching_files = glob.glob(os.path.join(folder_path, pattern))
    # 遍历所有匹配的文件并进行处理
    for f_path in matching_files:
        df_original = pd.read_csv(f_path, encoding='gbk')
        # 数据提取
        df = extract_flight_parameter(df_original, df_idx)
        out_path = f_path[:-15] + '(数据提取).csv'
        df.to_csv(out_path, index=False, encoding='utf-8-sig')
    # 关闭Tkinter窗口（虽然它已经被隐藏了）
    root.destroy()

def data_fk():
    # 输出处理   起落数统计 开车关车时间统计  告警数统计及持续时间段

    df = 1


if __name__ == '__main__':
    # 初始化提取参数-通用
    root = tk.Tk()
    center_window(root, 400, 300) # 创建主窗口
    root.title("飞参数据处理")
    if os.path.exists('init_flight_parameter.csv'):
        df_idx = pd.read_csv('init_flight_parameter.csv')
    else:
        # 如果文件不存在，创建一个新的空DataFrame
        messagebox.showinfo("文件缺失", "请新建文件init_flight_parameter.csv，并配置抽引参数")
        sys.exit()

    # 创建按钮并指定其点击时执行的函数
    # 单文件导出
    button1 = tk.Button(root, text="单个文件导出", command=on_button_click_1)
    button1.pack(pady=20)  # 使用pack布局管理器，并添加一些垂直填充
    button2 = tk.Button(root, text="批量文件导出", command=on_button_click_2)
    button2.pack(pady=20)  # 使用pack布局管理器，并添加一些垂直填充

    # 进入主事件循环
    root.mainloop()
