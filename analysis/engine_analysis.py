import re

import pandas as pd


def analyze_engine(df):
    """
    分析发动机数据：提取发动机转速和点火状态，计算转速变化
    """
    # 生成分析结果
    result = []
    takeoff_info = []  # 存储符合条件的发动机信息
    df_takeoff = pd.DataFrame(columns=['i', 'start_time'])  # 存储符合条件的发动机信息
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
        return "\n".join(result)

    # 提取转速数据并计算转速变化
    engine_rpm = pd.DataFrame({f"engine_{i}_rpm": df[col] for i, col in enumerate(rpm_columns, 1)})
    engine_rpm_diff = engine_rpm.diff()

    # 提取点火状态数据
    engine_ignition = pd.DataFrame({f"engine_{i}_ignition": df[col] for i, col in enumerate(ignition_columns, 1)})

    for i in range(1, len(rpm_columns) + 1):
        rpm = engine_rpm[f"engine_{i}_rpm"]
        ignition = engine_ignition[f"engine_{i}_ignition"]

        # 找到点火状态为1的期间
        ignition_on_periods = (ignition == 1).cumsum()

        # 定位第一个连续为1的期间
        first_period = ignition_on_periods[ignition_on_periods > 0].min()
        if first_period == 0:  # 没有找到任何点火状态为1的期间
            result.append(f"发动机 {i} 分析：未找到点火状态为1的期间！")
            continue

        # 获取第一个期间的数据
        period_data = rpm[ignition_on_periods == first_period]
        if period_data.empty:  # 该期间没有数据
            result.append(f"发动机 {i} 分析：点火状态为1的期间内无有效数据！")
            continue  # 跳过该期间

        # 找到转速从0提升至20的时刻
        rpm_0_to_20 = period_data[(period_data >= 0) & (period_data <= 20)]
        if rpm_0_to_20.empty:
            result.append(f"发动机 {i} 分析：未找到转速从0提升至20的时刻！")
            continue
        start_time = df.loc[rpm_0_to_20.index[0], '飞行时间']

        # 找到转速从不为0之后继续提升至80的时刻
        rpm_not_0_to_80 = rpm[(rpm > 0) & (rpm <= 80)]
        if rpm_not_0_to_80.empty:
            result.append(f"发动机 {i} 分析：未找到转速从不为0提升至80的时刻！")
            continue
        end_time = df.loc[rpm_not_0_to_80.index[-1], '飞行时间']

        # 检查结束时间是否超出点火状态为1的持续期间
        if end_time > df.loc[period_data.index[-1], '飞行时间']:
            end_time = df.loc[period_data.index[-1], '飞行时间']

        # 新增逻辑：记录符合条件的发动机信息
        takeoff_info.append(f"{i}号发动机开车时间为 {start_time}")
        # 创建新行数据
        new_row = pd.DataFrame({'i': [i], 'start_time': [start_time]})
        # 将新行追加到 DataFrame
        df_takeoff = pd.concat([df_takeoff, new_row], ignore_index=True)

    # 新增逻辑：输出符合条件的发动机信息
    if takeoff_info:
        takeoff_time = df_takeoff['start_time'].min()
        result.append(f"\n开车时间为：{takeoff_time} ")
        result.extend(takeoff_info)

    return "\n".join(result)
