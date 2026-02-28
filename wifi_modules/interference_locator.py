#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能干扰源定位器
实现RSSI三角定位、干扰源类型识别、缓解策略生成
"""

import math
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from enum import Enum


class InterferenceType(Enum):
    """干扰源类型"""
    MICROWAVE = "微波炉"
    BLUETOOTH = "蓝牙设备"
    WIRELESS_PHONE = "无线电话"
    BABY_MONITOR = "婴儿监视器"
    WIRELESS_CAMERA = "无线摄像头"
    ZIGBEE = "ZigBee设备"
    NEIGHBORING_WIFI = "邻近WiFi"
    RADAR = "雷达信号"
    OTHER_24G = "其他2.4GHz设备"
    OTHER_5G = "其他5GHz设备"
    UNKNOWN = "未知干扰源"


class InterferenceSeverity(Enum):
    """干扰严重程度"""
    CRITICAL = "严重"
    HIGH = "高"
    MEDIUM = "中等"
    LOW = "低"
    NEGLIGIBLE = "可忽略"


@dataclass
class MeasurementPoint:
    """RSSI测量点"""
    x: float  # 横坐标 (米)
    y: float  # 纵坐标 (米)
    rssi: float  # 信号强度 (dBm)
    frequency: float  # 频率 (MHz)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def distance_to(self, other: 'MeasurementPoint') -> float:
        """计算到另一点的距离"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


@dataclass
class InterferenceSource:
    """干扰源信息"""
    source_id: str
    interference_type: InterferenceType
    severity: InterferenceSeverity
    location: Optional[Tuple[float, float]] = None  # (x, y)
    location_confidence: float = 0.0  # 0-1
    frequency_range: Tuple[float, float] = (0.0, 0.0)  # (min, max) MHz
    avg_power: float = 0.0  # dBm
    detection_count: int = 0
    first_detected: datetime = field(default_factory=datetime.now)
    last_detected: datetime = field(default_factory=datetime.now)
    affected_channels: List[int] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)
    
    def get_severity_score(self) -> int:
        """获取严重程度评分 (0-100)"""
        severity_map = {
            InterferenceSeverity.CRITICAL: 90,
            InterferenceSeverity.HIGH: 70,
            InterferenceSeverity.MEDIUM: 50,
            InterferenceSeverity.LOW: 30,
            InterferenceSeverity.NEGLIGIBLE: 10
        }
        return severity_map.get(self.severity, 0)


class InterferenceLocator:
    """智能干扰源定位器"""
    
    # 干扰源特征库
    INTERFERENCE_SIGNATURES = {
        InterferenceType.MICROWAVE: {
            'frequency_range': (2400, 2500),
            'power_level': (-40, -20),
            'pattern': 'pulsed',
            'bandwidth': 20,
            'duty_cycle': 0.5
        },
        InterferenceType.BLUETOOTH: {
            'frequency_range': (2402, 2480),
            'power_level': (-70, -40),
            'pattern': 'hopping',
            'bandwidth': 1,
            'channels': 79
        },
        InterferenceType.WIRELESS_PHONE: {
            'frequency_range': (2400, 2483.5),
            'power_level': (-50, -30),
            'pattern': 'continuous',
            'bandwidth': 1.728
        },
        InterferenceType.BABY_MONITOR: {
            'frequency_range': (2400, 2483.5),
            'power_level': (-60, -30),
            'pattern': 'continuous',
            'bandwidth': 2
        },
        InterferenceType.WIRELESS_CAMERA: {
            'frequency_range': (2400, 2500),
            'power_level': (-50, -20),
            'pattern': 'continuous',
            'bandwidth': 5
        },
        InterferenceType.ZIGBEE: {
            'frequency_range': (2405, 2480),
            'power_level': (-80, -50),
            'pattern': 'hopping',
            'bandwidth': 2,
            'channels': 16
        }
    }
    
    def __init__(self):
        """初始化干扰源定位器"""
        self.measurement_points: List[MeasurementPoint] = []
        self.interference_sources: List[InterferenceSource] = []
        self.path_loss_exponent = 2.0  # 路径损耗指数 (自由空间=2, 室内=3-4)
        self.reference_distance = 1.0  # 参考距离 (米)
        self.reference_rssi = -40.0  # 参考RSSI (dBm @ 1米)
        
    def add_measurement(self, x: float, y: float, rssi: float, frequency: float):
        """添加测量点"""
        point = MeasurementPoint(x, y, rssi, frequency)
        self.measurement_points.append(point)
        return point
    
    def clear_measurements(self):
        """清空测量点"""
        self.measurement_points.clear()
    
    def rssi_to_distance(self, rssi: float) -> float:
        """
        RSSI转距离 (对数距离路径损耗模型)
        d = d0 * 10^((RSSI0 - RSSI) / (10 * n))
        """
        if rssi >= self.reference_rssi:
            return self.reference_distance
        
        exponent = (self.reference_rssi - rssi) / (10 * self.path_loss_exponent)
        distance = self.reference_distance * (10 ** exponent)
        return distance
    
    def distance_to_rssi(self, distance: float) -> float:
        """
        距离转RSSI
        RSSI = RSSI0 - 10 * n * log10(d / d0)
        """
        if distance <= 0:
            return self.reference_rssi
        
        rssi = self.reference_rssi - 10 * self.path_loss_exponent * math.log10(
            distance / self.reference_distance
        )
        return rssi
    
    def triangulate(self, points: List[MeasurementPoint]) -> Optional[Tuple[float, float, float]]:
        """
        三角定位算法
        返回: (x, y, confidence) 或 None
        """
        if len(points) < 3:
            return None
        
        # 使用最强的3个信号点
        points = sorted(points, key=lambda p: p.rssi, reverse=True)[:3]
        
        # 转换RSSI为距离
        distances = [self.rssi_to_distance(p.rssi) for p in points]
        
        # 三边定位 (Trilateration)
        try:
            x1, y1 = points[0].x, points[0].y
            x2, y2 = points[1].x, points[1].y
            x3, y3 = points[2].x, points[2].y
            r1, r2, r3 = distances[0], distances[1], distances[2]
            
            # 计算中间变量
            A = 2 * (x2 - x1)
            B = 2 * (y2 - y1)
            C = r1**2 - r2**2 - x1**2 + x2**2 - y1**2 + y2**2
            
            D = 2 * (x3 - x2)
            E = 2 * (y3 - y2)
            F = r2**2 - r3**2 - x2**2 + x3**2 - y2**2 + y3**2
            
            # 求解坐标
            if abs(A * E - B * D) < 1e-10:
                # 三点共线，无法定位
                return None
            
            x = (C * E - F * B) / (A * E - B * D)
            y = (C * D - A * F) / (B * D - A * E)
            
            # 计算置信度 (基于几何精度因子 GDOP)
            confidence = self._calculate_confidence(points, (x, y))
            
            return (x, y, confidence)
            
        except (ZeroDivisionError, ValueError):
            return None
    
    def _calculate_confidence(self, points: List[MeasurementPoint], 
                             location: Tuple[float, float]) -> float:
        """
        计算定位置信度
        基于测量点的几何分布和信号强度
        """
        x, y = location
        
        # 1. 几何因子 (GDOP)
        angles = []
        for p in points:
            angle = math.atan2(p.y - y, p.x - x)
            angles.append(angle)
        
        # 计算角度分布均匀性
        angles.sort()
        angle_diffs = []
        for i in range(len(angles)):
            diff = angles[(i + 1) % len(angles)] - angles[i]
            if diff < 0:
                diff += 2 * math.pi
            angle_diffs.append(diff)
        
        ideal_angle = 2 * math.pi / len(angles)
        angle_variance = sum((d - ideal_angle)**2 for d in angle_diffs)
        geometric_factor = 1.0 / (1.0 + angle_variance / ideal_angle**2)
        
        # 2. 信号强度因子
        avg_rssi = sum(p.rssi for p in points) / len(points)
        signal_factor = max(0, min(1, (avg_rssi + 80) / 40))  # -80dBm=0, -40dBm=1
        
        # 3. 测量点数量因子
        count_factor = min(1.0, len(points) / 5)  # 5个点为满分
        
        # 综合置信度
        confidence = (geometric_factor * 0.5 + signal_factor * 0.3 + count_factor * 0.2)
        return max(0.0, min(1.0, confidence))
    
    def identify_interference_type(self, frequency: float, rssi: float, 
                                   pattern: str = 'unknown') -> InterferenceType:
        """
        识别干扰源类型
        """
        candidates = []
        
        for itype, signature in self.INTERFERENCE_SIGNATURES.items():
            freq_min, freq_max = signature['frequency_range']
            power_min, power_max = signature['power_level']
            
            # 频率匹配
            freq_match = freq_min <= frequency <= freq_max
            
            # 功率匹配
            power_match = power_min <= rssi <= power_max
            
            # 计算匹配度
            if freq_match and power_match:
                score = 1.0
                
                # 调整评分
                if 'pattern' in signature:
                    if pattern == signature['pattern']:
                        score += 0.5
                
                candidates.append((itype, score))
        
        if candidates:
            # 返回得分最高的类型
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]
        
        # 根据频率范围推断
        if 2400 <= frequency <= 2500:
            return InterferenceType.OTHER_24G
        elif 5000 <= frequency <= 6000:
            return InterferenceType.OTHER_5G
        else:
            return InterferenceType.UNKNOWN
    
    def calculate_severity(self, rssi: float, frequency: float, 
                          affected_channels: List[int]) -> InterferenceSeverity:
        """
        计算干扰严重程度
        """
        # 1. 信号强度评分 (0-40分)
        if rssi >= -40:
            power_score = 40
        elif rssi >= -50:
            power_score = 30
        elif rssi >= -60:
            power_score = 20
        elif rssi >= -70:
            power_score = 10
        else:
            power_score = 5
        
        # 2. 影响信道数量 (0-40分)
        channel_score = min(40, len(affected_channels) * 10)
        
        # 3. 频段重要性 (0-20分)
        if 2400 <= frequency <= 2500:
            band_score = 20  # 2.4GHz拥挤，干扰影响大
        elif 5000 <= frequency <= 6000:
            band_score = 10  # 5GHz较空闲
        else:
            band_score = 5
        
        # 总分
        total_score = power_score + channel_score + band_score
        
        # 映射到严重等级
        if total_score >= 80:
            return InterferenceSeverity.CRITICAL
        elif total_score >= 60:
            return InterferenceSeverity.HIGH
        elif total_score >= 40:
            return InterferenceSeverity.MEDIUM
        elif total_score >= 20:
            return InterferenceSeverity.LOW
        else:
            return InterferenceSeverity.NEGLIGIBLE
    
    def detect_interference_sources(self) -> List[InterferenceSource]:
        """
        检测并定位干扰源
        """
        if len(self.measurement_points) < 3:
            return []
        
        # 按频率聚类
        frequency_clusters = self._cluster_by_frequency()
        
        sources = []
        for cluster_id, points in frequency_clusters.items():
            if len(points) < 3:
                continue
            
            # 三角定位
            location_result = self.triangulate(points)
            
            # 分析干扰源
            avg_freq = sum(p.frequency for p in points) / len(points)
            avg_rssi = sum(p.rssi for p in points) / len(points)
            
            # 识别类型
            itype = self.identify_interference_type(avg_freq, avg_rssi)
            
            # 计算影响的信道
            affected_channels = self._get_affected_channels(avg_freq)
            
            # 计算严重程度
            severity = self.calculate_severity(avg_rssi, avg_freq, affected_channels)
            
            # 创建干扰源对象
            source = InterferenceSource(
                source_id=f"INT_{cluster_id}_{datetime.now().strftime('%H%M%S')}",
                interference_type=itype,
                severity=severity,
                frequency_range=(min(p.frequency for p in points),
                               max(p.frequency for p in points)),
                avg_power=avg_rssi,
                detection_count=len(points),
                affected_channels=affected_channels
            )
            
            if location_result:
                x, y, confidence = location_result
                source.location = (x, y)
                source.location_confidence = confidence
            
            # 生成缓解策略
            source.mitigation_strategies = self._generate_mitigation_strategies(source)
            
            sources.append(source)
        
        self.interference_sources = sources
        return sources
    
    def _cluster_by_frequency(self, bandwidth: float = 20.0) -> Dict[int, List[MeasurementPoint]]:
        """
        按频率聚类测量点
        bandwidth: 聚类带宽 (MHz)
        """
        clusters = {}
        cluster_id = 0
        
        sorted_points = sorted(self.measurement_points, key=lambda p: p.frequency)
        
        for point in sorted_points:
            # 查找现有聚类
            found = False
            for cid, points in clusters.items():
                center_freq = sum(p.frequency for p in points) / len(points)
                if abs(point.frequency - center_freq) <= bandwidth / 2:
                    points.append(point)
                    found = True
                    break
            
            # 创建新聚类
            if not found:
                clusters[cluster_id] = [point]
                cluster_id += 1
        
        return clusters
    
    def _get_affected_channels(self, frequency: float, bandwidth: float = 20.0) -> List[int]:
        """
        获取受影响的WiFi信道
        """
        affected = []
        
        # 2.4GHz信道 (1-13)
        if 2400 <= frequency <= 2500:
            for ch in range(1, 14):
                ch_freq = 2412 + (ch - 1) * 5
                if abs(frequency - ch_freq) <= bandwidth:
                    affected.append(ch)
        
        # 5GHz信道
        elif 5000 <= frequency <= 6000:
            for ch in [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 
                      120, 124, 128, 132, 136, 140, 144, 149, 153, 157, 161, 165]:
                ch_freq = 5000 + ch * 5
                if abs(frequency - ch_freq) <= bandwidth:
                    affected.append(ch)
        
        return affected
    
    def _generate_mitigation_strategies(self, source: InterferenceSource) -> List[str]:
        """
        生成干扰缓解策略
        """
        strategies = []
        
        # 基于干扰类型的策略
        if source.interference_type == InterferenceType.MICROWAVE:
            strategies.append("建议: 将WiFi路由器远离微波炉至少3米")
            strategies.append("优化: 使用5GHz频段避开2.4GHz干扰")
            strategies.append("调整: 错开微波炉使用时间段")
        
        elif source.interference_type == InterferenceType.BLUETOOTH:
            strategies.append("优化: 启用WiFi 6的BSS颜色功能减少共信道干扰")
            strategies.append("建议: 使用5GHz频段，蓝牙仅在2.4GHz工作")
        
        elif source.interference_type == InterferenceType.WIRELESS_PHONE:
            strategies.append("建议: 更换为使用5.8GHz或DECT 6.0的无线电话")
            strategies.append("优化: 将WiFi路由器移至远离电话基站的位置")
        
        elif source.interference_type == InterferenceType.NEIGHBORING_WIFI:
            strategies.append(f"优化: 避开信道{source.affected_channels}，选择干净信道")
            strategies.append("建议: 调整AP发射功率，减少覆盖重叠")
            strategies.append("考虑: 启用DFS信道扩展可用频谱")
        
        # 基于严重程度的策略
        if source.severity == InterferenceSeverity.CRITICAL:
            strategies.insert(0, "⚠️ 紧急: 立即识别并移除干扰源")
            strategies.append("建议: 考虑使用屏蔽设备或改变网络拓扑")
        
        elif source.severity == InterferenceSeverity.HIGH:
            strategies.insert(0, "警告: 干扰影响较大，建议尽快处理")
        
        # 基于位置的策略
        if source.location and source.location_confidence > 0.6:
            x, y = source.location
            strategies.append(f"定位: 干扰源位于坐标({x:.1f}, {y:.1f})米，置信度{source.location_confidence*100:.0f}%")
            strategies.append("行动: 前往该位置排查干扰设备")
        
        # 通用策略
        if 2400 <= source.frequency_range[0] <= 2500:
            if not any("5GHz" in s for s in strategies):
                strategies.append("长期方案: 升级到5GHz或WiFi 6E (6GHz)频段")
        
        return strategies
    
    def get_heatmap_data(self, grid_size: int = 50) -> np.ndarray:
        """
        生成干扰强度热力图数据
        返回: grid_size x grid_size的矩阵
        """
        if not self.interference_sources:
            return np.zeros((grid_size, grid_size))
        
        # 确定范围
        if self.measurement_points:
            x_coords = [p.x for p in self.measurement_points]
            y_coords = [p.y for p in self.measurement_points]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
        else:
            x_min, y_min = 0, 0
            x_max, y_max = 10, 10
        
        # 扩展边界
        margin = (x_max - x_min) * 0.1
        x_min -= margin
        x_max += margin
        y_min -= margin
        y_max += margin
        
        # 创建网格
        x_range = np.linspace(x_min, x_max, grid_size)
        y_range = np.linspace(y_min, y_max, grid_size)
        heatmap = np.zeros((grid_size, grid_size))
        
        # 计算每个网格点的干扰强度
        for i, y in enumerate(y_range):
            for j, x in enumerate(x_range):
                total_interference = 0
                
                for source in self.interference_sources:
                    if source.location:
                        sx, sy = source.location
                        distance = math.sqrt((x - sx)**2 + (y - sy)**2)
                        
                        # 使用RSSI模型计算该点的干扰强度
                        if distance < 0.1:
                            distance = 0.1
                        
                        interference = source.avg_power + 10 * self.path_loss_exponent * math.log10(
                            self.reference_distance / distance
                        )
                        
                        # 权重衰减
                        weight = source.location_confidence * (source.get_severity_score() / 100)
                        total_interference += interference * weight
                
                heatmap[i, j] = total_interference
        
        return heatmap
    
    def export_report(self) -> Dict:
        """导出分析报告"""
        return {
            'timestamp': datetime.now().isoformat(),
            'measurement_count': len(self.measurement_points),
            'interference_sources': [
                {
                    'id': s.source_id,
                    'type': s.interference_type.value,
                    'severity': s.severity.value,
                    'severity_score': s.get_severity_score(),
                    'location': s.location,
                    'location_confidence': s.location_confidence,
                    'frequency_range': s.frequency_range,
                    'avg_power': s.avg_power,
                    'affected_channels': s.affected_channels,
                    'mitigation_strategies': s.mitigation_strategies
                }
                for s in self.interference_sources
            ],
            'settings': {
                'path_loss_exponent': self.path_loss_exponent,
                'reference_distance': self.reference_distance,
                'reference_rssi': self.reference_rssi
            }
        }


# 测试代码
if __name__ == "__main__":
    locator = InterferenceLocator()
    
    # 模拟测量数据
    print("添加模拟测量点...")
    locator.add_measurement(0, 0, -45, 2437)  # 位置1
    locator.add_measurement(5, 0, -55, 2437)  # 位置2
    locator.add_measurement(2.5, 4, -50, 2437)  # 位置3
    locator.add_measurement(10, 0, -75, 2450)  # 远处干扰
    locator.add_measurement(10, 5, -70, 2450)
    
    print(f"共{len(locator.measurement_points)}个测量点\n")
    
    # 检测干扰源
    print("检测干扰源...")
    sources = locator.detect_interference_sources()
    
    print(f"发现 {len(sources)} 个干扰源\n")
    print("=" * 80)
    
    for i, source in enumerate(sources, 1):
        print(f"\n[{i}] {source.source_id}")
        print(f"    类型: {source.interference_type.value}")
        print(f"    严重程度: {source.severity.value} ({source.get_severity_score()}/100)")
        print(f"    频率范围: {source.frequency_range[0]:.1f} - {source.frequency_range[1]:.1f} MHz")
        print(f"    平均功率: {source.avg_power:.1f} dBm")
        print(f"    影响信道: {source.affected_channels}")
        
        if source.location:
            x, y = source.location
            print(f"    定位: ({x:.2f}, {y:.2f}) 米")
            print(f"    置信度: {source.location_confidence*100:.1f}%")
        
        print(f"\n    缓解策略:")
        for strategy in source.mitigation_strategies:
            print(f"      • {strategy}")
    
    # 生成热力图
    print("\n" + "=" * 80)
    print("生成干扰热力图...")
    heatmap = locator.get_heatmap_data(grid_size=20)
    print(f"热力图尺寸: {heatmap.shape}")
    print(f"最大干扰强度: {np.max(heatmap):.1f} dBm")
    print(f"最小干扰强度: {np.min(heatmap):.1f} dBm")
