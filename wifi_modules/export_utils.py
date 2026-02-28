#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WiFi数据导出工具统一模块
整合CSV、JSON等导出功能
减少代码重复，提高可维护性
"""

import csv
import json
from datetime import datetime
from typing import List, Dict, Any
from tkinter import filedialog, messagebox


class DataExporter:
    """数据导出器 - 统一CSV/JSON导出逻辑"""
    
    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]], 
                      columns: List[str] = None,
                      filename: str = None,
                      default_prefix: str = "wifi_data") -> bool:
        """
        导出数据到CSV文件
        
        Args:
            data: 数据列表，每个元素为字典
            columns: 列名列表（None则自动从第一行提取）
            filename: 保存文件名（None则弹出对话框）
            default_prefix: 默认文件名前缀
        
        Returns:
            bool: 成功返回True，失败或取消返回False
        """
        if not data:
            messagebox.showwarning("警告", "没有可导出的数据")
            return False
        
        # 确定列名
        if columns is None:
            columns = list(data[0].keys())
        
        # 确定文件名
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                initialfile=f"{default_prefix}_{timestamp}.csv",
                filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
            )
            
            if not filename:
                return False
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                
                for row in data:
                    # 只写入columns中指定的列
                    filtered_row = {k: row.get(k, '') for k in columns}
                    writer.writerow(filtered_row)
            
            messagebox.showinfo("成功", f"数据已导出到:\n{filename}")
            return True
            
        except Exception as e:
            messagebox.showerror("错误", f"导出CSV失败:\n{str(e)}")
            return False
    
    @staticmethod
    def export_to_json(data: Any, 
                       filename: str = None,
                       default_prefix: str = "wifi_data",
                       indent: int = 2) -> bool:
        """
        导出数据到JSON文件
        
        Args:
            data: 要导出的数据（字典、列表等JSON可序列化对象）
            filename: 保存文件名（None则弹出对话框）
            default_prefix: 默认文件名前缀
            indent: JSON缩进空格数
        
        Returns:
            bool: 成功返回True，失败或取消返回False
        """
        if data is None:
            messagebox.showwarning("警告", "没有可导出的数据")
            return False
        
        # 确定文件名
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                initialfile=f"{default_prefix}_{timestamp}.json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            
            if not filename:
                return False
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent, default=str)
            
            messagebox.showinfo("成功", f"数据已导出到:\n{filename}")
            return True
            
        except Exception as e:
            messagebox.showerror("错误", f"导出JSON失败:\n{str(e)}")
            return False
    
    @staticmethod
    def export_monitoring_data(monitor_data: List[Dict], 
                              format_type: str = 'csv',
                              prefix: str = "realtime_monitor") -> bool:
        """
        导出实时监控数据（专用格式化）
        
        Args:
            monitor_data: 监控数据列表
            format_type: 导出格式 ('csv' 或 'json')
            prefix: 文件名前缀
        
        Returns:
            bool: 成功返回True
        """
        if not monitor_data:
            messagebox.showwarning("警告", "没有监控数据可导出")
            return False
        
        if format_type == 'csv':
            columns = ['timestamp', 'ssid', 'signal', 'signal_percent', 
                      'band', 'channel', 'bssid']
            return DataExporter.export_to_csv(
                data=monitor_data,
                columns=columns,
                default_prefix=prefix
            )
        elif format_type == 'json':
            export_data = {
                'export_time': datetime.now().isoformat(),
                'data_count': len(monitor_data),
                'monitoring_data': monitor_data
            }
            return DataExporter.export_to_json(
                data=export_data,
                default_prefix=prefix
            )
        else:
            messagebox.showerror("错误", f"不支持的格式: {format_type}")
            return False
    
    @staticmethod
    def export_heatmap_data(measurement_data: List[Dict],
                           ap_locations: List[Dict] = None,
                           obstacles: List[Dict] = None,
                           metadata: Dict = None) -> bool:
        """
        导出热力图项目数据（JSON格式）
        
        Args:
            measurement_data: 测量点数据列表
            ap_locations: AP位置列表
            obstacles: 障碍物列表
            metadata: 附加元数据
        
        Returns:
            bool: 成功返回True
        """
        if not measurement_data:
            messagebox.showwarning("警告", "没有测量数据可保存")
            return False
        
        export_data = {
            'version': '2.0',
            'export_time': datetime.now().isoformat(),
            'metadata': metadata or {},
            'measurement_data': measurement_data,
            'ap_locations': ap_locations or [],
            'obstacles': obstacles or []
        }
        
        return DataExporter.export_to_json(
            data=export_data,
            default_prefix="wifi_heatmap_project"
        )
    
    @staticmethod
    def export_wifi6_analysis(networks: List[Dict],
                             summary: Dict = None) -> bool:
        """
        导出WiFi 6分析报告（JSON格式）
        
        Args:
            networks: WiFi 6网络列表
            summary: 摘要信息
        
        Returns:
            bool: 成功返回True
        """
        if not networks:
            messagebox.showwarning("警告", "没有WiFi 6网络数据可导出")
            return False
        
        export_data = {
            'report_type': 'WiFi 6/6E Analysis',
            'export_time': datetime.now().isoformat(),
            'summary': summary or {},
            'networks': networks
        }
        
        return DataExporter.export_to_json(
            data=export_data,
            default_prefix="wifi6_analysis_report"
        )
    
    @staticmethod
    def export_interference_report(sources: List[Dict],
                                   measurement_points: List[Dict] = None) -> bool:
        """
        导出干扰定位报告（JSON格式）
        
        Args:
            sources: 干扰源列表
            measurement_points: 测量点列表
        
        Returns:
            bool: 成功返回True
        """
        if not sources:
            messagebox.showwarning("警告", "没有检测到干扰源")
            return False
        
        export_data = {
            'report_type': 'Interference Locator',
            'export_time': datetime.now().isoformat(),
            'interference_sources': sources,
            'measurement_points': measurement_points or []
        }
        
        return DataExporter.export_to_json(
            data=export_data,
            default_prefix="interference_report"
        )


# 导出接口
__all__ = ['DataExporter']
