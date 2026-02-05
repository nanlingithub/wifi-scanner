"""
UI工具函数库
提取重复的UI组件创建代码，提高代码复用性
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Optional, Callable, Tuple


def create_tree_widget(
    parent,
    columns: List[str],
    column_widths: Optional[Dict[str, int]] = None,
    show_headings: bool = True,
    height: int = 15,
    **kwargs
) -> ttk.Treeview:
    """创建标准化的树形控件
    
    Args:
        parent: 父容器
        columns: 列名列表
        column_widths: 列宽度字典 {列名: 宽度}
        show_headings: 是否显示列标题
        height: 树形控件高度
        **kwargs: 其他ttk.Treeview参数
    
    Returns:
        配置好的Treeview控件
    
    示例:
        tree = create_tree_widget(
            frame,
            ['SSID', 'Signal', 'Channel'],
            column_widths={'SSID': 200, 'Signal': 100}
        )
    """
    # 默认列宽
    if column_widths is None:
        column_widths = {}
    
    # 创建树形控件
    show_option = 'headings' if show_headings else 'tree'
    tree = ttk.Treeview(
        parent,
        columns=columns,
        show=show_option,
        height=height,
        **kwargs
    )
    
    # 配置列
    for col in columns:
        # 设置列标题
        tree.heading(col, text=col)
        
        # 设置列宽度
        width = column_widths.get(col, 100)  # 默认100像素
        tree.column(col, width=width, anchor='center')
    
    return tree


def create_scrollable_tree(
    parent,
    columns: List[str],
    column_widths: Optional[Dict[str, int]] = None,
    height: int = 15
) -> Tuple[ttk.Frame, ttk.Treeview]:
    """创建带滚动条的树形控件
    
    Args:
        parent: 父容器
        columns: 列名列表
        column_widths: 列宽度字典
        height: 树形控件高度
    
    Returns:
        (容器Frame, Treeview控件)
    
    示例:
        frame, tree = create_scrollable_tree(
            parent,
            ['SSID', 'BSSID', 'Signal']
        )
    """
    # 创建容器
    container = ttk.Frame(parent)
    
    # 创建树形控件
    tree = create_tree_widget(
        container,
        columns=columns,
        column_widths=column_widths,
        height=height
    )
    tree.pack(side='left', fill='both', expand=True)
    
    # 添加垂直滚动条
    vsb = ttk.Scrollbar(container, orient='vertical', command=tree.yview)
    vsb.pack(side='right', fill='y')
    tree.configure(yscrollcommand=vsb.set)
    
    # 添加水平滚动条
    hsb = ttk.Scrollbar(container, orient='horizontal', command=tree.xview)
    hsb.pack(side='bottom', fill='x')
    tree.configure(xscrollcommand=hsb.set)
    
    return container, tree


def populate_tree(
    tree: ttk.Treeview,
    data: List[Dict],
    columns: Optional[List[str]] = None,
    clear_first: bool = True
):
    """填充树形控件数据
    
    Args:
        tree: Treeview控件
        data: 数据列表，每项为字典
        columns: 列名顺序（如果None，使用tree的columns）
        clear_first: 是否先清空现有数据
    
    示例:
        populate_tree(tree, [
            {'ssid': 'WiFi-A', 'signal': -50},
            {'ssid': 'WiFi-B', 'signal': -60}
        ])
    """
    if clear_first:
        tree.delete(*tree.get_children())
    
    if columns is None:
        columns = tree['columns']
    
    for item in data:
        # 提取值，如果键不存在则用'N/A'
        values = [item.get(col, 'N/A') for col in columns]
        tree.insert('', 'end', values=values)


def create_label_value_pair(
    parent,
    label_text: str,
    value_text: str = '',
    label_width: int = 15,
    **kwargs
) -> Tuple[ttk.Label, ttk.Label]:
    """创建标签-值对组件
    
    Args:
        parent: 父容器
        label_text: 标签文本
        value_text: 值文本
        label_width: 标签宽度
        **kwargs: 其他Label参数
    
    Returns:
        (标签Label, 值Label)
    
    示例:
        label, value = create_label_value_pair(
            frame,
            "SSID:",
            "MyWiFi"
        )
    """
    label = ttk.Label(parent, text=label_text, width=label_width, **kwargs)
    value = ttk.Label(parent, text=value_text, **kwargs)
    
    return label, value


def create_button_group(
    parent,
    buttons: List[Dict],
    side: str = 'left',
    padding: int = 5
) -> List[tk.Button]:
    """创建按钮组
    
    Args:
        parent: 父容器
        buttons: 按钮配置列表，每项包含text, command等
        side: 布局方向
        padding: 按钮间距
    
    Returns:
        按钮列表
    
    示例:
        buttons = create_button_group(frame, [
            {'text': '扫描', 'command': scan_func},
            {'text': '停止', 'command': stop_func}
        ])
    """
    created_buttons = []
    
    for btn_config in buttons:
        btn = ttk.Button(parent, **btn_config)
        btn.pack(side=side, padx=padding)
        created_buttons.append(btn)
    
    return created_buttons


def create_combobox(
    parent,
    variable: tk.StringVar,
    values: List[str],
    default_value: Optional[str] = None,
    width: int = 20,
    state: str = 'readonly',
    on_change: Optional[Callable] = None,
    **kwargs
) -> ttk.Combobox:
    """创建下拉框
    
    Args:
        parent: 父容器
        variable: StringVar变量
        values: 选项列表
        default_value: 默认值
        width: 宽度
        state: 状态 ('readonly', 'normal')
        on_change: 选择变化回调函数
        **kwargs: 其他Combobox参数
    
    Returns:
        Combobox控件
    
    示例:
        var = tk.StringVar(value='全部')
        combo = create_combobox(
            frame,
            var,
            ['全部', '2.4GHz', '5GHz'],
            on_change=lambda e: print(var.get())
        )
    """
    combo = ttk.Combobox(
        parent,
        textvariable=variable,
        values=values,
        width=width,
        state=state,
        **kwargs
    )
    
    if default_value and default_value in values:
        variable.set(default_value)
    elif values:
        variable.set(values[0])
    
    if on_change:
        combo.bind('<<ComboboxSelected>>', on_change)
    
    return combo


def create_checkbutton_group(
    parent,
    options: List[Dict],
    side: str = 'left',
    padding: int = 5
) -> List[Tuple[ttk.Checkbutton, tk.BooleanVar]]:
    """创建复选框组
    
    Args:
        parent: 父容器
        options: 复选框配置列表，每项包含text, default等
        side: 布局方向
        padding: 间距
    
    Returns:
        [(Checkbutton, BooleanVar), ...]
    
    示例:
        checkboxes = create_checkbutton_group(frame, [
            {'text': '启用缓存', 'default': True},
            {'text': '自动刷新', 'default': False}
        ])
    """
    widgets = []
    
    for opt in options:
        var = tk.BooleanVar(value=opt.get('default', False))
        checkbutton = ttk.Checkbutton(
            parent,
            text=opt['text'],
            variable=var
        )
        checkbutton.pack(side=side, padx=padding)
        widgets.append((checkbutton, var))
    
    return widgets


def create_progress_window(
    title: str = '处理中',
    message: str = '请稍候...',
    maximum: int = 100
) -> Tuple[tk.Toplevel, ttk.Progressbar]:
    """创建进度条窗口
    
    Args:
        title: 窗口标题
        message: 提示信息
        maximum: 进度条最大值
    
    Returns:
        (窗口, 进度条)
    
    示例:
        window, progress = create_progress_window('扫描中')
        progress['value'] = 50
        window.update()
    """
    window = tk.Toplevel()
    window.title(title)
    window.geometry('400x100')
    window.transient()
    window.grab_set()
    
    # 提示信息
    ttk.Label(
        window,
        text=message,
        font=('Microsoft YaHei UI', 10)
    ).pack(pady=10)
    
    # 进度条
    progress = ttk.Progressbar(
        window,
        length=350,
        mode='determinate',
        maximum=maximum
    )
    progress.pack(pady=10)
    
    # 居中显示
    window.update_idletasks()
    x = (window.winfo_screenwidth() - window.winfo_width()) // 2
    y = (window.winfo_screenheight() - window.winfo_height()) // 2
    window.geometry(f'+{x}+{y}')
    
    return window, progress


def create_info_panel(
    parent,
    title: str,
    info_items: List[Tuple[str, str]],
    **kwargs
) -> ttk.LabelFrame:
    """创建信息面板
    
    Args:
        parent: 父容器
        title: 面板标题
        info_items: 信息项列表 [(标签, 值), ...]
        **kwargs: 其他LabelFrame参数
    
    Returns:
        LabelFrame控件
    
    示例:
        panel = create_info_panel(
            frame,
            '网络信息',
            [('SSID', 'MyWiFi'), ('信号', '-50 dBm')]
        )
    """
    panel = ttk.LabelFrame(parent, text=title, **kwargs)
    
    for i, (label_text, value_text) in enumerate(info_items):
        label, value = create_label_value_pair(
            panel,
            f'{label_text}:',
            value_text
        )
        label.grid(row=i, column=0, sticky='w', padx=5, pady=2)
        value.grid(row=i, column=1, sticky='w', padx=5, pady=2)
    
    return panel


def bind_tree_double_click(
    tree: ttk.Treeview,
    callback: Callable[[Dict], None],
    columns: Optional[List[str]] = None
):
    """为树形控件绑定双击事件
    
    Args:
        tree: Treeview控件
        callback: 双击回调函数，接收选中项数据字典
        columns: 列名列表（如果None，使用tree的columns）
    
    示例:
        def on_double_click(item):
            print(f"选中: {item}")
        
        bind_tree_double_click(tree, on_double_click)
    """
    if columns is None:
        columns = tree['columns']
    
    def handle_double_click(event):
        selection = tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        values = tree.item(item_id)['values']
        
        # 构建数据字典
        item_data = dict(zip(columns, values))
        callback(item_data)
    
    tree.bind('<Double-Button-1>', handle_double_click)


def create_status_label(
    parent,
    initial_text: str = '就绪',
    **kwargs
) -> ttk.Label:
    """创建状态标签（通常用于状态栏）
    
    Args:
        parent: 父容器
        initial_text: 初始文本
        **kwargs: 其他Label参数
    
    Returns:
        Label控件
    """
    label = ttk.Label(
        parent,
        text=initial_text,
        font=('Microsoft YaHei UI', 8),
        **kwargs
    )
    return label


# 便捷方法: 快速更新状态标签
def update_status(label: ttk.Label, text: str, color: str = 'black'):
    """更新状态标签
    
    Args:
        label: 状态标签
        text: 新文本
        color: 文字颜色
    """
    label.config(text=text, foreground=color)
