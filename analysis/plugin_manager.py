#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
插件管理器模块
==============

负责管理和协调分析插件的加载、注册和执行。
"""

import logging
import importlib
import pkgutil
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Callable, Optional
from abc import ABC, abstractmethod

from analysis.analysis_interface import AnalysisInterface

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class PluginConfig:
    """插件配置类"""
    
    def __init__(self, name: str, enabled: bool = True, priority: int = 0, dependencies: List[str] = None):
        """初始化插件配置
        
        Args:
            name (str): 插件名称
            enabled (bool): 是否启用插件
            priority (int): 插件优先级，数字越大优先级越高
            dependencies (List[str]): 依赖的其他插件列表
        """
        self.name = name
        self.enabled = enabled
        self.priority = priority
        self.dependencies = dependencies or []


class PluginManager:
    """插件管理器类，用于管理分析插件的生命周期"""
    
    def __init__(self):
        """初始化插件管理器"""
        self.plugins: Dict[str, AnalysisInterface] = {}
        self.plugin_configs: Dict[str, PluginConfig] = {}
        self.plugin_order: List[str] = []
        
    def register_plugin(self, name: str, plugin: AnalysisInterface, config: Optional[PluginConfig] = None):
        """注册一个插件
        
        Args:
            name (str): 插件名称
            plugin (AnalysisInterface): 插件实例
            config (PluginConfig, optional): 插件配置
        """
        if not isinstance(plugin, AnalysisInterface):
            raise TypeError("Plugin must implement AnalysisInterface")
            
        self.plugins[name] = plugin
        self.plugin_configs[name] = config or PluginConfig(name)
        self._update_plugin_order()
        logging.info(f"Registered plugin: {name}")
        
    def unregister_plugin(self, name: str):
        """注销一个插件
        
        Args:
            name (str): 插件名称
        """
        if name in self.plugins:
            del self.plugins[name]
            del self.plugin_configs[name]
            self._update_plugin_order()
            logging.info(f"Unregistered plugin: {name}")
            
    def get_plugin(self, name: str) -> AnalysisInterface:
        """获取指定插件实例
        
        Args:
            name (str): 插件名称
            
        Returns:
            AnalysisInterface: 插件实例
        """
        return self.plugins.get(name)
        
    def get_plugins(self) -> Dict[str, AnalysisInterface]:
        """获取所有插件
        
        Returns:
            Dict[str, AnalysisInterface]: 插件字典
        """
        return self.plugins.copy()
        
    def get_plugin_order(self) -> List[str]:
        """获取插件执行顺序
        
        Returns:
            List[str]: 插件名称列表
        """
        return self.plugin_order.copy()
        
    def set_plugin_config(self, name: str, config: PluginConfig):
        """设置插件配置
        
        Args:
            name (str): 插件名称
            config (PluginConfig): 插件配置
        """
        self.plugin_configs[name] = config
        self._update_plugin_order()
        
    def enable_plugin(self, name: str, enabled: bool = True):
        """启用或禁用插件
        
        Args:
            name (str): 插件名称
            enabled (bool): 是否启用
        """
        if name in self.plugin_configs:
            self.plugin_configs[name].enabled = enabled
            self._update_plugin_order()
            
    def _update_plugin_order(self):
        """根据优先级和依赖关系更新插件执行顺序"""
        # 只考虑启用的插件
        enabled_plugins = {name: config for name, config in self.plugin_configs.items() if config.enabled}
        
        # 按优先级排序
        sorted_plugins = sorted(enabled_plugins.items(), key=lambda x: x[1].priority, reverse=True)
        
        # 简单的依赖处理（实际项目中可能需要更复杂的拓扑排序）
        ordered_names = []
        for name, config in sorted_plugins:
            # 检查依赖是否满足
            deps_satisfied = all(dep in enabled_plugins for dep in config.dependencies)
            if deps_satisfied:
                ordered_names.append(name)
            else:
                logging.warning(f"Plugin {name} has unsatisfied dependencies and will be skipped")
                
        self.plugin_order = ordered_names
        
    def execute_analysis(self, df, **kwargs) -> Dict[str, Any]:
        """并行执行所有插件的分析
        
        Args:
            df: 要分析的数据
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 分析结果字典
        """
        results = {}
        
        # 使用线程池并行执行分析
        # 限制最大线程数以避免资源耗尽
        max_workers = min(4, len(self.plugin_order), multiprocessing.cpu_count())
        
        if max_workers <= 1:
            # 如果只有一个插件或者CPU核心数不足，串行执行
            for plugin_name in self.plugin_order:
                plugin = self.plugins[plugin_name]
                try:
                    # 传递之前插件的结果给后续插件
                    plugin_kwargs = kwargs.copy()
                    plugin_kwargs.update(results)
                    
                    result = plugin.analyze(df, **plugin_kwargs)
                    results[plugin_name] = result
                    logging.info(f"Executed analysis plugin: {plugin_name}")
                except Exception as e:
                    logging.error(f"Error executing plugin {plugin_name}: {str(e)}")
                    results[plugin_name] = {"error": str(e)}
        else:
            # 并行执行分析
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_plugin = {}
                for plugin_name in self.plugin_order:
                    plugin = self.plugins[plugin_name]
                    # 传递之前插件的结果给后续插件
                    plugin_kwargs = kwargs.copy()
                    plugin_kwargs.update(results)
                    
                    future = executor.submit(self._run_plugin_analysis, plugin, df, plugin_kwargs)
                    future_to_plugin[future] = plugin_name
                
                # 收集结果
                for future in as_completed(future_to_plugin):
                    plugin_name = future_to_plugin[future]
                    try:
                        result = future.result()
                        results[plugin_name] = result
                        logging.info(f"Executed analysis plugin: {plugin_name}")
                    except Exception as e:
                        logging.error(f"Error executing plugin {plugin_name}: {str(e)}")
                        results[plugin_name] = {"error": str(e)}
                        
        return results
    
    def _run_plugin_analysis(self, plugin, df, plugin_kwargs):
        """运行单个插件分析的包装函数"""
        return plugin.analyze(df, **plugin_kwargs)
        
    def generate_reports(self, analysis_data: Dict[str, Any]) -> Dict[str, str]:
        """生成所有插件的文本报告
        
        Args:
            analysis_data (Dict[str, Any]): 分析数据
            
        Returns:
            Dict[str, str]: 文本报告字典
        """
        reports = {}
        
        for plugin_name in self.plugin_order:
            plugin = self.plugins[plugin_name]
            try:
                # 获取对应插件的分析数据
                plugin_data = analysis_data.get(plugin_name, {})
                report = plugin.generate_text(plugin_data)
                reports[plugin_name] = report
                logging.info(f"Generated report for plugin: {plugin_name}")
            except Exception as e:
                logging.error(f"Error generating report for plugin {plugin_name}: {str(e)}")
                reports[plugin_name] = f"Error generating report: {str(e)}"
                
        return reports
        
    def discover_and_load_plugins(self, package_name: str = "analysis"):
        """动态发现并加载插件
        
        Args:
            package_name (str): 包名，默认为analysis
        """
        try:
            package = importlib.import_module(package_name)
            for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
                if ispkg:
                    continue
                    
                # 检查是否为分析插件（以_analysis.py结尾的文件）
                if modname.endswith('_analysis') and modname != 'data_analyzer':
                    try:
                        module = importlib.import_module(f"{package_name}.{modname}")
                        # 查找模块中的AnalysisInterface实现
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if (isinstance(attr, type) and 
                                issubclass(attr, AnalysisInterface) and 
                                attr != AnalysisInterface):
                                # 实例化插件
                                plugin_instance = attr()
                                plugin_name = plugin_instance.get_name()
                                self.register_plugin(plugin_name, plugin_instance)
                                logging.info(f"Discovered and loaded plugin: {plugin_name} from {modname}")
                    except Exception as e:
                        logging.warning(f"Failed to load plugin from {modname}: {str(e)}")
        except Exception as e:
            logging.error(f"Error discovering plugins: {str(e)}")