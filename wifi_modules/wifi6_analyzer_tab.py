#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WiFi 6/6E 高级分析器 - GUI标签页
提供WiFi 6特性可视化界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
from typing import List, Optional

from wifi_modules.wifi6_analyzer import (
    WiFi6Analyzer, WiFi6NetworkInfo, WiFi6Standard,
    BSSColorStatus, OFDMAAnalysis, BSSColorAnalysis,
    TWTAnalysis, MUMIMOAnalysis
)


class WiFi6AnalyzerTab:
    """WiFi 6/6E 分析器标签页"""
    
    def __init__(self, parent_notebook, language_manager=None):
        """初始化WiFi 6分析器标签页"""
        self.language = language_manager
        
        # 创建标签页
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="WiFi 6/6E 分析")
        
        # WiFi 6分析器
        self.analyzer = WiFi6Analyzer()
        self.networks: List[WiFi6NetworkInfo] = []
        self.is_scanning = False
        
        # 创建UI
        self._create_widgets()
        
    def _create_widgets(self):
        """创建UI组件"""
        # 顶部控制面板
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 扫描按钮
        self.scan_button = ttk.Button(
            control_frame,
            text="🔍 扫描WiFi 6网络",
            command=self._start_scan,
            style="Accent.TButton"
        )
        self.scan_button.pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        refresh_button = ttk.Button(
            control_frame,
            text="🔄 刷新",
            command=self._refresh_display
        )
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        # 导出按钮
        export_button = ttk.Button(
            control_frame,
            text="📊 导出报告",
            command=self._export_report
        )
        export_button.pack(side=tk.LEFT, padx=5)
        
        # 状态标签
        self.status_label = ttk.Label(
            control_frame,
            text="就绪",
            foreground="green"
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # 创建主容器
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧：网络列表
        left_frame = ttk.LabelFrame(main_container, text="WiFi 6/6E 网络列表", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 网络列表 (Treeview)
        columns = ('SSID', '标准', '信道', '信号', '评分')
        self.network_tree = ttk.Treeview(left_frame, columns=columns, show='tree headings', height=15)
        
        self.network_tree.heading('#0', text='#')
        self.network_tree.column('#0', width=40, anchor='center')
        
        for col in columns:
            self.network_tree.heading(col, text=col)
            if col == 'SSID':
                self.network_tree.column(col, width=200)
            elif col == '标准':
                self.network_tree.column(col, width=150)
            elif col == '信道':
                self.network_tree.column(col, width=80, anchor='center')
            elif col == '信号':
                self.network_tree.column(col, width=80, anchor='center')
            elif col == '评分':
                self.network_tree.column(col, width=80, anchor='center')
        
        # 滚动条
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.network_tree.yview)
        self.network_tree.configure(yscrollcommand=scrollbar.set)
        
        self.network_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.network_tree.bind('<<TreeviewSelect>>', self._on_network_selected)
        
        # 右侧：详细信息
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 摘要信息
        summary_frame = ttk.LabelFrame(right_frame, text="网络摘要", padding=5)
        summary_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.summary_text = tk.Text(summary_frame, height=6, wrap=tk.WORD, state='disabled')
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        # 详细信息 (Notebook)
        self.detail_notebook = ttk.Notebook(right_frame)
        self.detail_notebook.pack(fill=tk.BOTH, expand=True)
        
        # OFDMA标签页
        self.ofdma_frame = self._create_ofdma_tab()
        self.detail_notebook.add(self.ofdma_frame, text="OFDMA分析")
        
        # BSS颜色标签页
        self.bss_color_frame = self._create_bss_color_tab()
        self.detail_notebook.add(self.bss_color_frame, text="BSS颜色")
        
        # TWT标签页
        self.twt_frame = self._create_twt_tab()
        self.detail_notebook.add(self.twt_frame, text="TWT省电")
        
        # MU-MIMO标签页
        self.mu_mimo_frame = self._create_mu_mimo_tab()
        self.detail_notebook.add(self.mu_mimo_frame, text="MU-MIMO")
        
        # HE能力标签页
        self.he_cap_frame = self._create_he_capabilities_tab()
        self.detail_notebook.add(self.he_cap_frame, text="HE能力")
    
    def _create_ofdma_tab(self) -> ttk.Frame:
        """创建OFDMA标签页"""
        frame = ttk.Frame(self.detail_notebook, padding=10)
        
        # 状态
        status_frame = ttk.LabelFrame(frame, text="OFDMA状态", padding=5)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.ofdma_enabled_label = ttk.Label(status_frame, text="未启用", font=("", 10, "bold"))
        self.ofdma_enabled_label.pack()
        
        self.ofdma_direction_label = ttk.Label(status_frame, text="DL/UL: -/-")
        self.ofdma_direction_label.pack()
        
        # RU分配
        ru_frame = ttk.LabelFrame(frame, text="RU (Resource Unit) 分配", padding=5)
        ru_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.ofdma_ru_text = tk.Text(ru_frame, height=5, wrap=tk.WORD, state='disabled')
        self.ofdma_ru_text.pack(fill=tk.BOTH, expand=True)
        
        # 效率评分
        efficiency_frame = ttk.LabelFrame(frame, text="效率评估", padding=5)
        efficiency_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.ofdma_score_label = ttk.Label(efficiency_frame, text="评分: -/100", font=("", 12, "bold"))
        self.ofdma_score_label.pack()
        
        self.ofdma_users_label = ttk.Label(efficiency_frame, text="并发用户: -")
        self.ofdma_users_label.pack()
        
        # 建议
        recommend_frame = ttk.LabelFrame(frame, text="优化建议", padding=5)
        recommend_frame.pack(fill=tk.BOTH, expand=True)
        
        self.ofdma_recommend_text = tk.Text(recommend_frame, height=5, wrap=tk.WORD, state='disabled')
        self.ofdma_recommend_text.pack(fill=tk.BOTH, expand=True)
        
        return frame
    
    def _create_bss_color_tab(self) -> ttk.Frame:
        """创建BSS颜色标签页"""
        frame = ttk.Frame(self.detail_notebook, padding=10)
        
        # 颜色状态
        status_frame = ttk.LabelFrame(frame, text="BSS颜色状态", padding=5)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.bss_color_id_label = ttk.Label(status_frame, text="颜色ID: -", font=("", 12, "bold"))
        self.bss_color_id_label.pack()
        
        self.bss_color_status_label = ttk.Label(status_frame, text="状态: 未知")
        self.bss_color_status_label.pack()
        
        # 冲突信息
        conflict_frame = ttk.LabelFrame(frame, text="冲突检测", padding=5)
        conflict_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.bss_conflict_count_label = ttk.Label(conflict_frame, text="冲突数: 0")
        self.bss_conflict_count_label.pack()
        
        self.bss_conflict_text = tk.Text(conflict_frame, height=4, wrap=tk.WORD, state='disabled')
        self.bss_conflict_text.pack(fill=tk.BOTH, expand=True)
        
        # 优化建议
        recommend_frame = ttk.LabelFrame(frame, text="优化建议", padding=5)
        recommend_frame.pack(fill=tk.BOTH, expand=True)
        
        self.bss_optimal_label = ttk.Label(recommend_frame, text="推荐颜色: -", font=("", 10, "bold"))
        self.bss_optimal_label.pack()
        
        self.bss_recommend_text = tk.Text(recommend_frame, height=5, wrap=tk.WORD, state='disabled')
        self.bss_recommend_text.pack(fill=tk.BOTH, expand=True)
        
        return frame
    
    def _create_twt_tab(self) -> ttk.Frame:
        """创建TWT标签页"""
        frame = ttk.Frame(self.detail_notebook, padding=10)
        
        # TWT支持
        support_frame = ttk.LabelFrame(frame, text="TWT支持状态", padding=5)
        support_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.twt_supported_label = ttk.Label(support_frame, text="不支持", font=("", 10, "bold"))
        self.twt_supported_label.pack()
        
        self.twt_types_label = ttk.Label(support_frame, text="类型: -")
        self.twt_types_label.pack()
        
        # 省电效率
        efficiency_frame = ttk.LabelFrame(frame, text="省电效率", padding=5)
        efficiency_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.twt_efficiency_label = ttk.Label(efficiency_frame, text="效率: -%", font=("", 12, "bold"))
        self.twt_efficiency_label.pack()
        
        self.twt_wake_label = ttk.Label(efficiency_frame, text="唤醒间隔: - ms")
        self.twt_wake_label.pack()
        
        self.twt_sleep_label = ttk.Label(efficiency_frame, text="睡眠时长: - ms")
        self.twt_sleep_label.pack()
        
        # 建议
        recommend_frame = ttk.LabelFrame(frame, text="应用建议", padding=5)
        recommend_frame.pack(fill=tk.BOTH, expand=True)
        
        self.twt_recommend_text = tk.Text(recommend_frame, height=6, wrap=tk.WORD, state='disabled')
        self.twt_recommend_text.pack(fill=tk.BOTH, expand=True)
        
        return frame
    
    def _create_mu_mimo_tab(self) -> ttk.Frame:
        """创建MU-MIMO标签页"""
        frame = ttk.Frame(self.detail_notebook, padding=10)
        
        # MU-MIMO状态
        status_frame = ttk.LabelFrame(frame, text="MU-MIMO状态", padding=5)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mu_mimo_dl_label = ttk.Label(status_frame, text="下行MU-MIMO: -", font=("", 10, "bold"))
        self.mu_mimo_dl_label.pack()
        
        self.mu_mimo_ul_label = ttk.Label(status_frame, text="上行MU-MIMO: -")
        self.mu_mimo_ul_label.pack()
        
        # 性能参数
        performance_frame = ttk.LabelFrame(frame, text="性能参数", padding=5)
        performance_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mu_mimo_streams_label = ttk.Label(performance_frame, text="空间流: -")
        self.mu_mimo_streams_label.pack()
        
        self.mu_mimo_users_label = ttk.Label(performance_frame, text="最大用户: -")
        self.mu_mimo_users_label.pack()
        
        self.mu_mimo_beamforming_label = ttk.Label(performance_frame, text="波束成形: -")
        self.mu_mimo_beamforming_label.pack()
        
        # 效率评分
        efficiency_frame = ttk.LabelFrame(frame, text="效率评估", padding=5)
        efficiency_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mu_mimo_score_label = ttk.Label(efficiency_frame, text="评分: -/100", font=("", 12, "bold"))
        self.mu_mimo_score_label.pack()
        
        # 建议
        recommend_frame = ttk.LabelFrame(frame, text="优化建议", padding=5)
        recommend_frame.pack(fill=tk.BOTH, expand=True)
        
        self.mu_mimo_recommend_text = tk.Text(recommend_frame, height=5, wrap=tk.WORD, state='disabled')
        self.mu_mimo_recommend_text.pack(fill=tk.BOTH, expand=True)
        
        return frame
    
    def _create_he_capabilities_tab(self) -> ttk.Frame:
        """创建HE能力标签页"""
        frame = ttk.Frame(self.detail_notebook, padding=10)
        
        # 说明
        info_label = ttk.Label(
            frame,
            text="HE (High Efficiency) 能力列表 - WiFi 6特性支持情况",
            font=("", 9, "italic")
        )
        info_label.pack(pady=(0, 10))
        
        # 能力列表
        self.he_cap_tree = ttk.Treeview(frame, columns=('Capability', 'Status'), show='headings', height=15)
        self.he_cap_tree.heading('Capability', text='能力')
        self.he_cap_tree.heading('Status', text='状态')
        self.he_cap_tree.column('Capability', width=300)
        self.he_cap_tree.column('Status', width=100, anchor='center')
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.he_cap_tree.yview)
        self.he_cap_tree.configure(yscrollcommand=scrollbar.set)
        
        self.he_cap_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return frame
    
    def _start_scan(self):
        """开始扫描"""
        if self.is_scanning:
            messagebox.showinfo("提示", "正在扫描中，请稍候...")
            return
        
        self.is_scanning = True
        self.scan_button.config(state='disabled')
        self.status_label.config(text="正在扫描WiFi 6网络...", foreground="orange")
        
        # 在后台线程中扫描
        thread = threading.Thread(target=self._scan_thread, daemon=True)
        thread.start()
    
    def _scan_thread(self):
        """扫描线程"""
        try:
            self.networks = self.analyzer.scan_wifi6_networks()
            
            # 更新UI (需要在主线程中)
            self.frame.after(0, self._update_network_list)
            self.frame.after(0, self._update_summary)
            self.frame.after(0, lambda: self.status_label.config(
                text=f"扫描完成 - 发现 {len(self.networks)} 个网络",
                foreground="green"
            ))
        except Exception as e:
            self.frame.after(0, lambda: messagebox.showerror("错误", f"扫描失败: {e}"))
            self.frame.after(0, lambda: self.status_label.config(
                text=f"扫描失败: {e}",
                foreground="red"
            ))
        finally:
            self.is_scanning = False
            self.frame.after(0, lambda: self.scan_button.config(state='normal'))
    
    def _update_network_list(self):
        """更新网络列表"""
        # 清空列表
        for item in self.network_tree.get_children():
            self.network_tree.delete(item)
        
        # 添加网络
        for i, network in enumerate(self.networks, 1):
            # 格式化数据
            ssid = network.ssid if network.ssid else "(Hidden)"
            standard = network.standard.value
            channel = f"{network.channel} ({network.frequency}MHz)"
            signal = f"{network.signal_strength} dBm"
            score = f"{network.get_overall_score():.1f}"
            
            # 根据标准设置标签
            tags = ()
            if network.standard == WiFi6Standard.WIFI6E_AX:
                tags = ('wifi6e',)
            elif network.standard == WiFi6Standard.WIFI6_AX:
                tags = ('wifi6',)
            
            self.network_tree.insert(
                '',
                'end',
                text=str(i),
                values=(ssid, standard, channel, signal, score),
                tags=tags
            )
        
        # 配置标签颜色
        self.network_tree.tag_configure('wifi6e', foreground='#0066CC', font=("", 9, "bold"))
        self.network_tree.tag_configure('wifi6', foreground='#0099FF')
    
    def _update_summary(self):
        """更新摘要信息"""
        summary = self.analyzer.get_wifi6_summary()
        
        text = f"""总网络数: {summary['total_networks']}
WiFi 6网络: {summary['wifi6_count']} ({summary['wifi6_ratio']*100:.1f}%)
WiFi 6E网络: {summary['wifi6e_count']}
OFDMA启用: {summary['ofdma_enabled']}
MU-MIMO启用: {summary['mu_mimo_enabled']}
TWT支持: {summary['twt_supported']}
BSS颜色冲突: {summary['bss_color_conflicts']}
平均评分: {summary['average_score']:.1f}/100
扫描时间: {summary['scan_time']}"""
        
        self.summary_text.config(state='normal')
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', text)
        self.summary_text.config(state='disabled')
    
    def _on_network_selected(self, event):
        """网络选择事件"""
        selection = self.network_tree.selection()
        if not selection:
            return
        
        # 获取选中项的索引
        item = selection[0]
        index = int(self.network_tree.item(item, 'text')) - 1
        
        if 0 <= index < len(self.networks):
            network = self.networks[index]
            self._update_network_details(network)
    
    def _update_network_details(self, network: WiFi6NetworkInfo):
        """更新网络详细信息"""
        # OFDMA
        if network.ofdma_analysis:
            ofdma = network.ofdma_analysis
            
            enabled_text = "已启用 ✓" if ofdma.enabled else "未启用 ✗"
            self.ofdma_enabled_label.config(
                text=enabled_text,
                foreground="green" if ofdma.enabled else "red"
            )
            
            dl = "✓" if ofdma.dl_ofdma_enabled else "✗"
            ul = "✓" if ofdma.ul_ofdma_enabled else "✗"
            self.ofdma_direction_label.config(text=f"下行/上行: {dl}/{ul}")
            
            # RU分配
            ru_text = "\n".join([f"{k}: {v}" for k, v in ofdma.ru_allocation.items()])
            self._update_text_widget(self.ofdma_ru_text, ru_text)
            
            # 评分
            self.ofdma_score_label.config(text=f"评分: {ofdma.efficiency_score:.1f}/100")
            self.ofdma_users_label.config(text=f"并发用户: {ofdma.concurrent_users}")
            
            # 建议
            recommend_text = "\n".join([f"• {r}" for r in ofdma.recommendations])
            self._update_text_widget(self.ofdma_recommend_text, recommend_text)
        
        # BSS颜色
        if network.bss_color_analysis:
            bss = network.bss_color_analysis
            
            color_text = f"颜色ID: {bss.color_id}" if bss.color_id else "颜色ID: -"
            self.bss_color_id_label.config(text=color_text)
            
            status_text = f"状态: {bss.status.value}"
            color = "green" if bss.status == BSSColorStatus.UNIQUE else "orange" if bss.status == BSSColorStatus.CONFLICT else "gray"
            self.bss_color_status_label.config(text=status_text, foreground=color)
            
            self.bss_conflict_count_label.config(text=f"冲突数: {bss.conflict_count}")
            
            conflict_text = "\n".join(bss.conflicting_bssids) if bss.conflicting_bssids else "无冲突"
            self._update_text_widget(self.bss_conflict_text, conflict_text)
            
            optimal_text = f"推荐颜色: {bss.optimal_color}" if bss.optimal_color else "推荐颜色: 当前最优"
            self.bss_optimal_label.config(text=optimal_text)
            
            recommend_text = "\n".join([f"• {r}" for r in bss.recommendations])
            self._update_text_widget(self.bss_recommend_text, recommend_text)
        
        # TWT
        if network.twt_analysis:
            twt = network.twt_analysis
            
            supported_text = "支持 ✓" if twt.supported else "不支持 ✗"
            self.twt_supported_label.config(
                text=supported_text,
                foreground="green" if twt.supported else "red"
            )
            
            types = []
            if twt.individual_twt:
                types.append("个体")
            if twt.broadcast_twt:
                types.append("广播")
            if twt.flexible_twt:
                types.append("灵活")
            types_text = f"类型: {'/'.join(types)}" if types else "类型: -"
            self.twt_types_label.config(text=types_text)
            
            self.twt_efficiency_label.config(text=f"效率: {twt.power_save_efficiency:.1f}%")
            self.twt_wake_label.config(text=f"唤醒间隔: {twt.wake_interval} ms")
            self.twt_sleep_label.config(text=f"睡眠时长: {twt.avg_sleep_duration} ms")
            
            recommend_text = "\n".join([f"• {r}" for r in twt.recommendations])
            self._update_text_widget(self.twt_recommend_text, recommend_text)
        
        # MU-MIMO
        if network.mu_mimo_analysis:
            mu = network.mu_mimo_analysis
            
            dl_text = "支持 ✓" if mu.dl_mu_mimo else "不支持 ✗"
            self.mu_mimo_dl_label.config(
                text=f"下行MU-MIMO: {dl_text}",
                foreground="green" if mu.dl_mu_mimo else "red"
            )
            
            ul_text = "支持 ✓" if mu.ul_mu_mimo else "不支持 ✗"
            self.mu_mimo_ul_label.config(
                text=f"上行MU-MIMO: {ul_text}",
                foreground="green" if mu.ul_mu_mimo else "gray"
            )
            
            self.mu_mimo_streams_label.config(text=f"空间流: {mu.spatial_streams}")
            self.mu_mimo_users_label.config(text=f"最大用户: {mu.max_users}")
            
            bf_text = "支持 ✓" if mu.beamforming else "不支持 ✗"
            self.mu_mimo_beamforming_label.config(text=f"波束成形: {bf_text}")
            
            self.mu_mimo_score_label.config(text=f"评分: {mu.efficiency_score:.1f}/100")
            
            recommend_text = "\n".join([f"• {r}" for r in mu.recommendations])
            self._update_text_widget(self.mu_mimo_recommend_text, recommend_text)
        
        # HE能力
        if network.he_capabilities:
            # 清空列表
            for item in self.he_cap_tree.get_children():
                self.he_cap_tree.delete(item)
            
            # 添加能力
            for cap_name, supported in network.he_capabilities.items():
                status = "✓ 支持" if supported else "✗ 不支持"
                tags = ('supported',) if supported else ('not_supported',)
                self.he_cap_tree.insert('', 'end', values=(cap_name, status), tags=tags)
            
            # 配置标签颜色
            self.he_cap_tree.tag_configure('supported', foreground='green')
            self.he_cap_tree.tag_configure('not_supported', foreground='gray')
    
    def _update_text_widget(self, widget: tk.Text, text: str):
        """更新Text组件内容"""
        widget.config(state='normal')
        widget.delete('1.0', tk.END)
        widget.insert('1.0', text)
        widget.config(state='disabled')
    
    def _refresh_display(self):
        """刷新显示"""
        if self.networks:
            self._update_network_list()
            self._update_summary()
            self.status_label.config(text="已刷新", foreground="green")
        else:
            messagebox.showinfo("提示", "请先扫描网络")
    
    def _export_report(self):
        """导出报告"""
        if not self.networks:
            messagebox.showinfo("提示", "没有数据可导出，请先扫描网络")
            return
        
        try:
            from tkinter import filedialog
            import json
            
            # 选择保存位置
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
                initialfile=f"WiFi6_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            if file_path:
                # 准备导出数据
                export_data = {
                    'scan_time': datetime.now().isoformat(),
                    'summary': self.analyzer.get_wifi6_summary(),
                    'networks': []
                }
                
                for network in self.networks:
                    network_data = {
                        'ssid': network.ssid,
                        'bssid': network.bssid,
                        'channel': network.channel,
                        'frequency': network.frequency,
                        'bandwidth': network.bandwidth,
                        'standard': network.standard.value,
                        'signal_strength': network.signal_strength,
                        'overall_score': network.get_overall_score(),
                    }
                    
                    if network.ofdma_analysis:
                        network_data['ofdma'] = {
                            'enabled': network.ofdma_analysis.enabled,
                            'efficiency_score': network.ofdma_analysis.efficiency_score,
                            'concurrent_users': network.ofdma_analysis.concurrent_users,
                            'ru_allocation': network.ofdma_analysis.ru_allocation,
                        }
                    
                    if network.bss_color_analysis:
                        network_data['bss_color'] = {
                            'color_id': network.bss_color_analysis.color_id,
                            'status': network.bss_color_analysis.status.value,
                            'conflict_count': network.bss_color_analysis.conflict_count,
                        }
                    
                    if network.twt_analysis:
                        network_data['twt'] = {
                            'supported': network.twt_analysis.supported,
                            'power_save_efficiency': network.twt_analysis.power_save_efficiency,
                        }
                    
                    if network.mu_mimo_analysis:
                        network_data['mu_mimo'] = {
                            'dl_mu_mimo': network.mu_mimo_analysis.dl_mu_mimo,
                            'ul_mu_mimo': network.mu_mimo_analysis.ul_mu_mimo,
                            'spatial_streams': network.mu_mimo_analysis.spatial_streams,
                            'efficiency_score': network.mu_mimo_analysis.efficiency_score,
                        }
                    
                    export_data['networks'].append(network_data)
                
                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("成功", f"报告已导出到:\n{file_path}")
                self.status_label.config(text="报告导出成功", foreground="green")
        
        except Exception as e:
            messagebox.showerror("错误", f"导出报告失败: {e}")


# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.title("WiFi 6/6E 分析器测试")
    root.geometry("1200x800")
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    tab = WiFi6AnalyzerTab(notebook)
    
    root.mainloop()
