#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能测试脚本
"""

import time
import os
import tempfile
import pandas as pd
import numpy as np
from data_manager import DataManager
from analysis.data_analyzer import DataAnalyzer

def create_test_data(file_path, rows=1000):
    """创建测试数据"""
    # 创建测试数据
    data = {
        'col1': pd.date_range('2023-01-01', periods=rows, freq='1min'),
        'col2': np.random.randint(0, 2, rows),
        'col3': np.random.randint(0, 24, rows),
        'col4': np.random.randint(1, 32, rows),  # 日期
        'col5': np.random.randint(0, 2, rows),   # 标志位
        'col6': np.random.randint(0, 60, rows),  # 时间
        '发动机1转速': np.random.uniform(0, 100, rows),
        '发动机2转速': np.random.uniform(0, 100, rows),
        '发动机3转速': np.random.uniform(0, 100, rows),
        '发动机4转速': np.random.uniform(0, 100, rows),
        '显示告警系统1': np.random.randint(0, 2, rows),
        '显示告警系统2': np.random.randint(0, 2, rows),
    }
    
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    return file_path

def test_performance():
    """测试性能优化效果"""
    print("开始性能测试...")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"临时目录: {temp_dir}")
    
    # 创建测试文件
    test_files = []
    for i in range(5):
        file_path = os.path.join(temp_dir, f"test_data_{i}.csv")
        create_test_data(file_path, rows=2000)
        test_files.append(file_path)
        print(f"创建测试文件: {file_path}")
    
    # 测试数据管理器性能
    data_manager = DataManager()
    
    start_time = time.time()
    
    # 测试分析多个文件
    for i, file_path in enumerate(test_files):
        try:
            print(f"正在分析文件 {i+1}/{len(test_files)}: {os.path.basename(file_path)}")
            df = pd.read_csv(file_path, encoding='utf-8-sig', dtype={3: str})
            result = data_manager.data_analyzer.analyze(df)
            print(f"  分析完成，结果类型: {type(result)}")
        except Exception as e:
            print(f"  分析出错: {e}")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print(f"\n性能测试完成!")
    print(f"总共处理 {len(test_files)} 个文件")
    print(f"耗时: {elapsed_time:.2f} 秒")
    print(f"平均每个文件耗时: {elapsed_time/len(test_files):.2f} 秒")
    
    # 清理临时文件
    for file_path in test_files:
        try:
            os.remove(file_path)
        except:
            pass
    try:
        os.rmdir(temp_dir)
    except:
        pass

if __name__ == "__main__":
    test_performance()