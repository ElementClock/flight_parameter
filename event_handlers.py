import threading
import os
import pandas as pd
import wx
from wx import ID_CANCEL, NOT_FOUND


class EventHandlers:
    """事件处理类"""
    
    def __init__(self, app_frame):
        """初始化事件处理器
        
        Args:
            app_frame: 应用程序主窗口实例
        """
        self.app_frame = app_frame
    
    def load_data(self, event):
        """加载CSV数据文件"""
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

            # 在新线程中处理数据加载和分析，避免阻塞UI
            thread = threading.Thread(target=self.process_multiple_data, args=(pathnames,))
            thread.daemon = True
            thread.start()
    
    def process_multiple_data(self, pathnames):
        """在后台线程中处理多个数据文件
        
        Args:
            pathnames: 文件路径列表
        """
        for pathname in pathnames:
            try:
                # 尝试多种编码方式
                encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
                df = None
                last_error = None

                for encoding in encodings:
                    try:
                        df = pd.read_csv(pathname, encoding=encoding)
                        # 添加数据到数据管理器
                        data_container, error = self.app_frame.data_manager.add_data(df, os.path.basename(pathname))
                        if error:
                            raise Exception(error)
                        
                        # 在UI线程中更新界面
                        wx.CallAfter(self.on_single_data_loaded, pathname, encoding, data_container)
                        break
                    except UnicodeDecodeError as e:
                        last_error = e
                        continue
                    except Exception as e:
                        raise e

                if df is None:
                    raise last_error if last_error else Exception("无法读取文件")

            except Exception as e:
                # 在UI线程中显示错误消息
                wx.CallAfter(self.on_data_load_error, pathname, str(e))
    
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
            self.app_frame.content_panel.set_formatted_text(f"显示数据时出错: {str(e)}")
    
    def on_data_load_error(self, pathname, error_message):
        """在UI线程中更新界面 - 数据加载失败
        
        Args:
            pathname: 文件路径
            error_message: 错误信息
        """
        wx.MessageBox(f"无法读取文件 '{pathname}': {error_message}", "错误", wx.OK | wx.ICON_ERROR)
        self.app_frame.content_panel.set_formatted_text(f"加载文件失败: {error_message}")
    
    def save_analysis(self, event):
        """保存分析结果"""
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
                    wx.MessageBox(f"保存文件时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox("暂无分析数据可保存", "提示", wx.OK | wx.ICON_INFORMATION)
    
    def save_current_data(self, event):
        """保存当前选中的数据"""
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
                    wx.MessageBox(f"保存文件时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox("暂无数据可保存", "提示", wx.OK | wx.ICON_INFORMATION)
    
    def remove_analysis(self, event):
        """清除分析数据框信息"""
        self.app_frame.content_panel.set_formatted_text("")
    
    def remove_current_data(self, event):
        """清除当前选中的数据"""
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
    
    def display_current_data(self):
        """显示当前选中数据的分析结果"""
        current_container = self.app_frame.data_manager.get_current_data()
        if current_container:
            text_content = (
                f"文件名: {current_container.filename}\n"
                f"本次文件解析结果如下：\n{current_container.analysis_result}\n")
            self.app_frame.content_panel.set_formatted_text(text_content)
    
    def on_data_choice(self, event):
        """处理数据选择变化事件"""
        selection = self.app_frame.sidebar_panel.data_choice.GetSelection()
        if selection != NOT_FOUND:
            choices = self.app_frame.sidebar_panel.data_choice.GetItems()
            key = choices[selection]
            self.app_frame.data_manager.select_data(key)
            self.display_current_data()
    
    def single_button_event_1(self, event):
        """处理单个文件导出按钮点击事件"""
        # 提交任务到线程池
        pass
    
    def on_close(self, event):
        """处理窗口关闭事件"""
        # 销毁窗口
        self.app_frame.Destroy()