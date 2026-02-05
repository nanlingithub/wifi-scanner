"""
安全检测标签页
功能：开放网络检测、弱加密扫描、优化建议生成
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from .theme import ModernTheme, ModernButton


class SecurityTab:
    """安全检测标签页"""
    
    def __init__(self, parent, wifi_analyzer):
        self.parent = parent
        self.wifi_analyzer = wifi_analyzer
        self.frame = ttk.Frame(parent)
        
        self.scan_results = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 顶部控制栏
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        ModernButton(control_frame, text="🔍 安全扫描", 
                    command=self._security_scan, style='danger').pack(side='left', padx=5)
        
        ModernButton(control_frame, text="💡 优化建议", 
                    command=self._show_suggestions, style='success').pack(side='left', padx=5)
        
        ModernButton(control_frame, text="📋 生成报告", 
                    command=self._generate_report, style='primary').pack(side='left', padx=5)
        
        # 主内容区 - 四个类别
        notebook = ttk.Notebook(self.frame)
        notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 1. 开放网络
        open_frame = ttk.Frame(notebook)
        notebook.add(open_frame, text="🔓 开放网络")
        
        self.open_tree = self._create_result_tree(open_frame, 
                                                   ["SSID", "BSSID", "信号", "信道", "风险等级"])
        
        # 2. 弱加密
        weak_frame = ttk.Frame(notebook)
        notebook.add(weak_frame, text="🔐 弱加密")
        
        self.weak_tree = self._create_result_tree(weak_frame,
                                                   ["SSID", "BSSID", "加密方式", "信号", "风险等级"])
        
        # 3. 可疑AP
        suspicious_frame = ttk.Frame(notebook)
        notebook.add(suspicious_frame, text="⚠️ 可疑AP")
        
        self.suspicious_tree = self._create_result_tree(suspicious_frame,
                                                         ["SSID", "BSSID", "原因", "信号"])
        
        # 4. 优化建议
        suggestions_frame = ttk.Frame(notebook)
        notebook.add(suggestions_frame, text="💡 优化建议")
        
        self.suggestions_text = scrolledtext.ScrolledText(suggestions_frame, 
                                                          font=('Microsoft YaHei', 10),
                                                          padx=10, pady=10)
        self.suggestions_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 统计面板
        stats_frame = ttk.LabelFrame(self.frame, text="📊 扫描统计", padding=10)
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="未进行扫描",
                                    font=('Microsoft YaHei', 9))
        self.stats_label.pack()
    
    def _create_result_tree(self, parent, columns):
        """创建结果树形视图"""
        tree = ttk.Treeview(parent, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            width = 150 if col == "SSID" else 140 if col == "BSSID" else 100
            tree.column(col, width=width, anchor='center' if col != 'SSID' else 'w')
        
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')
        
        return tree
    
    def _security_scan(self):
        """执行安全扫描"""
        try:
            # 清空之前的结果
            for tree in [self.open_tree, self.weak_tree, self.suspicious_tree]:
                tree.delete(*tree.get_children())
            
            # 扫描网络
            networks = self.wifi_analyzer.scan_wifi_networks(force_refresh=True)
            
            # 分析结果
            open_networks = []
            weak_encryption = []
            suspicious_aps = []
            
            for network in networks:
                ssid = network.get('ssid', 'N/A')
                bssid = network.get('bssid', 'N/A')
                auth = network.get('authentication', 'N/A')
                signal = network.get('signal', -100)
                signal_percent = network.get('signal_percent', 0)
                
                # 检测开放网络
                if auth.lower() in ['open', '开放']:
                    risk = "高" if signal_percent > 50 else "中"
                    open_networks.append((ssid, bssid, f"{signal}dBm", 
                                        network.get('channel', 'N/A'), risk))
                
                # 检测弱加密
                elif 'wep' in auth.lower():
                    weak_encryption.append((ssid, bssid, auth, f"{signal}dBm", "高"))
                elif 'wpa' in auth.lower() and 'wpa2' not in auth.lower() and 'wpa3' not in auth.lower():
                    weak_encryption.append((ssid, bssid, auth, f"{signal}dBm", "中"))
                
                # 检测可疑AP（默认SSID、隐藏SSID等）
                if ssid.lower() in ['tp-link', 'netgear', 'linksys', 'default', 'wireless']:
                    suspicious_aps.append((ssid, bssid, "使用默认SSID", f"{signal}dBm"))
                elif ssid == '':
                    suspicious_aps.append((ssid, bssid, "隐藏SSID", f"{signal}dBm"))
            
            # 显示结果
            for data in open_networks:
                self.open_tree.insert('', 'end', values=data)
            
            for data in weak_encryption:
                self.weak_tree.insert('', 'end', values=data)
            
            for data in suspicious_aps:
                self.suspicious_tree.insert('', 'end', values=data)
            
            # 更新统计
            stats = f"扫描完成: 发现 {len(networks)} 个网络 | "
            stats += f"开放网络: {len(open_networks)} | "
            stats += f"弱加密: {len(weak_encryption)} | "
            stats += f"可疑AP: {len(suspicious_aps)}"
            
            self.stats_label.config(text=stats)
            
            # 保存结果
            self.scan_results = {
                'total': len(networks),
                'open': open_networks,
                'weak': weak_encryption,
                'suspicious': suspicious_aps
            }
            
            # 自动生成建议
            self._generate_suggestions()
            
            messagebox.showinfo("完成", "安全扫描完成")
            
        except Exception as e:
            messagebox.showerror("错误", f"扫描失败: {str(e)}")
    
    def _generate_suggestions(self):
        """生成优化建议"""
        if not self.scan_results:
            return
        
        suggestions = "=== WiFi安全与优化建议 ===\n\n"
        
        # 安全建议
        suggestions += "【安全建议】\n\n"
        
        if self.scan_results['open']:
            suggestions += f"1. 发现 {len(self.scan_results['open'])} 个开放网络\n"
            suggestions += "   • 避免连接开放网络，数据可能被窃听\n"
            suggestions += "   • 如果是您的网络，请立即设置WPA2/WPA3加密\n\n"
        
        if self.scan_results['weak']:
            suggestions += f"2. 发现 {len(self.scan_results['weak'])} 个弱加密网络\n"
            suggestions += "   • WEP加密已过时，极易被破解\n"
            suggestions += "   • WPA加密存在安全漏洞\n"
            suggestions += "   • 建议升级到WPA2-PSK(AES)或WPA3\n\n"
        
        if self.scan_results['suspicious']:
            suggestions += f"3. 发现 {len(self.scan_results['suspicious'])} 个可疑AP\n"
            suggestions += "   • 使用默认SSID可能是新安装路由器\n"
            suggestions += "   • 隐藏SSID并不能真正提高安全性\n"
            suggestions += "   • 建议修改为自定义SSID\n\n"
        
        # 优化建议
        suggestions += "\n【性能优化建议】\n\n"
        
        suggestions += "1. 路由器设置优化\n"
        suggestions += "   • 启用WPA2-PSK(AES)或WPA3加密\n"
        suggestions += "   • 设置强密码（至少12位，包含大小写字母、数字、符号）\n"
        suggestions += "   • 修改默认管理员密码\n"
        suggestions += "   • 定期更新路由器固件\n\n"
        
        suggestions += "2. 信道优化\n"
        suggestions += "   • 2.4GHz建议使用信道1、6、11（互不干扰）\n"
        suggestions += "   • 5GHz优先使用DFS信道（较少干扰）\n"
        suggestions += "   • 启用自动信道选择功能\n\n"
        
        suggestions += "3. 设备管理\n"
        suggestions += "   • 启用MAC地址过滤（可选）\n"
        suggestions += "   • 禁用WPS功能（存在安全漏洞）\n"
        suggestions += "   • 启用访客网络隔离\n"
        suggestions += "   • 定期检查连接设备列表\n\n"
        
        suggestions += "4. 覆盖优化\n"
        suggestions += "   • 路由器放置在居中位置\n"
        suggestions += "   • 避免金属物体和电器干扰\n"
        suggestions += "   • 大户型考虑使用Mesh组网\n"
        suggestions += "   • 调整天线方向以优化覆盖\n\n"
        
        suggestions += "5. QoS设置\n"
        suggestions += "   • 为视频会议、游戏等分配优先级\n"
        suggestions += "   • 限制BT下载等占用带宽的应用\n"
        suggestions += "   • 启用流量控制避免拥塞\n"
        
        self.suggestions_text.delete('1.0', 'end')
        self.suggestions_text.insert('1.0', suggestions)
    
    def _show_suggestions(self):
        """显示建议"""
        if not self.scan_results:
            messagebox.showwarning("提示", "请先执行安全扫描")
            return
        
        self._generate_suggestions()
        messagebox.showinfo("提示", "优化建议已生成，请查看'优化建议'标签页")
    
    def _generate_report(self):
        """生成报告"""
        if not self.scan_results:
            messagebox.showwarning("提示", "请先执行安全扫描")
            return
        
        from datetime import datetime
        
        report = f"""WiFi安全扫描报告
生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}

=== 扫描概况 ===
扫描网络总数: {self.scan_results['total']}
开放网络: {len(self.scan_results['open'])}
弱加密网络: {len(self.scan_results['weak'])}
可疑AP: {len(self.scan_results['suspicious'])}

=== 详细信息 ===

【开放网络】
"""
        
        for ssid, bssid, signal, channel, risk in self.scan_results['open']:
            report += f"  • {ssid} ({bssid})\n"
            report += f"    信号: {signal}, 信道: {channel}, 风险: {risk}\n"
        
        report += "\n【弱加密网络】\n"
        for ssid, bssid, auth, signal, risk in self.scan_results['weak']:
            report += f"  • {ssid} ({bssid})\n"
            report += f"    加密: {auth}, 信号: {signal}, 风险: {risk}\n"
        
        report += "\n【可疑AP】\n"
        for ssid, bssid, reason, signal in self.scan_results['suspicious']:
            report += f"  • {ssid or '(隐藏)'} ({bssid})\n"
            report += f"    原因: {reason}, 信号: {signal}\n"
        
        report += "\n" + "="*50 + "\n"
        report += self.suggestions_text.get('1.0', 'end')
        
        # 显示报告窗口
        report_window = tk.Toplevel(self.frame)
        report_window.title("WiFi安全扫描报告")
        report_window.geometry("700x600")
        
        text = scrolledtext.ScrolledText(report_window, font=('Microsoft YaHei', 9),
                                        padx=10, pady=10)
        text.pack(fill='both', expand=True)
        text.insert('1.0', report)
        text.config(state='disabled')
        
        # 保存按钮
        def save_report():
            from tkinter import filedialog
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                initialfile=f"wifi_security_report_{timestamp}.txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                messagebox.showinfo("成功", "报告已保存")
        
        btn_frame = ttk.Frame(report_window)
        btn_frame.pack(pady=10)
        ModernButton(btn_frame, text="💾 保存报告", command=save_report, style='primary').pack()
    
    def get_frame(self):
        """获取框架"""
        return self.frame
