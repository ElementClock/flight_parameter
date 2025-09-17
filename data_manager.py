import pandas as pd
from analysis.analysis_data import analysis_data, AnalysisResult as BaseAnalysisResult


class DataContainer:
    """数据容器类，用于封装原始数据和分析结果"""
    
    def __init__(self, analysis_result, filename):
        """初始化数据容器
        
        Args:
            analysis_result: 分析结果对象
            filename (str): 文件名
        """
        # 使用更灵活的方式处理对象属性，避免手动维护属性对应关系
        self.filename = filename
        self.analysis_result_obj = analysis_result
        
        # 动态获取analysis_result的所有属性
        for attr in dir(analysis_result):
            if not attr.startswith('_'):  # 忽略私有属性
                setattr(self, attr, getattr(analysis_result, attr))
        
        # 合并文本分析结果
        text_parts = []
        if hasattr(analysis_result, 'text_analyze') and analysis_result.text_analyze:
            text_parts.append(analysis_result.text_analyze)
        if hasattr(analysis_result, 'text_engine') and analysis_result.text_engine:
            text_parts.append(analysis_result.text_engine)
        if hasattr(analysis_result, 'text_cas') and analysis_result.text_cas:
            text_parts.append(analysis_result.text_cas)
        
        self.analysis_result = "\n".join(text_parts) if text_parts else ""


class DataManager:
    """数据管理类，用于管理多个数据容器"""
    
    def __init__(self):
        """初始化数据管理器"""
        self.data_containers = {}
        self.current_data_key = None
    
    def add_data(self, df, filename):
        """添加新数据
        
        Args:
            df (pandas.DataFrame): 数据
            filename (str): 文件名
            
        Returns:
            tuple: (数据容器对象, 错误信息)
        """
        try:
            # 分析数据
            analysis_result = analysis_data(df)
            
            # 创建数据容器
            data_container = DataContainer(analysis_result, filename)
            
            # 存储数据容器
            key = data_container.filename
            self.data_containers[key] = data_container
            self.current_data_key = key
            
            return data_container, None
        except Exception as e:
            return None, str(e)
    
    def remove_data(self, key):
        """移除指定数据
        
        Args:
            key (str): 数据键
            
        Returns:
            bool: 是否成功移除
        """
        if key in self.data_containers:
            del self.data_containers[key]
            if self.current_data_key == key:
                self.current_data_key = next(iter(self.data_containers), None) if self.data_containers else None
            return True
        return False
    
    def get_current_data(self):
        """获取当前选中的数据
        
        Returns:
            DataContainer: 当前数据容器对象，如果不存在则返回None
        """
        if self.current_data_key and self.current_data_key in self.data_containers:
            return self.data_containers[self.current_data_key]
        return None
    
    def get_data_keys(self):
        """获取所有数据键列表
        
        Returns:
            list: 数据键列表
        """
        return list(self.data_containers.keys())
    
    def select_data(self, key):
        """选择指定数据
        
        Args:
            key (str): 数据键
            
        Returns:
            bool: 是否成功选择
        """
        if key in self.data_containers:
            self.current_data_key = key
            return True
        return False
    
    def clear_all_data(self):
        """清除所有数据"""
        self.data_containers.clear()
        self.current_data_key = None