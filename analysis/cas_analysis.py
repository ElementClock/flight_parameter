import logging
import pandas as pd
from datetime import datetime, time  # 新增time模块导入

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def find_alarm_periods(alarm_times):
    """找到连续告警的时间段"""
    if alarm_times.empty:
        return []

    periods = []
    start_time = None

    for i, time in enumerate(alarm_times):
        if start_time is None:
            start_time = time

        # 判断是否连续，只要存在间断，则结束当前时间段
        if i < len(alarm_times) - 1 and (alarm_times.iloc[i + 1] - time).total_seconds() > 1:
            end_time = time
            periods.append((start_time, end_time))
            start_time = None
        elif i == len(alarm_times) - 1:
            end_time = time
            periods.append((start_time, end_time))

    return periods


def extract_alarm_periods(df_cas, column):
    """
    提取某一列的告警时间段
    """
    try:
        mask = df_cas[column] == 1
        assert mask.ndim == 1, f"索引条件 {column} 不是一维的"
        alarm_times = df_cas.loc[mask, '飞行时间']
        if isinstance(alarm_times, pd.DataFrame):
            alarm_times = alarm_times.squeeze()
        return find_alarm_periods(alarm_times) if not alarm_times.empty else []
    except KeyError:
        logging.warning(f"列 {column} 或 '飞行时间' 列存在问题")
        return []
    except AssertionError as e:
        logging.warning(f"断言错误: {e}")
        return []


def analyze_cas(df, engine_start_time, engine_end_time):
    """
    告警分析主函数
    """
    result = []

    if df.empty:
        result.append("输入的 DataFrame 为空，请检查数据源")
        return "\n".join(result)

    if '飞行时间' not in df.columns:
        result.append("DataFrame 中缺少 '飞行时间' 列")
        return "\n".join(result)

    alarm_columns = df.filter(like='显示告警系统').columns
    if alarm_columns.empty:
        result.append("未找到包含 '显示告警系统' 的列")
        return "\n".join(result)

    df_cas = df[['飞行时间'] + alarm_columns.tolist()]
    alarm_periods_dict = {}

    for column in alarm_columns:
        periods = extract_alarm_periods(df_cas, column)
        if periods:
            alarm_periods_dict[column] = periods

    # 新建 df_summary 并填充数据
    summary_data = []
    for column, periods in alarm_periods_dict.items():
        for start, end in periods:
            # 添加时间范围过滤条件
            if (engine_start_time is None or start >= engine_start_time) and (engine_end_time is None or end <= engine_end_time):
                duration = (end - start).total_seconds()+1
                minutes, seconds = divmod(int(duration), 60)
                duration_str = f"{minutes} 分钟 {seconds} 秒" if duration >= 60 else f"{duration:.0f} 秒"
                summary_data.append({
                    '告警名称': column,
                    '开始时间': start.strftime('%H:%M:%S'),
                    '结束时间': end.strftime('%H:%M:%S'),
                    '持续时间': duration_str
                })

    df_summary = pd.DataFrame(summary_data)

    # 使用 '**' 标记标题行，便于后续格式化处理
    title = "**CAS告警分析结果**"
    formatted_title = title.center(100, '-')
    result.append(formatted_title)

    # 自定义格式化输出
    # 初始化当前告警变量为None，用于后续判断是否为同一个告警
    current_alarm = None

    # 定义各列名称及对应宽度，以便后续格式化输出
    # 遍历摘要数据框的每一行，iterrows()返回索引和行数据
    for _, row in df_summary.iterrows():
        # 提取当前行的告警信息
        alarm_name = row['告警名称']
        start_time = row['开始时间']
        end_time = row['结束时间']
        duration = row['持续时间']

        time_info = (
            f"{' '.ljust(30, ' ')}"
            f" 时间：{start_time}-{end_time.ljust(15)}"
            f" 持续时间：{duration}"
        )
        # 判断当前告警与上一条告警是否相同
        if alarm_name != current_alarm:
            # 如果不相同，先输出告警名称
            result.append(f"{alarm_name}")
            result.append(time_info)
            # 更新当前告警变量
            current_alarm = alarm_name
        else:
            result.append(time_info)

    return "\n".join(result)