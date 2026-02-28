"""
主题和UI工具类
提供现代化的界面主题和自定义组件
"""

import tkinter as tk
from tkinter import ttk

class ModernTheme:
    """现代化主题配色方案 - 企业增强版"""
    
    LIGHT = {
        'bg': '#f8f9fa',           # 更柔和的背景色
        'fg': '#2c3e50',           # 深色文字
        'primary': '#4a90e2',      # 主色调 - 现代蓝
        'primary_dark': '#357abd', # 主色调深色
        'secondary': '#95a5a6',    # 次要色
        'success': '#2ecc71',      # 成功绿色
        'warning': '#f39c12',      # 警告橙色
        'danger': '#e74c3c',       # 危险红色
        'info': '#3498db',         # 信息蓝色
        'card_bg': '#ffffff',      # 卡片背景
        'card_shadow': '#e0e0e0',  # 卡片阴影
        'border': '#dee2e6',       # 边框色
        'hover': '#e9ecef',        # 悬停色
        'input_bg': '#ffffff',     # 输入框背景
        'input_border': '#ced4da', # 输入框边框
        'text_muted': '#6c757d',   # 次要文字
        'gradient_start': '#667eea',# 渐变起始
        'gradient_end': '#764ba2'   # 渐变结束
    }
    
    DARK = {
        'bg': '#1a1d23',           # 深色背景
        'fg': '#e4e6eb',           # 浅色文字
        'primary': '#5dade2',      # 主色调
        'primary_dark': '#3498db', # 主色调深色
        'secondary': '#7f8c8d',    # 次要色
        'success': '#27ae60',      # 成功绿色
        'warning': '#f39c12',      # 警告橙色
        'danger': '#e74c3c',       # 危险红色
        'info': '#3498db',         # 信息蓝色
        'card_bg': '#242830',      # 卡片背景
        'card_shadow': '#0d0f12',  # 卡片阴影
        'border': '#3a3f4b',       # 边框色
        'hover': '#2d3139',        # 悬停色
        'input_bg': '#2d3139',     # 输入框背景
        'input_border': '#3a3f4b', # 输入框边框
        'text_muted': '#8b92a0',   # 次要文字
        'gradient_start': '#667eea',# 渐变起始
        'gradient_end': '#764ba2'   # 渐变结束
    }
    
    # 🏢 企业商务蓝主题 - 专业、稳重、信赖
    ENTERPRISE_BLUE = {
        'bg': '#f5f7fa',           # 浅灰蓝背景
        'fg': '#1e3a5f',           # 深蓝文字
        'primary': '#0066cc',      # IBM蓝/企业蓝
        'primary_dark': '#004a99', # 深企业蓝
        'secondary': '#6c7a89',    # 商务灰
        'success': '#00a86b',      # 商务绿
        'warning': '#ff8c00',      # 商务橙
        'danger': '#cc0000',       # 商务红
        'info': '#0099cc',         # 信息蓝
        'card_bg': '#ffffff',      # 纯白卡片
        'card_shadow': '#d1d9e6',  # 蓝灰阴影
        'border': '#c5d0de',       # 蓝灰边框
        'hover': '#e8eef5',        # 浅蓝悬停
        'input_bg': '#ffffff',     # 白色输入框
        'input_border': '#b8c5d6', # 蓝灰边框
        'text_muted': '#5a6c7d',   # 灰蓝文字
        'gradient_start': '#0066cc',# 企业蓝渐变
        'gradient_end': '#003d7a'   # 深蓝渐变
    }
    
    # 🏢 企业专业灰主题 - 简约、高端、专注
    ENTERPRISE_GRAY = {
        'bg': '#f4f5f7',           # 浅灰背景
        'fg': '#2d3436',           # 深灰文字
        'primary': '#555555',      # 中性灰
        'primary_dark': '#333333', # 深灰
        'secondary': '#74788d',    # 蓝灰
        'success': '#28a745',      # 绿色
        'warning': '#fd7e14',      # 橙色
        'danger': '#dc3545',       # 红色
        'info': '#17a2b8',         # 青色
        'card_bg': '#ffffff',      # 纯白卡片
        'card_shadow': '#dfe3e8',  # 灰色阴影
        'border': '#d4d9df',       # 浅灰边框
        'hover': '#e9ecef',        # 浅灰悬停
        'input_bg': '#ffffff',     # 白色输入框
        'input_border': '#ced4da', # 灰色边框
        'text_muted': '#6c757d',   # 次要灰色
        'gradient_start': '#555555',# 灰色渐变
        'gradient_end': '#2d3436'   # 深灰渐变
    }
    
    # 🏢 企业科技黑主题 - 现代、科技、专业
    ENTERPRISE_TECH = {
        'bg': '#0d1117',           # 深黑背景
        'fg': '#c9d1d9',           # 浅灰文字
        'primary': '#00d4ff',      # 科技蓝
        'primary_dark': '#00a8cc', # 深科技蓝
        'secondary': '#8b949e',    # 灰色
        'success': '#00ff9f',      # 荧光绿
        'warning': '#ffcc00',      # 警示黄
        'danger': '#ff3366',       # 荧光红
        'info': '#58a6ff',         # 亮蓝
        'card_bg': '#161b22',      # 深灰卡片
        'card_shadow': '#010409',  # 纯黑阴影
        'border': '#30363d',       # 深灰边框
        'hover': '#21262d',        # 悬停深灰
        'input_bg': '#0d1117',     # 黑色输入框
        'input_border': '#30363d', # 深灰边框
        'text_muted': '#8b949e',   # 次要灰色
        'gradient_start': '#00d4ff',# 科技蓝渐变
        'gradient_end': '#0066ff'   # 蓝色渐变
    }
    
    # 🏢 企业金融主题 - 稳健、权威、高端
    ENTERPRISE_FINANCE = {
        'bg': '#fafbfc',           # 极浅灰背景
        'fg': '#24292e',           # 近黑文字
        'primary': '#1a5490',      # 深蓝（金融色）
        'primary_dark': '#0e3a66', # 深海军蓝
        'secondary': '#586069',    # 深灰
        'success': '#1e7e34',      # 深绿（稳健）
        'warning': '#c67a00',      # 金色
        'danger': '#b31d28',       # 深红
        'info': '#0969da',         # 金融蓝
        'card_bg': '#ffffff',      # 纯白卡片
        'card_shadow': '#e1e4e8',  # 浅灰阴影
        'border': '#d0d7de',       # 边框灰
        'hover': '#f3f4f6',        # 极浅灰悬停
        'input_bg': '#ffffff',     # 白色输入框
        'input_border': '#d0d7de', # 灰色边框
        'text_muted': '#57606a',   # 次要文字
        'gradient_start': '#1a5490',# 金融蓝渐变
        'gradient_end': '#0e3a66'   # 深蓝渐变
    }
    
    # 🏢 企业医疗主题 - 清洁、可靠、专业
    ENTERPRISE_MEDICAL = {
        'bg': '#f8f9fc',           # 医疗白背景
        'fg': '#1f2937',           # 深灰文字
        'primary': '#0284c7',      # 医疗蓝
        'primary_dark': '#075985', # 深医疗蓝
        'secondary': '#64748b',    # 中性灰
        'success': '#059669',      # 医疗绿
        'warning': '#ea580c',      # 医疗橙
        'danger': '#dc2626',       # 医疗红
        'info': '#0ea5e9',         # 信息蓝
        'card_bg': '#ffffff',      # 纯白卡片
        'card_shadow': '#e5e7eb',  # 浅灰阴影
        'border': '#d1d5db',       # 灰色边框
        'hover': '#f0f4f8',        # 浅蓝悬停
        'input_bg': '#ffffff',     # 白色输入框
        'input_border': '#cbd5e1', # 灰蓝边框
        'text_muted': '#6b7280',   # 次要文字
        'gradient_start': '#0284c7',# 医疗蓝渐变
        'gradient_end': '#0369a1'   # 深医疗蓝渐变
    }
    
    # 主题名称映射
    THEME_NAMES = {
        'light': '浅色经典',
        'dark': '深色经典',
        'enterprise_blue': '🏢 商务蓝',
        'enterprise_gray': '🏢 专业灰',
        'enterprise_tech': '🏢 科技黑',
        'enterprise_finance': '🏢 金融版',
        'enterprise_medical': '🏢 医疗版'
    }
    
    @classmethod
    def get_theme(cls, theme_name='light'):
        """获取主题配色"""
        theme_map = {
            'dark': cls.DARK,
            'enterprise_blue': cls.ENTERPRISE_BLUE,
            'enterprise_gray': cls.ENTERPRISE_GRAY,
            'enterprise_tech': cls.ENTERPRISE_TECH,
            'enterprise_finance': cls.ENTERPRISE_FINANCE,
            'enterprise_medical': cls.ENTERPRISE_MEDICAL
        }
        return theme_map.get(theme_name.lower(), cls.LIGHT)
    
    @classmethod
    def get_all_themes(cls):
        """获取所有可用主题列表"""
        return list(cls.THEME_NAMES.keys())
    
    @classmethod
    def get_theme_display_name(cls, theme_name):
        """获取主题显示名称"""
        return cls.THEME_NAMES.get(theme_name, theme_name)


class ModernButton(tk.Button):
    """现代化按钮组件 - 增强版（支持主题切换）"""
    
    def __init__(self, master, text="", command=None, style='primary', theme_name='light', **kwargs):
        # 获取主题色
        theme = ModernTheme.get_theme(theme_name)
        
        # 根据样式设置颜色
        style_colors = {
            'primary': theme['primary'],
            'success': theme['success'],
            'warning': theme['warning'],
            'danger': theme['danger'],
            'secondary': theme['secondary'],
            'info': theme['info']
        }
        
        bg_color = style_colors.get(style, theme['primary'])
        
        # 默认按钮配置 - 增强样式
        default_config = {
            'text': text,
            'command': command,
            'bg': bg_color,
            'fg': 'white',
            'activebackground': self._darken_color(bg_color),
            'activeforeground': 'white',
            'relief': 'flat',
            'borderwidth': 0,
            'padx': 12,              # 紧凑内边距（原20）
            'pady': 6,               # 紧凑内边距（原10）
            'font': ('Microsoft YaHei UI', 9, 'bold'),
            'cursor': 'hand2',
            'highlightthickness': 0
        }
        
        # 合并用户配置
        default_config.update(kwargs)
        
        super().__init__(master, **default_config)
        
        # 绑定悬停效果和点击效果
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)
        self.bind('<ButtonRelease-1>', self._on_release)
        
        self._original_bg = bg_color
        self._is_hover = False
    
    def _on_enter(self, event):
        """鼠标进入时 - 颜色加深"""
        self._is_hover = True
        self.config(bg=self._darken_color(self._original_bg, 0.15))
    
    def _on_leave(self, event):
        """鼠标离开时"""
        self._is_hover = False
        self.config(bg=self._original_bg)
    
    def _on_click(self, event):
        """点击时 - 颜色更深"""
        self.config(bg=self._darken_color(self._original_bg, 0.25))
    
    def _on_release(self, event):
        """释放时"""
        if self._is_hover:
            self.config(bg=self._darken_color(self._original_bg, 0.15))
        else:
            self.config(bg=self._original_bg)
    
    @staticmethod
    def _darken_color(color_hex, factor=0.2):
        """颜色加深效果 - 增强版支持自定义系数"""
        try:
            # 移除#号
            color_hex = color_hex.lstrip('#')
            
            # 转换为RGB
            r, g, b = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
            
            # 降低亮度（根据factor）
            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))
            
            return f'#{r:02x}{g:02x}{b:02x}'
        except (ValueError, AttributeError):
            # 颜色格式错误，返回原值
            return color_hex


class ModernCard(tk.Frame):
    """现代化卡片组件 - 带阴影效果（支持主题切换）"""
    
    def __init__(self, master, title="", theme_name='light', **kwargs):
        theme = ModernTheme.get_theme(theme_name)
        
        # 外层容器（用于阴影效果）
        shadow_config = {
            'bg': theme['card_shadow'],
            'relief': 'flat',
            'borderwidth': 0
        }
        shadow_config.update(kwargs)
        super().__init__(master, **shadow_config)
        
        # 内层卡片
        self.card = tk.Frame(self, bg=theme['card_bg'], relief='flat', borderwidth=0)
        self.card.pack(fill='both', expand=True, padx=2, pady=2)
        
        # 卡片标题（如果提供）
        if title:
            title_frame = tk.Frame(self.card, bg=theme['card_bg'])
            title_frame.pack(fill='x', padx=15, pady=(15, 5))
            
            tk.Label(title_frame, text=title, 
                    font=('Microsoft YaHei UI', 11, 'bold'),
                    bg=theme['card_bg'], fg=theme['fg']).pack(side='left')
            
            # 分隔线
            separator = tk.Frame(self.card, height=1, bg=theme['border'])
            separator.pack(fill='x', padx=15, pady=(5, 10))
        
        # 内容容器
        self.content = tk.Frame(self.card, bg=theme['card_bg'])
        self.content.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        # 添加别名以兼容不同命名习惯
        self.content_frame = self.content
    
    def get_content_frame(self):
        """获取内容框架"""
        return self.content


class ModernProgressBar(ttk.Progressbar):
    """现代化进度条"""
    
    def __init__(self, master, **kwargs):
        default_config = {
            'mode': 'indeterminate',
            'length': 200,
            'style': 'Modern.Horizontal.TProgressbar'
        }
        default_config.update(kwargs)
        super().__init__(master, **default_config)


class StatusBadge(tk.Label):
    """状态徽章组件（支持主题切换）"""
    
    def __init__(self, master, text="", status='info', theme_name='light', **kwargs):
        theme = ModernTheme.get_theme(theme_name)
        
        # 状态颜色映射
        status_colors = {
            'success': theme['success'],
            'warning': theme['warning'],
            'danger': theme['danger'],
            'info': theme['info'],
            'primary': theme['primary']
        }
        
        bg_color = status_colors.get(status, theme['info'])
        
        default_config = {
            'text': text,
            'bg': bg_color,
            'fg': 'white',
            'font': ('Microsoft YaHei UI', 8, 'bold'),
            'padx': 10,
            'pady': 4,
            'relief': 'flat',
            'borderwidth': 0
        }
        default_config.update(kwargs)
        
        super().__init__(master, **default_config)


class ModernTooltip:
    """现代化工具提示 - 增强版"""
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.delay_id = None
        
        # 绑定事件
        self.widget.bind('<Enter>', self._schedule_show)
        self.widget.bind('<Leave>', self._hide)
        self.widget.bind('<Button>', self._hide)
    
    def _schedule_show(self, event):
        """延迟显示提示"""
        self._cancel_schedule()
        self.delay_id = self.widget.after(500, lambda: self._show(event))
    
    def _cancel_schedule(self):
        """取消延迟显示"""
        if self.delay_id:
            self.widget.after_cancel(self.delay_id)
            self.delay_id = None
        self.widget.bind('<Button-1>', self._hide)
    
    def _show(self, event=None):
        """显示提示"""
        if self.tooltip_window or not self.text:
            return
        
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            tw,
            text=self.text,
            justify='left',
            background='#2c3e50',
            foreground='white',
            relief='solid',
            borderwidth=1,
            font=('Microsoft YaHei', 9),
            padx=8,
            pady=5
        )
        label.pack()
    
    def _hide(self, event=None):
        """隐藏提示"""
        self._cancel_schedule()
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def create_section_title(parent, text, icon="", theme_name='light'):
    """创建章节标题（支持主题切换）"""
    theme = ModernTheme.get_theme(theme_name)
    
    frame = tk.Frame(parent, bg=theme['bg'])
    frame.pack(fill='x', pady=(15, 10))
    
    # 左侧装饰条
    accent_bar = tk.Frame(frame, width=4, bg=theme['primary'])
    accent_bar.pack(side='left', fill='y', padx=(0, 10))
    
    # 标题文本
    title_text = f"{icon} {text}" if icon else text
    tk.Label(frame, text=title_text,
            font=('Microsoft YaHei UI', 12, 'bold'),
            bg=theme['bg'], fg=theme['fg']).pack(side='left')
    
    return frame


def create_info_label(parent, label_text, value_text="", icon="", theme_name='light'):
    """创建信息标签（支持主题切换）"""
    theme = ModernTheme.get_theme(theme_name)
    
    frame = tk.Frame(parent, bg=theme['card_bg'])
    
    # 图标（如果有）
    if icon:
        tk.Label(frame, text=icon, font=('Segoe UI Emoji', 14),
                bg=theme['card_bg']).pack(side='left', padx=(0, 8))
    
    # 标签文本
    tk.Label(frame, text=label_text,
            font=('Microsoft YaHei UI', 9),
            bg=theme['card_bg'], fg=theme['text_muted']).pack(side='left')
    
    # 值文本
    if value_text:
        tk.Label(frame, text=value_text,
                font=('Microsoft YaHei UI', 9, 'bold'),
                bg=theme['card_bg'], fg=theme['fg']).pack(side='left', padx=(5, 0))
    
    return frame


def apply_modern_style(root, theme_name='light'):
    """应用现代化样式到整个应用（支持主题切换）"""
    theme = ModernTheme.get_theme(theme_name)
    style = ttk.Style()
    
    # 使用clam主题作为基础
    style.theme_use('clam')
    
    # 配置Notebook样式
    style.configure('TNotebook', 
                   background=theme['bg'],
                   borderwidth=0)
    
    style.configure('TNotebook.Tab',
                   background=theme['card_bg'],
                   foreground=theme['fg'],
                   padding=[20, 12],
                   font=('Microsoft YaHei UI', 10),
                   borderwidth=0)
    
    style.map('TNotebook.Tab',
             background=[('selected', theme['primary']),
                        ('active', theme['hover'])],
             foreground=[('selected', 'white')])
    
    # 配置Frame样式
    style.configure('TFrame', background=theme['bg'])
    style.configure('Card.TFrame', background=theme['card_bg'])
    
    # 配置Label样式
    style.configure('TLabel',
                   background=theme['bg'],
                   foreground=theme['fg'],
                   font=('Microsoft YaHei UI', 9))
    
    style.configure('Title.TLabel',
                   font=('Microsoft YaHei UI', 12, 'bold'))
    
    style.configure('Subtitle.TLabel',
                   font=('Microsoft YaHei UI', 10))
    
    # 配置Button样式
    style.configure('TButton',
                   background=theme['primary'],
                   foreground='white',
                   borderwidth=0,
                   focuscolor='none',
                   font=('Microsoft YaHei UI', 9))
    
    # 配置Combobox样式
    style.configure('TCombobox',
                   fieldbackground=theme['input_bg'],
                   background=theme['input_bg'],
                   foreground=theme['fg'],
                   borderwidth=1,
                   relief='solid')
    
    # 配置Progress bar样式
    style.configure('Modern.Horizontal.TProgressbar',
                   background=theme['primary'],
                   troughcolor=theme['border'],
                   borderwidth=0,
                   thickness=8)
    
    # 配置Treeview样式
    style.configure('Treeview',
                   background=theme['card_bg'],
                   foreground=theme['fg'],
                   fieldbackground=theme['card_bg'],
                   borderwidth=0,
                   font=('Microsoft YaHei UI', 9))
    
    style.configure('Treeview.Heading',
                   background=theme['primary'],
                   foreground='white',
                   borderwidth=0,
                   font=('Microsoft YaHei UI', 9, 'bold'))
    
    style.map('Treeview',
             background=[('selected', theme['primary'])],
             foreground=[('selected', 'white')])
    
    return style
