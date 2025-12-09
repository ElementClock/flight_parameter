import matplotlib
matplotlib.use('Agg')  # 设置matplotlib后端为非交互式
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
import pandas as pd
from adjustText import adjust_text
import random
from rtree import index
import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import os
from abc import ABC, abstractmethod
from openpyxl import Workbook
import logging
import os
from typing import Dict, List, Tuple, Any

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np
from shapely.geometry import Point
import rtree as index

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CoordinateParser(ABC):
    """坐标解析器抽象基类"""
    
    @abstractmethod
    def parse(self, coord_str):
        """解析坐标字符串，返回(纬度, 经度)的十进制度数"""
        pass


class DDMMFormatParser(CoordinateParser):
    """DDMM.M格式坐标解析器（度分格式，带小数）"""
    
    def parse(self, coord_str):
        if not isinstance(coord_str, str):
            return None, None
        
        # 移除空格
        coord_str = coord_str.replace(' ', '')
        
        # 提取纬度和经度部分
        if 'N' in coord_str and 'E' in coord_str:
            parts = coord_str.split('E')
            lat_part = parts[0].replace('N', '')
            lon_part = parts[1]
            
            # 解析纬度 (格式为 DDMM.M ，例如 3045.100)
            if '.' in lat_part and len(lat_part) > 2 and lat_part[2] != '.':  
                degrees = int(lat_part[:2])
                minutes = float(lat_part[2:])
                latitude = degrees + minutes / 60
            else:
                return None, None
            
            # 解析经度 (格式为 DDDMM.M ，例如 11151.180)
            if '.' in lon_part and len(lon_part) > 3 and lon_part[3] != '.':  
                degrees = int(lon_part[:3])
                minutes = float(lon_part[3:])
                longitude = degrees + minutes / 60
            else:
                return None, None
                
            return latitude, longitude
        
        return None, None


class DDMMSSFormatParser(CoordinateParser):
    """DDMMSS格式坐标解析器（度分秒格式）"""
    
    def parse(self, coord_str):
        if not isinstance(coord_str, str):
            return None, None
        
        # 移除空格
        coord_str = coord_str.replace(' ', '')
        
        # 提取纬度和经度部分
        if 'N' in coord_str and 'E' in coord_str:
            parts = coord_str.split('E')
            lat_part = parts[0].replace('N', '')
            lon_part = parts[1]
            
            # 解析纬度 (格式为 DDMMSS ，例如 304510)
            if len(lat_part) >= 6:
                degrees = int(lat_part[:2])
                minutes = int(lat_part[2:4])
                seconds = int(lat_part[4:6])
                latitude = degrees + minutes/60 + seconds/3600
            else:
                return None, None
            
            # 解析经度 (格式为 DDDMMSS ，例如 1115118)
            if len(lon_part) >= 7:
                degrees = int(lon_part[:3])
                minutes = int(lon_part[3:5])
                seconds = int(lon_part[5:7])
                longitude = degrees + minutes/60 + seconds/3600
            else:
                return None, None
                
            return latitude, longitude
        
        return None, None


class DDDecimalFormatParser(CoordinateParser):
    """DD.D格式坐标解析器（只有度，带小数）"""
    
    def parse(self, coord_str):
        if not isinstance(coord_str, str):
            return None, None
        
        # 移除空格
        coord_str = coord_str.replace(' ', '')
        
        # 提取纬度和经度部分
        if 'N' in coord_str and 'E' in coord_str:
            parts = coord_str.split('E')
            lat_part = parts[0].replace('N', '')
            lon_part = parts[1]
            
            # 解析纬度 (格式为 DD.D ，例如 30.75)
            if '.' in lat_part and len(lat_part) <= 5:  # 限制长度避免误判
                try:
                    latitude = float(lat_part)
                except ValueError:
                    return None, None
            else:
                return None, None
            
            # 解析经度 (格式为 DDD.D ，例如 111.85)
            if '.' in lon_part and len(lon_part) <= 6:  # 限制长度避免误判
                try:
                    longitude = float(lon_part)
                except ValueError:
                    return None, None
            else:
                return None, None
                
            return latitude, longitude
        
        return None, None


class CoordinateParserFactory:
    """坐标解析器工厂类"""
    
    @staticmethod
    def create_parser(coord_str):
        """根据坐标字符串特征创建适当的解析器"""
        if not isinstance(coord_str, str):
            return None
        
        coord_str = coord_str.replace(' ', '')
        
        if 'N' not in coord_str or 'E' not in coord_str:
            return None
        
        parts = coord_str.split('E')
        if len(parts) != 2:
            return None
            
        lat_part = parts[0].replace('N', '')
        lon_part = parts[1]
        
        # 判断纬度格式
        lat_is_ddmm_m = '.' in lat_part and len(lat_part) > 2 and lat_part[2] != '.'
        lat_is_ddmmss = len(lat_part) >= 6 and '.' not in lat_part
        lat_is_d_decimal = '.' in lat_part and (len(lat_part) <= 5 or lat_part[2] == '.')
        
        # 判断经度格式
        lon_is_dddmm_m = '.' in lon_part and len(lon_part) > 3 and lon_part[3] != '.'
        lon_is_dddmmss = len(lon_part) >= 7 and '.' not in lon_part
        lon_is_ddd_decimal = '.' in lon_part and (len(lon_part) <= 6 or lon_part[3] == '.')
        
        # 根据组合判断使用哪种解析器
        if lat_is_ddmm_m and lon_is_dddmm_m:
            return DDMMFormatParser()
        elif lat_is_ddmmss and lon_is_dddmmss:
            return DDMMSSFormatParser()
        elif lat_is_d_decimal and lon_is_ddd_decimal:
            return DDDecimalFormatParser()
        
        # 默认返回DDMM格式解析器
        return DDMMFormatParser()


# 省会城市数据
capital_cities = {
    '沈阳': (123.4291, 41.7969),
    '长春': (125.3245, 43.8868),
    '哈尔滨': (126.6424, 45.7569),
    '呼和浩特': (111.6708, 40.8183),
    '北京': (116.4074, 39.9042),
    '天津': (117.1902, 39.1256),
    '石家庄': (114.5025, 38.0455),
    '太原': (112.5489, 37.8564),
    '济南': (117.0009, 36.6758),
    '郑州': (113.6189, 34.7474),
    '西安': (108.9480, 34.2632),
    '兰州': (103.8236, 36.0580),
    '银川': (106.2782, 38.4664),
    '西宁': (101.7789, 36.6232),
    '乌鲁木齐': (87.6177, 43.7928),
    '合肥': (117.2830, 31.8612),
    '南京': (118.7969, 32.0603),
    '武汉': (114.3052, 30.5929),
    '长沙': (112.9823, 28.1955),
    '南昌': (115.8582, 28.6829),
    '杭州': (120.1551, 30.2741),
    '上海': (121.4737, 31.2304),
    '福州': (119.3062, 26.0753),
    '广州': (113.2806, 23.1252),
    '海口': (110.3312, 20.0319),
    '南宁': (108.3200, 22.8240),
    '重庆': (106.5505, 29.5638),
    '成都': (104.0659, 30.6595),
    '昆明': (102.7123, 25.0406),
    '贵阳': (106.7135, 26.5783),
    '拉萨': (91.1322, 29.6604),
    '台北': (121.5091, 25.0443),
    '香港': (114.1095, 22.3964),
    '澳门': (113.5491, 22.1990)
}

# 省份名称映射和颜色配置
PROVINCE_NAME_MAPPING = {
    'Hubei': '湖北',
    'Henan': '河南', 
    'Shanxi': '山西',
    'Hebei': '河北',
    'Tianjin': '天津',
    'Beijing': '北京',
    'Anhui': '安徽',
    'Jiangsu': '江苏',
    'Shandong': '山东',
    'Shaanxi': '陕西'
}

PROVINCE_COLORS_MAPPED = {
    'Hubei': '#FFCCCC', 
    'Henan': '#CCFFCC', 
    'Shanxi': '#CCCCFF', 
    'Hebei': '#FFEECC', 
    'Tianjin': '#EECCFF', 
    'Beijing': '#CCFFEE',
    'Anhui': '#FFCCCC',  # 使用相同颜色
    'Jiangsu': '#CCFFCC',  # 使用相同颜色
    'Shandong': '#CCCCFF',  # 使用相同颜色
    'Shaanxi': '#FFEECC'   # 使用相同颜色
}

HIGH_CONTRAST_COLORS = [
    '#9D65C9',   # 深紫色
    '#4ECDC4',   # 青色
    '#FF9F1C',   # 亮橙色
    '#E71D36'    # 红色
]

PROVINCE_TO_CAPITAL = {
    'Hubei': '武汉',
    'Anhui': '合肥',
    'Jiangsu': '南京',
    'Shandong': '济南',
    'Henan': '郑州',
    'Shanxi': '太原',
    'Hebei': '石家庄',
    'Tianjin': '天津',
    'Beijing': '北京',
    'Shaanxi': '西安'
}

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class DataLoader(ABC):
    """数据加载器抽象基类，使用模板方法模式"""
    
    def load_data(self, file_path, sheet_name=0):
        """
        模板方法：定义数据加载的算法骨架
        
        参数:
        file_path (str): 文件路径
        sheet_name (str or int): 工作表名称或索引
        
        返回:
        tuple: (waypoints, route_order)
        """
        if not self.check_file_exists(file_path):
            self.create_template(file_path)
        
        return self.parse_data(file_path, sheet_name)
    
    def check_file_exists(self, file_path):
        """检查文件是否存在"""
        return os.path.exists(file_path)
    
    @abstractmethod
    def create_template(self, file_path):
        """创建模板文件"""
        pass
    
    @abstractmethod
    def parse_data(self, file_path, sheet_name):
        """解析数据"""
        pass


class ExcelDataLoader(DataLoader):
    """Excel数据加载器"""
    
    def create_template(self, file_path):
        """
        创建示例Excel文件，包含基本的航路点数据格式
        
        参数:
        file_path (str): 要创建的Excel文件路径
        """
        # 创建一个新的工作簿
        wb = Workbook()
        
        # 创建示例工作表
        ws = wb.active
        ws.title = "Sheet1"
        
        # 添加表头
        headers = ['序号', '航路点', '频率', '坐标', '最低安全高度（M）', '距离（KM）']
        for col_idx, header in enumerate(headers, start=1):
            ws.cell(row=1, column=col_idx, value=header)
        
        # 添加示例行数据
        sample_data = [
            [1, '武汉机场', '110.50', 'N3045.100E11151.180', 1000, 0],
            [2, '合肥VL', '112.70', 'N3185.100E11715.180', 1200, 200],
            [3, '南京机场', '114.20', 'N3205.100E11895.180', 900, 400]
        ]
        
        for row_idx, row_data in enumerate(sample_data, start=2):
            for col_idx, cell_value in enumerate(row_data, start=1):
                ws.cell(row=row_idx, column=col_idx, value=cell_value)
        
        # 保存文件
        wb.save(file_path)
        print(f"已创建示例Excel文件: {file_path}")
    
    def parse_data(self, file_path, sheet_name=0):
        """
        从Excel文件加载航路点数据
        
        参数:
        file_path (str): Excel文件路径
        sheet_name (str or int): 工作表名称或索引，默认为第一个工作表
        
        返回:
        waypoints (dict): 航路点数据，格式为 {名称: {"lat": 纬度, "lon": 经度, "type": 类型}}
        route_order (list): 航路点顺序列表
        """
        # 读取Excel文件的指定工作表
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.error(f"读取Excel文件失败: {e}")
            return {}, []
        
        # 检查是否是空的工作表
        if df.empty:
            logger.warning(f"工作表 '{sheet_name}' 是空的")
            return {}, []
        
        waypoints = {}
        route_order = []
        
        # 定义点类型映射
        def get_point_type(name):
            if '机场' in name:
                return 'airport'
            elif any(x in name for x in ['VL', 'ML', 'LYA', 'GU', 'SQ', 'YIH', 'DRZ', 'HFE', 'WTM', 'WHA']):
                return 'vor'
            else:
                return 'fix'
        
        # 统一处理所有工作表
        # 确定正确的列名
        if '航路点' in df.columns:
            name_column = '航路点'
            coord_column = '坐标'
        else:
            # 如果列名包含特殊字符或者没有正确识别，使用位置索引
            name_column = df.columns[1]  # 第二列应该是航路点名称
            coord_column = df.columns[3]  # 第四列应该是坐标
            
        # 删除航路点名称为空的行
        df = df.dropna(subset=[name_column])
        
        for _, row in df.iterrows():
            name = str(row[name_column]).strip()
            coord = row[coord_column]
            
            # 解析坐标
            lat, lon = parse_coordinates(coord)
            
            if lat is not None and lon is not None:
                point_type = get_point_type(name)
                waypoints[name] = {
                    "lat": lat,
                    "lon": lon,
                    "type": point_type
                }
                route_order.append(name)
            else:
                logger.warning(f"警告: 无法解析航路点 {name} 的坐标: {coord}", exc_info=coord_error)
        
        return waypoints, route_order


def parse_coordinates(coord_str):
    """
    解析坐标字符串，格式如：N305901E1120314 或 N304510E1115118
    返回 (纬度, 经度) 的十进制度数
    """
    parser = CoordinateParserFactory.create_parser(coord_str)
    if parser:
        return parser.parse(coord_str)
    return None, None


# 缓存shapefile reader以提高性能
_shapefile_reader = None

def _get_shapefile_reader():
    """获取shapefile reader实例，带缓存"""
    global _shapefile_reader
    if _shapefile_reader is None:
        try:
            # 使用10米分辨率的数据以提高边界精度
            shpfilename = shpreader.natural_earth(resolution='10m',
                                                  category='cultural',
                                                  name='admin_1_states_provinces')
            _shapefile_reader = shpreader.Reader(shpfilename)
        except Exception as e:
            print(f"无法加载省份shapefile数据: {e}")
            _shapefile_reader = None
    return _shapefile_reader


def draw_route_map(waypoints, route_order, title='航路图', save_path=None, figure_size=(12, 9), margins=None, show_all_provinces=True):
    """
    绘制航路图
    
    参数:
    waypoints (dict): 航路点数据，格式为 {名称: {"lat": 纬度, "lon": 经度, "type": 类型}}
    route_order (list): 航路点顺序列表
    title (str): 图表标题
    save_path (str): 保存路径，如果为None则不保存
    figure_size (tuple): 图像大小 (宽度, 高度)
    margins (dict): 边距设置 {'left': 0.1, 'right': 0.9, 'top': 0.9, 'bottom': 0.1}
    show_all_provinces (bool): 保留参数，但当前实现中未使用
    """
    # 创建matplotlib图形和轴，使用4:3的比例
    fig = plt.figure(figsize=figure_size)
    fig.set_tight_layout(True)  # 使用tight_layout确保内容填满图形
    
    try:
        # 尝试使用系统中文字体，如果失败则使用默认字体
        try:
            chinese_font = fm.FontProperties(fname=r'C:\Windows\Fonts\simhei.ttf')
        except:
            try:
                chinese_font = fm.FontProperties(fname='/System/Library/Fonts/PingFang.ttc')  # macOS
            except:
                chinese_font = fm.FontProperties()  # Linux或其他系统
    except:
        chinese_font = fm.FontProperties()

    # 设置边距
    if margins:
        plt.subplots_adjust(left=margins.get('left', 0.1), 
                           right=margins.get('right', 0.9), 
                           top=margins.get('top', 0.9), 
                           bottom=margins.get('bottom', 0.1))

    # 设置地图投影和范围
    ax = plt.axes(projection=ccrs.Mercator())
    ax.set_extent([105, 125, 28, 41], crs=ccrs.PlateCarree())

    # 添加地图要素
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.add_feature(cfeature.LAKES, alpha=0.3)
    ax.add_feature(cfeature.RIVERS, linewidth=0.5)

    # 过滤掉不在waypoints中的点
    filtered_route_order = [point for point in route_order if point in waypoints]
    
    # 转换航路点坐标
    route_lons = [waypoints[point]["lon"] for point in filtered_route_order]
    route_lats = [waypoints[point]["lat"] for point in filtered_route_order]

    # 打印起点和终点信息，用于调试
    if filtered_route_order:
        print(f"航线起点: {filtered_route_order[0]} ({waypoints[filtered_route_order[0]]['lon']}, {waypoints[filtered_route_order[0]]['lat']})")
        print(f"航线终点: {filtered_route_order[-1]} ({waypoints[filtered_route_order[-1]]['lon']}, {waypoints[filtered_route_order[-1]]['lat']})")
    
    try:
        # 获取shapefile reader
        reader = _get_shapefile_reader()
        if reader is None:
            # 如果无法加载shapefile数据，使用默认的陆地颜色
            ax.add_feature(cfeature.LAND, facecolor='lightgray')
        else:
            # 只读取需要的记录以提高性能
            all_records = list(reader.records())
            
            # 筛选出中国省份的数据以提高性能
            records = [record for record in all_records if record.attributes.get('adm0_a3') == 'CHN' or 
                       record.attributes.get('name') in ['Taiwan', 'Hong Kong', 'Macau']]
            
            # 通过检查航路点确定航线经过的省份
            provinces_crossed = set()
            from shapely.geometry import Point
            
            # 预先计算所有省份的边界框并构建空间索引以提高性能
            spatial_index = index.Index()
            province_geoms = {}  # 保存省份几何对象以便后续查询
            
            # 为每个省份构建空间索引
            for i, record in enumerate(records):
                name = record.attributes.get('name', '')
                bounds = record.geometry.bounds  # (minx, miny, maxx, maxy)
                province_geoms[i] = {
                    'geometry': record.geometry,
                    'name': name,
                    'bounds': bounds
                }
                # 将省份的边界框加入空间索引
                spatial_index.insert(i, bounds)
            
            # 检查每个航路点所在的省份
            for waypoint_name, data in waypoints.items():
                point = Point(data["lon"], data["lat"])
                point_coords = (data["lon"], data["lat"])
                
                # 使用空间索引快速找到可能包含该点的省份候选
                candidates = list(spatial_index.intersection(point_coords + point_coords))
                
                # 只对候选省份进行精确的包含检查
                for i in candidates:
                    province_data = province_geoms[i]
                    try:
                        if province_data['geometry'].contains(point):
                            provinces_crossed.add(province_data['name'])
                            break  # 找到所在省份后跳出循环
                    except Exception as e:
                        pass  # 忽略单个点的计算错误
            
            # 固定随机种子以确保一致性
            random.seed(42)
            
            # 为每个经过的省份分配颜色
            province_colors = {}
            province_list = list(provinces_crossed)
            
            if province_list:
                # 为每个省份分配颜色，确保相邻省份颜色不同
                # 使用预定义的高对比度颜色
                color_count = len(HIGH_CONTRAST_COLORS)
                
                # 创建一个字典来存储省份之间的相邻关系
                province_adjacency = {}
                
                # 构建省份相邻关系图，使用空间索引来提高性能
                province_geometries = {}  # 保存省份几何信息以供后续使用
                province_bounds = {}      # 保存省份边界框
                province_items = {}       # 保存省份索引项
                province_index = index.Index()  # 空间索引
                
                # 预处理省份数据
                for i, record in enumerate(records):
                    name = record.attributes.get('name', '')
                    if name in province_list:
                        province_geometries[name] = record.geometry
                        bounds = record.geometry.bounds
                        province_bounds[name] = bounds
                        province_items[name] = i
                        province_index.insert(i, bounds)
                
                # 计算省份之间的相邻关系
                for name1 in province_list:
                    province_adjacency[name1] = []
                    # 使用空间索引找到邻近的省份候选
                    nearby_candidates = list(province_index.intersection(province_bounds[name1]))
                    
                    for i in nearby_candidates:
                        # 获取候选省份名称
                        candidate_names = [name for name, idx in province_items.items() if idx == i]
                        if candidate_names:
                            name2 = candidate_names[0]
                            if name1 != name2 and name1 in province_geometries and name2 in province_geometries:
                                try:
                                    # 检查两个省份是否相邻
                                    if province_geometries[name1].touches(province_geometries[name2]):
                                        province_adjacency[name1].append(name2)
                                except Exception as e:
                                    # 如果 touches 方法失败，尝试使用 intersects 方法
                                    try:
                                        # 检查两个几何图形是否相交（但不包含）
                                        if (province_geometries[name1].intersects(province_geometries[name2]) and 
                                            not province_geometries[name1].contains(province_geometries[name2]) and
                                            not province_geometries[name2].contains(province_geometries[name1])):
                                            province_adjacency[name1].append(name2)
                                    except Exception as e2:
                                        pass  # 忽略计算错误
                
                # 使用贪心算法为省份着色，确保相邻省份颜色不同
                # 按相邻省份数量排序，优先为与更多省份相邻的省份着色
                sorted_provinces = sorted(province_list, 
                                        key=lambda p: len(province_adjacency.get(p, [])), 
                                        reverse=True)
                
                # 为每个省份分配颜色
                for i, province in enumerate(sorted_provinces):
                    # 获取相邻省份已使用的颜色
                    adjacent_provinces = province_adjacency.get(province, [])
                    used_colors = set()
                    for adj_province in adjacent_provinces:
                        if adj_province in province_colors:
                            used_colors.add(province_colors[adj_province])
                    
                    # 尽量使用所有可用颜色以增加视觉丰富度
                    available_colors = [color for color in HIGH_CONTRAST_COLORS if color not in used_colors]
                    if available_colors:
                        # 优先使用未被使用的颜色
                        province_colors[province] = available_colors[0]
                    else:
                        # 如果没有完全未使用的颜色，尝试找到一个使用次数最少的颜色
                        # 统计当前各颜色的使用次数
                        color_usage = {color: 0 for color in HIGH_CONTRAST_COLORS}
                        for color in province_colors.values():
                            if color in color_usage:
                                color_usage[color] += 1
                        
                        # 选择使用次数最少且不与相邻省份冲突的颜色
                        best_color = HIGH_CONTRAST_COLORS[0]
                        min_usage = float('inf')
                        
                        for color in HIGH_CONTRAST_COLORS:
                            # 检查是否与相邻省份冲突
                            conflict = False
                            for adj_province in adjacent_provinces:
                                if adj_province in province_colors and province_colors[adj_province] == color:
                                    conflict = True
                                    break
                            
                            # 如果不冲突且使用次数更少，则选择该颜色
                            if not conflict and color_usage[color] < min_usage:
                                best_color = color
                                min_usage = color_usage[color]
                        
                        province_colors[province] = best_color
            
            print(f"航线经过的省份: {provinces_crossed}")
            print(f"省份相邻关系: {province_adjacency}")
            print(f"省份颜色分配: {province_colors}")
            
            # 确定航线经过的省份对应的省会城市
            capitals_to_show = set()
            
            # 使用字典映射方式查找省会城市，提高效率
            for province in provinces_crossed:
                if province in PROVINCE_TO_CAPITAL:
                    capitals_to_show.add(PROVINCE_TO_CAPITAL[province])
            
            # 添加省份 - 绘制所有省份的边界，但只对经过的省份填充颜色和边界
            for record in records:
                name = record.attributes.get('name', '')
                if name in provinces_crossed:
                    # 如果省份被航路经过，则填充颜色并绘制边界
                    ax.add_geometries([record.geometry], ccrs.PlateCarree(),
                                      facecolor=province_colors.get(name, 'gray'), 
                                      edgecolor='black', alpha=0.6)
                else:
                    # 对于未经过的省份，不绘制任何内容（无填充也无边界）
                    pass
    except Exception as e:
        print(f"处理省份shapefile数据时出错: {e}")
        import traceback
        traceback.print_exc()
        # 使用默认的陆地颜色
        ax.add_feature(cfeature.LAND, facecolor='lightgray')

    # 绘制经纬度网格
    gl = ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False

    # 绘制航路线
    ax.plot(route_lons, route_lats, color='red', linewidth=2, marker='', 
            transform=ccrs.PlateCarree(), label='航路')

    # 绘制航路点并标注
    texts = []  # 存储文本对象，供adjust_text使用
    
    # 预定义点的样式，避免在循环中重复创建
    point_styles = {
        'airport': {'color': 'green', 'marker': 's', 'size': 80},
        'vor': {'color': 'blue', 'marker': '^', 'size': 50},
        'fix': {'color': 'red', 'marker': 'o', 'size': 30}
    }
    
    for name, data in waypoints.items():
        # 使用预定义样式，提高代码可读性和维护性
        style = point_styles.get(data['type'], point_styles['fix'])  # 默认使用fix样式

        ax.scatter(data['lon'], data['lat'], s=style['size'], c=style['color'], marker=style['marker'], 
                   zorder=5, transform=ccrs.PlateCarree())

        # 添加标签到列表中，稍后统一调整位置
        text = ax.text(data['lon'], data['lat'], name, fontsize=6,
                      transform=ccrs.PlateCarree(), fontproperties=chinese_font,
                      ha='center', va='center',
                      bbox=dict(boxstyle="round,pad=0.1", facecolor='white', alpha=0.8, edgecolor='gray', linewidth=0.5))
        texts.append(text)

    # 使用adjust_text自动调整标签位置，避免重叠
    if texts:  # 只有在有文本时才调整
        adjust_text(texts, 
                    ax=ax,
                    precision=0.1,  # 降低精度要求以提高速度
                    expand_text=(1.05, 1.05),
                    expand_points=(0.6, 0.6),
                    force_text=(0.8, 1.0),
                    force_points=(1.0, 1.0),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=0.4, alpha=0.9, shrinkA=4.0, shrinkB=4.0),
                    avoid_points=True,
                    avoid_text=True,
                    save_steps=False,
                    lim=100)  # 限制最大迭代次数

    # 添加航线经过省份的省会城市标注
    for city, (lon, lat) in capital_cities.items():
        if city in capitals_to_show:
            ax.text(lon, lat, city, fontsize=9, fontproperties=chinese_font,
                    transform=ccrs.PlateCarree(), ha='center', va='center',
                    color='darkred', fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='yellow', alpha=0.7, edgecolor='orange'))

    # 添加标题
    plt.title(title, fontsize=16, fontproperties=chinese_font)

    # 显示地图
    plt.tight_layout()
    
    # 保存图片（如果指定了路径）
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    # 使用wxPython显示图像
    show_plot_in_wx_frame(fig)
    
    # 清理图形以释放内存
    plt.close(fig)


def show_plot_in_wx_frame(figure):
    """
    在wxPython框架中显示matplotlib图形
    
    参数:
    figure: matplotlib图形对象
    """
    import threading
    
    # 创建事件处理函数，在主线程中执行GUI操作
    def show_image():
        # 检查是否已有wx.App实例在运行
        app = wx.App.Get()
        need_exit_app = False
        
        # 如果没有现有的app实例，则创建一个新的
        if app is None:
            app = wx.App(clearSigInt=True)
            need_exit_app = True
        
        # 获取屏幕尺寸
        screen_width, screen_height = wx.GetDisplaySize()
        
        # 设置窗口尺寸和位置，使其居中
        window_width, window_height = 1200, 900
        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2
        
        # 创建合适大小的窗口
        frame = wx.Frame(None, title="航线图", pos=(window_x, window_y), size=(window_width, window_height))
        panel = wx.Panel(frame)
        
        # 创建matplotlib画布
        canvas = FigureCanvas(panel, -1, figure)
        
        # 创建保存按钮
        save_button = wx.Button(panel, label="保存图片")
        
        # 创建保存观察者
        save_observer = SaveToFileObserver()
        
        # 按钮事件处理
        def on_save(event):
            # 使用观察者处理保存请求
            save_observer.on_save_requested(figure, frame)
        
        save_button.Bind(wx.EVT_BUTTON, on_save)
        
        # 窗口关闭事件处理
        def on_close(event):
            frame.Destroy()
            if need_exit_app:
                app.ExitMainLoop()
        
        frame.Bind(wx.EVT_CLOSE, on_close)
        
        # 布局
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(canvas, 1, wx.EXPAND | wx.ALL, 10)  # 添加边距使图形不紧贴窗口边缘
        sizer.Add(save_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)  # 添加保存按钮
        panel.SetSizer(sizer)
        
        # 绑定窗口大小调整事件
        def on_size(event):
            # 重新绘制图形以适应新大小
            canvas.draw()
            event.Skip()
            
        frame.Bind(wx.EVT_SIZE, on_size)
        
        frame.Show()
        # 只有在创建了新的app时才进入MainLoop
        if need_exit_app:
            app.MainLoop()
    
    # 在主线程中运行GUI应用程序
    if threading.current_thread() is threading.main_thread():
        show_image()
    else:
        # 如果当前不在主线程，则使用CallAfter在主线程中执行
        wx.CallAfter(show_image)


class SaveObserver(ABC):
    """保存操作观察者抽象类"""
    
    @abstractmethod
    def on_save_requested(self, figure, parent_window=None):
        """当保存请求发生时调用"""
        pass


class SaveToFileObserver(SaveObserver):
    """保存到文件的观察者实现"""
    
    def on_save_requested(self, figure, parent_window=None):
        """处理保存到文件的请求"""
        if parent_window is None:
            print("错误：需要提供父窗口")
            return
        
        # 获取当前工作目录作为默认保存位置
        default_dir = os.getcwd()
        default_file = os.path.join(default_dir, "航线图.png")
        
        with wx.FileDialog(parent_window, "保存图片文件", 
                          defaultDir=default_dir,
                          defaultFile=default_file,
                          wildcard="PNG files (*.png)|*.png|JPEG files (*.jpg)|*.jpg|PDF files (*.pdf)|*.pdf",
                          style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            try:
                figure.savefig(pathname, dpi=300, bbox_inches='tight')
                wx.MessageBox(f"图片已保存至: {pathname}", "保存成功", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"保存失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)


def draw_route_from_sheet(file_path, sheet_name, title=None, figure_size=(12, 9), margins=None, show_all_provinces=True):
    """
    从指定的工作表绘制航线
    
    参数:
    file_path (str): Excel文件路径
    sheet_name (str or int): 工作表名称或索引
    title (str): 图表标题，默认为基于工作表名称的标题
    figure_size (tuple): 图像大小 (宽度, 高度)
    margins (dict): 边距设置 {'left': 0.1, 'right': 0.9, 'top': 0.9, 'bottom': 0.1}
    show_all_provinces (bool): 是否显示所有省份边界，默认为True（显示所有省份边界），
                              False则只显示航线经过的省份边界
    """
    if title is None:
        title = f'航路图（基于Excel数据 - {sheet_name}）'
    
    print(f"正在从{sheet_name}加载航路点...")
    loader = ExcelDataLoader()
    waypoints, route_order = loader.load_data(file_path, sheet_name)
    
    if not waypoints:
        print(f"未找到{sheet_name}中的航路点数据")
        return
    
    # 打印加载的数据以供检查
    print(f"{sheet_name}中的航路点:")
    for name, data in waypoints.items():
        print(f"{name}: lat={data['lat']}, lon={data['lon']}, type={data['type']}")
    
    print(f"\n{sheet_name}中的航路点顺序:")
    print(route_order)
    
    # 调用函数绘制航路图，使用4:3比例
    draw_route_map(waypoints, route_order, title, figure_size=figure_size, margins=margins, show_all_provinces=show_all_provinces)


# 添加主函数保护，防止在模块导入时执行
if __name__ == "__main__":
    # 绘制Sheet1中的航线，设置图像大小和边距
    margins_config = {
        'left': 0.30,
        'right': 0.70,
        'top': 0.70,
        'bottom': 0.30
    }

    for sheet in ['Sheet6']:
        # 显示所有省份边界（默认）
        draw_route_from_sheet('航路点.xlsx', sheet, f'航路图',
                             figure_size=(10, 8), margins=margins_config)
        break  # 只运行一次，避免程序卡住
