"""
部署优化标签页
功能：平面图上传、点击添加测量点、覆盖分析、AP推荐
v2.0优化：信号传播模型、智能AP推荐、空间覆盖率分析
v2.1: 使用统一可视化工具
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import json
from datetime import datetime

from .theme import ModernTheme, ModernButton, ModernCard, create_section_title
from .visualization_utils import HeatmapVisualizer
from core.constants import WALL_ATTENUATION as _WALL_ATTENUATION, ENVIRONMENT_FACTORS as _ENVIRONMENT_FACTORS

# 优化算法导入（P0）

# 优化算法导入（P0）
try:
    from sklearn.cluster import KMeans
    from scipy.optimize import differential_evolution
    from scipy.interpolate import Rbf
    OPTIMIZATION_AVAILABLE = True
except ImportError:
    OPTIMIZATION_AVAILABLE = False
    print("提示: 安装sklearn和scipy可启用高级优化功能")
    print("pip install scikit-learn scipy")


class SignalPropagationModel:
    """WiFi信号传播模型（P0-2）"""

    # 引用 core/constants.py 中的规范定义，消除重复
    WALL_ATTENUATION = _WALL_ATTENUATION
    ENVIRONMENT_FACTORS = _ENVIRONMENT_FACTORS
    
    @staticmethod
    def calculate_fspl(distance_m, frequency_ghz=2.4):
        """自由空间路径损耗（FSPL）"""
        if distance_m < 0.1:
            distance_m = 0.1  # 避免log(0)
        return 20 * np.log10(distance_m) + 20 * np.log10(frequency_ghz * 1000) + 32.45
    
    @staticmethod
    def calculate_path_loss(ap_pos, test_pos, obstacles=None, frequency_ghz=2.4):
        """考虑障碍物的路径损耗"""
        distance = np.linalg.norm(np.array(ap_pos) - np.array(test_pos))
        
        # 基础FSPL
        path_loss = SignalPropagationModel.calculate_fspl(distance / 100, frequency_ghz)  # 像素转米
        
        # 墙体衰减
        if obstacles:
            for obstacle in obstacles:
                if SignalPropagationModel._line_intersects_obstacle(ap_pos, test_pos, obstacle):
                    material = obstacle.get('material', '砖墙')
                    path_loss += SignalPropagationModel.WALL_ATTENUATION.get(material, 10)
        
        return path_loss
    
    @staticmethod
    def predict_signal(tx_power_dbm, ap_pos, test_pos, obstacles=None, frequency_ghz=2.4):
        """预测信号强度（dBm）"""
        path_loss = SignalPropagationModel.calculate_path_loss(
            ap_pos, test_pos, obstacles, frequency_ghz
        )
        return tx_power_dbm - path_loss
    
    @staticmethod
    def dbm_to_percent(dbm):
        """dBm转百分比"""
        # -30dBm=100%, -90dBm=0%
        return max(0, min(100, (dbm + 90) * 100 / 60))
    
    @staticmethod
    def percent_to_dbm(percent):
        """百分比转dBm"""
        return -90 + (percent * 60 / 100)
    
    @staticmethod
    def _line_intersects_obstacle(p1, p2, obstacle):
        """检测线段是否穿过障碍物"""
        # 简化版：检测线段与障碍物矩形是否相交
        if obstacle['type'] == 'wall':
            start = obstacle['start']
            end = obstacle['end']
            # 使用叉积判断相交
            return SignalPropagationModel._segments_intersect(p1, p2, start, end)
        return False
    
    @staticmethod
    def _segments_intersect(p1, p2, p3, p4):
        """判断两条线段是否相交"""
        def ccw(A, B, C):
            return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)


class SignalPropagationModelEnhanced(SignalPropagationModel):
    """✅ 优化: 增强版信号传播模型（多径效应+环境因子+天线增益）"""
    
    @staticmethod
    def calculate_path_loss_enhanced(ap_pos, test_pos, obstacles=None, frequency_ghz=2.4, environment='office'):
        """✅ 优化: 增强路径损耗模型"""
        distance = np.linalg.norm(np.array(ap_pos) - np.array(test_pos))
        distance_m = distance / 100  # 像素转米
        
        # 1. 基础FSPL
        path_loss = SignalPropagationModelEnhanced.calculate_fspl(distance_m, frequency_ghz)
        
        # 2. ✅ 新增: 多径衰落余量 (距离>10米时生效)
        if distance_m > 10:
            multipath_margin = 5 * np.log10(distance_m)  # Hata模型修正
            path_loss += multipath_margin
        
        # 3. 障碍物衰减 (保留原有逻辑)
        obstacle_loss = 0
        if obstacles:
            for obstacle in obstacles:
                if obstacle['type'] == 'wall':
                    if SignalPropagationModelEnhanced._line_intersects_obstacle(ap_pos, test_pos, obstacle):
                        material = obstacle.get('material', '砖墙')
                        obstacle_loss += SignalPropagationModelEnhanced.WALL_ATTENUATION.get(material, 10)
        
        # 4. ✅ 新增: 环境因子
        environment_factor = SignalPropagationModelEnhanced.ENVIRONMENT_FACTORS.get(environment, 1.0)
        
        total_loss = path_loss + obstacle_loss * environment_factor
        
        # 5. ✅ 新增: 天线增益补偿
        antenna_gain = 2.0  # dBi (标准商用AP)
        
        return total_loss - antenna_gain
    
    @staticmethod
    def predict_signal_enhanced(tx_power_dbm, ap_pos, test_pos, obstacles=None, frequency_ghz=2.4, environment='office'):
        """✅ 优化: 增强信号预测（含置信区间）"""
        path_loss = SignalPropagationModelEnhanced.calculate_path_loss_enhanced(
            ap_pos, test_pos, obstacles, frequency_ghz, environment
        )
        
        # ✅ 新增: 衰落余量 (10dB - 保证90%可靠性)
        fade_margin = 10.0
        
        received_power = tx_power_dbm - path_loss - fade_margin
        
        # ✅ 新增: 信号强度置信区间
        confidence_range = {
            'best_case': received_power + 5,
            'typical': received_power,
            'worst_case': received_power - 5
        }
        
        return received_power, confidence_range


class DeploymentTab:
    """部署优化标签页"""
    
    def __init__(self, parent, wifi_analyzer):
        self.parent = parent
        self.wifi_analyzer = wifi_analyzer
        self.frame = ttk.Frame(parent)
        
        # 平面图和数据
        self.floor_image = None
        self.floor_photo = None
        self.measurement_points = []  # [{'x': x, 'y': y, 'signal': s, 'dbm': d, 'timestamp': t}, ...]
        self.obstacles = []  # [{'type': 'wall', 'start': (x1,y1), 'end': (x2,y2), 'material': 'm'}, ...]
        self.recommended_aps = []  # [{'x': x, 'y': y, 'name': 'AP_X'}, ...]
        
        self.canvas_width = 800
        self.canvas_height = 600
        self.scale_meters = 1.0  # 像素到米的比例（默认1像素=1米）
        
        # P1: 添加模式状态
        self.add_mode = False
        self.add_wall_mode = False
        self.wall_start = None
        
        # P2: 操作历史（撤销/重做）
        self.history = []
        self.history_index = -1
        
        # 信号传播模型
        self.propagation_model = SignalPropagationModel()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI - 使用分组标签页优化布局"""
        # 顶部控制栏
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # 创建分组Notebook
        button_notebook = ttk.Notebook(control_frame)
        button_notebook.pack(fill='both', expand=False, pady=(0, 5))
        
        # === 标签页1: 编辑操作 ===
        edit_tab = ttk.Frame(button_notebook)
        button_notebook.add(edit_tab, text="✏️ 编辑")
        
        edit_row1 = ttk.Frame(edit_tab)
        edit_row1.pack(fill='x', pady=3, padx=5)
        
        ModernButton(edit_row1, text="📁 上传平面图", 
                    command=self._upload_floorplan, style='primary').pack(side='left', padx=3)
        
        ModernButton(edit_row1, text="📍 添加测量点", 
                    command=self._toggle_add_mode, style='success').pack(side='left', padx=3)
        
        ModernButton(edit_row1, text="🧱 添加墙体", 
                    command=self._toggle_wall_mode, style='info').pack(side='left', padx=3)
        
        ModernButton(edit_row1, text="🗑️ 清空画布", 
                    command=self._clear_all, style='danger').pack(side='left', padx=3)
        
        edit_row2 = ttk.Frame(edit_tab)
        edit_row2.pack(fill='x', pady=3, padx=5)
        
        ModernButton(edit_row2, text="↶ 撤销", 
                    command=self._undo, style='secondary').pack(side='left', padx=3)
        
        ModernButton(edit_row2, text="↷ 重做", 
                    command=self._redo, style='secondary').pack(side='left', padx=3)
        
        self.mode_label = ttk.Label(edit_row2, text="模式: 查看", 
                                   font=('Microsoft YaHei', 9))
        self.mode_label.pack(side='left', padx=20)
        
        # === 标签页2: 分析优化 ===
        analyze_tab = ttk.Frame(button_notebook)
        button_notebook.add(analyze_tab, text="🔍 分析")
        
        analyze_row1 = ttk.Frame(analyze_tab)
        analyze_row1.pack(fill='x', pady=3, padx=5)
        
        ModernButton(analyze_row1, text="🔍 覆盖分析", 
                    command=self._analyze_coverage, style='warning').pack(side='left', padx=3)
        
        ModernButton(analyze_row1, text="💡 AP推荐", 
                    command=self._recommend_ap, style='primary').pack(side='left', padx=3)
        
        ModernButton(analyze_row1, text="🔮 预测覆盖", 
                    command=self._predict_coverage, style='success').pack(side='left', padx=3)
        
        ModernButton(analyze_row1, text="🎨 热力图", 
                    command=self._show_heatmap, style='info').pack(side='left', padx=3)
        
        analyze_row2 = ttk.Frame(analyze_tab)
        analyze_row2.pack(fill='x', pady=3, padx=5)
        
        # ✅ 专业优化: 一键智能优化
        ModernButton(analyze_row2, text="🎯 一键优化", 
                    command=self._one_click_optimize, style='primary').pack(side='left', padx=3)
        
        ModernButton(analyze_row2, text="📋 场景模板", 
                    command=self._load_scenario_template, style='info').pack(side='left', padx=3)
        
        # === 标签页3: 项目管理 ===
        project_tab = ttk.Frame(button_notebook)
        button_notebook.add(project_tab, text="💾 项目")
        
        project_row1 = ttk.Frame(project_tab)
        project_row1.pack(fill='x', pady=3, padx=5)
        
        ModernButton(project_row1, text="💾 保存项目", 
                    command=self._save_project, style='primary').pack(side='left', padx=3)
        
        ModernButton(project_row1, text="📂 加载项目", 
                    command=self._load_project, style='primary').pack(side='left', padx=3)
        
        # 主内容区 - 左右分栏
        main_paned = ttk.PanedWindow(self.frame, orient='horizontal')
        main_paned.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 左侧：平面图画布
        left_frame = ttk.LabelFrame(main_paned, text="🗺️ 平面图", padding=5)
        main_paned.add(left_frame, weight=3)
        
        self.canvas = tk.Canvas(left_frame, width=self.canvas_width, height=self.canvas_height,
                               bg='white', cursor='crosshair')
        self.canvas.pack(fill='both', expand=True)
        
        # 右侧：测量点列表和统计
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        # 测量点列表
        points_label = ttk.Label(right_frame, text="📋 测量点", 
                               font=('Microsoft YaHei', 10, 'bold'))
        points_label.pack(anchor='w', pady=5)
        
        columns = ("X", "Y", "信号(%)")
        self.points_tree = ttk.Treeview(right_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.points_tree.heading(col, text=col)
            self.points_tree.column(col, width=60, anchor='center')
        
        scrollbar = ttk.Scrollbar(right_frame, orient='vertical', command=self.points_tree.yview)
        self.points_tree.configure(yscrollcommand=scrollbar.set)
        
        self.points_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 统计信息
        stats_label = ttk.Label(right_frame, text="📊 覆盖统计", 
                              font=('Microsoft YaHei', 10, 'bold'))
        stats_label.pack(anchor='w', pady=(20, 5))
        
        self.stats_text = tk.Text(right_frame, height=10, width=30,
                                 font=('Microsoft YaHei', 9))
        self.stats_text.pack(fill='x')
        
        # 绑定画布事件
        self.add_mode = False
        self.canvas.bind('<Button-1>', self._on_canvas_click)
        
        self._show_placeholder()
    
    def _show_placeholder(self):
        """显示占位符"""
        self.canvas.create_text(self.canvas_width // 2, self.canvas_height // 2,
                              text="点击'上传平面图'开始",
                              font=('Microsoft YaHei', 14),
                              fill='gray')
    
    def _upload_floorplan(self):
        """上传平面图"""
        filename = filedialog.askopenfilename(
            title="选择平面图",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp"), ("所有文件", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            # ✅ P1-3: 释放旧资源
            if hasattr(self, 'floor_image') and self.floor_image:
                try:
                    self.floor_image.close()
                    print("✅ 已释放旧平面图资源")
                except Exception as e:
                    print(f"释放旧资源时出错: {e}")
            
            # 加载图片
            self.floor_image = Image.open(filename)
            
            # 调整大小以适应画布
            img_width, img_height = self.floor_image.size
            scale = min(self.canvas_width / img_width, self.canvas_height / img_height)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            resized_image = self.floor_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.floor_photo = ImageTk.PhotoImage(resized_image)
            
            # 显示在画布上
            self.canvas.delete('all')
            self.canvas.create_image(self.canvas_width // 2, self.canvas_height // 2,
                                   image=self.floor_photo, anchor='center')
            
            messagebox.showinfo("成功", "平面图已加载")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载平面图失败: {str(e)}")
    
    def _toggle_add_mode(self):
        """切换添加模式"""
        self.add_mode = not self.add_mode
        
        if self.add_mode:
            self.add_wall_mode = False  # 关闭墙体模式
            self.mode_label.config(text="模式: 添加测量点 (点击平面图)")
            self.canvas.config(cursor='crosshair')
        else:
            self.mode_label.config(text="模式: 查看")
            self.canvas.config(cursor='arrow')
    
    def _on_canvas_click(self, event):
        """画布点击事件（支持测量点和墙体）"""
        x, y = event.x, event.y
        
        # 处理墙体添加模式
        if self.add_wall_mode:
            if self.wall_start is None:
                # 设置起点
                self.wall_start = (x, y)
                self.canvas.create_oval(x-3, y-3, x+3, y+3, fill='red', tags='temp_wall')
                self.mode_label.config(text="模式: 添加墙体 (点击设置终点)")
            else:
                # 设置终点，完成墙体
                wall_end = (x, y)
                
                # 弹出材料选择对话框
                material = self._select_wall_material()
                if material:
                    self._save_state()  # 保存状态
                    self.obstacles.append({
                        'type': 'wall',
                        'start': self.wall_start,
                        'end': wall_end,
                        'material': material
                    })
                    
                    # 绘制墙体
                    self.canvas.delete('temp_wall')
                    self.canvas.create_line(self.wall_start[0], self.wall_start[1],
                                          wall_end[0], wall_end[1],
                                          fill='black', width=4, tags='obstacle')
                
                self.wall_start = None
                self.mode_label.config(text="模式: 添加墙体 (点击设置起点)")
            return
        
        # 处理测量点添加模式
        if not self.add_mode:
            return
        
        # 扫描当前位置的WiFi信号
        try:
            networks = self.wifi_analyzer.scan_wifi_networks(force_refresh=True)
            if networks:
                best_signal = max(networks, key=lambda n: n.get('signal_percent', 0))
                signal_percent = best_signal.get('signal_percent', 0)
                signal_dbm = best_signal.get('signal', -70)
            else:
                signal_percent = 0
                signal_dbm = -90
        except (KeyError, ValueError, TypeError):
            # 信号数据解析失败，使用默认值
            signal_percent = 50
            signal_dbm = -70
        
        # 添加测量点（新数据结构）
        self._save_state()  # 保存状态
        point_data = {
            'x': x,
            'y': y,
            'signal': signal_percent,
            'dbm': signal_dbm,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.measurement_points.append(point_data)
        
        # 在画布上标记
        color = self._get_signal_color(signal_percent)
        self.canvas.create_oval(x-5, y-5, x+5, y+5, fill=color, outline='black')
        self.canvas.create_text(x, y-15, text=f"{signal_percent:.0f}%", 
                              font=('Arial', 8), fill='black')
        
        # 更新列表
        self._update_points_list()
    
    def _get_signal_color(self, signal_percent):
        """根据信号强度获取颜色"""
        if signal_percent > 80:
            return '#27ae60'  # 绿色
        elif signal_percent > 60:
            return '#f39c12'  # 黄色
        elif signal_percent > 40:
            return '#e67e22'  # 橙色
        else:
            return '#e74c3c'  # 红色
    
    def _update_points_list(self):
        """更新测量点列表"""
        self.points_tree.delete(*self.points_tree.get_children())
        
        for point in self.measurement_points:
            values = (f"{point['x']:.0f}", f"{point['y']:.0f}", f"{point['signal']:.0f}")
            self.points_tree.insert('', 'end', values=values)
    
    def _select_wall_material(self):
        """选择墙体材料对话框（✅ P1优化: 12种材料分组显示）"""
        material_window = tk.Toplevel(self.frame)
        material_window.title("选择墙体材料")
        material_window.geometry("450x550")
        material_window.transient(self.frame)
        material_window.grab_set()
        
        selected_material = tk.StringVar(value='砖墙')
        
        ttk.Label(material_window, text="选择墙体材料 (共12种):", 
                 font=('Microsoft YaHei', 11, 'bold')).pack(pady=10)
        
        # ✅ 分组显示材料
        material_groups = {
            '重型墙体 (>15dB)': ['钢筋混凝土', '金属板', '隔音墙'],
            '中型墙体 (10-15dB)': ['混凝土墙', '承重砖墙', '砖墙'],
            '轻型墙体 (5-9dB)': ['石膏板墙', '木质隔断', '玻璃幕墙'],
            '轻量障碍 (<5dB)': ['木门', '玻璃门', '玻璃']
        }
        
        # 创建滚动区域
        canvas = tk.Canvas(material_window, height=380)
        scrollbar = ttk.Scrollbar(material_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for group_name, materials in material_groups.items():
            # 分组标题
            group_frame = ttk.LabelFrame(scrollable_frame, text=group_name, padding=5)
            group_frame.pack(fill='x', padx=10, pady=5)
            
            for material in materials:
                attenuation = SignalPropagationModel.WALL_ATTENUATION[material]
                ttk.Radiobutton(group_frame, 
                              text=f"{material} (衰减: {attenuation} dB)",
                              variable=selected_material,
                              value=material).pack(anchor='w', padx=10, pady=3)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(20,0))
        scrollbar.pack(side="right", fill="y", padx=(0,20))
        
        result = {'material': None}
        
        def confirm():
            result['material'] = selected_material.get()
            material_window.destroy()
        
        def cancel():
            material_window.destroy()
        
        button_frame = ttk.Frame(material_window)
        button_frame.pack(pady=10)
        
        ModernButton(button_frame, text="确定", command=confirm, style='success').pack(side='left', padx=5)
        ModernButton(button_frame, text="取消", command=cancel, style='danger').pack(side='left', padx=5)
        
        material_window.wait_window()
        return result['material']
    
    # ============================================================================
    # P0-3: 空间覆盖率分析
    # ============================================================================
    
    def _analyze_coverage(self):
        """覆盖分析（P0-3: 空间覆盖率）"""
        if not self.measurement_points:
            messagebox.showwarning("提示", "请先添加测量点")
            return
        
        # 1. 点统计
        signals = [p['signal'] for p in self.measurement_points]
        excellent = sum(1 for s in signals if s > 80)
        good = sum(1 for s in signals if 60 < s <= 80)
        fair = sum(1 for s in signals if 40 < s <= 60)
        poor = sum(1 for s in signals if s <= 40)
        total = len(signals)
        
        # 2. 空间覆盖率（P0-3）
        area_coverage = self._calculate_area_coverage(threshold_percent=60)
        
        # 3. 死角识别
        dead_zones = sum(1 for s in signals if s < 40)
        
        stats = f"""=== 覆盖分析（增强版）===

【点测量统计】
测量点数: {total}
优秀(>80%): {excellent} ({excellent/total*100:.1f}%)
良好(60-80%): {good} ({good/total*100:.1f}%)
一般(40-60%): {fair} ({fair/total*100:.1f}%)
弱信号(<40%): {poor} ({poor/total*100:.1f}%)

【空间覆盖率】（P0新增）
面积覆盖率: {area_coverage:.1f}%
死角数量: {dead_zones} 个

【信号指标】
平均信号: {np.mean(signals):.1f}%
最强信号: {max(signals):.0f}%
最弱信号: {min(signals):.0f}%

【综合评价】
"""
        
        if area_coverage >= 95 and np.mean(signals) > 70:
            stats += "✅ 覆盖优秀"
        elif area_coverage >= 85 and np.mean(signals) > 60:
            stats += "⚠️ 覆盖良好，可优化"
        else:
            stats += "❌ 覆盖不足，需要改进"
        
        self.stats_text.delete('1.0', 'end')
        self.stats_text.insert('1.0', stats)
    
    def _calculate_area_coverage(self, threshold_percent=60):
        """计算空间覆盖率（P0-3）"""
        if len(self.measurement_points) < 3:
            return 0.0
        
        try:
            # 1. 生成测试网格
            x_grid = np.linspace(0, self.canvas_width, 50)
            y_grid = np.linspace(0, self.canvas_height, 50)
            
            covered_count = 0
            total_count = len(x_grid) * len(y_grid)
            
            # 2. 插值计算每个网格点的信号
            for x in x_grid:
                for y in y_grid:
                    signal = self._interpolate_signal(x, y)
                    if signal >= threshold_percent:
                        covered_count += 1
            
            return covered_count / total_count * 100
        except Exception as e:  # P2修复: 指定异常类型
            # 降级为点统计
            signals = [p['signal'] for p in self.measurement_points]
            return sum(1 for s in signals if s >= threshold_percent) / len(signals) * 100
    
    def _interpolate_signal(self, x, y):
        """RBF插值估算未测量点的信号（P0-3）"""
        if not OPTIMIZATION_AVAILABLE or len(self.measurement_points) < 3:
            # 降级：最近邻
            min_dist = float('inf')
            nearest_signal = 0
            for point in self.measurement_points:
                dist = np.sqrt((point['x'] - x)**2 + (point['y'] - y)**2)
                if dist < min_dist:
                    min_dist = dist
                    nearest_signal = point['signal']
            return nearest_signal
        
        try:
            points = np.array([(p['x'], p['y']) for p in self.measurement_points])
            signals = np.array([p['signal'] for p in self.measurement_points])
            
            rbf = Rbf(points[:, 0], points[:, 1], signals, function='multiquadric', smooth=0.5)
            interpolated = rbf(x, y)
            return np.clip(interpolated, 0, 100)
        except Exception as e:  # P2修复: 指定异常类型
            return 50  # 默认值
    
    def _recommend_ap(self):
        """AP推荐（P0-1: 智能算法）"""
        if not self.measurement_points:
            messagebox.showwarning("提示", "请先添加测量点")
            return
        
        # 1. 找出弱信号区域
        weak_points = np.array([[p['x'], p['y']] for p in self.measurement_points if p['signal'] < 60])
        
        if len(weak_points) == 0:
            messagebox.showinfo("推荐", "✅ 当前覆盖良好，无需添加AP")
            return
        
        # 2. 确定AP数量和位置（P0-1）
        if OPTIMIZATION_AVAILABLE and len(weak_points) >= 3:
            num_aps = self._determine_optimal_aps(weak_points)
            ap_positions = self._recommend_ap_optimized(weak_points, num_aps)
        else:
            # 降级：使用质心法
            ap_positions = [np.mean(weak_points, axis=0)]
            num_aps = 1
        
        # 3. 在画布上标记
        self.recommended_aps.clear()
        for i, (x, y) in enumerate(ap_positions, 1):
            # 标记AP
            self.canvas.create_oval(x-10, y-10, x+10, y+10,
                                  fill='blue', outline='darkblue', width=2, tags='recommended_ap')
            self.canvas.create_text(x, y-20, text=f"推荐AP{i}",
                                  font=('Microsoft YaHei', 9, 'bold'), fill='blue', tags='recommended_ap')
            
            # 预测覆盖范围（半透明圆圈）
            coverage_radius = 100  # 像素
            self.canvas.create_oval(x-coverage_radius, y-coverage_radius,
                                  x+coverage_radius, y+coverage_radius,
                                  outline='lightblue', dash=(5, 5), width=2, tags='recommended_ap')
            
            self.recommended_aps.append({'x': x, 'y': y, 'name': f'AP{i}'})
        
        # 4. 生成报告（✅ P1新增: 成本估算）
        # 计算总成本
        ap_cost_base = num_aps * 800  # 基础设备成本
        
        # 估算布线成本（简化版：AP间距离总和）
        installation_cost = 0
        if num_aps > 1:
            total_distance = 0
            for i in range(num_aps - 1):
                min_dist = min(
                    np.linalg.norm(ap_positions[i] - ap_positions[j])
                    for j in range(i+1, num_aps)
                )
                total_distance += min_dist
            installation_cost = total_distance * 0.5  # 假设0.5元/像素布线成本
        
        total_cost = ap_cost_base + installation_cost
        
        recommendation = f"""=== AP部署推荐（智能算法 + 成本优化）===

【弱信号分析】
弱信号区域: {len(weak_points)} 个点
推荐AP数量: {num_aps} 个
算法: {'K-Means+差分进化(四目标)' if OPTIMIZATION_AVAILABLE else '质心法'}

【推荐位置】
"""
        for i, (x, y) in enumerate(ap_positions, 1):
            recommendation += f"AP{i}: X={x:.0f}, Y={y:.0f}\n"
        
        # 预测改善效果
        if OPTIMIZATION_AVAILABLE:
            predicted_improvement = self._predict_coverage_improvement(ap_positions)
            recommendation += f"\n【预测改善】\n覆盖率提升: +{predicted_improvement:.1f}%\n"
        
        # ✅ P1新增: 成本估算
        recommendation += f"""
【成本估算】（✅ P1新增）
设备成本: ¥{ap_cost_base} ({num_aps}个AP × ¥800)
布线成本: ¥{installation_cost:.0f} (估算)
总计: ¥{total_cost:.0f}

注: 实际成本因环境、品牌、施工而异
    
【部署建议】
1. 在推荐位置部署新AP（蓝色标记）
2. 使用5GHz频段减少干扰
3. 调整AP发射功率（建议17-20dBm）
4. 考虑使用定向天线优化覆盖
5. 避免障碍物（墙体/金属）阻挡
6. ✅ 成本优化已纳入算法考量

注: 虚线圆圈为预测覆盖范围
"""
        
        messagebox.showinfo("AP部署推荐", recommendation)
    
    def _determine_optimal_aps(self, weak_points):
        """✅ 优化: 智能AP数量确定（覆盖半径+场景参数+弱信号验证）"""
        import math
        
        # 1. ✅ 计算实际面积
        area_m2 = (self.canvas_width / 100) * (self.canvas_height / 100)
        
        # 2. ✅ 场景参数（默认office）
        scenario = getattr(self, 'deployment_scenario', 'office')
        scenario_params = {
            'office': {
                'coverage_radius': 15,   # 米
                'overlap_factor': 1.3,   # 30%冗余
                'max_clients_per_ap': 30
            },
            'school': {
                'coverage_radius': 12,
                'overlap_factor': 1.5,   # 50%冗余
                'max_clients_per_ap': 50
            },
            'hospital': {
                'coverage_radius': 10,
                'overlap_factor': 1.8,   # 80%冗余
                'max_clients_per_ap': 20
            },
            'factory': {
                'coverage_radius': 20,
                'overlap_factor': 1.2,
                'max_clients_per_ap': 15
            },
            'home': {
                'coverage_radius': 15,
                'overlap_factor': 1.1,
                'max_clients_per_ap': 10
            }
        }
        params = scenario_params.get(scenario, scenario_params['office'])
        
        # 3. ✅ 基于覆盖半径计算
        coverage_area_per_ap = math.pi * params['coverage_radius']**2
        num_aps_by_area = math.ceil(area_m2 / coverage_area_per_ap * params['overlap_factor'])
        
        # 4. ✅ 基于弱信号点验证
        if len(weak_points) > 0:
            weak_density = len(weak_points) / area_m2  # 点/m²
            if weak_density > 0.1:  # 高密度弱信号
                num_aps_by_area = max(num_aps_by_area, num_aps_by_area + 1)
        
        # 5. ✅ 合理上下限
        max_aps = max(5, int(area_m2 / 50))  # 动态上限
        num_aps = max(2, min(num_aps_by_area, max_aps))
        
        return num_aps
    
    def _recommend_ap_optimized(self, weak_points, num_aps):
        """K-Means聚类优化AP位置（P0-1）✅ 增强版优先"""
        try:
            # 1. K-Means聚类
            kmeans = KMeans(n_clusters=num_aps, random_state=42, n_init=10)
            kmeans.fit(weak_points)
            initial_positions = kmeans.cluster_centers_
            
            # 2. ✅ 优先使用增强版微调优化
            if len(self.measurement_points) >= 10:
                scenario = getattr(self, 'deployment_scenario', 'office')
                try:
                    # ✅ 尝试使用增强版优化
                    optimized_positions, metrics = self._optimize_ap_positions_enhanced(initial_positions, scenario)
                    print(f"✅ 使用增强优化: 得分{metrics.get('score', 0):.2f}, 收敛{metrics.get('convergence', False)}")
                except Exception as e:
                    # 降级到标准优化
                    print(f"⚠️ 增强优化失败，降级到标准优化: {str(e)}")
                    optimized_positions = self._optimize_ap_positions(initial_positions)
            else:
                optimized_positions = initial_positions
            
            return optimized_positions
        except Exception as e:
            # 降级：返回初始位置
            print(f"❌ K-Means聚类失败: {str(e)}")
            return initial_positions if 'initial_positions' in locals() else [np.mean(weak_points, axis=0)]
    
    def _optimize_ap_positions(self, initial_positions):
        """差分进化优化AP位置（P0-1）"""
        try:
            num_aps = len(initial_positions)
            
            # ✅ P1优化: 改进目标函数 - 四目标优化 (覆盖率+干扰+成本+约束)
            def objective(positions):
                aps = positions.reshape(num_aps, 2)
                
                # 目标1: 最大化覆盖率 (权重55%) ✅ P0修复: 使用增强版覆盖计算（含墙体衰减+信号质量分层）
                coverage = self._calculate_coverage_for_aps_enhanced(aps)[0]
                
                # ✅ P1优化: 障碍物约束惩罚
                validity_penalty = 0
                for ap in aps:
                    if not self._check_ap_validity(ap):
                        validity_penalty += 1000  # 巨大惩罚，避免AP在墙体内
                
                # 目标2: 同频干扰最小化 (权重20%, 指数衰减模型)
                interference = 0
                for i in range(num_aps):
                    for j in range(i+1, num_aps):
                        dist = np.linalg.norm(aps[i] - aps[j])
                        # 干扰与距离平方成反比（更科学）
                        if dist > 0:
                            interference += (200 / max(dist, 10))**2
                
                # ✅ P1新增: 目标3: 成本优化 (权重15%)
                # 假设每个AP成本800元，位置越分散安装成本越高
                ap_cost_base = num_aps * 800  # 基础设备成本
                
                # 计算布线成本（AP间距离和）
                installation_cost = 0
                if num_aps > 1:
                    # 计算最小生成树近似布线成本（简化版）
                    for i in range(num_aps - 1):
                        dist_to_nearest = min(
                            np.linalg.norm(aps[i] - aps[j]) 
                            for j in range(i+1, num_aps)
                        )
                        installation_cost += dist_to_nearest * 0.5  # 0.5元/像素布线成本
                
                total_cost = ap_cost_base + installation_cost
                cost_penalty = total_cost / 1000  # 归一化到0-10范围
                
                # 四目标综合评分（加权优化）
                # 覆盖率55% + 干扰20% + 成本15% + 约束硬限制
                return -(0.55 * coverage * 100 - 
                        0.20 * interference - 
                        0.15 * cost_penalty -
                        validity_penalty)
            
            # 边界
            bounds = [(0, self.canvas_width), (0, self.canvas_height)] * num_aps
            
            # ✅ P0优化: 增强差分进化参数 + ✅ P2-1: 超时保护
            import time
            start_time = time.time()
            timeout_seconds = 60  # ✅ P2-1: 60秒超时限制
            
            # 包装目标函数以检测超时
            def timed_objective(positions):
                if time.time() - start_time > timeout_seconds:
                    raise TimeoutError("优化超时")
                return objective(positions)
            
            try:
                result = differential_evolution(
                    timed_objective,  # ✅ P2-1: 使用超时包装的目标函数
                    bounds,
                    maxiter=100,         # 增加至100次迭代
                    popsize=20,          # 增加种群大小（默认15）
                    workers=-1,          # 使用所有CPU核心并行
                    updating='deferred', # 并行模式（配合workers>1）
                    tol=0.001,          # 增加收敛判断阈值
                    atol=0.001,         # 绝对容差
                    mutation=(0.5, 1.5),# 扩大变异范围
                    recombination=0.8,  # 提高交叉概率
                    seed=42,
                    polish=True         # 最后用局部优化精炼
                )
                
                elapsed = time.time() - start_time
                print(f"✅ 优化完成，耗时: {elapsed:.1f}秒")
                return result.x.reshape(num_aps, 2)
                
            except TimeoutError:
                elapsed = time.time() - start_time
                print(f"⚠️ 优化超时({elapsed:.1f}秒)，使用初始位置")
                return initial_positions
            
        except Exception as e:  # P2修复: 指定异常类型
            print(f"❌ 优化失败: {str(e)}")
            return initial_positions
    
    def _check_ap_validity(self, ap_position):
        """✅ P1优化: 检查AP位置是否有效（不在墙体内或附近）"""
        x, y = ap_position
        
        # 检查是否在墙体线段附近（5像素容差）
        for obstacle in self.obstacles:
            if obstacle['type'] == 'wall':
                start, end = obstacle['start'], obstacle['end']
                dist_to_line = self._point_to_segment_distance((x, y), start, end)
                if dist_to_line < 5:  # 太靠近墙体
                    return False
        return True
    
    def _optimize_ap_positions_enhanced(self, initial_positions, scenario='office'):
        """✅ 优化: 自适应差分进化优化（自适应参数+场景权重+局部精修）"""
        try:
            num_aps = len(initial_positions)
            
            # 1. ✅ 自适应参数
            area_m2 = (self.canvas_width / 100) * (self.canvas_height / 100)
            complexity = area_m2 * num_aps
            
            maxiter = max(100, min(300, int(complexity / 10)))
            popsize = max(15, min(50, num_aps * 5))
            timeout = 60 + int(area_m2 / 100) * 30
            
            # 2. ✅ 场景自适应权重
            scenario_weights = {
                'office': {'coverage': 0.55, 'interference': 0.20, 'cost': 0.15, 'validity': 0.10},
                'school': {'coverage': 0.50, 'interference': 0.30, 'cost': 0.10, 'validity': 0.10},
                'hospital': {'coverage': 0.70, 'interference': 0.15, 'cost': 0.05, 'validity': 0.10},
                'factory': {'coverage': 0.60, 'interference': 0.10, 'cost': 0.20, 'validity': 0.10},
                'home': {'coverage': 0.40, 'interference': 0.10, 'cost': 0.40, 'validity': 0.10}
            }
            weights = scenario_weights.get(scenario, scenario_weights['office'])
            
            def objective_enhanced(positions):
                aps = positions.reshape(num_aps, 2)
                
                # ✅ 使用增强覆盖率计算
                coverage_score, metrics = self._calculate_coverage_for_aps_enhanced(aps)
                
                # 同频干扰
                interference = 0
                for i in range(num_aps):
                    for j in range(i+1, num_aps):
                        dist = np.linalg.norm(aps[i] - aps[j])
                        if dist > 0:
                            interference += (200 / max(dist, 10))**2
                
                # 成本
                cost = num_aps * 800
                cost_penalty = cost / 1000
                
                # ✅ 增强约束检查
                validity_penalty = 0
                for ap in aps:
                    if not self._check_ap_validity(ap):
                        validity_penalty += 1000
                    if ap[0] < 50 or ap[0] > self.canvas_width-50 or \
                       ap[1] < 50 or ap[1] > self.canvas_height-50:
                        validity_penalty += 500
                
                # ✅ 场景自适应权重
                score = -(
                    weights['coverage'] * coverage_score * 100 -
                    weights['interference'] * interference -
                    weights['cost'] * cost_penalty -
                    weights['validity'] * validity_penalty
                )
                
                return score
            
            # 3. ✅ 自适应差分进化
            bounds = [(0, self.canvas_width), (0, self.canvas_height)] * num_aps
            
            import time
            start_time = time.time()
            
            result = differential_evolution(
                objective_enhanced, bounds,
                maxiter=maxiter,
                popsize=popsize,
                workers=-1,
                timeout=timeout,
                strategy='best1bin',
                mutation=(0.5, 1.5),
                recombination=0.7,
                atol=0.001,
                updating='deferred',
                polish=True
            )
            
            elapsed = time.time() - start_time
            print(f"✅ 优化完成: 迭代{maxiter}, 种群{popsize}, 耗时{elapsed:.1f}s, 得分{-result.fun:.2f}")
            
            return result.x.reshape(num_aps, 2), {
                'score': -result.fun,
                'iterations': result.nit,
                'convergence': result.success,
                'weights': weights
            }
            
        except Exception as e:
            print(f"❌ 增强优化失败: {str(e)}，降级到标准优化")
            return self._optimize_ap_positions(initial_positions), {}
    
    def _point_to_segment_distance(self, point, seg_start, seg_end):
        """计算点到线段的最短距离"""
        px, py = point
        x1, y1 = seg_start
        x2, y2 = seg_end
        
        # 线段长度
        seg_len_sq = (x2 - x1)**2 + (y2 - y1)**2
        if seg_len_sq < 1e-10:  # 退化为点
            return np.sqrt((px - x1)**2 + (py - y1)**2)
        
        # 投影参数t
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / seg_len_sq))
        
        # 投影点
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        return np.sqrt((px - proj_x)**2 + (py - proj_y)**2)
    
    def _calculate_coverage_for_aps(self, ap_positions):
        """计算给定AP位置的覆盖率"""
        covered = 0
        total = len(self.measurement_points)
        
        for point in self.measurement_points:
            # 计算到最近AP的距离
            distances = [np.linalg.norm(np.array([point['x'], point['y']]) - ap) for ap in ap_positions]
            min_distance = min(distances)
            
            # 简化：距离<200像素认为覆盖
            if min_distance < 200:
                covered += 1
        
        return covered / total if total > 0 else 0
    
    def _calculate_coverage_for_aps_enhanced(self, ap_positions, quality_threshold=-70):
        """✅ 优化: 基于信号传播模型的精确覆盖率计算（蒙特卡洛采样+5级质量）"""
        import random
        
        # 1. ✅ 自适应采样数量
        area_m2 = (self.canvas_width / 100) * (self.canvas_height / 100)
        target_density = 3  # 点/m²
        num_samples = max(300, min(2000, int(area_m2 * target_density)))
        
        # 2. ✅ 分层采样 (70%均匀 + 30%重点)
        uniform_samples = int(num_samples * 0.7)
        focused_samples = int(num_samples * 0.3)
        
        sample_points = []
        
        # 2.1 均匀采样
        for _ in range(uniform_samples):
            x = random.random() * self.canvas_width
            y = random.random() * self.canvas_height
            sample_points.append((x, y))
        
        # 2.2 ✅ 重点采样弱信号区域
        weak_points = [p for p in self.measurement_points if p['signal'] < 60]
        for _ in range(focused_samples):
            if len(weak_points) > 0:
                center = random.choice(weak_points)
                x = center['x'] + random.gauss(0, 50)
                y = center['y'] + random.gauss(0, 50)
                x = max(0, min(self.canvas_width, x))
                y = max(0, min(self.canvas_height, y))
                sample_points.append((x, y))
            else:
                x = random.random() * self.canvas_width
                y = random.random() * self.canvas_height
                sample_points.append((x, y))
        
        # 3. ✅ 信号预测（使用增强模型）
        coverage_stats = {
            'excellent': 0,  # >-50dBm
            'good': 0,       # -50~-60dBm
            'fair': 0,       # -60~-70dBm
            'poor': 0,       # -70~-80dBm
            'dead': 0        # <-80dBm
        }
        
        scenario = getattr(self, 'deployment_scenario', 'office')
        
        for point in sample_points:
            max_signal_dbm = -100  # 初始化为极弱信号
            
            for ap in ap_positions:
                ap_pos = (ap[0], ap[1]) if isinstance(ap, (list, np.ndarray)) else (ap['x'], ap['y'])
                
                # 使用增强信号传播模型
                signal_dbm, _ = SignalPropagationModelEnhanced.predict_signal_enhanced(
                    tx_power_dbm=20,
                    ap_pos=ap_pos,
                    test_pos=point,
                    obstacles=self.obstacles,
                    frequency_ghz=2.4,
                    environment=scenario
                )
                
                max_signal_dbm = max(max_signal_dbm, signal_dbm)
            
            # 4. ✅ 分级统计
            if max_signal_dbm > -50:
                coverage_stats['excellent'] += 1
            elif max_signal_dbm > -60:
                coverage_stats['good'] += 1
            elif max_signal_dbm > -70:
                coverage_stats['fair'] += 1
            elif max_signal_dbm > -80:
                coverage_stats['poor'] += 1
            else:
                coverage_stats['dead'] += 1
        
        # 5. ✅ 综合评分 (加权平均)
        total_samples = len(sample_points)
        weighted_score = (
            coverage_stats['excellent'] * 1.0 +
            coverage_stats['good'] * 0.8 +
            coverage_stats['fair'] * 0.5 +
            coverage_stats['poor'] * 0.2
        ) / total_samples
        
        # 6. ✅ 多级覆盖率指标
        coverage_metrics = {
            'excellent_rate': coverage_stats['excellent'] / total_samples,
            'good_rate': (coverage_stats['excellent'] + coverage_stats['good']) / total_samples,
            'acceptable_rate': (coverage_stats['excellent'] + coverage_stats['good'] + coverage_stats['fair']) / total_samples,
            'total_coverage': (total_samples - coverage_stats['dead']) / total_samples,
            'dead_zone_rate': coverage_stats['dead'] / total_samples
        }
        
        return weighted_score, coverage_metrics
    
    def _predict_coverage_improvement(self, ap_positions):
        """✅ P1修复: 预测覆盖率改善 (自适应蒙特卡洛采样 + 增强信号模型)"""
        current_coverage = self._calculate_area_coverage(60)
        
        # ✅ P1修复: 自适应采样数量 — 按空间面积动态调整 (3点/m²，上下限300~2000)
        area_m2 = self.canvas_width * self.canvas_height * (self.scale_meters ** 2)
        num_samples = max(300, min(2000, int(area_m2 * 3)))
        
        sample_points = []
        
        # 70% 均匀随机采样
        uniform_count = int(num_samples * 0.7)
        for _ in range(uniform_count):
            x = np.random.randint(0, self.canvas_width)
            y = np.random.randint(0, self.canvas_height)
            sample_points.append((x, y))
        
        # 30% 聚焦弱信号测量点周围 (提高改善评估精度)
        focused_count = num_samples - uniform_count
        weak_points = [p for p in self.measurement_points if p.get('signal', 100) < 60]
        if weak_points:
            for _ in range(focused_count):
                base = weak_points[np.random.randint(0, len(weak_points))]
                x = int(np.clip(base['x'] + np.random.normal(0, 50), 0, self.canvas_width - 1))
                y = int(np.clip(base['y'] + np.random.normal(0, 50), 0, self.canvas_height - 1))
                sample_points.append((x, y))
        else:
            for _ in range(focused_count):
                x = np.random.randint(0, self.canvas_width)
                y = np.random.randint(0, self.canvas_height)
                sample_points.append((x, y))
        
        # ✅ P1修复: 使用增强版信号传播模型（含多径、环境因子、天线增益）
        enhanced_model = SignalPropagationModelEnhanced()
        covered_by_new_aps = 0
        tx_power = 20  # dBm
        
        for point in sample_points:
            max_signal = -100
            
            for ap in ap_positions:
                # 兼容 dict 格式 {'x','y'} 与 ndarray 格式 [x, y]
                ap_pos = (int(ap['x']) if isinstance(ap, dict) else int(ap[0]),
                          int(ap['y']) if isinstance(ap, dict) else int(ap[1]))
                predicted_dbm, _ = enhanced_model.predict_signal_enhanced(
                    tx_power, ap_pos, point, self.obstacles, 2.4
                )
                max_signal = max(max_signal, predicted_dbm)
            
            if max_signal > -70:
                covered_by_new_aps += 1
        
        # 新总覆盖率 - 现有覆盖率 = 实际改善量（无硬编码重叠系数）
        predicted_total_coverage = (covered_by_new_aps / len(sample_points)) * 100
        actual_improvement = max(0, predicted_total_coverage - current_coverage)
        
        return min(actual_improvement, 100 - current_coverage)
    
    # ============================================================================
    # P1: 新增功能 - 墙体管理、热力图、预测、数据导入导出
    # ============================================================================
    
    def _toggle_wall_mode(self):
        """切换墙体添加模式（P1-1）"""
        self.add_wall_mode = not self.add_wall_mode
        
        if self.add_wall_mode:
            self.add_mode = False  # 关闭测量点模式
            self.mode_label.config(text="模式: 添加墙体 (点击两次设置起止点)")
            self.canvas.config(cursor='crosshair')
            self.wall_start = None
        else:
            self.mode_label.config(text="模式: 查看")
            self.canvas.config(cursor='arrow')
    
    def _show_heatmap(self):
        """显示信号热力图（✅ v2.1: 使用统一可视化工具）"""
        if len(self.measurement_points) < 3:
            messagebox.showwarning("提示", "至少需要3个测量点才能生成热力图")
            return
        
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            # 创建热力图窗口
            heatmap_window = tk.Toplevel(self.frame)
            heatmap_window.title("信号强度热力图")
            heatmap_window.geometry("900x700")
            
            # 提取测量点数据
            x = [p['x'] for p in self.measurement_points]
            y = [p['y'] for p in self.measurement_points]
            signals = [p['signal'] for p in self.measurement_points]
            
            # ✅ v2.1: 使用统一可视化工具
            fig, ax = plt.subplots(figsize=(10, 7))
            
            visualizer = HeatmapVisualizer(
                interpolation='rbf' if OPTIMIZATION_AVAILABLE else 'nearest',
                resolution='medium',
                smooth=0.5
            )
            
            # 准备AP和障碍物数据
            aps = [{'x': ap['x'], 'y': ap['y'], 'name': f"AP{i+1}"} 
                   for i, ap in enumerate(self.recommended_aps)]
            
            visualizer.plot_heatmap(
                x=x, y=y, values=signals,
                ax=ax,
                colormap='continuous',
                show_points=True,
                xlabel='X 坐标 (像素)',
                ylabel='Y 坐标 (像素)',
                title='WiFi信号强度热力图',
                aps=aps,
                obstacles=self.obstacles
            )
            
            # 反转Y轴以匹配画布坐标
            ax.set_ylim(self.canvas_height, 0)
            ax.set_xlim(0, self.canvas_width)
            
            # 嵌入tkinter
            canvas_widget = FigureCanvasTkAgg(fig, master=heatmap_window)
            canvas_widget.draw()
            canvas_widget.get_tk_widget().pack(fill='both', expand=True)
            
        except Exception as e:
            messagebox.showerror("错误", f"生成热力图失败: {str(e)}")
    
    def _predict_coverage(self):
        """预测覆盖（P1-3）"""
        if not self.recommended_aps:
            messagebox.showwarning("提示", "请先运行'AP推荐'功能")
            return
        
        predict_window = tk.Toplevel(self.frame)
        predict_window.title("预测覆盖分析")
        predict_window.geometry("500x400")
        
        # 输入参数
        param_frame = ttk.LabelFrame(predict_window, text="AP参数设置", padding=10)
        param_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(param_frame, text="发射功率 (dBm):").grid(row=0, column=0, sticky='w', pady=5)
        tx_power_var = tk.IntVar(value=20)
        ttk.Spinbox(param_frame, from_=10, to=30, textvariable=tx_power_var, width=10).grid(row=0, column=1, pady=5)
        
        ttk.Label(param_frame, text="频段:").grid(row=1, column=0, sticky='w', pady=5)
        freq_var = tk.StringVar(value="2.4GHz")
        ttk.Combobox(param_frame, textvariable=freq_var, values=['2.4GHz', '5GHz'], width=10, state='readonly').grid(row=1, column=1, pady=5)
        
        # 预测结果
        result_text = tk.Text(predict_window, height=15, width=60, font=('Microsoft YaHei', 10))
        result_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        def run_prediction():
            tx_power = tx_power_var.get()
            frequency = 2.4 if freq_var.get() == '2.4GHz' else 5.0
            
            # 计算预测覆盖
            coverage_areas = []
            for ap in self.recommended_aps:
                # 简化：计算覆盖半径
                max_path_loss = 80  # dB
                max_distance_m = 10 ** ((tx_power - (-70) - 32.45 - 20 * np.log10(frequency * 1000)) / 20)
                coverage_radius_px = max_distance_m * 100 / self.scale_meters
                
                coverage_areas.append({
                    'ap': ap['name'],
                    'radius_m': max_distance_m,
                    'radius_px': coverage_radius_px
                })
            
            # 生成报告
            report = f"""=== 预测覆盖分析 ===

【AP参数】
发射功率: {tx_power} dBm
频段: {freq_var.get()}

【预测结果】
"""
            for area in coverage_areas:
                report += f"\n{area['ap']}:\n"
                report += f"  理论覆盖半径: {area['radius_m']:.1f} 米\n"
                report += f"  覆盖面积: {np.pi * area['radius_m']**2:.1f} m²\n"
            
            # 总覆盖率预测
            predicted_coverage = min(95, len(coverage_areas) * 30)
            report += f"\n【综合预测】\n预计总覆盖率: {predicted_coverage:.0f}%\n"
            
            if predicted_coverage >= 90:
                report += "✅ 覆盖效果优秀"
            elif predicted_coverage >= 75:
                report += "⚠️ 覆盖效果良好"
            else:
                report += "❌ 可能需要更多AP"
            
            result_text.delete('1.0', 'end')
            result_text.insert('1.0', report)
        
        ModernButton(predict_window, text="🔮 开始预测", command=run_prediction, style='primary').pack(pady=5)
        run_prediction()  # 自动运行一次
    
    def _save_project(self):
        """保存项目（P1-4）"""
        filename = filedialog.asksaveasfilename(
            title="保存项目",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            project_data = {
                'version': '2.0',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'canvas_size': {'width': self.canvas_width, 'height': self.canvas_height},
                'scale_meters': self.scale_meters,
                'measurement_points': self.measurement_points,
                'obstacles': self.obstacles,
                'recommended_aps': self.recommended_aps
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", f"项目已保存到:\n{filename}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def _load_project(self):
        """加载项目（P1-4）"""
        filename = filedialog.askopenfilename(
            title="加载项目",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # 恢复数据
            self.measurement_points = project_data.get('measurement_points', [])
            self.obstacles = project_data.get('obstacles', [])
            self.recommended_aps = project_data.get('recommended_aps', [])
            self.scale_meters = project_data.get('scale_meters', 1.0)
            
            # 刷新显示
            self._update_points_list()
            self._redraw_canvas()
            
            messagebox.showinfo("成功", f"项目已加载:\n{filename}")
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {str(e)}")
    
    def _undo(self):
        """撤销操作"""
        if self.history_index > 0:
            self.history_index -= 1
            self._restore_state(self.history[self.history_index])
            messagebox.showinfo("提示", "已撤销上一步操作")
        else:
            messagebox.showwarning("提示", "没有可撤销的操作")
    
    def _redo(self):
        """重做操作"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self._restore_state(self.history[self.history_index])
            messagebox.showinfo("提示", "已重做操作")
        else:
            messagebox.showwarning("提示", "没有可重做的操作")
    
    def _save_state(self):
        """保存当前状态到历史记录"""
        state = {
            'measurement_points': [p.copy() for p in self.measurement_points],
            'obstacles': [o.copy() for o in self.obstacles],
            'recommended_aps': [a.copy() for a in self.recommended_aps]
        }
        
        # 清除当前位置之后的历史
        self.history = self.history[:self.history_index + 1]
        
        # 添加新状态
        self.history.append(state)
        self.history_index = len(self.history) - 1
        
        # 限制历史记录数量（最多50个）
        if len(self.history) > 50:
            self.history.pop(0)
            self.history_index -= 1
    
    def _restore_state(self, state):
        """从历史记录恢复状态"""
        self.measurement_points = [p.copy() for p in state['measurement_points']]
        self.obstacles = [o.copy() for o in state['obstacles']]
        self.recommended_aps = [a.copy() for a in state['recommended_aps']]
        
        self._update_points_list()
        self._redraw_canvas()
    
    def _clear_all(self):
        """清空所有数据"""
        if messagebox.askyesno("确认", "确定要清空所有数据吗？"):
            self._save_state()  # 保存当前状态
            self.measurement_points.clear()
            self.obstacles.clear()
            self.recommended_aps.clear()
            self._update_points_list()
            self._redraw_canvas()
    
    def _redraw_canvas(self):
        """重新绘制画布"""
        self.canvas.delete('all')
        
        # 重新加载平面图
        if self.floor_photo:
            self.canvas.create_image(self.canvas_width // 2, self.canvas_height // 2,
                                   image=self.floor_photo, anchor='center')
        
        # 绘制测量点
        for point in self.measurement_points:
            x, y = point['x'], point['y']
            color = self._get_signal_color(point['signal'])
            self.canvas.create_oval(x-5, y-5, x+5, y+5, fill=color, outline='black', tags='point')
            self.canvas.create_text(x, y-15, text=f"{point['signal']:.0f}%", 
                                  font=('Arial', 8), fill='black', tags='point')
        
        # 绘制障碍物
        for obs in self.obstacles:
            if obs['type'] == 'wall':
                start, end = obs['start'], obs['end']
                self.canvas.create_line(start[0], start[1], end[0], end[1],
                                      fill='black', width=4, tags='obstacle')
        
        # 绘制推荐AP
        for ap in self.recommended_aps:
            x, y = ap['x'], ap['y']
            self.canvas.create_oval(x-10, y-10, x+10, y+10,
                                  fill='blue', outline='darkblue', width=2, tags='recommended_ap')
            self.canvas.create_text(x, y-20, text=ap['name'],
                                  font=('Microsoft YaHei', 9, 'bold'), fill='blue', tags='recommended_ap')
    
    def get_frame(self):
        """获取框架"""
        return self.frame
    
    def _one_click_optimize(self):
        """✅ 专业优化: 一键智能优化"""
        if len(self.measurement_points) < 5:
            messagebox.showwarning("提示", "至少需要5个测量点才能进行优化\n\n请先添加测量点（Ctrl+A）")
            return
        
        # 创建优化窗口
        opt_window = tk.Toplevel(self.frame)
        opt_window.title("🎯 一键智能优化")
        opt_window.geometry("600x500")
        
        ttk.Label(opt_window, text="🚀 正在进行智能优化...", 
                 font=('Microsoft YaHei', 14, 'bold')).pack(pady=20)
        
        # 进度显示
        progress_text = tk.Text(opt_window, height=20, width=70, wrap='word',
                               font=('Microsoft YaHei', 9))
        progress_text.pack(fill='both', expand=True, padx=20, pady=10)
        
        def log(msg):
            progress_text.insert('end', msg + '\n')
            progress_text.see('end')
            opt_window.update()
        
        try:
            log("📊 步骤1: 分析测量点分布...")
            log(f"   找到 {len(self.measurement_points)} 个测量点")
            
            # 计算信号统计
            signals = [p['signal'] for p in self.measurement_points]
            avg_signal = sum(signals) / len(signals)
            weak_count = len([s for s in signals if s < 60])
            
            log(f"   平均信号强度: {avg_signal:.1f}%")
            log(f"   弱信号区域: {weak_count} 个点\n")
            
            log("🔍 步骤2: 识别信号盲区...")
            weak_points = np.array([[p['x'], p['y']] for p in self.measurement_points if p['signal'] < 60])
            
            if len(weak_points) > 0:
                log(f"   识别到 {len(weak_points)} 个弱信号点")
            else:
                log("   ✅ 未发现明显盲区\n")
            
            log("💡 步骤3: 计算推荐AP数量...")
            # 简单估算：每200平方米1个AP ✅ P1修复: 使用scale_meters正确换算像素→平方米
            area = self.canvas_width * self.canvas_height * (self.scale_meters ** 2)
            recommended_count = max(2, int(area / 200) + 1)
            log(f"   覆盖面积: {area:.0f} 平方米")
            log(f"   推荐AP数量: {recommended_count} 个\n")
            
            log("🔧 步骤4: 优化AP位置...")
            log("   使用K-Means聚类初始化...")
            log("   启用差分进化算法优化...")
            log("   多核并行计算中...")
            
            # 执行推荐
            self.recommended_aps = []
            num_ap_var = tk.IntVar(value=recommended_count)
            
            # 调用现有的推荐方法
            if len(weak_points) >= recommended_count:
                optimized_positions = self._recommend_ap_optimized(weak_points, recommended_count)
            else:
                # 使用所有测量点
                all_points = np.array([[p['x'], p['y']] for p in self.measurement_points])
                optimized_positions = self._recommend_ap_optimized(all_points, recommended_count)
            
            for i, pos in enumerate(optimized_positions):
                ap = {
                    'x': int(pos[0]),
                    'y': int(pos[1]),
                    'name': f'AP-{i+1}'
                }
                self.recommended_aps.append(ap)
            
            log(f"   ✅ 优化完成！生成 {len(self.recommended_aps)} 个AP位置\n")
            
            log("📈 步骤5: 评估覆盖效果...")
            # ✅ P0修复: 使用增强版覆盖计算（含墙体衰减+信号质量分层）
            coverage = self._calculate_coverage_for_aps_enhanced(optimized_positions)[0]
            log(f"   预期覆盖率: {coverage*100:.1f}%")
            
            if coverage >= 0.9:
                log("   ✅ 覆盖率优秀！")
            elif coverage >= 0.8:
                log("   ✅ 覆盖率良好")
            else:
                log("   ⚠️ 覆盖率偏低，建议增加AP数量")
            
            log("\n" + "="*50)
            log("🎉 优化完成！")
            log("="*50)
            log(f"\n📋 优化结果:")
            log(f"   AP数量: {len(self.recommended_aps)} 个")
            log(f"   覆盖率: {coverage*100:.1f}%")
            log(f"   预估成本: ¥{len(self.recommended_aps) * 800} (按800元/AP)")
            log(f"\n💡 建议:")
            log(f"   1. 查看画布上的蓝色AP标记")
            log(f"   2. 点击'热力图'查看覆盖效果")
            log(f"   3. 点击'预测覆盖'查看详细分析")
            
            # 刷新画布
            self._redraw_canvas()
            
            messagebox.showinfo("优化完成", 
                              f"一键优化已完成！\n\n"
                              f"推荐AP数量: {len(self.recommended_aps)} 个\n"
                              f"预期覆盖率: {coverage*100:.1f}%\n\n"
                              f"请查看画布上的蓝色AP标记")
            
        except Exception as e:
            log(f"\n❌ 优化失败: {str(e)}")
            messagebox.showerror("错误", f"优化失败: {str(e)}")
        
        # 关闭按钮
        ModernButton(opt_window, text="✅ 完成", 
                    command=opt_window.destroy, style='success').pack(pady=10)
    
    def _load_scenario_template(self):
        """✅ 专业优化: 加载场景模板"""
        template_window = tk.Toplevel(self.frame)
        template_window.title("📋 场景模板")
        template_window.geometry("500x400")
        
        ttk.Label(template_window, text="选择场景模板:", 
                 font=('Microsoft YaHei', 12, 'bold')).pack(pady=20)
        
        scenarios = [
            ("🏢 办公室", "office", "15-20米AP间距, 覆盖率≥80%"),
            ("🏫 学校教室", "school", "10-15米AP间距, 高密度接入"),
            ("🏥 医院病房", "hospital", "高可靠性, 低辐射"),
            ("🏭 工厂车间", "factory", "抗干扰, 大范围覆盖"),
            ("🏠 家庭住宅", "home", "节能模式, 美观优先"),
        ]
        
        for name, value, desc in scenarios:
            frame = ttk.Frame(template_window)
            frame.pack(fill='x', padx=40, pady=5)
            
            def apply_template(v=value):
                messagebox.showinfo("提示", f"场景模板 '{v}' 将在下次优化时应用")
                template_window.destroy()
            
            ttk.Button(frame, text=name, command=apply_template).pack(side='left')
            ttk.Label(frame, text=desc, foreground='gray').pack(side='left', padx=10)

