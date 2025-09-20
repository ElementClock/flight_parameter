import re
import pandas as pd


def analyze_engine(df):
    """
    分析发动机数据：提取发动机转速和点火状态，计算转速变化
    发动机启动成功	发动机转速＞77.5%
    发动机关车	发动机转速≤3%
    
    Args:
        df (pandas.DataFrame): 包含发动机数据的DataFrame
        
    Returns:
        dict: 发动机分析结果
    """
    # 初始化返回数据
    engine_result = {
        'type': 'engine',
        'has_takeoff_info': False,
        'takeoff_info': [],
        'takeoff_start_time': None,
        'takeoff_end_time': None,
        'start_time': None,
        'end_time': None
    }
    
    # 存储符合条件的发动机信息
    takeoff_info = []
    
    # 新增初始化字段用于返回起飞时间
    takeoff_start_time = None
    takeoff_end_time = None
    
    # 新增：记录发动机重启信息
    restart_info = {}

    # 使用正则表达式匹配所有需要的列
    rpm_pattern = re.compile(r'(\d)发发动机转速')
    ignition_pattern = re.compile(r'(\d)发点火状态')

    # 提取转速和点火状态列
    rpm_columns = sorted([col for col in df.columns if rpm_pattern.search(col)],
                         key=lambda x: int(rpm_pattern.search(x).group(1)))
    ignition_columns = sorted([col for col in df.columns if ignition_pattern.search(col)],
                              key=lambda x: int(ignition_pattern.search(x).group(1)))

    # 检查是否有数据
    if not rpm_columns or not ignition_columns:
        engine_result['errors'] = [
            "未找到包含 '机电信息采集系统' 的列",
            "未找到包含 '主飞控系统' 的列"
        ]
        return engine_result

    try:
        # 优化内存使用：只选择需要的列进行处理
        selected_columns = ['飞行时间'] + rpm_columns + ignition_columns
        df_selected = df[selected_columns].copy()
        
        # 提取转速数据并计算转速变化
        engine_rpm = pd.DataFrame({f"engine_{i}_rpm": df_selected[col] for i, col in enumerate(rpm_columns, 1)})
        engine_rpm_diff = engine_rpm.diff()

        # 提取点火状态数据
        engine_ignition = pd.DataFrame({f"engine_{i}_ignition": df_selected[col] for i, col in enumerate(ignition_columns, 1)})

        # 新增：存储所有发动机的启动和关车时间
        all_engine_start_times = []
        all_engine_end_times = []
        
        for i in range(1, len(rpm_columns) + 1):
            rpm = engine_rpm[f"engine_{i}_rpm"]
            ignition = engine_ignition[f"engine_{i}_ignition"]

            # 找到点火状态为1的期间
            ignition_on_periods = (ignition == 1).cumsum()
            
            # 新增：记录该发动机的所有启动和关车时间
            engine_start_times = []
            engine_end_times = []
            engine_restart_times = []  # 记录该发动机的重启时间

            # 获取所有点火状态为1的期间
            periods = ignition_on_periods[ignition_on_periods > 0].unique()
            
            for period in periods:
                # 获取该期间的数据
                period_data = rpm[ignition_on_periods == period]
                if period_data.empty:  # 该期间没有数据
                    continue  # 跳过该期间

                # 找到转速大于等于77.5%的时刻，认为发动机启动成功
                rpm_start = period_data[period_data >= 77.5]

                if not rpm_start.empty:
                    start_time = df_selected.loc[rpm_start.index[0], '飞行时间']
                    engine_start_times.append(start_time)
                    
                    # 找到转速小于等于3%的时期，认为发动机关车
                    rpm_shutdown = period_data[period_data <= 3.0]
                    if not rpm_shutdown.empty:
                        end_time = df_selected.loc[rpm_shutdown.index[-1], '飞行时间']
                        engine_end_times.append(end_time)
            
            # 如果有多次启动，记录重启信息
            if len(engine_start_times) > 1:
                restart_info[i] = engine_start_times[1:]  # 除了第一次启动，其余都是重启
            
            # 记录该发动机的首次启动和最终关车时间
            if engine_start_times:
                all_engine_start_times.append(min(engine_start_times))
                takeoff_info.append({
                    'engine_id': i,
                    'start_time': min(engine_start_times)
                })
                # 如果有重启，添加重启信息
                if i in restart_info:
                    takeoff_info[-1]['restart_times'] = restart_info[i]
            
            if engine_end_times:
                all_engine_end_times.append(max(engine_end_times))

        # 确定所有发动机首次启动时间（最早的一次）和最终关车时间（最晚的一次）
        if all_engine_start_times:
            takeoff_start_time = min(all_engine_start_times)
        
        if all_engine_end_times:
            takeoff_end_time = max(all_engine_end_times)

        # 填充返回数据
        engine_result['has_takeoff_info'] = bool(takeoff_info)
        engine_result['takeoff_info'] = takeoff_info
        engine_result['takeoff_start_time'] = takeoff_start_time
        engine_result['takeoff_end_time'] = takeoff_end_time
        engine_result['start_time'] = df_selected['飞行时间'].iloc[0] if not df_selected.empty and '飞行时间' in df_selected.columns else None
        engine_result['end_time'] = df_selected['飞行时间'].iloc[-1] if not df_selected.empty and '飞行时间' in df_selected.columns else None
        
        # 清理临时数据以释放内存
        del df_selected, engine_rpm, engine_rpm_diff, engine_ignition
    except Exception as e:
        engine_result['errors'] = [f"分析发动机数据时出错: {str(e)}"]
    
    return engine_result