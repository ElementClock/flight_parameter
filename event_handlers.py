import threading
import os
import pandas as pd
import wx
import logging
from wx import ID_CANCEL, NOT_FOUND

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class EventHandlers:
    """事件处理类"""
    
    def __init__(self, app_frame):
        """初始化事件处理器
        
        Args:
            app_frame: 应用程序主窗口实例
        """
        try:
            self.app_frame = app_frame
            self.current_progress = 0
        except Exception as e:
            logging.error(f"初始化事件处理器时出错: {str(e)}")
            raise e
    
    def load_data(self, event):
        """加载CSV数据文件"""
        try:
            with wx.FileDialog(
                    self.app_frame,
                    message="选择CSV文件",
                    wildcard="CSV文件 (*.csv)|*.csv",
                    style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE
            ) as fileDialog:
                if fileDialog.ShowModal() == ID_CANCEL:
                    return

                pathnames = fileDialog.GetPaths()
                # 显示正在加载的消息
                self.app_frame.content_panel.textbox.SetValue("正在加载和分析数据，请稍候...\n")
                # 显示进度条
                self.app_frame.sidebar_panel.show_progress(True)

                # 在新线程中处理数据加载和分析，避免阻塞UI
                thread = threading.Thread(target=self.process_multiple_data, args=(pathnames,))
                thread.daemon = True
                thread.start()
        except Exception as e:
            logging.error(f"加载数据时出错: {str(e)}")
            wx.MessageBox(f"加载数据时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def _update_analysis_progress(self, value, message=""):
        """更新分析进度的内部方法
        
        Args:
            value (int): 进度值(0-100)
            message (str): 进度消息
        """
        try:
            # 确保进度值在有效范围内
            value = max(0, min(100, value))
            self.current_progress = value
            wx.CallAfter(self.app_frame.sidebar_panel.update_progress, value, message)
        except Exception as e:
            logging.error(f"更新分析进度时出错: {str(e)}")
    
    def _detect_file_encoding(self, filepath, encodings=['utf-8', 'gbk', 'gb2312', 'latin1']):
        """
        尝试用不同编码读取文件来检测文件编码
        
        Args:
            filepath (str): 文件路径
            encodings (list): 尝试的编码列表
            
        Returns:
            str: 检测到的编码，如果无法检测则返回None
        """
        # 读取文件的前几行进行测试
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    f.read(1024)  # 读取前1024个字符
                logging.info(f"使用 {encoding} 编码成功读取文件头部")
                return encoding
            except UnicodeDecodeError:
                logging.warning(f"使用 {encoding} 编码读取文件失败")
                continue
            except Exception as e:
                logging.warning(f"使用 {encoding} 编码读取文件时出现其他错误: {str(e)}")
                continue
        return None
    
    def _read_large_csv_in_chunks(self, pathname, encoding, chunksize=10000):
        """分块读取大型CSV文件以优化内存使用
        
        Args:
            pathname (str): 文件路径
            encoding (str): 文件编码
            chunksize (int): 每次读取的行数
            
        Returns:
            pandas.DataFrame: 读取的完整数据框
        """
        try:
            # 先读取列名以确定数据结构
            df_sample = pd.read_csv(pathname, encoding=encoding, nrows=5)
            columns = df_sample.columns.tolist()
            
            chunks = []
            total_rows = 0
            
            # 获取总行数用于进度计算
            with open(pathname, 'r', encoding=encoding) as f:
                total_rows = sum(1 for _ in f) - 1  # 减去标题行
            
            rows_read = 0
            for chunk in pd.read_csv(pathname, encoding=encoding, chunksize=chunksize):
                chunks.append(chunk)
                rows_read += len(chunk)
                
                # 更新进度（前20%用于文件读取）
                progress_msg = f"正在读取文件: {os.path.basename(pathname)} ({rows_read}/{total_rows} 行)"
                wx.CallAfter(self.app_frame.sidebar_panel.update_progress, 
                             int((rows_read / total_rows) * 20), progress_msg)
            
            # 合并所有块
            df = pd.concat(chunks, ignore_index=True)
            
            # 清理临时数据以释放内存
            del chunks
            
            return df
        except UnicodeDecodeError as e:
            logging.error(f"使用 {encoding} 编码分块读取CSV文件时出错: {str(e)}")
            raise e
        except Exception as e:
            logging.error(f"分块读取CSV文件时出错: {str(e)}")
            raise e
    
    def process_multiple_data(self, pathnames):
        """在后台线程中处理多个数据文件
        
        Args:
            pathnames: 文件路径列表
        """
        try:
            total_files = len(pathnames)
            for i, pathname in enumerate(pathnames):
                try:
                    # 更新进度
                    progress_msg = f"正在处理文件 {i+1}/{total_files}: {os.path.basename(pathname)}"
                    wx.CallAfter(self.app_frame.sidebar_panel.update_progress, 
                                 int((i / total_files) * 10), progress_msg)  # 前10%用于文件准备
                    
                    # 首先尝试检测文件编码
                    detected_encoding = self._detect_file_encoding(pathname)
                    
                    # 定义尝试的编码列表
                    encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
                    if detected_encoding and detected_encoding not in encodings:
                        # 将检测到的编码放在首位
                        encodings.insert(0, detected_encoding)
                    elif detected_encoding:
                        # 如果检测到的编码在列表中，将其移到首位
                        encodings.remove(detected_encoding)
                        encodings.insert(0, detected_encoding)
                    
                    df = None
                    last_error = None

                    for encoding in encodings:
                        try:
                            # 检查文件大小以决定是否使用分块读取
                            file_size = os.path.getsize(pathname)
                            size_threshold = 50 * 1024 * 1024  # 50MB阈值
                            
                            if file_size > size_threshold:
                                # 对大文件使用分块读取
                                df = self._read_large_csv_in_chunks(pathname, encoding)
                            else:
                                # 对小文件直接读取
                                df = pd.read_csv(pathname, encoding=encoding)
                            
                            # 添加数据到数据管理器，传递进度回调函数
                            data_container, error = self.app_frame.data_manager.add_data(
                                df, 
                                os.path.basename(pathname),
                                progress_callback=self._update_analysis_progress
                            )
                            if error:
                                raise Exception(error)
                            
                            # 在UI线程中更新界面
                            wx.CallAfter(self.on_single_data_loaded, pathname, encoding, data_container)
                            break
                        except UnicodeDecodeError as e:
                            last_error = e
                            logging.warning(f"使用 {encoding} 编码读取文件失败: {str(e)}")
                            continue
                        except Exception as e:
                            logging.error(f"处理文件 {pathname} 时出错: {str(e)}")
                            raise e

                    if df is None:
                        error_msg = f"无法使用任何编码读取文件: {pathname}"
                        logging.error(error_msg)
                        raise last_error if last_error else Exception(error_msg)

                except Exception as e:
                    # 在UI线程中显示错误消息
                    wx.CallAfter(self.on_data_load_error, pathname, str(e))
            
            # 完成所有文件处理后隐藏进度条
            wx.CallAfter(self.app_frame.sidebar_panel.show_progress, False)
        except Exception as e:
            logging.error(f"处理多个数据文件时出错: {str(e)}")
            wx.CallAfter(self.app_frame.sidebar_panel.show_progress, False)
            wx.CallAfter(self.on_data_load_error, "所有文件", str(e))
    
    def on_single_data_loaded(self, pathname, encoding, data_container):
        """在UI线程中更新界面 - 单个数据加载成功
        
        Args:
            pathname: 文件路径
            encoding: 文件编码
            data_container: 数据容器对象
        """
        try:
            # 更新下拉菜单
            choices = self.app_frame.data_manager.get_data_keys()
            self.app_frame.sidebar_panel.data_choice.Set(choices)
            
            # 设置当前加载的数据为选中状态
            if choices:
                self.app_frame.sidebar_panel.data_choice.SetSelection(len(choices) - 1)  # 选择最新添加的项
            
            # 使用富文本格式显示数据
            text_content = (
                f"成功加载文件({encoding}编码): {pathname}\n"
                f"文件名: {data_container.filename}\n"
                f"本次文件解析结果如下：\n{data_container.analysis_result}\n")
            
            self.app_frame.content_panel.set_formatted_text(text_content)
        except Exception as e:
            logging.error(f"显示加载数据时出错: {str(e)}")
            self.app_frame.content_panel.set_formatted_text(f"显示数据时出错: {str(e)}")
    
    def on_data_load_error(self, pathname, error_message):
        """在UI线程中更新界面 - 数据加载失败
        
        Args:
            pathname: 文件路径
            error_message: 错误信息
        """
        try:
            logging.error(f"无法读取文件 '{pathname}': {error_message}")
            wx.MessageBox(f"无法读取文件 '{pathname}': {error_message}", "错误", wx.OK | wx.ICON_ERROR)
            self.app_frame.content_panel.set_formatted_text(f"加载文件失败: {error_message}")
            # 隐藏进度条
            self.app_frame.sidebar_panel.show_progress(False)
        except Exception as e:
            logging.error(f"处理数据加载错误时出错: {str(e)}")
    
    def save_analysis(self, event):
        """保存分析结果"""
        try:
            current_container = self.app_frame.data_manager.get_current_data()
            if current_container:
                with wx.FileDialog(
                    self.app_frame,
                    message="保存分析结果",
                    wildcard="文本文件 (*.txt)|*.txt",
                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                ) as fileDialog:
                    if fileDialog.ShowModal() == wx.ID_CANCEL:
                        return

                    pathname = fileDialog.GetPath()
                    if not pathname.endswith('.txt'):
                        pathname += '.txt'
                    # 确保目录存在
                    os.makedirs(os.path.dirname(pathname) or '.', exist_ok=True)
                    
                    try:
                        # 从当前数据容器中获取分析结果
                        with open(pathname, 'w', encoding='utf-8') as f:
                            f.write(current_container.analysis_result)
                        self.app_frame.content_panel.set_formatted_text(f"分析结果已保存至: {pathname}")
                    except Exception as e:
                        logging.error(f"保存分析结果时出错: {str(e)}")
                        wx.MessageBox(f"保存文件时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            else:
                wx.MessageBox("暂无分析数据可保存", "提示", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            logging.error(f"保存分析结果时出错: {str(e)}")
            wx.MessageBox(f"保存分析结果时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def save_current_data(self, event):
        """保存当前选中的数据"""
        try:
            current_container = self.app_frame.data_manager.get_current_data()
            if current_container:
                with wx.FileDialog(
                    self.app_frame,
                    message="保存CSV数据",
                    wildcard="CSV文件 (*.csv)|*.csv",
                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                ) as fileDialog:
                    if fileDialog.ShowModal() == wx.ID_CANCEL:
                        return

                    pathname = fileDialog.GetPath()
                    if not pathname.endswith('.csv'):
                        pathname += '.csv'
                    # 确保目录存在
                    os.makedirs(os.path.dirname(pathname) or '.', exist_ok=True)
                    
                    try:
                        current_container.df.to_csv(pathname, encoding='utf-8-sig', index=False)
                        self.app_frame.content_panel.set_formatted_text(f"数据已保存至: {pathname}")
                    except Exception as e:
                        logging.error(f"保存数据时出错: {str(e)}")
                        wx.MessageBox(f"保存文件时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            else:
                wx.MessageBox("暂无数据可保存", "提示", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            logging.error(f"保存当前数据时出错: {str(e)}")
            wx.MessageBox(f"保存当前数据时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def remove_analysis(self, event):
        """清除分析数据框信息"""
        try:
            self.app_frame.content_panel.set_formatted_text("")
        except Exception as e:
            logging.error(f"清除分析时出错: {str(e)}")
    
    def remove_current_data(self, event):
        """清除当前选中的数据"""
        try:
            current_key = self.app_frame.data_manager.current_data_key
            if current_key:
                # 从数据管理器中移除数据
                success = self.app_frame.data_manager.remove_data(current_key)
                
                if success:
                    # 更新下拉菜单选项
                    choices = self.app_frame.data_manager.get_data_keys()
                    self.app_frame.sidebar_panel.data_choice.Set(choices)
                    
                    # 如果还有其他数据，选择第一个；否则清空当前选择
                    if choices:
                        self.app_frame.data_manager.select_data(choices[0])
                        self.app_frame.sidebar_panel.data_choice.SetSelection(0)
                        # 显示选中的数据
                        self.display_current_data()
                    else:
                        self.app_frame.content_panel.set_formatted_text("所有数据已清除")
                else:
                    wx.MessageBox("没有选中的数据可清除", "提示", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox("没有选中的数据可清除", "提示", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            logging.error(f"清除当前数据时出错: {str(e)}")
            wx.MessageBox(f"清除当前数据时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def display_current_data(self):
        """显示当前选中数据的分析结果"""
        try:
            current_container = self.app_frame.data_manager.get_current_data()
            if current_container:
                text_content = (
                    f"文件名: {current_container.filename}\n"
                    f"本次文件解析结果如下：\n{current_container.analysis_result}\n")
                self.app_frame.content_panel.set_formatted_text(text_content)
        except Exception as e:
            logging.error(f"显示当前数据时出错: {str(e)}")
            self.app_frame.content_panel.set_formatted_text(f"显示当前数据时出错: {str(e)}")
    
    def on_data_choice(self, event):
        """处理数据选择变化事件"""
        try:
            selection = self.app_frame.sidebar_panel.data_choice.GetSelection()
            if selection != NOT_FOUND:
                choices = self.app_frame.sidebar_panel.data_choice.GetItems()
                key = choices[selection]
                self.app_frame.data_manager.select_data(key)
                self.display_current_data()
        except Exception as e:
            logging.error(f"处理数据选择变化时出错: {str(e)}")
            self.app_frame.content_panel.set_formatted_text(f"处理数据选择变化时出错: {str(e)}")
    
    def single_button_event_1(self, event):
        """处理单个文件导出按钮点击事件"""
        try:
            # 提交任务到线程池
            pass
        except Exception as e:
            logging.error(f"处理单个文件导出按钮点击事件时出错: {str(e)}")
    
    def on_close(self, event):
        """处理窗口关闭事件"""
        try:
            # 销毁窗口
            self.app_frame.Destroy()
        except Exception as e:
            logging.error(f"处理窗口关闭事件时出错: {str(e)}")