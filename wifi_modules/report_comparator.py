"""
WiFi报告对比分析工具
支持多次扫描报告的对比和趋势分析
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import numpy as np


class ReportComparator:
    """WiFi报告对比分析器"""
    
    def __init__(self, reports_dir: str = 'reports/history'):
        """
        初始化报告对比器
        
        Args:
            reports_dir: 历史报告存储目录
        """
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
    
    def save_report(self, report_data: Dict, report_name: Optional[str] = None):
        """
        保存报告数据
        
        Args:
            report_data: 报告数据
            report_name: 报告名称（可选，默认使用时间戳）
        """
        if not report_name:
            report_name = datetime.now().strftime('report_%Y%m%d_%H%M%S')
        
        # 添加元数据
        report_with_metadata = {
            'metadata': {
                'report_name': report_name,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            },
            'data': report_data
        }
        
        # 保存到文件
        file_path = os.path.join(self.reports_dir, f'{report_name}.json')
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_with_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存报告失败: {e}")
    
    def load_report(self, report_name: str) -> Optional[Dict]:
        """
        加载报告数据
        
        Args:
            report_name: 报告名称
            
        Returns:
            报告数据或None
        """
        file_path = os.path.join(self.reports_dir, f'{report_name}.json')
        
        if not os.path.exists(file_path):
            print(f"报告文件不存在: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载报告失败: {e}")
            return None
    
    def list_reports(self) -> List[Dict]:
        """
        列出所有历史报告
        
        Returns:
            报告列表
        """
        reports = []
        
        if not os.path.exists(self.reports_dir):
            return reports
        
        for filename in os.listdir(self.reports_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.reports_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                        metadata = report.get('metadata', {})
                        
                        reports.append({
                            'name': metadata.get('report_name', filename.replace('.json', '')),
                            'timestamp': metadata.get('timestamp', 'Unknown'),
                            'file_path': file_path
                        })
                except Exception as e:
                    print(f"读取报告元数据失败: {e}")
        
        # 按时间戳排序
        reports.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return reports
    
    def compare_reports(self, report1_name: str, report2_name: str) -> Dict:
        """
        对比两份报告
        
        Args:
            report1_name: 第一份报告名称（基准）
            report2_name: 第二份报告名称（对比）
            
        Returns:
            对比结果
        """
        # 加载报告
        report1 = self.load_report(report1_name)
        report2 = self.load_report(report2_name)
        
        if not report1 or not report2:
            return {'error': '无法加载报告'}
        
        data1 = report1.get('data', {})
        data2 = report2.get('data', {})
        
        # 对比信号质量
        signal_comparison = self._compare_signal_quality(data1, data2)
        
        # 对比干扰情况
        interference_comparison = self._compare_interference(data1, data2)
        
        # 对比AP数量
        ap_comparison = self._compare_ap_count(data1, data2)
        
        # 对比安全性
        security_comparison = self._compare_security(data1, data2)
        
        return {
            'report1': {
                'name': report1_name,
                'timestamp': report1.get('metadata', {}).get('timestamp')
            },
            'report2': {
                'name': report2_name,
                'timestamp': report2.get('metadata', {}).get('timestamp')
            },
            'comparisons': {
                'signal_quality': signal_comparison,
                'interference': interference_comparison,
                'ap_count': ap_comparison,
                'security': security_comparison
            },
            'summary': self._generate_comparison_summary(
                signal_comparison,
                interference_comparison,
                ap_comparison,
                security_comparison
            )
        }
    
    def _compare_signal_quality(self, data1: Dict, data2: Dict) -> Dict:
        """对比信号质量"""
        signal1 = data1.get('signal_quality', {})
        signal2 = data2.get('signal_quality', {})
        
        avg1 = signal1.get('average_signal', 0)
        avg2 = signal2.get('average_signal', 0)
        
        change = avg2 - avg1
        change_percent = (change / avg1 * 100) if avg1 > 0 else 0
        
        return {
            'baseline': avg1,
            'current': avg2,
            'change': change,
            'change_percent': change_percent,
            'trend': 'improved' if change > 0 else 'degraded' if change < 0 else 'stable',
            'significance': 'significant' if abs(change) > 10 else 'minor'
        }
    
    def _compare_interference(self, data1: Dict, data2: Dict) -> Dict:
        """对比干扰情况"""
        interference1 = data1.get('interference_analysis', {})
        interference2 = data2.get('interference_analysis', {})
        
        score1 = interference1.get('interference_score', 0)
        score2 = interference2.get('interference_score', 0)
        
        change = score2 - score1
        
        return {
            'baseline': score1,
            'current': score2,
            'change': change,
            'trend': 'worsened' if change > 0 else 'improved' if change < 0 else 'stable',
            'significance': 'significant' if abs(change) > 15 else 'minor'
        }
    
    def _compare_ap_count(self, data1: Dict, data2: Dict) -> Dict:
        """对比AP数量"""
        count1 = data1.get('total_networks', 0)
        count2 = data2.get('total_networks', 0)
        
        change = count2 - count1
        
        return {
            'baseline': count1,
            'current': count2,
            'change': change,
            'trend': 'increased' if change > 0 else 'decreased' if change < 0 else 'stable'
        }
    
    def _compare_security(self, data1: Dict, data2: Dict) -> Dict:
        """对比安全性"""
        security1 = data1.get('security_assessment', {})
        security2 = data2.get('security_assessment', {})
        
        score1 = security1.get('overall_score', 0)
        score2 = security2.get('overall_score', 0)
        
        vuln1 = len(security1.get('vulnerabilities', []))
        vuln2 = len(security2.get('vulnerabilities', []))
        
        return {
            'baseline_score': score1,
            'current_score': score2,
            'score_change': score2 - score1,
            'baseline_vulnerabilities': vuln1,
            'current_vulnerabilities': vuln2,
            'vulnerabilities_change': vuln2 - vuln1,
            'trend': 'improved' if score2 > score1 else 'degraded' if score2 < score1 else 'stable'
        }
    
    def _generate_comparison_summary(self, signal: Dict, interference: Dict,
                                      ap_count: Dict, security: Dict) -> List[str]:
        """生成对比摘要"""
        summary = []
        
        # 信号质量摘要
        if signal['trend'] == 'improved':
            summary.append(f"✓ 信号质量提升 {signal['change']:.1f}%")
        elif signal['trend'] == 'degraded':
            summary.append(f"✗ 信号质量下降 {abs(signal['change']):.1f}%")
        else:
            summary.append("= 信号质量保持稳定")
        
        # 干扰摘要
        if interference['trend'] == 'improved':
            summary.append(f"✓ 干扰减少 {abs(interference['change']):.1f}分")
        elif interference['trend'] == 'worsened':
            summary.append(f"✗ 干扰增加 {interference['change']:.1f}分")
        else:
            summary.append("= 干扰水平保持稳定")
        
        # AP数量摘要
        if ap_count['trend'] == 'increased':
            summary.append(f"↑ AP数量增加 {ap_count['change']}个")
        elif ap_count['trend'] == 'decreased':
            summary.append(f"↓ AP数量减少 {abs(ap_count['change'])}个")
        else:
            summary.append("= AP数量保持稳定")
        
        # 安全性摘要
        if security['trend'] == 'improved':
            summary.append(f"✓ 安全评分提升 {security['score_change']:.1f}分")
        elif security['trend'] == 'degraded':
            summary.append(f"✗ 安全评分下降 {abs(security['score_change']):.1f}分")
        else:
            summary.append("= 安全状况保持稳定")
        
        return summary
    
    def analyze_trend(self, metric: str, report_names: List[str]) -> Dict:
        """
        分析多份报告的趋势
        
        Args:
            metric: 指标类型 ('signal', 'interference', 'ap_count', 'security')
            report_names: 报告名称列表（按时间顺序）
            
        Returns:
            趋势分析结果
        """
        values = []
        timestamps = []
        
        for report_name in report_names:
            report = self.load_report(report_name)
            
            if not report:
                continue
            
            data = report.get('data', {})
            timestamp = report.get('metadata', {}).get('timestamp', '')
            
            # 提取对应指标值
            if metric == 'signal':
                value = data.get('signal_quality', {}).get('average_signal', 0)
            elif metric == 'interference':
                value = data.get('interference_analysis', {}).get('interference_score', 0)
            elif metric == 'ap_count':
                value = data.get('total_networks', 0)
            elif metric == 'security':
                value = data.get('security_assessment', {}).get('overall_score', 0)
            else:
                continue
            
            values.append(value)
            timestamps.append(timestamp)
        
        if not values:
            return {'error': '无法提取数据'}
        
        # 计算趋势
        values_array = np.array(values)
        
        return {
            'metric': metric,
            'data_points': len(values),
            'values': values,
            'timestamps': timestamps,
            'statistics': {
                'min': float(np.min(values_array)),
                'max': float(np.max(values_array)),
                'mean': float(np.mean(values_array)),
                'std': float(np.std(values_array))
            },
            'trend': self._calculate_overall_trend(values)
        }
    
    def _calculate_overall_trend(self, values: List[float]) -> str:
        """计算总体趋势"""
        if len(values) < 2:
            return 'insufficient_data'
        
        # 使用线性回归计算斜率
        x = np.arange(len(values))
        y = np.array(values)
        
        # 计算斜率
        slope = np.polyfit(x, y, 1)[0]
        
        # 判断趋势
        if abs(slope) < 1:
            return 'stable'
        elif slope > 0:
            return 'increasing'
        else:
            return 'decreasing'
