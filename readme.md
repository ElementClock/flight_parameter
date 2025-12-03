# 飞行参数分析工具

## 项目简介

飞行参数分析工具是一个专门用于分析飞行数据的桌面应用程序。该工具可以帮助航空工程技术人员和飞行数据分析人员快速处理和分析飞行参数数据，生成专业的分析报告。

本项目以 [app.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/app.py) 作为主程序，使用 wxPython 构建现代化的图形用户界面。

## 功能特点

### 1. 数据加载与管理
- 支持加载CSV格式的飞行参数数据文件
- 支持同时加载多个数据文件
- 自动尝试多种编码格式（UTF-8、GBK、GB2312等）以确保文件兼容性
- 提供数据管理功能，可在多个加载的文件间切换查看

### 2. 专业飞行数据分析
- **发动机参数分析**：
  - 自动识别发动机启动和关车时间点
  - 检测发动机转速变化情况
  - 分析发动机点火状态
  - 识别发动机起飞状态时间段
  - 检测发动机重启事件
- **CAS告警分析**：
  - 识别CAS告警时间段
  - 分析不同告警类型的发生时间
  - 提供告警持续时间统计
  - 按照警告级、戒备级、提示级、状态级对告警分类
- **燃油系统分析**：
  - 分析各油箱燃油量及消耗情况
  - 监测低油量事件
  - 检测油箱间燃油不平衡情况
  - 分析发动机燃油消耗
  - 检测传感器数据差异
- **电源系统分析**：
  - 分析直流发电机状态（电压、电流、功率）
  - 分析交流发电机状态（电压、电流、功率）
  - 监测汇流条电压和电流
  - 检测发电机负载状态

### 3. 结果展示与交互
- 图形化用户界面，操作简便直观
- 实时显示分析结果
- 支持在多个加载的数据文件间切换查看
- 提供清晰的结果展示区域
- 支持彩色文本显示（告警、重点信息等）

### 4. 数据导出功能
- **保存分析结果**：将分析结果导出为文本文件
- **保存原始数据**：将处理后的数据导出为CSV文件
- **快捷保存**：一键保存当前数据和分析结果，自动命名
- **自动保存**：程序关闭时自动保存加载的数据

### 5. 数据清理功能
- 支持清除当前分析结果显示
- 支持清除当前加载的数据
- 支持清除所有加载的数据

### 6. 用户体验优化
- 高DPI屏幕支持，界面清晰
- 自适应窗口大小，适配不同屏幕分辨率
- 多线程处理数据加载，避免界面卡顿
- 友好的错误提示和操作反馈
- 保存对话框预填充推荐文件名

## 技术架构

### 核心组件

1. **主程序** ([app.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/app.py))
   - 使用wxPython构建图形用户界面
   - 负责窗口管理、事件处理和UI协调
   - 程序入口点

2. **UI组件** ([ui_components.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/ui_components.py))
   - [SidebarPanel](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/ui_components.py#L31-L95)：侧边栏面板，包含操作按钮和数据选择器
   - [ContentPanel](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/ui_components.py#L186-L222)：内容面板，用于显示分析结果

3. **事件处理** ([event_handlers.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/event_handlers.py))
   - 处理用户界面的各种事件
   - 包括数据加载、保存、分析等操作
   - 实现快捷保存功能

4. **数据管理** ([data_manager.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/data_manager.py))
   - 管理加载的数据和分析结果
   - 提供数据访问接口
   - 跟踪原始文件路径

5. **分析模块** ([analysis/](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/analysis))
   - [analysis_data.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/analysis/analysis_data.py)：主分析流程，协调各专业分析模块
   - [engine_analysis.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/analysis/engine_analysis.py)：发动机参数分析
   - [cas_analysis.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/analysis/cas_analysis.py)：CAS告警分析
   - [fuel_analysis.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/analysis/fuel_analysis.py)：燃油系统分析
   - [power_analysis.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/analysis/power_analysis.py)：电源系统分析

6. **工具函数** ([utils.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/utils.py))
   - 提供辅助函数，如窗口尺寸计算等

## 分析功能详解

### 发动机分析 ([engine_analysis.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/analysis/engine_analysis.py))

#### 功能说明
分析发动机数据，提取发动机转速和点火状态，计算转速变化。

#### 判据规则
- 发动机启动成功：发动机转速＞77.5%
- 发动机关车：发动机转速≤3%

#### 识别内容
- 发动机启动和关车时间点
- 发动机转速变化情况
- 发动机点火状态
- 发动机起飞状态时间段
- 发动机重启事件

#### 调用函数
- `analyze_engine(df)`：主分析函数

### CAS告警分析 ([cas_analysis.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/analysis/cas_analysis.py))

#### 功能说明
分析CAS告警数据，识别告警时间段、类型及持续时间统计。

#### 判据规则
- 告警连续性判断：时间间隔超过1秒则认为是不同时间段
- 告警级别分类：基于cas_level.csv文件中的定义

#### 识别内容
- CAS告警时间段
- 不同告警类型的发生时间
- 告警持续时间统计
- 告警级别分类（警告级、戒备级、提示级、状态级）

#### 调用函数
- `analyze_cas(df, engine_start_time, engine_end_time)`：主分析函数
- `find_alarm_periods(alarm_times)`：查找连续告警时间段
- `extract_alarm_periods(df_cas, column)`：提取某一列的告警时间段
- `load_alarm_levels()`：加载告警级别信息
- `group_alarms_by_level(alarms, alarm_levels)`：按级别分组告警

### 燃油系统分析 ([fuel_analysis.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/analysis/fuel_analysis.py))

#### 功能说明
分析燃油系统数据，包括燃油消耗、油箱状态等关键参数。

#### 判据规则
- 低油量阈值：油量低于200kg
- 不平衡油量阈值：左右两侧油量差异超过100kg
- 传感器差异阈值：同一油箱多个传感器数据差异超过20kg

#### 识别内容
- 各油箱燃油量及消耗情况
- 低油量事件监测
- 油箱间燃油不平衡情况
- 发动机燃油消耗
- 传感器数据差异检测

#### 调用函数
- `analyze_fuel(df)`：主分析函数
- `generate_fuel_text_with_markers(fuel_data)`：生成格式化文本输出

### 电源系统分析 ([power_analysis.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/analysis/power_analysis.py))

#### 功能说明
分析电源系统数据，包括直流发电机、交流发电机和汇流条等关键参数。

#### 判据规则
- 直流发电机负载状态：电流≤3200A为正常
- 交流发电机负载状态：电流≤400A为正常

#### 识别内容
- 直流发电机状态（电压、电流、功率）
- 交流发电机状态（电压、电流、功率）
- 汇流条电压和电流
- 发电机负载状态

#### 调用函数
- `analyze_power(df)`：主分析函数
- `generate_power_text_with_markers(power_data)`：生成格式化文本输出

### 标识符识别规则

在保存文件时，系统会根据分析结果自动为文件添加标识符前缀：

- **F**：飞行架次（发动机运行时间超过10分钟）
- **D**：地面试验开车（发动机启动但运行时间较短）
- **N**：未开车（没有发动机启动记录）

文件命名格式为：标识符+时间（年月日），例如：F20251201.csv

## 安装与运行

### 环境要求

- Python 3.6或更高版本
- wxPython
- pandas

### 安装步骤

1. 克隆或下载项目代码
2. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```

### 运行方式

直接运行主程序：
```bash
python app.py
```

### 打包为可执行文件（可选）

使用PyInstaller打包：
```bash
pyinstaller --onefile --windowed app.py
```

## 使用说明

1. **加载数据**：点击"加载数据"按钮，选择CSV格式的飞行参数文件
2. **查看分析结果**：数据加载后会自动进行分析，结果会显示在右侧文本区域
3. **切换数据**：如果有多个数据文件，可以通过下拉菜单切换查看
4. **保存数据**：点击"保存数据"按钮将当前数据保存到文件，对话框会预填充推荐文件名
5. **保存分析**：点击"保存分析"按钮将分析结果保存到文件，对话框会预填充推荐文件名
6. **快捷保存**：点击"快捷保存"按钮一键保存当前数据和分析结果到原始文件所在目录
7. **清除操作**：
   - "清除分析"：清除当前分析结果
   - "清除数据"：清除所有加载的数据

## 项目结构

```
flight_parameter/
├── analysis/                 # 分析模块
│   ├── analysis_data.py      # 主分析流程
│   ├── cas_analysis.py       # CAS告警分析
│   ├── engine_analysis.py    # 发动机分析
│   ├── fuel_analysis.py      # 燃油系统分析
│   └── power_analysis.py     # 电源系统分析
├── visualization/             # 可视化模块
│   └── route_visualization.py # 航线可视化
├── oldfile/                  # 旧版本文件（历史版本，不再维护）
│   ├── App_fparameter.py     # 旧版基于Tkinter的实现
│   └── App_fparameter_wx.py  # 旧版基于wxPython的实现
├── app.py                    # 主程序（当前版本）
├── data_manager.py           # 数据管理器
├── event_handlers.py         # 事件处理器
├── ui_components.py          # UI组件
├── utils.py                  # 工具函数
├── requirements.txt          # 项目依赖
└── readme.md                 # 项目说明文档
```

## 开发规范

- 采用模块化设计，各功能模块职责分离
- UI与业务逻辑分离，便于维护和扩展
- 遵循Python编码规范

## 版本说明

当前主程序为 [app.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/app.py)，使用 wxPython 构建现代化图形界面。

[oldfile/](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/oldfile) 目录中包含旧版本的实现：
- [App_fparameter.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/oldfile/App_fparameter.py)：基于 Tkinter 的旧版本实现
- [App_fparameter_wx.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/oldfile/App_fparameter_wx.py)：早期基于 wxPython 的实现

这些旧版本文件仅作为历史参考，不再维护。

## 待办事项

- [ ] 分离专业分析的子函数功能
- [ ] 增强错误处理机制
- [ ] 优化用户界面体验
- [ ] 增加更多分析模块（如液压、环控等系统）
- [ ] 完善README中的功能说明和使用指南

## 许可证

本项目仅供内部使用。

## 更新历史

- **v1.0**：初始版本，包含基本的飞行参数分析功能
- **v1.1**：重构代码结构，分离UI组件和业务逻辑
- **v2.0**：重新设计架构，以 [app.py](file:///C:/Users/ZZY/Desktop/Test/flight_parameter/app.py) 作为主程序，实现更清晰的模块化结构