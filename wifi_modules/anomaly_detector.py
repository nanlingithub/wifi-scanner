"""
WiFi网络异常检测器（机器学习）
基于历史数据预测网络异常
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import numpy as np


class WiFiAnomalyDetector:
    """WiFi网络异常检测器"""
    
    def __init__(self, model_dir: str = 'models'):
        """
        初始化异常检测器
        
        Args:
            model_dir: 模型存储目录
        """
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        self.training_data: List[Dict] = []
        self.model_trained = False
        
        # 异常检测阈值
        self.thresholds = {
            'signal_drop_threshold': 20,  # 信号下降>20%视为异常
            'interference_threshold': 60,  # 干扰评分>60视为异常
            'ap_count_change': 3,          # AP数量变化>3视为异常
        }
    
    def extract_features(self, network_data: Dict) -> np.ndarray:
        """
        从网络数据中提取特征
        
        Args:
            network_data: 网络分析数据
            
        Returns:
            特征向量
        """
        features = []
        
        # 1. 平均信号强度
        signal_quality = network_data.get('signal_quality', {})
        avg_signal = signal_quality.get('average_signal', 0)
        features.append(avg_signal)
        
        # 2. 信号稳定性（标准差）
        signal_std = signal_quality.get('signal_std_dev', 0)
        features.append(signal_std)
        
        # 3. AP总数
        total_aps = network_data.get('total_networks', 0)
        features.append(total_aps)
        
        # 4. 干扰评分
        interference = network_data.get('interference_analysis', {})
        interference_score = interference.get('interference_score', 0)
        features.append(interference_score)
        
        # 5. 信道拥堵程度
        channel_data = network_data.get('channel_analysis', {})
        max_channel_usage = max(channel_data.values()) if channel_data else 0
        features.append(max_channel_usage)
        
        # 6. 2.4GHz vs 5GHz比例
        coverage = network_data.get('coverage_analysis', {})
        band_2_4g = coverage.get('band_2_4g_count', 0)
        band_5g = coverage.get('band_5g_count', 0)
        band_ratio = band_5g / (band_2_4g + 1)  # 避免除零
        features.append(band_ratio)
        
        return np.array(features)
    
    def detect_anomaly_rule_based(self, current_data: Dict, 
                                   historical_data: Optional[Dict] = None) -> Dict:
        """
        基于规则的异常检测（无需训练）
        
        Args:
            current_data: 当前网络数据
            historical_data: 历史数据（可选）
            
        Returns:
            异常检测结果
        """
        anomalies = []
        
        # 提取当前特征
        signal_quality = current_data.get('signal_quality', {})
        interference = current_data.get('interference_analysis', {})
        
        # 1. 检测信号质量异常
        avg_signal = signal_quality.get('average_signal', 0)
        if avg_signal < 30:
            anomalies.append({
                'type': '信号质量过低',
                'severity': 'HIGH',
                'description': f'平均信号强度仅{avg_signal:.1f}%，低于30%阈值',
                'recommendation': '建议增加AP或调整AP位置'
            })
        
        # 2. 检测干扰异常
        interference_score = interference.get('interference_score', 0)
        if interference_score > self.thresholds['interference_threshold']:
            anomalies.append({
                'type': '严重干扰',
                'severity': 'HIGH',
                'description': f'干扰评分{interference_score:.1f}分，超过{self.thresholds["interference_threshold"]}分阈值',
                'recommendation': '建议调整信道或更换频段'
            })
        
        # 3. 对比历史数据（如果提供）
        if historical_data:
            hist_signal = historical_data.get('signal_quality', {}).get('average_signal', 0)
            signal_drop = hist_signal - avg_signal
            
            if signal_drop > self.thresholds['signal_drop_threshold']:
                anomalies.append({
                    'type': '信号突然下降',
                    'severity': 'MEDIUM',
                    'description': f'信号强度相比历史数据下降{signal_drop:.1f}%',
                    'recommendation': '检查AP状态或环境变化'
                })
        
        # 4. 检测AP数量异常
        total_aps = current_data.get('total_networks', 0)
        if historical_data:
            hist_aps = historical_data.get('total_networks', 0)
            ap_change = abs(total_aps - hist_aps)
            
            if ap_change > self.thresholds['ap_count_change']:
                anomalies.append({
                    'type': 'AP数量显著变化',
                    'severity': 'MEDIUM',
                    'description': f'检测到{ap_change}个AP数量变化（当前{total_aps}个，历史{hist_aps}个）',
                    'recommendation': '检查是否有未授权AP或AP离线'
                })
        
        return {
            'is_anomaly': len(anomalies) > 0,
            'anomaly_count': len(anomalies),
            'anomalies': anomalies,
            'detection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'detection_method': 'rule_based'
        }
    
    def save_training_data(self, network_data: Dict, is_anomaly: bool = False):
        """
        保存训练数据
        
        Args:
            network_data: 网络数据
            is_anomaly: 是否为异常数据
        """
        training_sample = {
            'timestamp': datetime.now().isoformat(),
            'features': self.extract_features(network_data).tolist(),
            'is_anomaly': is_anomaly,
            'data': network_data
        }
        
        self.training_data.append(training_sample)
        
        # 自动保存到文件
        self._save_to_file()
    
    def _save_to_file(self):
        """保存训练数据到文件"""
        data_file = os.path.join(self.model_dir, 'training_data.json')
        
        try:
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.training_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存训练数据失败: {e}")
    
    def load_training_data(self):
        """从文件加载训练数据"""
        data_file = os.path.join(self.model_dir, 'training_data.json')
        
        if not os.path.exists(data_file):
            return
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                self.training_data = json.load(f)
        except Exception as e:
            print(f"加载训练数据失败: {e}")
    
    def get_statistics(self) -> Dict:
        """
        获取检测统计信息
        
        Returns:
            统计信息
        """
        if not self.training_data:
            return {
                'total_samples': 0,
                'anomaly_samples': 0,
                'normal_samples': 0,
                'anomaly_rate': 0.0
            }
        
        total = len(self.training_data)
        anomalies = sum(1 for sample in self.training_data if sample.get('is_anomaly', False))
        
        return {
            'total_samples': total,
            'anomaly_samples': anomalies,
            'normal_samples': total - anomalies,
            'anomaly_rate': f"{anomalies / total * 100:.1f}%" if total > 0 else "0%"
        }
