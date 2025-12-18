# 开发者文档

## 项目结构

```
flight_parameter/
├── src/
│   └── flight_parameter/
│       ├── __init__.py
│       ├── main.py               # 主程序入口
│       ├── core/                 # 核心应用模块
│       │   ├── __init__.py
│       │   ├── app.py            # 应用程序主类
│       │   └── data_manager.py   # 数据管理器
│       ├── analysis/             # 分析模块
│       │   ├── __init__.py
│       │   ├── analysis_interface.py # 分析接口定义
│       │   ├── config.py         # 分析配置
│       │   ├── logger.py         # 日志模块
│       │   ├── utils.py          # 分析工具函数
│       │   ├── plugin_manager.py # 插件管理器
│       │   ├── data_analyzer.py  # 主分析流程
│       │   ├── engines/          # 发动机分析模块
│       │   │   ├── __init__.py
│       │   │   └── engine_analysis.py
│       │   ├── cas/              # CAS告警分析模块
│       │   │   ├── __init__.py
│       │   │   └── cas_analysis.py
│       │   ├── fuel/             # 燃油系统分析模块
│       │   │   ├── __init__.py
│       │   │   └── fuel_analysis.py
│       │   └── power/            # 电源系统分析模块
│       │       ├── __init__.py
│       │       └── power_analysis.py
│       ├── event_handlers/       # 事件处理器模块
│       │   ├── __init__.py
│       │   ├── base.py           # 基础类和常量
│       │   ├── route_visualization.py  # 航路点绘制处理器
│       │   ├── data_loading.py   # 数据加载处理器
│       │   ├── data_saving.py    # 数据保存处理器
│       │   ├── analysis_saving.py# 分析结果保存处理器
│       │   ├── quick_saving.py   # 快捷保存处理器
│       │   ├── batch_processing.py# 批量处理处理器
│       │   ├── data_clearing.py  # 数据清除处理器
│       │   ├── analysis_clearing.py# 分析清除处理器
│       │   ├── data_selection.py # 数据选择处理器
│       │   └── closing.py        # 关闭事件处理器
│       ├── ui/                   # UI组件模块
│       │   ├── __init__.py
│       │   └── components.py     # UI组件
│       ├── utils/                # 工具模块
│       │   ├── __init__.py
│       │   ├── file_utils.py     # 文件工具
│       │   └── system_utils.py   # 系统工具
│       ├── config/               # 配置模块
│       │   ├── __init__.py
│       │   └── app_config.py     # 应用配置
│       └── resources/            # 资源文件
│           ├── __init__.py
│           └── app_icon.ico      # 应用图标
├── tests/                        # 测试用例
│   ├── __init__.py
│   ├── test_engine_analysis.py
│   └── test_data_analyzer.py
├── visualization/                # 可视化模块
│   └── route_visualization.py    # 航线可视化
├── app.py                       # 向后兼容的主程序入口
├── data_manager.py              # 向后兼容的数据管理器
├── ui_components.py             # 向后兼容的UI组件
├── utils.py                     # 向后兼容的工具函数
├── requirements.txt             # 项目依赖
├── setup.py                    # 安装配置
└── README.md                   # 项目说明文档
```

## 开发环境搭建

### 1. 克隆项目代码

```bash
git clone <repository-url>
cd flight_parameter
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

### 3. 安装依赖包

```bash
pip install -r requirements.txt
```

## 代码规范

### 命名规范

1. 类名使用大驼峰命名法（CamelCase）
2. 函数和变量名使用小写字母，单词间用下划线分隔（snake_case）
3. 常量名全部大写，单词间用下划线分隔（UPPER_CASE）
4. 私有成员以单下划线开头（_private_method）

### 注释规范

1. 所有公共类和函数都应有文档字符串（docstring）
2. 复杂逻辑应有行内注释解释
3. 使用中文编写注释和文档

### 代码组织

1. 每个模块应有明确的职责
2. 遵循SOLID原则设计类和接口
3. 使用类型提示增强代码可读性

## 测试

### 运行测试

```bash
python -m unittest discover tests
```

### 编写测试

1. 每个模块应有对应的测试文件
2. 测试应覆盖正常情况和异常情况
3. 使用unittest框架编写测试用例

## 架构设计

### 设计原则

1. **单一职责原则**：每个类只负责一项功能
2. **开闭原则**：对扩展开放，对修改封闭
3. **里氏替换原则**：子类可以替换父类
4. **接口隔离原则**：使用多个专门的接口，而不是一个总接口
5. **依赖倒置原则**：依赖抽象，而不是具体实现

### 模块关系

```
app.py -> event_handlers.py -> data_manager.py -> analysis/
                                                -> ui_components.py
                                                -> utils.py
```

### 分析模块接口

所有分析模块都应实现`AnalysisInterface`接口：

```python
class AnalysisInterface(ABC):
    @abstractmethod
    def analyze(self, df, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def generate_text(self, analysis_data: Dict[str, Any]) -> str:
        pass
```

## 性能优化

### 数据处理优化

1. 避免使用`df.iterrows()`，优先使用向量化操作
2. 使用`df.copy()`时注意内存使用
3. 及时释放不需要的大对象

### 内存管理

1. 避免不必要的数据复制
2. 使用生成器处理大数据集
3. 及时清理临时变量

## 发布流程

### 版本号管理

遵循语义化版本控制（SemVer）：
- MAJOR版本：不兼容的API修改
- MINOR版本：向下兼容的功能性新增
- PATCH版本：向下兼容的问题修正

### 打包发布

```bash
python setup.py sdist bdist_wheel
twine upload dist/*
```