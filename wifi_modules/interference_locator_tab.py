#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能干扰源定位器 - GUI标签页
提供交互式测量、定位和可视化功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime
from typing import Optional, List
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from wifi_modules.interference_locator import (
    InterferenceLocator, InterferenceSource, MeasurementPoint,
    InterferenceType, InterferenceSeverity
)


class InterferenceLocatorTab:
    """干扰源定位器标签页"""
    
    def __init__(self, parent_notebook, language_manager=None):
        """初始化标签页"""
        self.language = language_manager
        
        # 创建标签页
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="📡 智能干扰定位")
        
        # 干扰定位器
        self.locator = InterferenceLocator()
        
        # 当前选中的干扰源
        self.selected_source: Optional[InterferenceSource] = None
        
        # 创建UI
        self._create_widgets()
        
    def _create_widgets(self):
        """创建UI组件"""
        # 顶部控制面板
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 左侧按钮组
        left_buttons = ttk.Frame(control_frame)
        left_buttons.pack(side=tk.LEFT)
        
        ttk.Button(
            left_buttons,
            text="➕ 添加测量点",
            command=self._add_measurement_dialog
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            left_buttons,
            text="🔍 检测干扰源",
            command=self._detect_interference
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            left_buttons,
            text="🗑️ 清空数据",
            command=self._clear_data
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            left_buttons,
            text="📊 导出报告",
            command=self._export_report
        ).pack(side=tk.LEFT, padx=2)
        
        # 右侧状态
        self.status_label = ttk.Label(
            control_frame,
            text="就绪 | 测量点: 0 | 干扰源: 0",
            font=("", 9)
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # 主容器 (左右分割)
        main_paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧面板
        left_panel = ttk.Frame(main_paned)
        main_paned.add(left_panel, weight=1)
        
        # 右侧面板
        right_panel = ttk.Frame(main_paned)
        main_paned.add(right_panel, weight=2)
        
        # === 左侧：数据列表 ===
        
        # 测量点列表
        measurement_frame = ttk.LabelFrame(left_panel, text="📍 测量点列表", padding=5)
        measurement_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 测量点表格
        columns = ('X', 'Y', 'RSSI', '频率')
        self.measurement_tree = ttk.Treeview(
            measurement_frame,
            columns=columns,
            show='tree headings',
            height=8
        )
        
        self.measurement_tree.heading('#0', text='#')
        self.measurement_tree.column('#0', width=30, anchor='center')
        
        for col in columns:
            self.measurement_tree.heading(col, text=col)
            if col in ['X', 'Y']:
                self.measurement_tree.column(col, width=60, anchor='center')
            elif col == 'RSSI':
                self.measurement_tree.column(col, width=70, anchor='center')
            else:
                self.measurement_tree.column(col, width=80, anchor='center')
        
        scrollbar_m = ttk.Scrollbar(measurement_frame, orient=tk.VERTICAL, command=self.measurement_tree.yview)
        self.measurement_tree.configure(yscrollcommand=scrollbar_m.set)
        
        self.measurement_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_m.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 干扰源列表
        source_frame = ttk.LabelFrame(left_panel, text="⚠️ 检测到的干扰源", padding=5)
        source_frame.pack(fill=tk.BOTH, expand=True)
        
        # 干扰源表格
        columns = ('类型', '严重度', '信道')
        self.source_tree = ttk.Treeview(
            source_frame,
            columns=columns,
            show='tree headings',
            height=8
        )
        
        self.source_tree.heading('#0', text='#')
        self.source_tree.column('#0', width=30, anchor='center')
        
        for col in columns:
            self.source_tree.heading(col, text=col)
            if col == '类型':
                self.source_tree.column(col, width=100)
            elif col == '严重度':
                self.source_tree.column(col, width=80, anchor='center')
            else:
                self.source_tree.column(col, width=80)
        
        scrollbar_s = ttk.Scrollbar(source_frame, orient=tk.VERTICAL, command=self.source_tree.yview)
        self.source_tree.configure(yscrollcommand=scrollbar_s.set)
        
        self.source_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_s.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.source_tree.bind('<<TreeviewSelect>>', self._on_source_selected)
        
        # === 右侧：可视化和详情 ===
        
        # 创建Notebook
        self.detail_notebook = ttk.Notebook(right_panel)
        self.detail_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 1. 定位地图标签页
        map_frame = ttk.Frame(self.detail_notebook, padding=5)
        self.detail_notebook.add(map_frame, text="🗺️ 定位地图")
        
        # Matplotlib图表
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=map_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 2. 热力图标签页
        heatmap_frame = ttk.Frame(self.detail_notebook, padding=5)
        self.detail_notebook.add(heatmap_frame, text="🔥 干扰热力图")
        
        self.heatmap_fig = Figure(figsize=(8, 6), dpi=100)
        self.heatmap_ax = self.heatmap_fig.add_subplot(111)
        self.heatmap_canvas = FigureCanvasTkAgg(self.heatmap_fig, master=heatmap_frame)
        self.heatmap_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 3. 详细信息标签页
        detail_frame = ttk.Frame(self.detail_notebook, padding=5)
        self.detail_notebook.add(detail_frame, text="📋 详细信息")
        
        # 干扰源详情
        info_label_frame = ttk.LabelFrame(detail_frame, text="干扰源信息", padding=5)
        info_label_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_text = tk.Text(info_label_frame, height=10, wrap=tk.WORD, state='disabled')
        info_scrollbar = ttk.Scrollbar(info_label_frame, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 缓解策略
        strategy_label_frame = ttk.LabelFrame(detail_frame, text="缓解策略", padding=5)
        strategy_label_frame.pack(fill=tk.BOTH, expand=True)
        
        self.strategy_text = tk.Text(strategy_label_frame, height=12, wrap=tk.WORD, state='disabled')
        strategy_scrollbar = ttk.Scrollbar(strategy_label_frame, command=self.strategy_text.yview)
        self.strategy_text.configure(yscrollcommand=strategy_scrollbar.set)
        self.strategy_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        strategy_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 4. 设置标签页
        settings_frame = ttk.Frame(self.detail_notebook, padding=10)
        self.detail_notebook.add(settings_frame, text="⚙️ 设置")
        
        # 路径损耗参数
        ttk.Label(settings_frame, text="路径损耗指数 (n):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.path_loss_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(
            settings_frame,
            from_=1.5,
            to=4.5,
            increment=0.1,
            textvariable=self.path_loss_var,
            width=10
        ).grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Label(settings_frame, text="(自由空间=2, 室内=3-4)", font=("", 8, "italic")).grid(
            row=0, column=2, sticky=tk.W, padx=5
        )
        
        # 参考距离
        ttk.Label(settings_frame, text="参考距离 (米):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ref_distance_var = tk.DoubleVar(value=1.0)
        ttk.Spinbox(
            settings_frame,
            from_=0.1,
            to=10.0,
            increment=0.1,
            textvariable=self.ref_distance_var,
            width=10
        ).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 参考RSSI
        ttk.Label(settings_frame, text="参考RSSI (dBm):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ref_rssi_var = tk.DoubleVar(value=-40.0)
        ttk.Spinbox(
            settings_frame,
            from_=-60.0,
            to=-20.0,
            increment=1.0,
            textvariable=self.ref_rssi_var,
            width=10
        ).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # 应用按钮
        ttk.Button(
            settings_frame,
            text="应用设置",
            command=self._apply_settings
        ).grid(row=3, column=0, columnspan=2, pady=10)
        
        # 初始化图表
        self._update_map()
        self._update_heatmap()
    
    def _add_measurement_dialog(self):
        """添加测量点对话框"""
        dialog = tk.Toplevel(self.frame)
        dialog.title("添加测量点")
        dialog.geometry("400x250")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # X坐标
        ttk.Label(frame, text="X 坐标 (米):").grid(row=0, column=0, sticky=tk.W, pady=5)
        x_var = tk.DoubleVar(value=0.0)
        ttk.Entry(frame, textvariable=x_var, width=15).grid(row=0, column=1, pady=5)
        
        # Y坐标
        ttk.Label(frame, text="Y 坐标 (米):").grid(row=1, column=0, sticky=tk.W, pady=5)
        y_var = tk.DoubleVar(value=0.0)
        ttk.Entry(frame, textvariable=y_var, width=15).grid(row=1, column=1, pady=5)
        
        # RSSI
        ttk.Label(frame, text="RSSI (dBm):").grid(row=2, column=0, sticky=tk.W, pady=5)
        rssi_var = tk.DoubleVar(value=-50.0)
        ttk.Spinbox(frame, from_=-100, to=-20, increment=1, textvariable=rssi_var, width=15).grid(
            row=2, column=1, pady=5
        )
        
        # 频率
        ttk.Label(frame, text="频率 (MHz):").grid(row=3, column=0, sticky=tk.W, pady=5)
        freq_var = tk.DoubleVar(value=2437.0)
        ttk.Spinbox(frame, from_=2400, to=5900, increment=5, textvariable=freq_var, width=15).grid(
            row=3, column=1, pady=5
        )
        
        # 按钮
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        def add_point():
            try:
                x = x_var.get()
                y = y_var.get()
                rssi = rssi_var.get()
                freq = freq_var.get()
                
                self.locator.add_measurement(x, y, rssi, freq)
                self._update_measurement_list()
                self._update_status()
                
                messagebox.showinfo("成功", f"已添加测量点 ({x}, {y})")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"添加失败: {e}")
        
        ttk.Button(button_frame, text="添加", command=add_point, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)
    
    def _detect_interference(self):
        """检测干扰源"""
        if len(self.locator.measurement_points) < 3:
            messagebox.showwarning("警告", "至少需要3个测量点才能进行定位")
            return
        
        try:
            sources = self.locator.detect_interference_sources()
            
            if not sources:
                messagebox.showinfo("结果", "未检测到干扰源")
                return
            
            self._update_source_list()
            self._update_map()
            self._update_heatmap()
            self._update_status()
            
            messagebox.showinfo("成功", f"检测到 {len(sources)} 个干扰源")
            
        except Exception as e:
            messagebox.showerror("错误", f"检测失败: {e}")
    
    def _clear_data(self):
        """清空数据"""
        if messagebox.askyesno("确认", "确定要清空所有数据吗？"):
            self.locator.clear_measurements()
            self.locator.interference_sources.clear()
            
            self._update_measurement_list()
            self._update_source_list()
            self._update_map()
            self._update_heatmap()
            self._update_status()
            self._clear_detail_info()
    
    def _export_report(self):
        """导出报告"""
        if not self.locator.interference_sources:
            messagebox.showwarning("警告", "没有数据可导出，请先检测干扰源")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
                initialfile=f"Interference_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            if file_path:
                report = self.locator.export_report()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("成功", f"报告已导出到:\n{file_path}")
        
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {e}")
    
    def _apply_settings(self):
        """应用设置"""
        try:
            self.locator.path_loss_exponent = self.path_loss_var.get()
            self.locator.reference_distance = self.ref_distance_var.get()
            self.locator.reference_rssi = self.ref_rssi_var.get()
            
            messagebox.showinfo("成功", "设置已应用")
            
            # 重新计算（如果有数据）
            if self.locator.measurement_points:
                self._detect_interference()
        
        except Exception as e:
            messagebox.showerror("错误", f"应用设置失败: {e}")
    
    def _update_measurement_list(self):
        """更新测量点列表"""
        # 清空列表
        for item in self.measurement_tree.get_children():
            self.measurement_tree.delete(item)
        
        # 添加测量点
        for i, point in enumerate(self.locator.measurement_points, 1):
            self.measurement_tree.insert(
                '',
                'end',
                text=str(i),
                values=(
                    f"{point.x:.1f}",
                    f"{point.y:.1f}",
                    f"{point.rssi:.0f} dBm",
                    f"{point.frequency:.0f} MHz"
                )
            )
    
    def _update_source_list(self):
        """更新干扰源列表"""
        # 清空列表
        for item in self.source_tree.get_children():
            self.source_tree.delete(item)
        
        # 添加干扰源
        for i, source in enumerate(self.locator.interference_sources, 1):
            channels = ', '.join(map(str, source.affected_channels[:5]))
            if len(source.affected_channels) > 5:
                channels += f" (+{len(source.affected_channels)-5})"
            
            # 根据严重程度设置标签
            tags = ()
            if source.severity == InterferenceSeverity.CRITICAL:
                tags = ('critical',)
            elif source.severity == InterferenceSeverity.HIGH:
                tags = ('high',)
            
            self.source_tree.insert(
                '',
                'end',
                text=str(i),
                values=(
                    source.interference_type.value,
                    source.severity.value,
                    channels
                ),
                tags=tags
            )
        
        # 配置标签颜色
        self.source_tree.tag_configure('critical', foreground='red', font=("", 9, "bold"))
        self.source_tree.tag_configure('high', foreground='orange')
    
    def _update_map(self):
        """更新定位地图"""
        self.ax.clear()
        
        if not self.locator.measurement_points:
            self.ax.text(0.5, 0.5, '暂无数据\n请添加测量点', 
                        ha='center', va='center', fontsize=12, color='gray')
            self.ax.set_xlim(0, 10)
            self.ax.set_ylim(0, 10)
            self.canvas.draw()
            return
        
        # 绘制测量点
        x_coords = [p.x for p in self.locator.measurement_points]
        y_coords = [p.y for p in self.locator.measurement_points]
        rssi_values = [p.rssi for p in self.locator.measurement_points]
        
        scatter = self.ax.scatter(
            x_coords, y_coords,
            c=rssi_values,
            cmap='RdYlGn',
            s=100,
            alpha=0.6,
            edgecolors='black',
            linewidths=1
        )
        
        # 添加标签
        for i, (x, y, rssi) in enumerate(zip(x_coords, y_coords, rssi_values), 1):
            self.ax.annotate(
                f"M{i}\n{rssi:.0f}dBm",
                (x, y),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8
            )
        
        # 绘制干扰源
        if self.locator.interference_sources:
            for i, source in enumerate(self.locator.interference_sources, 1):
                if source.location:
                    sx, sy = source.location
                    
                    # 根据严重程度选择颜色
                    color_map = {
                        InterferenceSeverity.CRITICAL: 'red',
                        InterferenceSeverity.HIGH: 'orange',
                        InterferenceSeverity.MEDIUM: 'yellow',
                        InterferenceSeverity.LOW: 'green',
                        InterferenceSeverity.NEGLIGIBLE: 'blue'
                    }
                    color = color_map.get(source.severity, 'gray')
                    
                    # 绘制干扰源
                    self.ax.plot(sx, sy, marker='*', markersize=20, color=color, 
                               markeredgecolor='black', markeredgewidth=1.5)
                    
                    # 标签
                    self.ax.annotate(
                        f"I{i}\n{source.interference_type.value[:4]}",
                        (sx, sy),
                        xytext=(10, -10),
                        textcoords='offset points',
                        fontsize=9,
                        fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.3)
                    )
                    
                    # 绘制置信圈
                    if source.location_confidence > 0.3:
                        radius = 2 * (1 - source.location_confidence)
                        circle = plt.Circle(
                            (sx, sy), radius,
                            color=color, fill=False,
                            linestyle='--', alpha=0.5
                        )
                        self.ax.add_patch(circle)
        
        # 设置图表
        self.ax.set_xlabel('X 坐标 (米)', fontsize=10)
        self.ax.set_ylabel('Y 坐标 (米)', fontsize=10)
        self.ax.set_title('干扰源定位地图', fontsize=12, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect('equal')
        
        # 添加颜色条
        if self.locator.measurement_points:
            cbar = self.fig.colorbar(scatter, ax=self.ax)
            cbar.set_label('RSSI (dBm)', fontsize=9)
        
        # 图例
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                  markersize=10, label='测量点'),
            Line2D([0], [0], marker='*', color='w', markerfacecolor='red', 
                  markersize=15, label='干扰源')
        ]
        self.ax.legend(handles=legend_elements, loc='upper right', fontsize=8)
        
        self.canvas.draw()
    
    def _update_heatmap(self):
        """更新热力图"""
        self.heatmap_ax.clear()
        
        if not self.locator.interference_sources:
            self.heatmap_ax.text(0.5, 0.5, '暂无干扰源数据\n请先检测干扰源', 
                               ha='center', va='center', fontsize=12, color='gray')
            self.heatmap_ax.set_xlim(0, 10)
            self.heatmap_ax.set_ylim(0, 10)
            self.heatmap_canvas.draw()
            return
        
        # 生成热力图数据
        heatmap_data = self.locator.get_heatmap_data(grid_size=50)
        
        # 绘制热力图
        im = self.heatmap_ax.imshow(
            heatmap_data,
            cmap='hot_r',
            origin='lower',
            aspect='auto',
            interpolation='bilinear'
        )
        
        # 添加颜色条
        cbar = self.heatmap_fig.colorbar(im, ax=self.heatmap_ax)
        cbar.set_label('干扰强度 (dBm)', fontsize=9)
        
        # 设置标题
        self.heatmap_ax.set_title('干扰强度热力图', fontsize=12, fontweight='bold')
        self.heatmap_ax.set_xlabel('X 坐标', fontsize=10)
        self.heatmap_ax.set_ylabel('Y 坐标', fontsize=10)
        
        self.heatmap_canvas.draw()
    
    def _update_status(self):
        """更新状态栏"""
        m_count = len(self.locator.measurement_points)
        s_count = len(self.locator.interference_sources)
        
        status = f"就绪 | 测量点: {m_count} | 干扰源: {s_count}"
        
        if s_count > 0:
            critical_count = sum(
                1 for s in self.locator.interference_sources 
                if s.severity == InterferenceSeverity.CRITICAL
            )
            if critical_count > 0:
                status += f" | ⚠️ 严重干扰: {critical_count}"
        
        self.status_label.config(text=status)
    
    def _on_source_selected(self, event):
        """干扰源选择事件"""
        selection = self.source_tree.selection()
        if not selection:
            return
        
        # 获取选中项索引
        item = selection[0]
        index = int(self.source_tree.item(item, 'text')) - 1
        
        if 0 <= index < len(self.locator.interference_sources):
            self.selected_source = self.locator.interference_sources[index]
            self._update_detail_info()
    
    def _update_detail_info(self):
        """更新详细信息"""
        if not self.selected_source:
            return
        
        source = self.selected_source
        
        # 基本信息
        info = f"""干扰源ID: {source.source_id}
类型: {source.interference_type.value}
严重程度: {source.severity.value} ({source.get_severity_score()}/100)

频率范围: {source.frequency_range[0]:.1f} - {source.frequency_range[1]:.1f} MHz
平均功率: {source.avg_power:.1f} dBm
检测次数: {source.detection_count}

首次检测: {source.first_detected.strftime('%Y-%m-%d %H:%M:%S')}
最后检测: {source.last_detected.strftime('%Y-%m-%d %H:%M:%S')}

影响信道: {', '.join(map(str, source.affected_channels))}
"""
        
        if source.location:
            x, y = source.location
            info += f"\n定位坐标: ({x:.2f}, {y:.2f}) 米"
            info += f"\n置信度: {source.location_confidence*100:.1f}%"
        else:
            info += "\n定位坐标: 未定位"
        
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', tk.END)
        self.info_text.insert('1.0', info)
        self.info_text.config(state='disabled')
        
        # 缓解策略
        if source.mitigation_strategies:
            strategies = "\n\n".join([f"{i}. {s}" for i, s in enumerate(source.mitigation_strategies, 1)])
        else:
            strategies = "暂无缓解策略"
        
        self.strategy_text.config(state='normal')
        self.strategy_text.delete('1.0', tk.END)
        self.strategy_text.insert('1.0', strategies)
        self.strategy_text.config(state='disabled')
    
    def _clear_detail_info(self):
        """清空详细信息"""
        self.selected_source = None
        
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', tk.END)
        self.info_text.config(state='disabled')
        
        self.strategy_text.config(state='normal')
        self.strategy_text.delete('1.0', tk.END)
        self.strategy_text.config(state='disabled')
    
    def get_frame(self):
        """获取框架"""
        return self.frame


# 导入plt（延迟导入以避免循环）
import matplotlib.pyplot as plt


# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.title("智能干扰源定位器测试")
    root.geometry("1200x800")
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    tab = InterferenceLocatorTab(notebook)
    
    root.mainloop()
