"""
性能基准测试GUI窗口
集成WiFi网速测试功能
"""
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.dates as mdates
from datetime import datetime
import os
from wifi_modules.performance_benchmark import WiFiPerformanceBenchmark
from wifi_modules.theme import ModernButton
from wifi_modules.icon_system import PROFESSIONAL_ICONS

class PerformanceBenchmarkWindow:
    """性能基准测试窗口"""
    
    def __init__(self, parent):
        """
        初始化窗口
        
        Args:
            parent: 父窗口
        """
        self.window = tk.Toplevel(parent)
        self.window.title(f"{PROFESSIONAL_ICONS['performance']} WiFi性能基准测试")
        self.window.geometry("1000x700")
        
        # 设置窗口图标
        try:
            # 获取项目根目录（从wifi_modules目录向上一级）
            root_dir = os.path.dirname(os.path.dirname(__file__))
            icon_path = os.path.join(root_dir, 'wifi_professional.ico')
            if os.path.exists(icon_path):
                self.window.iconbitmap(icon_path)
        except Exception as e:
            print(f"[警告] 无法加载图标: {e}")
        
        self.benchmark = WiFiPerformanceBenchmark()
        self.is_testing = False
        
        self._setup_ui()
        self._refresh_display()
    
    def _setup_ui(self):
        """设置UI"""
        # 顶部控制栏
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        ModernButton(control_frame, text=f"{PROFESSIONAL_ICONS['start']} 开始测速", 
                    command=self._start_test, style='primary').pack(side='left', padx=5)
        
        ModernButton(control_frame, text=f"{PROFESSIONAL_ICONS['table']} 查看历史", 
                    command=self._show_history, style='info').pack(side='left', padx=5)
        
        ModernButton(control_frame, text=f"{PROFESSIONAL_ICONS['chart_line']} 查看趋势", 
                    command=self._show_trend, style='success').pack(side='left', padx=5)
        
        ModernButton(control_frame, text=f"{PROFESSIONAL_ICONS['export']} 导出CSV", 
                    command=self._export_csv, style='secondary').pack(side='left', padx=5)
        
        ModernButton(control_frame, text=f"{PROFESSIONAL_ICONS['delete']} 清空历史", 
                    command=self._clear_history, style='danger').pack(side='left', padx=5)
        
        self.status_label = tk.Label(control_frame, text="就绪", 
                                     font=('Microsoft YaHei', 10), fg='green')
        self.status_label.pack(side='right', padx=10)
        
        # 实时测试进度区域
        progress_frame = ttk.LabelFrame(self.window, text=f"{PROFESSIONAL_ICONS['hourglass']} 测试进度", padding=10)
        progress_frame.pack(fill='x', padx=10, pady=5)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                           variable=self.progress_var,
                                           maximum=100, 
                                           mode='determinate')
        self.progress_bar.pack(fill='x', pady=5)
        
        # 实时状态文本
        self.progress_text = tk.Text(progress_frame, height=4, 
                                     font=('Microsoft YaHei', 9),
                                     bg='#f8f9fa', state='disabled')
        self.progress_text.pack(fill='x')
        
        # 当前测试结果区域
        result_frame = ttk.LabelFrame(self.window, text=f"{PROFESSIONAL_ICONS['chart_bar']} 当前测试结果", padding=10)
        result_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 左侧: 速度仪表盘
        left_frame = ttk.Frame(result_frame)
        left_frame.pack(side='left', fill='both', expand=True)
        
        # 下载速度
        tk.Label(left_frame, text="下载速度", font=('Microsoft YaHei', 12, 'bold')).pack(pady=5)
        self.download_label = tk.Label(left_frame, text="-- Mbps", 
                                       font=('Microsoft YaHei', 24, 'bold'), fg='#3498db')
        self.download_label.pack()
        
        # 上传速度
        tk.Label(left_frame, text="上传速度", font=('Microsoft YaHei', 12, 'bold')).pack(pady=5)
        self.upload_label = tk.Label(left_frame, text="-- Mbps", 
                                     font=('Microsoft YaHei', 24, 'bold'), fg='#e74c3c')
        self.upload_label.pack()
        
        # 延迟
        tk.Label(left_frame, text="延迟", font=('Microsoft YaHei', 12, 'bold')).pack(pady=5)
        self.ping_label = tk.Label(left_frame, text="-- ms", 
                                   font=('Microsoft YaHei', 24, 'bold'), fg='#f39c12')
        self.ping_label.pack()
        
        # 抖动（新增）
        tk.Label(left_frame, text="抖动", font=('Microsoft YaHei', 12, 'bold')).pack(pady=5)
        self.jitter_label = tk.Label(left_frame, text="-- ms", 
                                     font=('Microsoft YaHei', 18), fg='#9b59b6')
        self.jitter_label.pack()
        
        # 丢包率（新增）
        tk.Label(left_frame, text="丢包率", font=('Microsoft YaHei', 12, 'bold')).pack(pady=5)
        self.packet_loss_label = tk.Label(left_frame, text="-- %", 
                                          font=('Microsoft YaHei', 18), fg='#e67e22')
        self.packet_loss_label.pack()
        
        # 右侧: 详细信息和评级
        right_frame = ttk.Frame(result_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=10)
        
        tk.Label(right_frame, text=f"{PROFESSIONAL_ICONS['star']} 质量评级", 
                font=('Microsoft YaHei', 12, 'bold')).pack(pady=5)
        self.rating_text = tk.Text(right_frame, height=10, font=('Microsoft YaHei', 10))
        self.rating_text.pack(fill='both', expand=True)
        
        tk.Label(right_frame, text=f"{PROFESSIONAL_ICONS['server']} 服务器信息", 
                font=('Microsoft YaHei', 10, 'bold')).pack(pady=5)
        self.server_text = tk.Text(right_frame, height=5, font=('Microsoft YaHei', 9))
        self.server_text.pack(fill='both', expand=True)
        
        # 统计信息区域
        stats_frame = ttk.LabelFrame(self.window, text=f"{PROFESSIONAL_ICONS['chart_line']} 历史统计", padding=10)
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=4, font=('Microsoft YaHei', 9))
        self.stats_text.pack(fill='x')
    
    def _update_progress_text(self, message):
        """更新进度文本"""
        self.progress_text.config(state='normal')
        self.progress_text.insert('end', message)
        self.progress_text.see('end')  # 自动滚动到底部
        self.progress_text.config(state='disabled')
    
    def _start_test(self):
        """开始测速"""
        if self.is_testing:
            messagebox.showwarning("提示", "测试正在进行中，请稍候...")
            return
        
        # 确认开始测试
        if not messagebox.askyesno("确认", 
                                   "网速测试需要30-60秒时间，是否开始？\n"
                                   "（需要联网且会消耗少量流量）"):
            return
        
        self.is_testing = True
        self.status_label.config(text="测试中...", fg='orange')
        
        # 重置进度显示
        self.progress_var.set(0)
        self._update_progress_text("🚀 开始网速测试...\n")
        
        # 禁用按钮
        for widget in self.window.winfo_children():
            if isinstance(widget, ttk.Frame):
                for btn in widget.winfo_children():
                    if isinstance(btn, ModernButton):
                        btn.config(state='disabled')
        
        def progress_callback(status):
            """进度回调 - 必须通过 after(0) 切回主线程操作 tkinter"""
            def _ui_update():
                self.status_label.config(text=status)
                if "安装" in status:
                    self.progress_var.set(10)
                    self._update_progress_text(f"📦 {status}\n")
                elif "获取" in status or "选择" in status:
                    self.progress_var.set(20)
                    self._update_progress_text(f"🌐 {status}\n")
                elif "测试延迟" in status or "ping" in status.lower():
                    self.progress_var.set(30)
                    self._update_progress_text(f"📡 {status}\n")
                elif "下载" in status or "download" in status.lower():
                    self.progress_var.set(50)
                    self._update_progress_text(f"⬇️ {status}\n")
                elif "上传" in status or "upload" in status.lower():
                    self.progress_var.set(80)
                    self._update_progress_text(f"⬆️ {status}\n")
                elif "完成" in status or "成功" in status:
                    self.progress_var.set(100)
                    self._update_progress_text(f"✅ {status}\n")
                else:
                    self._update_progress_text(f"ℹ️ {status}\n")
            # 通过 after(0) 确保在主线程执行，tkinter 线程安全
            self.window.after(0, _ui_update)

        def complete_callback(result):
            """完成回调 - 通过 after(0) 切回主线程"""
            def _on_complete():
                self.is_testing = False
                # 启用按钮
                for widget in self.window.winfo_children():
                    if isinstance(widget, ttk.Frame):
                        for btn in widget.winfo_children():
                            if isinstance(btn, ModernButton):
                                btn.config(state='normal')
                if 'error' in result:
                    self.status_label.config(text=f"失败: {result['error']}", fg='red')
                    messagebox.showerror("测试失败", result['error'])
                else:
                    self.status_label.config(text="测试完成", fg='green')
                    self._display_result(result)
                    self._refresh_display()
                    messagebox.showinfo("测试完成", "网速测试成功完成！")
            self.window.after(0, _on_complete)
        
        # 异步执行测试
        self.benchmark.run_speed_test_async(
            callback_progress=progress_callback,
            callback_complete=complete_callback
        )
    
    def _display_result(self, result):
        """显示测试结果"""
        # 显示速度
        self.download_label.config(text=f"{result['download']} Mbps")
        self.upload_label.config(text=f"{result['upload']} Mbps")
        self.ping_label.config(text=f"{result['ping']} ms")
        
        # 显示抖动和丢包率（新增）
        if 'jitter' in result:
            jitter_text = f"{result['jitter']} ms" if result['jitter'] > 0 else "N/A"
            self.jitter_label.config(text=jitter_text)
        
        if 'packet_loss' in result:
            loss_text = f"{result['packet_loss']} %" if result['packet_loss'] > 0 else "N/A"
            self.packet_loss_label.config(text=loss_text)
        
        # 显示评级（传入已有协议值，避免重复调用 netsh）
        rating = self.benchmark.get_quality_rating(
            result['download'],
            result['upload'],
            result['ping'],
            wifi_protocol=result.get('wifi_protocol')
        )
        
        self.rating_text.delete('1.0', 'end')
        rating_info = f"""
综合评级: {rating['overall_rating']} ({rating['overall_score']}分)

下载速度: {rating['download_rating']}
上传速度: {rating['upload_rating']}
延迟: {rating['ping_rating']}
"""
        # 添加抖动和丢包率评级（如果有）
        if 'jitter_rating' in result and result['jitter_rating'] != 'N/A':
            rating_info += f"抖动: {result['jitter_rating']}\n"
        if 'packet_loss_rating' in result and result['packet_loss_rating'] != 'N/A':
            rating_info += f"丢包率: {result['packet_loss_rating']}\n"
        
        rating_info += f"\n测试时间: {result['timestamp']}"
        rating_info = rating_info.strip()
        
        self.rating_text.insert('1.0', rating_info)
        
        # 显示服务器信息
        self.server_text.delete('1.0', 'end')
        server_info = f"""
服务器: {result['server']['name']}
国家: {result['server']['country']}
ISP: {result['client']['isp']}
        """.strip()
        self.server_text.insert('1.0', server_info)
    
    def _refresh_display(self):
        """刷新显示"""
        stats = self.benchmark.get_statistics()
        
        if stats['total_tests'] == 0:
            stats_info = "暂无历史数据"
        else:
            stats_info = f"""
总测试次数: {stats['total_tests']}
平均下载: {stats['avg_download']} Mbps  |  最高: {stats['max_download']} Mbps
平均上传: {stats['avg_upload']} Mbps  |  最高: {stats['max_upload']} Mbps
平均延迟: {stats['avg_ping']} ms  |  最低: {stats['min_ping']} ms
            """.strip()
        
        self.stats_text.delete('1.0', 'end')
        self.stats_text.insert('1.0', stats_info)
    
    def _show_history(self):
        """显示历史记录"""
        history = self.benchmark.get_history(limit=20)
        
        if not history:
            messagebox.showinfo("提示", "暂无历史记录")
            return
        
        # 创建历史窗口
        history_win = tk.Toplevel(self.window)
        history_win.title("📊 测速历史记录")
        history_win.geometry("800x500")

        # 容器 frame，用 grid 布局保证滚动条始终可见
        container = ttk.Frame(history_win)
        container.pack(fill='both', expand=True, padx=10, pady=10)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # 创建表格
        columns = ('时间', '下载(Mbps)', '上传(Mbps)', '延迟(ms)', '服务器')
        tree = ttk.Treeview(container, columns=columns, show='headings')

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        # 填充数据
        for record in reversed(history):  # 最新的在前
            tree.insert('', 'end', values=(
                record['timestamp'],
                record['download'],
                record['upload'],
                record['ping'],
                record['server']['name']
            ))

        # 滚动条与 Treeview 同时 grid，确保滚动条可见
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=tree.yview)
        tree.config(yscrollcommand=scrollbar.set)
        tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
    
    def _show_trend(self):
        """显示趋势图"""
        history = self.benchmark.get_history(limit=50)
        
        if not history:
            messagebox.showinfo("提示", "暂无历史数据")
            return
        
        # 创建趋势窗口
        trend_win = tk.Toplevel(self.window)
        trend_win.title("📈 性能趋势分析")
        trend_win.geometry("1000x600")
        
        # 准备数据
        timestamps = [datetime.strptime(r['timestamp'], "%Y-%m-%d %H:%M:%S") for r in history]
        downloads = [r['download'] for r in history]
        uploads = [r['upload'] for r in history]
        pings = [r['ping'] for r in history]
        
        # 创建图表
        fig = Figure(figsize=(10, 8), facecolor='white')
        
        # 下载速度
        ax1 = fig.add_subplot(311)
        ax1.plot(timestamps, downloads, marker='o', color='#3498db', linewidth=2, markersize=4)
        ax1.set_ylabel('下载速度 (Mbps)', fontsize=11, fontweight='bold')
        ax1.set_title('网速趋势分析', fontsize=13, fontweight='bold')
        ax1.grid(alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # 上传速度
        ax2 = fig.add_subplot(312)
        ax2.plot(timestamps, uploads, marker='s', color='#e74c3c', linewidth=2, markersize=4)
        ax2.set_ylabel('上传速度 (Mbps)', fontsize=11, fontweight='bold')
        ax2.grid(alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # 延迟
        ax3 = fig.add_subplot(313)
        ax3.plot(timestamps, pings, marker='^', color='#f39c12', linewidth=2, markersize=4)
        ax3.set_ylabel('延迟 (ms)', fontsize=11, fontweight='bold')
        ax3.set_xlabel('时间', fontsize=11, fontweight='bold')
        ax3.grid(alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax3.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # 自动旋转时间标签
        fig.autofmt_xdate()
        fig.tight_layout()
        
        # 显示图表
        canvas = FigureCanvasTkAgg(fig, trend_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        toolbar = NavigationToolbar2Tk(canvas, trend_win)
        toolbar.update()
    
    def _export_csv(self):
        """导出CSV"""
        try:
            filename = self.benchmark.export_history_csv()
            messagebox.showinfo("成功", f"历史记录已导出:\n{filename}")
        except Exception as e:
            messagebox.showerror("失败", str(e))
    
    def _clear_history(self):
        """清空历史"""
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗？"):
            self.benchmark.clear_history()
            self._refresh_display()
            messagebox.showinfo("成功", "历史记录已清空")
