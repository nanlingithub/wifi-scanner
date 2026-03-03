"""
WiFi信号罗盘模块 - 从 network_overview.py 提取
提供基于RSSI的12方向信号强度扫描，帮助用户寻找AP方向（精度±30-60°）
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import re
import platform
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .theme import ModernButton

# Windows命令执行配置
if platform.system().lower() == "windows":
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0


def show_signal_compass(parent, scanned_networks):
    """
    显示信号强度罗盘弹窗 - RSSI方向提示工具 v1.5
    
    参数:
        parent: 父级tk窗口
        scanned_networks: 已扫描的WiFi网络列表（list of dict）
    """
    try:
        # 检查是否有扫描数据
        if not scanned_networks:
            messagebox.showwarning("提示", "请先扫描WiFi网络！")
            return

        # 选择要分析的WiFi
        ssid_list = [net.get('ssid', '未知') for net in scanned_networks if net.get('ssid')]
        if not ssid_list:
            messagebox.showwarning("提示", "没有可用的WiFi网络")
            return

        # 创建选择对话框
        compass_window = tk.Toplevel(parent)
        compass_window.title("🧭 WiFi信号罗盘 - 方向提示工具 v1.5")
        compass_window.geometry("1300x820")
        compass_window.resizable(True, True)

        # 说明文字
        info_frame = ttk.Frame(compass_window)
        info_frame.pack(fill='x', padx=20, pady=15)

        ttk.Label(info_frame, text="📡 WiFi信号方向提示工具",
                  font=('Microsoft YaHei', 13, 'bold')).pack(anchor='w', pady=(0, 8))
        ttk.Label(info_frame, text="原理：记录您旋转360°时各方向的信号强度（RSSI），推算AP大致方向",
                  font=('Microsoft YaHei', 10), foreground='#666').pack(anchor='w', pady=3)
        ttk.Label(info_frame, text="精度：±30-60° (参考级别，受墙壁、反射、多径效应影响)",
                  font=('Microsoft YaHei', 10), foreground='#dc3545').pack(anchor='w', pady=3)
        ttk.Label(info_frame, text="使用方法：1) 选择WiFi  2) 设置采样频率  3) 开始扫描  4) 慢慢旋转360°  5) 查看信号方向分布",
                  font=('Microsoft YaHei', 10), foreground='#28a745').pack(anchor='w', pady=3)

        # 控制区
        control_frame = ttk.Frame(compass_window)
        control_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(control_frame, text="目标WiFi:", font=('Microsoft YaHei', 11, 'bold')).pack(side='left', padx=(0, 10))
        target_var = tk.StringVar(value=ssid_list[0])
        target_combo = ttk.Combobox(control_frame, textvariable=target_var,
                                    values=ssid_list, width=50, state='readonly')
        target_combo.pack(side='left', padx=5)

        # 采样频率控制
        ttk.Label(control_frame, text="采样频率:", font=('Microsoft YaHei', 10)).pack(side='left', padx=(15, 5))
        sample_interval_var = tk.StringVar(value="1秒")
        interval_combo = ttk.Combobox(control_frame, textvariable=sample_interval_var,
                                      values=["0.5秒", "1秒", "2秒", "3秒", "5秒"],
                                      width=8, state='readonly')
        interval_combo.pack(side='left', padx=5)

        # 扫描控制状态
        scan_active = {
            'running': False,
            'direction_data': {},
            'current_angle': 0,
            'sample_count': 0  # 采样计数器
        }

        def get_direction_name(angle):
            """根据角度获取方位名称"""
            angle = angle % 360
            directions = [
                "正北", "北偏东", "东北", "东偏北",
                "正东", "东偏南", "东南", "南偏东",
                "正南", "南偏西", "西南", "西偏南",
                "正西", "西偏北", "西北", "北偏西"
            ]
            index = int((angle + 11.25) / 22.5) % 16
            return directions[index]

        def update_compass_display():
            """更新罗盘显示 - 箭头指向最强信号"""
            try:
                compass_fig.clear()
                ax = compass_fig.add_subplot(111, projection='polar')

                ax.set_theta_direction(-1)
                ax.set_theta_zero_location('N')

                angles = []
                signals = []
                angle_signal_map = {}

                for angle in sorted(scan_active['direction_data'].keys()):
                    avg_signal = np.mean(scan_active['direction_data'][angle])
                    angles.append(np.deg2rad(angle))
                    signals.append(avg_signal)
                    angle_signal_map[angle] = avg_signal

                if angles:
                    angles.append(angles[0])
                    signals.append(signals[0])

                    ax.plot(angles, signals, 'b-', linewidth=2.5, label='信号强度', zorder=5)
                    ax.fill(angles, signals, alpha=0.25, color='blue', zorder=4)

                    max_idx = signals[:-1].index(max(signals[:-1]))
                    max_angle = angles[max_idx]
                    max_signal = signals[max_idx]
                    max_angle_deg = np.rad2deg(max_angle)
                    direction_name = get_direction_name(max_angle_deg)

                    # 信号点分级着色
                    for angle, signal in angle_signal_map.items():
                        angle_rad = np.deg2rad(angle)

                        if signal >= -50:
                            point_color = '#00CC00'
                            point_size = 12
                        elif signal >= -60:
                            point_color = '#66FF66'
                            point_size = 10
                        elif signal >= -70:
                            point_color = '#FF9900'
                            point_size = 10
                        elif signal >= -80:
                            point_color = '#FF3300'
                            point_size = 8
                        else:
                            point_color = '#CC0000'
                            point_size = 8

                        ax.plot([angle_rad], [signal], 'o',
                                color=point_color, markersize=point_size,
                                markeredgecolor='white', markeredgewidth=1,
                                zorder=6)

                        is_min_point = (signal == min(angle_signal_map.values()))
                        angle_diff = abs(angle - np.rad2deg(max_angle)) % 360
                        if angle_diff > 180:
                            angle_diff = 360 - angle_diff
                        is_near_max = angle_diff < 30

                        if is_min_point and not is_near_max:
                            label_offset = 6
                            label_r = signal + label_offset

                            ax.text(angle_rad, label_r, f'{signal:.0f}',
                                    ha='center', va='center',
                                    fontsize=6.5, fontweight='bold',
                                    color=point_color,
                                    bbox=dict(boxstyle='round,pad=0.15',
                                              facecolor='white',
                                              edgecolor=point_color,
                                              alpha=0.8),
                                    zorder=7)

                    # 增强指针显示
                    pointer_end_r = max_signal * 0.92

                    ax.annotate('',
                                xy=(max_angle, pointer_end_r),
                                xytext=(max_angle, -100),
                                arrowprops=dict(
                                    arrowstyle='-|>',
                                    color='red',
                                    lw=3.5,
                                    alpha=0.85,
                                    mutation_scale=20
                                ),
                                zorder=9)

                    ax.plot([max_angle], [max_signal], '*',
                            color='red', markersize=18,
                            markeredgecolor='darkred', markeredgewidth=1.5,
                            label=f'最强: {direction_name} ({max_angle_deg:.0f}°)',
                            zorder=10)

                    if abs(max_angle_deg) < 45 or abs(max_angle_deg - 360) < 45:
                        annotation_angle = max_angle + np.deg2rad(30)
                        annotation_r = -20 + 8
                    else:
                        annotation_angle = max_angle
                        annotation_r = -20 + 12

                    annotation_text = f'★ {direction_name}\n{max_angle_deg:.0f}° | {max_signal:.1f}dBm'
                    ax.annotate(annotation_text,
                                xy=(max_angle, max_signal),
                                xytext=(annotation_angle, annotation_r),
                                ha='center', va='center',
                                fontsize=7.5, fontweight='bold',
                                color='darkred',
                                bbox=dict(boxstyle='round,pad=0.35',
                                          facecolor='#FFFACD',
                                          edgecolor='red',
                                          linewidth=1.2,
                                          alpha=0.88),
                                arrowprops=dict(arrowstyle='->',
                                               color='red',
                                               lw=1.2,
                                               alpha=0.65),
                                zorder=11)

                ax.set_ylim(-100, -10)
                title_text = f'WiFi信号方位罗盘\n目标: {target_var.get()}'
                ax.set_title(title_text, fontsize=11, pad=20, fontweight='bold')
                ax.legend(loc='upper left', bbox_to_anchor=(-0.15, 1.08), fontsize=8, framealpha=0.9)
                ax.grid(True, alpha=0.3, linestyle='--')

                compass_canvas.draw_idle()
            except Exception as e:
                print(f"罗盘显示错误: {e}")

        def analyze_direction_data():
            """分析方向数据，给出建议"""
            if not scan_active['direction_data']:
                result_text.delete('1.0', 'end')
                result_text.insert('end', "⚠ 没有扫描数据\n")
                return

            direction_avg = {}
            for angle, signals in scan_active['direction_data'].items():
                direction_avg[angle] = np.mean(signals)

            best_angle = max(direction_avg.items(), key=lambda x: x[1])
            worst_angle = min(direction_avg.items(), key=lambda x: x[1])

            best_direction = get_direction_name(best_angle[0])
            worst_direction = get_direction_name(worst_angle[0])

            signal_range = best_angle[1] - worst_angle[1]

            result_text.delete('1.0', 'end')
            result_text.insert('end', f"📊 WiFi信号方位分析报告\n{'='*55}\n\n")
            result_text.insert('end', f"目标WiFi: {target_var.get()}\n")
            result_text.insert('end', f"扫描方位数: {len(direction_avg)} 个\n")
            result_text.insert('end', f"总采样次数: {scan_active['sample_count']}\n\n")

            result_text.insert('end', "🎯 推荐方向:\n")
            result_text.insert('end', f"   最强: {best_direction} ({best_angle[0]}°) → {best_angle[1]:.1f} dBm\n", 'highlight')
            result_text.insert('end', f"   最弱: {worst_direction} ({worst_angle[0]}°) → {worst_angle[1]:.1f} dBm\n")
            result_text.insert('end', f"   信号差异: {signal_range:.1f} dB\n\n")

            result_text.insert('end', "💡 建议:\n")
            if best_angle[1] > -50:
                result_text.insert('end', f"   ✅ 信号很强，AP可能在{best_direction}方向约50米内\n")
            elif best_angle[1] > -70:
                result_text.insert('end', f"   ✓ 信号良好，AP可能在{best_direction}方向约100米内\n")
            else:
                result_text.insert('end', "   ⚠ 信号较弱，AP可能较远或有遮挡\n")

            result_text.insert('end', "\n📍 测向精度评估:\n")
            if signal_range > 20:
                result_text.insert('end', "   ✅ 信号差异大，方向性明显，精度高（±30°）\n")
            elif signal_range > 10:
                result_text.insert('end', "   ✓ 信号差异中等，有一定方向性（±45°）\n")
            else:
                result_text.insert('end', "   ⚠ 信号差异小，可能有多径干扰或全向天线（±60°）\n")

            result_text.insert('end', "\n📝 注意事项:\n")
            result_text.insert('end', "   • 方向精度: ±30-60°（受墙壁、反射、多径效应影响）\n")
            result_text.insert('end', "   • 室内环境下，反射信号可能干扰测向精度\n")
            result_text.insert('end', "   • 建议在空旷环境或室外测试以获得更准确结果\n")
            result_text.insert('end', "   • 方向角度为相对方向，以开始扫描位置为0°基准\n")

            result_text.insert('end', f"\n📊 所有方位数据（按信号强度排序）:\n")
            result_text.insert('end', f"{'='*55}\n")

            sorted_directions = sorted(direction_avg.items(), key=lambda x: x[1], reverse=True)

            for i, (angle, signal) in enumerate(sorted_directions, 1):
                dir_name = get_direction_name(angle)
                samples = len(scan_active['direction_data'][angle])

                bar_length = int((signal + 100) / 2)
                bar = '█' * max(0, bar_length)

                if i == 1:
                    result_text.insert('end', f"  🥇 {dir_name:8s} ({angle:3d}°) {signal:6.1f} dBm {bar} [{samples}次]\n")
                elif i == len(sorted_directions):
                    result_text.insert('end', f"  ❌ {dir_name:8s} ({angle:3d}°) {signal:6.1f} dBm {bar} [{samples}次]\n")
                else:
                    result_text.insert('end', f"     {dir_name:8s} ({angle:3d}°) {signal:6.1f} dBm {bar} [{samples}次]\n")

            result_text.insert('end', "\n🔍 算法说明:\n")
            result_text.insert('end', "   1. 将360°分为12个方位扇区（每30°）\n")
            result_text.insert('end', "   2. 每个方位多次采样取平均值，减少随机误差\n")
            result_text.insert('end', "   3. 基于信号强度差异评估测向可靠性\n")
            result_text.insert('end', "   4. 起始位置作为0°基准，顺时针旋转增加\n")

        def stop_compass_scan():
            """停止扫描"""
            scan_active['running'] = False
            start_btn.config(state='normal')
            stop_btn.config(state='disabled')
            status_label.config(text="✅ 扫描完成", foreground='#007bff')
            analyze_direction_data()

        def start_compass_scan():
            """开始罗盘扫描"""
            if scan_active['running']:
                messagebox.showwarning("提示", "扫描正在进行中")
                return

            scan_active['running'] = True
            scan_active['direction_data'] = {}
            scan_active['current_angle'] = 0
            scan_active['sample_count'] = 0
            start_btn.config(state='disabled')
            stop_btn.config(state='normal')
            status_label.config(text="🔄 正在扫描... 请慢慢顺时针旋转360°", foreground='#28a745')

            def scan_loop():
                if not scan_active['running']:
                    return

                target_ssid = target_var.get()
                current_signal = -100

                try:
                    result = subprocess.run(
                        ['netsh', 'wlan', 'show', 'networks', 'mode=bssid'],
                        capture_output=True, timeout=3,
                        creationflags=CREATE_NO_WINDOW
                    )

                    if result.stdout:
                        try:
                            output_text = result.stdout.decode('gbk', errors='ignore')
                        except Exception:
                            output_text = result.stdout.decode('utf-8', errors='ignore')
                    else:
                        output_text = ""

                    if output_text:
                        lines = output_text.split('\n')
                        for i, line in enumerate(lines):
                            if target_ssid in line and 'SSID' in line:
                                for j in range(i, min(i + 10, len(lines))):
                                    if '信号' in lines[j] or 'Signal' in lines[j]:
                                        signal_match = re.search(r'(\d+)%', lines[j])
                                        if signal_match:
                                            signal_percent = int(signal_match.group(1))
                                            # 标准 Windows RSSI 换算: signal% / 2 - 100
                                            current_signal = (signal_percent / 2) - 100
                                            break
                                break
                except Exception as e:
                    print(f"扫描错误: {e}")

                scan_active['sample_count'] += 1
                relative_angle = scan_active['current_angle']

                sector_angle = round(relative_angle / 30) * 30
                sector_angle = sector_angle % 360

                if sector_angle not in scan_active['direction_data']:
                    scan_active['direction_data'][sector_angle] = []
                scan_active['direction_data'][sector_angle].append(current_signal)

                # 每次采样后将角度推进 30°（12 扇区覆盖 360°，假设用户匀速旋转）
                scan_active['current_angle'] = (scan_active['current_angle'] + 30) % 360

                direction_name = get_direction_name(relative_angle)

                info_labels['direction'].config(
                    text=f"{direction_name} ({relative_angle}°)",
                    foreground='#007bff'
                )

                if current_signal >= -50:
                    signal_color = '#00CC00'
                    signal_bar = '●●●●●'
                elif current_signal >= -60:
                    signal_color = '#66FF66'
                    signal_bar = '●●●●○'
                elif current_signal >= -70:
                    signal_color = '#FF9900'
                    signal_bar = '●●●○○'
                elif current_signal >= -80:
                    signal_color = '#FF3300'
                    signal_bar = '●●○○○'
                else:
                    signal_color = '#CC0000'
                    signal_bar = '●○○○○'

                info_labels['signal'].config(
                    text=f"{current_signal:.1f} dBm {signal_bar}",
                    foreground=signal_color
                )

                info_labels['samples'].config(text=f"{scan_active['sample_count']} 次")

                if scan_active['direction_data']:
                    # 用扇区数×30° 表示已覆盖角度，避免 max-min 对满圈显示 330° 的问题
                    coverage = len(scan_active['direction_data']) * 30
                    info_labels['coverage'].config(text=f"{coverage}°")

                status_label.config(
                    text=f"🔄 扫描中... 已采样: {scan_active['sample_count']} 次 | "
                         f"当前方位: {direction_name} ({relative_angle}°) | 信号: {current_signal:.1f} dBm"
                )

                if scan_active['sample_count'] % 5 == 0:
                    result_text.delete('1.0', 'end')
                    result_text.insert('end', f"📡 实时采样数据\n{'='*50}\n\n")
                    result_text.insert('end', f"目标WiFi: {target_var.get()}\n")
                    result_text.insert('end', f"总采样次数: {scan_active['sample_count']}\n\n")
                    result_text.insert('end', "最近10次采样:\n")

                    all_samples = []
                    for ang in sorted(scan_active['direction_data'].keys()):
                        for sig in scan_active['direction_data'][ang]:
                            all_samples.append((ang, sig))

                    for i, (ang, sig) in enumerate(all_samples[-10:], 1):
                        dir_name = get_direction_name(ang)
                        result_text.insert('end', f"  [{i}] {dir_name} ({ang}°) → {sig:.1f} dBm\n")

                    result_text.insert('end', "\n💡 提示: 红色箭头指向最强信号方向...\n")

                update_compass_display()

                interval_text = sample_interval_var.get()
                interval_ms = int(float(interval_text.replace('秒', '')) * 1000)

                compass_window.after(interval_ms, scan_loop)

            scan_loop()

        # 按钮区
        button_frame = ttk.Frame(compass_window)
        button_frame.pack(fill='x', padx=15, pady=10)

        start_btn = ModernButton(button_frame, text="▶ 开始扫描",
                                 command=start_compass_scan, style='success')
        start_btn.pack(side='left', padx=8)

        stop_btn = ModernButton(button_frame, text="⏹ 停止",
                                command=stop_compass_scan, style='danger')
        stop_btn.pack(side='left', padx=8)
        stop_btn.config(state='disabled')

        status_label = ttk.Label(button_frame, text="⏳ 准备就绪",
                                 font=('Microsoft YaHei', 10), foreground='#666')
        status_label.pack(side='left', padx=20)

        # 罗盘显示区
        display_frame = ttk.Frame(compass_window)
        display_frame.pack(fill='both', expand=True, padx=15, pady=10)

        # 左侧：WiFi罗盘图
        left_frame = ttk.Frame(display_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # 右侧：信息面板
        right_frame = ttk.Frame(display_frame)
        right_frame.pack(side='right', fill='both', padx=(10, 0))

        # WiFi信息面板
        info_panel = ttk.LabelFrame(right_frame, text="🎯 目标网络信息", padding=15)
        info_panel.pack(fill='x', pady=(0, 10))

        def get_target_network_info():
            """获取当前选中WiFi的详细信息"""
            target_ssid = target_var.get()
            for net in scanned_networks:
                if net.get('ssid') == target_ssid:
                    return net
            return {}

        info_labels = {}
        info_grid = ttk.Frame(info_panel)
        info_grid.pack(fill='x')

        ttk.Label(info_grid, text="SSID:", font=('Microsoft YaHei', 10, 'bold')).grid(
            row=0, column=0, sticky='w', pady=4, padx=(0, 10))
        info_labels['ssid'] = ttk.Label(info_grid, text=target_var.get(),
                                        font=('Consolas', 10), foreground='#007bff')
        info_labels['ssid'].grid(row=0, column=1, sticky='w', padx=8, pady=4)

        ttk.Label(info_grid, text="BSSID:", font=('Microsoft YaHei', 10, 'bold')).grid(
            row=1, column=0, sticky='w', pady=4, padx=(0, 10))
        info_labels['bssid'] = ttk.Label(info_grid, text="--", font=('Consolas', 10))
        info_labels['bssid'].grid(row=1, column=1, sticky='w', padx=8, pady=4)

        ttk.Label(info_grid, text="频段:", font=('Microsoft YaHei', 10, 'bold')).grid(
            row=2, column=0, sticky='w', pady=4, padx=(0, 10))
        info_labels['band'] = ttk.Label(info_grid, text="--", font=('Consolas', 10))
        info_labels['band'].grid(row=2, column=1, sticky='w', padx=8, pady=4)

        ttk.Label(info_grid, text="加密:", font=('Microsoft YaHei', 10, 'bold')).grid(
            row=3, column=0, sticky='w', pady=4, padx=(0, 10))
        info_labels['auth'] = ttk.Label(info_grid, text="--", font=('Consolas', 10))
        info_labels['auth'].grid(row=3, column=1, sticky='w', padx=8, pady=4)

        # 扫描状态面板
        status_panel = ttk.LabelFrame(right_frame, text="📊 当前扫描状态", padding=15)
        status_panel.pack(fill='x', pady=(0, 10))

        status_grid = ttk.Frame(status_panel)
        status_grid.pack(fill='x')

        ttk.Label(status_grid, text="当前方位:", font=('Microsoft YaHei', 11, 'bold')).grid(
            row=0, column=0, sticky='w', pady=5, padx=(0, 15))
        info_labels['direction'] = ttk.Label(status_grid, text="准备中",
                                             font=('Consolas', 11), foreground='#666')
        info_labels['direction'].grid(row=0, column=1, sticky='w', padx=10, pady=5)

        ttk.Label(status_grid, text="实时信号:", font=('Microsoft YaHei', 11, 'bold')).grid(
            row=1, column=0, sticky='w', pady=5, padx=(0, 15))
        info_labels['signal'] = ttk.Label(status_grid, text="-- dBm", font=('Consolas', 11))
        info_labels['signal'].grid(row=1, column=1, sticky='w', padx=10, pady=5)

        ttk.Label(status_grid, text="已采样:", font=('Microsoft YaHei', 11, 'bold')).grid(
            row=2, column=0, sticky='w', pady=5, padx=(0, 15))
        info_labels['samples'] = ttk.Label(status_grid, text="0 次", font=('Consolas', 11))
        info_labels['samples'].grid(row=2, column=1, sticky='w', padx=10, pady=5)

        ttk.Label(status_grid, text="覆盖角度:", font=('Microsoft YaHei', 11, 'bold')).grid(
            row=3, column=0, sticky='w', pady=5, padx=(0, 15))
        info_labels['coverage'] = ttk.Label(status_grid, text="0°", font=('Consolas', 11))
        info_labels['coverage'].grid(row=3, column=1, sticky='w', padx=10, pady=5)

        def update_wifi_info():
            """更新WiFi网络信息"""
            net = get_target_network_info()
            if net:
                info_labels['ssid'].config(text=net.get('ssid', '--'))
                info_labels['bssid'].config(text=net.get('bssid', '--'))

                channel = net.get('channel', '--')
                if channel and channel != '--':
                    try:
                        ch_num = int(channel)
                        if ch_num <= 14:
                            band_text = f"2.4GHz (信道 {ch_num})"
                        else:
                            band_text = f"5GHz (信道 {ch_num})"
                    except Exception:
                        band_text = f"信道 {channel}"
                else:
                    band_text = "--"
                info_labels['band'].config(text=band_text)

                auth = net.get('authentication', '--')
                info_labels['auth'].config(text=auth)

        update_wifi_info()
        # 切换目标 WiFi 时同步刷新信息栏
        target_combo.bind('<<ComboboxSelected>>', lambda e: update_wifi_info())

        # 罗盘图（左侧主显示区）
        compass_fig = Figure(figsize=(8, 7), dpi=100)
        compass_canvas = FigureCanvasTkAgg(compass_fig, left_frame)
        compass_canvas.get_tk_widget().pack(fill='both', expand=True)

        ax = compass_fig.add_subplot(111, projection='polar')
        ax.set_theta_direction(-1)
        ax.set_theta_zero_location('N')
        ax.set_ylim(-100, -20)
        ax.set_title('等待开始扫描...', fontsize=12, pad=20)
        ax.grid(True)
        compass_canvas.draw()

        # 分析结果面板
        result_frame = ttk.LabelFrame(right_frame, text="📋 分析结果", padding=12)
        result_frame.pack(fill='both', expand=True)

        result_text = scrolledtext.ScrolledText(result_frame, height=15, width=38,
                                                font=('Consolas', 9), wrap='word')
        result_text.pack(fill='both', expand=True)
        result_text.tag_config('highlight', foreground='#dc3545', font=('Consolas', 9, 'bold'))

        result_text.insert('end', "等待扫描数据...\n\n")
        result_text.insert('end', "使用说明：\n")
        result_text.insert('end', "1. 选择要定位的WiFi网络\n")
        result_text.insert('end', "2. 点击'开始扫描'\n")
        result_text.insert('end', "3. 保持设备水平，慢慢旋转360°\n")
        result_text.insert('end', "4. 完成一圈后点击'停止'\n")
        result_text.insert('end', "5. 查看推荐方向\n\n")
        result_text.insert('end', "⚠ 此功能基于RSSI值推测方向\n")
        result_text.insert('end', "精度受环境影响，仅供参考！\n")

    except Exception as e:
        messagebox.showerror("错误", f"信号罗盘启动失败: {str(e)}")
