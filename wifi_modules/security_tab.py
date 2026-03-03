"""
WiFi安全检测标签页（专业版）
功能：WPS漏洞、Evil Twin、密码强度、风险评分、DNS劫持检测
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import threading

from .theme import ModernTheme, ModernButton, ModernCard, StatusBadge, create_section_title
from .security import (
    VulnerabilityDetector,
    PasswordStrengthAnalyzer,
    SecurityScoreCalculator,
    DNSHijackDetector
)


class SecurityTab:
    """安全检测标签页（专业版）"""
    
    def __init__(self, parent, wifi_analyzer):
        self.parent = parent
        self.wifi_analyzer = wifi_analyzer
        self.frame = ttk.Frame(parent)
        
        # 初始化专业检测模块
        self.vulnerability_detector = VulnerabilityDetector()
        self.password_analyzer = PasswordStrengthAnalyzer()
        self.score_calculator = SecurityScoreCalculator()
        self.dns_detector = DNSHijackDetector()
        
        self.scan_results = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 顶部控制栏
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        ModernButton(control_frame, text="🔍 安全扫描", 
                    command=self._security_scan, style='danger').pack(side='left', padx=5)
        
        ModernButton(control_frame, text="🔐 WPS检测", 
                    command=self._wps_scan, style='warning').pack(side='left', padx=5)
        
        ModernButton(control_frame, text="🔍 DNS扫描", 
                    command=self._dns_check, style='info').pack(side='left', padx=5)
        
        ModernButton(control_frame, text="🧮 计算评分", 
                    command=self._show_risk_score, style='primary').pack(side='left', padx=5)
        
        ModernButton(control_frame, text="📋 生成报告", 
                    command=self._generate_report, style='success').pack(side='left', padx=5)
        
        # 主内容区 - 标签页
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
        
        # 3. WPS漏洞
        wps_frame = ttk.Frame(notebook)
        notebook.add(wps_frame, text="⚡ WPS漏洞")
        self.wps_tree = self._create_result_tree(wps_frame,
                                                  ["SSID", "BSSID", "漏洞类型", "严重程度", "破解时间"])
        
        # 4. Evil Twin
        evil_frame = ttk.Frame(notebook)
        notebook.add(evil_frame, text="👿 钓鱼热点")
        self.evil_tree = self._create_result_tree(evil_frame,
                                                   ["SSID", "BSSID", "可疑原因", "置信度", "建议"])
        
        # 5. SSID欺骗
        spoof_frame = ttk.Frame(notebook)
        notebook.add(spoof_frame, text="🎭 SSID欺骗")
        self.spoof_tree = self._create_result_tree(spoof_frame,
                                                    ["SSID1", "SSID2", "相似度", "警告", "严重度"])
        
        # 6. PMF检测（新增）
        pmf_frame = ttk.Frame(notebook)
        notebook.add(pmf_frame, text="🛡️ PMF防护")
        self.pmf_tree = self._create_result_tree(pmf_frame,
                                                  ["SSID", "BSSID", "PMF状态", "风险等级", "建议"])
        
        # 7. KRACK漏洞（新增）
        krack_frame = ttk.Frame(notebook)
        notebook.add(krack_frame, text="🔴 KRACK")
        self.krack_tree = self._create_result_tree(krack_frame,
                                                    ["SSID", "BSSID", "CVE数量", "CVSS评分", "状态"])
        
        # 8. 风险评分
        score_frame = ttk.Frame(notebook)
        notebook.add(score_frame, text="📊 风险评分")
        self.score_text = scrolledtext.ScrolledText(score_frame, 
                                                     font=('Microsoft YaHei', 10),
                                                     padx=10, pady=10)
        self.score_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 9. DNS检测
        dns_frame = ttk.Frame(notebook)
        notebook.add(dns_frame, text="🌐 DNS检测")
        self.dns_text = scrolledtext.ScrolledText(dns_frame, 
                                                   font=('Microsoft YaHei', 10),
                                                   padx=10, pady=10)
        self.dns_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 统计面板
        stats_frame = ttk.LabelFrame(self.frame, text="📊 扫描统计", padding=10)
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="未进行扫描",
                                    font=('Microsoft YaHei', 9))
        self.stats_label.pack()
    
    def _create_result_tree(self, parent, columns):
        """创建结果树形视图"""
        tree = ttk.Treeview(parent, columns=columns, show='headings', height=12)
        
        for col in columns:
            tree.heading(col, text=col)
            width = 150 if "SSID" in col else 140 if "BSSID" in col else 100
            tree.column(col, width=width, anchor='center' if 'SSID' not in col else 'w')
        
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')
        
        return tree
    
    def _security_scan(self):
        """执行全面安全扫描 - 异步版本"""
        # 禁用按钮防止重复点击
        for child in self.frame.winfo_children():
            if isinstance(child, ttk.Frame):
                for btn in child.winfo_children():
                    if isinstance(btn, (ttk.Button, tk.Button)):
                        try:
                            btn.config(state='disabled')
                        except:
                            pass
        
        # 显示进度提示
        self.stats_label.config(text="⏳ 正在扫描中，请稍候...")
        
        def scan_worker():
            try:
                self._security_scan_worker()
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("错误", f"扫描失败: {str(e)}"))
            finally:
                # 恢复按钮状态
                def restore_buttons():
                    for child in self.frame.winfo_children():
                        if isinstance(child, ttk.Frame):
                            for btn in child.winfo_children():
                                if isinstance(btn, (ttk.Button, tk.Button)):
                                    try:
                                        btn.config(state='normal')
                                    except:
                                        pass
                self.frame.after(0, restore_buttons)
        
        # 使用守护线程执行扫描
        threading.Thread(target=scan_worker, daemon=True).start()
    
    def _security_scan_worker(self):
        """安全扫描工作线程"""
        # ✅ P0修复: 仅通过 after() 在主线程中清空Tree，不在工作线程中直接操作tkinter控件
        self.frame.after(0, self._clear_all_trees)
        try:
            # 扫描网络
            networks = self.wifi_analyzer.scan_wifi_networks(force_refresh=True)
            
            # 分析结果
            open_networks = []
            weak_encryption = []
            wps_vulnerabilities = []
            pmf_issues = []  # 新增：PMF防护问题
            krack_vulnerabilities = []  # 新增：KRACK漏洞
            
            for network in networks:
                ssid = network.get('ssid', 'N/A')
                bssid = network.get('bssid', 'N/A')
                auth = network.get('authentication', 'N/A')
                
                # 修复：从signal_percent获取信号强度并转换为dBm
                signal_percent = network.get('signal_percent', 0)
                # 修复：确保signal_percent是整数类型（增强安全性）
                try:
                    if isinstance(signal_percent, str):
                        if signal_percent == '未知' or not signal_percent:
                            signal_percent = 0
                        else:
                            signal_percent = int(signal_percent.rstrip('%'))
                    elif not isinstance(signal_percent, (int, float)):
                        signal_percent = 0
                except (ValueError, AttributeError) as e:
                    signal_percent = 0  # 转换失败时默认为0
                
                # 将百分比转换为dBm（公式：dBm ≈ (percent / 2) - 100）
                if signal_percent > 0:
                    signal_dbm = int((signal_percent / 2) - 100)
                else:
                    signal_dbm = -100
                
                channel = network.get('channel', 'N/A')
                
                # 1. 检测开放网络
                if auth.lower() in ['open', '开放']:
                    risk = "高" if signal_percent > 50 else "中"
                    open_networks.append((ssid, bssid, f"{signal_dbm}dBm", channel, risk))
                
                # 2. 加密详细分析（增强：包含PMF和KRACK检测）
                enc_analysis = self.vulnerability_detector.analyze_encryption_detail(network)
                
                # 2.1 PMF检测
                pmf_result = self.vulnerability_detector.check_pmf_support(network)
                
                # 2.2 KRACK漏洞检测
                krack_result = self.vulnerability_detector.check_krack_vulnerability_detailed(network)
                
                # 收集PMF问题网络
                if pmf_result['risk_level'] in ['MEDIUM', 'HIGH', 'CRITICAL']:
                    pmf_status = "强制" if pmf_result['pmf_required'] else "可选" if pmf_result['pmf_capable'] else "不支持"
                    risk_emoji = {
                        'LOW': '✅',
                        'MEDIUM': '🟡',
                        'HIGH': '🟠',
                        'CRITICAL': '🔴'
                    }.get(pmf_result['risk_level'], '⚪')
                    
                    recommendation = "启用PMF" if not pmf_result['pmf_capable'] else "已启用PMF" if pmf_result['pmf_required'] else "建议启用PMF"
                    pmf_issues.append((
                        ssid, bssid, pmf_status,
                        f"{risk_emoji} {pmf_result['risk_level']}",
                        recommendation
                    ))
                
                # 收集KRACK漏洞网络
                if krack_result['vulnerable']:
                    cve_count = len(krack_result['cve_list'])
                    cvss_score = krack_result['cvss_score']
                    status = "🔴 脆弱" if cvss_score >= 8.0 else "🟡 中危"
                    krack_vulnerabilities.append((
                        ssid, bssid,
                        f"{cve_count}个CVE",
                        f"{cvss_score} (CRITICAL)",
                        status
                    ))
                
                # 合并安全评估
                combined_risk = "低"
                if enc_analysis['security_level'] < 70:
                    combined_risk = "高" if enc_analysis['security_level'] < 40 else "中"
                
                # 提升KRACK漏洞网络的风险等级
                if krack_result['vulnerable']:
                    combined_risk = "高"
                
                # 提升未启用PMF的WPA2网络风险等级
                if pmf_result['risk_level'] in ['HIGH', 'CRITICAL']:
                    if combined_risk == "低":
                        combined_risk = "中"
                
                # 添加到弱加密列表（显示综合风险）
                # WPA2-Enterprise 的 KRACK severity=HIGH 不计入「弱加密」；
                # 只有 severity=CRITICAL（WPA2-PSK）才触发弱加密标记。
                krack_critical = krack_result.get('vulnerable') and krack_result.get('severity') == 'CRITICAL'
                if enc_analysis['security_level'] < 70 or krack_critical or pmf_result['risk_level'] in ['HIGH', 'CRITICAL']:
                    # 构建风险原因
                    risk_reasons = []
                    if enc_analysis['security_level'] < 40:
                        risk_reasons.append("弱加密")
                    if krack_critical:
                        risk_reasons.append("KRACK")
                    if pmf_result['risk_level'] == 'CRITICAL':
                        risk_reasons.append("无PMF")
                    
                    risk_detail = f"{combined_risk}({','.join(risk_reasons)})" if risk_reasons else combined_risk
                    weak_encryption.append((ssid, bssid, auth, f"{signal_dbm}dBm", risk_detail))
                
                # 3. WPS漏洞检测
                wps_result = self.vulnerability_detector.check_wps_vulnerability(network)
                if wps_result['vulnerable']:
                    wps_vulnerabilities.append((
                        ssid, bssid,
                        wps_result['vulnerability_type'],
                        wps_result['severity'],
                        wps_result['exploit_time']
                    ))
            
            # 4. Evil Twin检测
            evil_twins = self.vulnerability_detector.detect_evil_twin(networks)
            
            # 5. SSID欺骗检测
            ssid_spoofing = self.vulnerability_detector.detect_ssid_spoofing(networks)
            
            # 6. DNS增强检测
            dns_result = None
            try:
                dns_result = self.dns_detector.check_dns_hijacking()
                # 同时更新DNS标签页
                self._update_dns_display(dns_result)
            except Exception as e:
                print(f"DNS检测失败: {e}")
            
            # 7. 风险评分计算
            risk_score_result = None
            try:
                risk_score_result = self._calculate_risk_scores(networks, weak_encryption, wps_vulnerabilities)
            except Exception as e:
                print(f"风险评分失败: {e}")
            
            # 显示结果（使用after确保在主线程更新UI）
            def update_ui():
                for data in open_networks:
                    self.open_tree.insert('', 'end', values=data)
                
                for data in weak_encryption:
                    self.weak_tree.insert('', 'end', values=data)
                
                for data in wps_vulnerabilities:
                    self.wps_tree.insert('', 'end', values=data)
                
                # 新增：显示PMF检测结果
                for data in pmf_issues:
                    self.pmf_tree.insert('', 'end', values=data)
                
                # 新增：显示KRACK检测结果
                for data in krack_vulnerabilities:
                    self.krack_tree.insert('', 'end', values=data)
                
                for evil in evil_twins:
                    self.evil_tree.insert('', 'end', values=(
                        evil['ssid'], evil['bssid'],
                        ', '.join(evil['reasons'][:2]),  # 前2个原因
                        f"{evil['confidence']}%",
                        evil['recommendation'][:20] + '...'
                    ))
                
                for spoof in ssid_spoofing:
                    self.spoof_tree.insert('', 'end', values=(
                        spoof['ssid1'], spoof['ssid2'],
                        f"{spoof['similarity']}%",
                        spoof['warning'][:30] + '...',
                        spoof['severity']
                    ))
                
                # 更新统计
                stats = f"扫描完成: {len(networks)}个网络 | "
                stats += f"开放: {len(open_networks)} | "
                stats += f"弱加密: {len(weak_encryption)} | "
                stats += f"WPS漏洞: {len(wps_vulnerabilities)} | "
                stats += f"PMF问题: {len(pmf_issues)} | "
                stats += f"KRACK: {len(krack_vulnerabilities)} | "
                stats += f"Evil Twin: {len(evil_twins)} | "
                stats += f"SSID欺骗: {len(ssid_spoofing)}"
                
                self.stats_label.config(text=stats)
                
                # 保存结果
                self.scan_results = {
                    'total': len(networks),
                    'networks': networks,
                    'open': open_networks,
                    'weak': weak_encryption,
                    'wps': wps_vulnerabilities,
                    'pmf': pmf_issues,  # 新增
                    'krack': krack_vulnerabilities,  # 新增
                    'evil_twin': evil_twins,
                    'ssid_spoof': ssid_spoofing,
                    'dns': dns_result,
                    'risk_score': risk_score_result
                }
                
                # 生成扫描摘要
                dns_status = "正常"
                if dns_result and dns_result.get('hijacked'):
                    dns_status = f"⚠️检测到{len(dns_result.get('hijacked_domains', []))}个异常"
                
                # 风险评分摘要
                risk_summary = "未评分"
                if risk_score_result and risk_score_result.get('env_score'):
                    env_score = risk_score_result['env_score']
                    risk_summary = f"{env_score['rating_emoji']} {env_score['score']}/100 ({env_score['rating']})"
                
                messagebox.showinfo("完成", 
                                  f"安全扫描完成\n"
                                  f"发现 {len(wps_vulnerabilities)} 个WPS漏洞\n"
                                  f"发现 {len(krack_vulnerabilities)} 个KRACK漏洞\n"
                                  f"发现 {len(pmf_issues)} 个PMF防护问题\n"
                                  f"发现 {len(evil_twins)} 个可疑Evil Twin\n"
                                  f"DNS状态: {dns_status}\n"
                                  f"环境风险: {risk_summary}")
            
            self.frame.after(0, update_ui)

            
        except Exception as e:
            def show_error():
                messagebox.showerror("错误", f"扫描失败: {str(e)}")
            self.frame.after(0, show_error)
    
    def _clear_all_trees(self):
        """清空所有树形控件"""
        for tree in [self.open_tree, self.weak_tree, self.wps_tree, 
                    self.evil_tree, self.spoof_tree, self.pmf_tree, self.krack_tree]:
            tree.delete(*tree.get_children())
    
    def _wps_scan(self):
        """WPS专项扫描 - 异步版本"""
        # 禁用按钮防止重复点击
        for child in self.frame.winfo_children():
            if isinstance(child, ttk.Frame):
                for btn in child.winfo_children():
                    if isinstance(btn, (ttk.Button, tk.Button)):
                        try:
                            btn.config(state='disabled')
                        except:
                            pass
        
        # 显示进度提示
        self.stats_label.config(text="⏳ 正在扫描WPS漏洞，请稍候...")
        
        def scan_worker():
            try:
                self._wps_scan_worker()
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("错误", f"WPS扫描失败: {str(e)}"))
            finally:
                # 恢复按钮状态
                def restore_buttons():
                    for child in self.frame.winfo_children():
                        if isinstance(child, ttk.Frame):
                            for btn in child.winfo_children():
                                if isinstance(btn, (ttk.Button, tk.Button)):
                                    try:
                                        btn.config(state='normal')
                                    except:
                                        pass
                self.frame.after(0, restore_buttons)
        
        # 使用守护线程执行扫描
        threading.Thread(target=scan_worker, daemon=True).start()
    
    def _wps_scan_worker(self):
        """WPS扫描工作线程"""
        try:
            networks = self.wifi_analyzer.scan_wifi_networks(force_refresh=True)
            
            wps_count = 0
            vulnerable_count = 0
            results = []
            
            for network in networks:
                wps_result = self.vulnerability_detector.check_wps_vulnerability(network)
                
                if wps_result['wps_enabled']:
                    wps_count += 1
                    
                    if wps_result['vulnerable']:
                        vulnerable_count += 1
                        results.append((
                            network.get('ssid', 'N/A'),
                            network.get('bssid', 'N/A'),
                            wps_result['vulnerability_type'],
                            wps_result['severity'],
                            wps_result['exploit_time']
                        ))
            
            # 使用after在主线程更新UI
            def update_ui():
                self.wps_tree.delete(*self.wps_tree.get_children())
                for data in results:
                    self.wps_tree.insert('', 'end', values=data)
                
                messagebox.showinfo("WPS扫描完成", 
                                  f"检测到 {wps_count} 个启用WPS的网络\n"
                                  f"其中 {vulnerable_count} 个存在已知漏洞")
            
            self.frame.after(0, update_ui)
            
        except Exception as e:
            def show_error():
                messagebox.showerror("错误", f"WPS扫描失败: {str(e)}")
            self.frame.after(0, show_error)
    
    def _dns_check(self):
        """DNS劫持检测"""
        try:
            self.dns_text.delete('1.0', 'end')
            self.dns_text.insert('1.0', "正在检测DNS劫持...\n\n")
            self.dns_text.update()
            
            # DNS劫持检测
            dns_result = self.dns_detector.check_dns_hijacking()
            
            # 更新显示
            self._update_dns_display(dns_result)
            
        except Exception as e:
            self.dns_text.insert('end', f"\n\n错误: {str(e)}")
    
    def _update_dns_display(self, dns_result):
        """更新DNS检测显示"""
        if not dns_result:
            return
        
        try:
            report = "=== DNS劫持检测报告 ===\n\n"
            
            report += f"【当前DNS服务器】\n"
            if dns_result.get('current_dns'):
                for dns in dns_result['current_dns']:
                    report += f"  • {dns}\n"
            else:
                report += "  未检测到\n"
            
            report += f"\n【检测结果】\n"
            if dns_result.get('hijacked'):
                report += "⚠️ 检测到DNS可能被劫持！\n\n"
                hijacked_domains = dns_result.get('hijacked_domains', [])
                if hijacked_domains:
                    report += f"可疑域名: {', '.join(hijacked_domains)}\n\n"
            else:
                report += "✅ DNS查询正常，未检测到劫持\n\n"
            
            report += "【详细测试】\n"
            for test in dns_result.get('test_results', []):
                report += f"\n域名: {test.get('domain', 'N/A')}\n"
                report += f"  当前解析: {test.get('current_ip', 'N/A')}\n"
                if test.get('trusted_ips'):
                    report += f"  可信解析: {', '.join(test['trusted_ips'].values())}\n"
                if test.get('suspicious'):
                    report += f"  ⚠️ {test.get('reason', '')}\n"
                else:
                    report += f"  ✅ 正常\n"
            
            report += "\n【建议】\n"
            for rec in dns_result.get('recommendations', []):
                report += f"{rec}\n"
            
            self.dns_text.delete('1.0', 'end')
            self.dns_text.insert('1.0', report)
            
        except Exception as e:
            print(f"更新DNS显示失败: {e}")
    
    def _calculate_risk_scores(self, networks, weak_encryption, wps_vulnerabilities):
        """计算风险评分并更新显示"""
        try:
            # 1. 环境整体评分
            env_score = self.score_calculator.calculate_environment_score(networks)
            
            # 2. 个别网络评分（前5个）
            network_scores = []
            for network in networks[:5]:
                # 加密分析
                enc_analysis = self.vulnerability_detector.analyze_encryption_detail(network)
                # WPS检测
                wps_result = self.vulnerability_detector.check_wps_vulnerability(network)
                # 计算评分
                score_result = self.score_calculator.calculate_network_score(
                    network, enc_analysis, wps_result
                )
                network_scores.append({
                    'network': network,
                    'score': score_result
                })
            
            # 保存结果
            result = {
                'env_score': env_score,
                'network_scores': network_scores,
                'total_networks': len(networks),
                'weak_count': len(weak_encryption),
                'wps_count': len(wps_vulnerabilities)
            }
            
            # 更新显示
            self._update_risk_score_display(result)
            
            return result
            
        except Exception as e:
            print(f"计算风险评分失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _update_risk_score_display(self, risk_result):
        """更新风险评分显示"""
        if not risk_result:
            return
        
        try:
            self.score_text.delete('1.0', 'end')
            
            report = "=== WiFi安全风险评分报告 ==="
            
            # 环境整体评分
            env_score = risk_result['env_score']
            report += "\n\n【环境整体评分】\n"
            report += f"评分: {env_score['rating_emoji']} {env_score['score']}/100 - {env_score['rating']}\n"
            report += f"检测到 {env_score['total_networks']} 个网络\n"
            if env_score.get('issues'):
                report += "问题:\n"
                for issue in env_score['issues']:
                    report += f"  • {issue}\n"
            
            # 个别网络评分
            report += "\n【个别网络评分】（前5个）\n\n"
            
            for i, item in enumerate(risk_result['network_scores']):
                network = item['network']
                score_result = item['score']
                ssid = network.get('ssid', 'N/A')
                
                report += f"{i+1}. {ssid}\n"
                report += f"   总分: {score_result['rating_emoji']} {score_result['total_score']}/100 ({score_result['rating']})\n"
                report += f"   等级: {score_result['security_level']}\n"
                
                report += f"   分项评分:\n"
                for category, score in score_result['category_scores'].items():
                    report += f"     • {category}: {score}/100\n"
                
                if score_result.get('risks'):
                    report += f"   风险:\n"
                    for risk in score_result['risks'][:2]:  # 前2个风险
                        report += f"     ⚠️ {risk['type']} ({risk['severity']})\n"
                
                if score_result.get('priority_actions'):
                    report += f"   优先行动:\n"
                    for action in score_result['priority_actions'][:2]:
                        report += f"     {action}\n"
                
                report += "\n"
            
            self.score_text.insert('1.0', report)
            
        except Exception as e:
            print(f"更新风险评分显示失败: {e}")
    
    def _show_risk_score(self):
        """显示风险评分"""
        if not self.scan_results.get('networks'):
            messagebox.showwarning("提示", "请先执行安全扫描")
            return
        
        # 如果已有评分结果，直接显示
        if self.scan_results.get('risk_score'):
            self._update_risk_score_display(self.scan_results['risk_score'])
            return
        
        try:
            self.score_text.delete('1.0', 'end')
            
            report = "=== WiFi安全风险评分报告 ===\n\n"
            
            # 1. 环境整体评分
            env_score = self.score_calculator.calculate_environment_score(
                self.scan_results['networks']
            )
            
            report += f"【环境整体评分】\n"
            report += f"评分: {env_score['score']}/100 - {env_score['rating']}\n"
            report += f"检测到 {env_score['total_networks']} 个网络\n"
            if env_score['issues']:
                report += "问题:\n"
                for issue in env_score['issues']:
                    report += f"  • {issue}\n"
            
            # 2. 个别网络评分（前5个）
            report += "\n【个别网络评分】（前5个）\n\n"
            
            for i, network in enumerate(self.scan_results['networks'][:5]):
                ssid = network.get('ssid', 'N/A')
                
                # 加密分析
                enc_analysis = self.vulnerability_detector.analyze_encryption_detail(network)
                
                # WPS检测
                wps_result = self.vulnerability_detector.check_wps_vulnerability(network)
                
                # 计算评分
                score_result = self.score_calculator.calculate_network_score(
                    network, enc_analysis, wps_result
                )
                
                report += f"{i+1}. {ssid}\n"
                report += f"   总分: {score_result['rating_emoji']} {score_result['total_score']}/100 ({score_result['rating']})\n"
                report += f"   等级: {score_result['security_level']}\n"
                
                report += f"   分项评分:\n"
                for category, score in score_result['category_scores'].items():
                    report += f"     • {category}: {score}/100\n"
                
                if score_result['risks']:
                    report += f"   风险:\n"
                    for risk in score_result['risks'][:2]:  # 前2个风险
                        report += f"     ⚠️ {risk['type']} ({risk['severity']})\n"
                
                if score_result['priority_actions']:
                    report += f"   优先行动:\n"
                    for action in score_result['priority_actions'][:2]:
                        report += f"     {action}\n"
                
                report += "\n"
            
            self.score_text.insert('1.0', report)
            
        except Exception as e:
            messagebox.showerror("错误", f"评分失败: {str(e)}")
    
    def _generate_report(self):
        """生成专业报告"""
        if not self.scan_results:
            messagebox.showwarning("提示", "请先执行安全扫描")
            return
        
        try:
            # ✅ P0修复: 报告中补充 KRACK 和 PMF 检测结果
            report = f"""WiFi安全扫描专业报告
生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
扫描工具: WiFi专业工具 v2.0

{'='*60}
【扫描概况】
{'='*60}
扫描网络总数: {self.scan_results['total']}
开放网络: {len(self.scan_results['open'])}
弱加密网络: {len(self.scan_results['weak'])}
WPS漏洞网络: {len(self.scan_results['wps'])}
KRACK漏洞网络: {len(self.scan_results.get('krack', []))}
PMF防护问题: {len(self.scan_results.get('pmf', []))}
可疑Evil Twin: {len(self.scan_results['evil_twin'])}
SSID欺骗: {len(self.scan_results['ssid_spoof'])}

{'='*60}
【严重威胁】
{'='*60}

"""
            
            # KRACK漏洞（CVE-2017-13077族）
            if self.scan_results.get('krack'):
                report += "🔴 KRACK漏洞（CVE-2017-13077族）:\n"
                for ssid, bssid, cve_count, cvss, status in self.scan_results['krack']:
                    report += f"  • {ssid} ({bssid})\n"
                    report += f"    CVE数量: {cve_count}, CVSS评分: {cvss}\n"
                    report += f"    状态: {status}\n"
                    report += f"    建议: 更新路由器固件或升级到WPA3-SAE\n\n"

            # PMF防护问题
            if self.scan_results.get('pmf'):
                report += "🟠 PMF管理帧防护问题（802.11w）:\n"
                for ssid, bssid, pmf_status, risk_level, recommendation in self.scan_results['pmf']:
                    report += f"  • {ssid} ({bssid})\n"
                    report += f"    PMF状态: {pmf_status}, 风险等级: {risk_level}\n"
                    report += f"    建议: {recommendation}\n\n"

            # WPS漏洞
            if self.scan_results['wps']:
                report += "⚠️ WPS漏洞（CRITICAL）:\n"
                for ssid, bssid, vuln_type, severity, exploit_time in self.scan_results['wps']:
                    report += f"  • {ssid} ({bssid})\n"
                    report += f"    漏洞类型: {vuln_type}\n"
                    report += f"    严重程度: {severity}\n"
                    report += f"    破解时间: {exploit_time}\n\n"
            
            # Evil Twin
            if self.scan_results['evil_twin']:
                report += "👿 可疑Evil Twin:\n"
                for evil in self.scan_results['evil_twin']:
                    report += f"  • {evil['ssid']} ({evil['bssid']})\n"
                    report += f"    置信度: {evil['confidence']}%\n"
                    report += f"    原因: {', '.join(evil['reasons'])}\n"
                    report += f"    建议: {evil['recommendation']}\n\n"
            
            # 开放网络
            if self.scan_results['open']:
                report += "🔓 开放网络:\n"
                for ssid, bssid, signal, channel, risk in self.scan_results['open']:
                    report += f"  • {ssid} ({bssid})\n"
                    report += f"    信号: {signal}, 信道: {channel}, 风险: {risk}\n\n"
            
            report += f"\n{'='*60}\n【专业建议】\n{'='*60}\n\n"
            
            # 生成建议
            step = 1
            if self.scan_results.get('krack'):
                report += f"{step}. KRACK漏洞修复（优先级: 最高）\n"
                report += "   • 立即更新路由器固件（KRACK补丁）\n"
                report += "   • 更新所有WiFi客户端设备驱动程序\n"
                report += "   • 升级到WPA3-SAE（根本解决方案）\n"
                report += "   • 临时措施：使用VPN加密所有流量\n\n"
                step += 1

            if self.scan_results.get('pmf'):
                report += f"{step}. PMF管理帧防护（优先级: 高）\n"
                report += "   • 在路由器后台启用802.11w（PMF）功能\n"
                report += "   • 防止Deauthentication/Disassociation攻击\n"
                report += "   • 或升级到WPA3（强制启用PMF）\n\n"
                step += 1

            if self.scan_results['wps']:
                report += f"{step}. WPS漏洞修复（优先级: 最高）\n"
                report += "   • 立即禁用所有路由器的WPS功能\n"
                report += "   • 更新路由器固件到最新版本\n"
                report += "   • 使用WPA2-AES或WPA3加密\n\n"
                step += 1
            
            if self.scan_results['evil_twin']:
                report += f"{step}. Evil Twin防护\n"
                report += "   • 不要连接可疑的WiFi网络\n"
                report += "   • 使用VPN加密数据传输\n"
                report += "   • 检查路由器MAC地址和IP配置\n\n"
                step += 1
            
            report += f"{step}. 通用安全建议\n"
            report += "   • 使用WPA2-PSK(AES)或WPA3加密\n"
            report += "   • 设置12位以上强密码\n"
            report += "   • 定期更换WiFi密码\n"
            report += "   • 启用路由器防火墙\n"
            report += "   • 禁用远程管理功能\n"
            
            # 显示报告窗口
            report_window = tk.Toplevel(self.frame)
            report_window.title("WiFi安全扫描专业报告")
            report_window.geometry("900x700")
            
            text = scrolledtext.ScrolledText(report_window, 
                                           font=('Consolas', 9),
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
                    initialfile=f"wifi_security_pro_report_{timestamp}.txt",
                    filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
                )
                if filename:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(report)
                    messagebox.showinfo("成功", "报告已保存")
            
            btn_frame = ttk.Frame(report_window)
            btn_frame.pack(pady=10)
            ModernButton(btn_frame, text="💾 保存报告", 
                        command=save_report, style='primary').pack()
            
        except Exception as e:
            messagebox.showerror("错误", f"报告生成失败: {str(e)}")
    
    def get_frame(self):
        """获取框架"""
        return self.frame
