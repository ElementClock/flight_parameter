import re
import pandas as pd


def analyze_engine(df):
    """
    分析发动机数据：提取发动机转速和点火状态，计算转速变化
    发动机启动成功	发动机转速＞77.5%
    发动机关车	发动机转速≤3%
    """
    # 生成分析结果
    result = []
    takeoff_info = []  # 存储符合条件的发动机信息
    df_takeoff = pd.DataFrame(columns=['i', 'start_time'])  # 存储符合条件的发动机信息
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
        result.append(f"未找到包含 '机电信息采集系统' 的列")
        result.append(f"未找到包含 '主飞控系统' 的列")
        # 修改返回值为三元组避免解包错误
        return "\n".join(result), None, None

    # 提取转速数据并计算转速变化
    engine_rpm = pd.DataFrame({f"engine_{i}_rpm": df[col] for i, col in enumerate(rpm_columns, 1)})
    engine_rpm_diff = engine_rpm.diff()

    # 提取点火状态数据
    engine_ignition = pd.DataFrame({f"engine_{i}_ignition": df[col] for i, col in enumerate(ignition_columns, 1)})

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
                start_time = df.loc[rpm_start.index[0], '飞行时间']
                engine_start_times.append(start_time)
                
                # 找到转速小于等于3%的时期，认为发动机关车
                rpm_shutdown = period_data[period_data <= 3.0]
                if not rpm_shutdown.empty:
                    end_time = df.loc[rpm_shutdown.index[-1], '飞行时间']
                    engine_end_times.append(end_time)
        
        # 如果有多次启动，记录重启信息
        if len(engine_start_times) > 1:
            restart_info[i] = engine_start_times[1:]  # 除了第一次启动，其余都是重启
        
        # 记录该发动机的首次启动和最终关车时间
        if engine_start_times:
            all_engine_start_times.append(min(engine_start_times))
            takeoff_info.append(f"{i}号发动机首次开车时间为 {min(engine_start_times)}")
            # 如果有重启，添加重启信息
            if i in restart_info:
                restart_times_str = ", ".join([str(t) for t in restart_info[i]])
                takeoff_info.append(f"{i}号发动机存在 {len(restart_info[i])} 次重启，重启时间点为: {restart_times_str}")
        
        if engine_end_times:
            all_engine_end_times.append(max(engine_end_times))

    # 确定所有发动机首次启动时间（最早的一次）和最终关车时间（最晚的一次）
    if all_engine_start_times:
        takeoff_start_time = min(all_engine_start_times)
    
    if all_engine_end_times:
        takeoff_end_time = max(all_engine_end_times)

    # 新增逻辑：输出符合条件的发动机信息
    if takeoff_info:
        # 使用 '**' 标记标题行，便于后续格式化处理
        title = "**动力分析结果**"
        formatted_title = title.center(100, '-')
        result.append(formatted_title)
        if takeoff_start_time and takeoff_end_time:
            gap_time = takeoff_end_time - takeoff_start_time
            result.append(f" 开关车时间为：{takeoff_start_time}-{takeoff_end_time}，耗时：{gap_time} ")
        result.extend(takeoff_info)
    # 新增逻辑：当所有发动机都未启动时，说明分析时间范围并提示无开车记录
    else:
        start_time = df['飞行时间'].iloc[0]
        end_time = df['飞行时间'].iloc[-1]
        result.append(f"本文件时间为： {start_time} 到 {end_time}\n 本次数据分析：飞机未启动发动机，请检查数据" )

    # 修改返回值包含起飞时间字段
    return "\n".join(result), takeoff_start_time, takeoff_end_time
