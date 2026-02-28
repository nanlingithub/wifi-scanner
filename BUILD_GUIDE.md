# WiFi专业工具 - EXE打包指南

## 📦 快速打包

### 一键打包（推荐）

直接运行打包脚本：

```batch
build_exe.bat
```

脚本将自动完成：
1. ✅ 检查Python环境
2. ✅ 安装PyInstaller（如未安装）
3. ✅ 清理旧构建文件
4. ✅ 执行打包流程
5. ✅ 复制配置文件
6. ✅ 创建启动脚本

### 手动打包

如需手动控制打包过程：

```batch
# 1. 安装PyInstaller
pip install pyinstaller

# 2. 执行打包
pyinstaller wifi_professional.spec --clean

# 3. 复制配置文件
copy config.json dist\WiFi专业工具\
```

---

## 📋 打包配置说明

### PyInstaller配置文件

**文件**: [wifi_professional.spec](wifi_professional.spec)

**关键配置**:

```python
# 单文件模式 vs 文件夹模式
onefile=False  # False=文件夹模式（推荐），True=单文件模式

# 控制台窗口
console=False  # False=无控制台（GUI应用），True=显示控制台（调试用）

# UPX压缩
upx=True  # 启用UPX压缩减小文件大小

# 隐藏导入模块
hiddenimports=[...]  # 手动指定需要打包的模块
```

### 依赖收集策略

程序会自动收集以下依赖：

1. **Python标准库**：tkinter, json, os, sys等
2. **第三方库**：matplotlib, numpy, pandas, reportlab等
3. **项目模块**：core/, wifi_modules/及所有子模块
4. **数据文件**：config.json, matplotlib字体数据等

---

## 🔧 常见问题解决

### 1. 打包失败：模块未找到

**问题**: `ModuleNotFoundError: No module named 'xxx'`

**解决方案**:
```python
# 在 wifi_professional.spec 的 hiddenimports 中添加缺失模块
hiddenimports = [
    # ... 现有模块
    'missing_module_name',  # 添加缺失模块
]
```

### 2. 打包后运行报错：缺少DLL

**问题**: `ImportError: DLL load failed`

**解决方案**:
```batch
# 重新安装依赖包
pip uninstall numpy scipy matplotlib
pip install numpy scipy matplotlib --no-cache-dir
```

### 3. 中文显示乱码

**问题**: GUI中中文显示为方块或乱码

**解决方案**:
- 确保系统已安装 **Microsoft YaHei** 或 **SimHei** 字体
- Windows 10/11 默认已安装，无需额外操作

### 4. 打包文件过大

**问题**: dist目录超过500MB

**优化方案**:

**方法1**: 排除不必要的库
```python
# 在 wifi_professional.spec 中
excludes=[
    'IPython', 'jupyter', 'notebook',  # 排除开发工具
    'pytest', 'unittest', 'test',      # 排除测试框架
    'sphinx', 'distutils',             # 排除文档工具
]
```

**方法2**: 使用单文件模式
```python
# 修改 wifi_professional.spec
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,      # 添加这些
    a.zipfiles,      # 添加这些
    a.datas,         # 添加这些
    [],
    name='WiFi专业工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    onefile=True,    # 启用单文件模式
)

# 注释掉 COLLECT 部分
# coll = COLLECT(...)
```

**方法3**: 启用更激进的UPX压缩
```batch
# 安装UPX (https://upx.github.io/)
# 在打包后手动压缩所有DLL文件
cd dist\WiFi专业工具
upx --best --lzma *.dll
```

### 5. 杀毒软件误报

**问题**: Windows Defender或其他杀毒软件报毒

**原因**: PyInstaller打包的exe常被误报为恶意软件

**解决方案**:
1. **添加信任**：在杀毒软件中添加为信任程序
2. **代码签名**：购买代码签名证书并签名exe
3. **换打包工具**：尝试 Nuitka (编译为C代码)

### 6. 首次运行慢

**问题**: 双击exe后需等待10-30秒才启动

**原因**: 
- 单文件模式需先解压到临时目录
- 大量Python库需要初始化

**优化方案**:
- 使用文件夹模式（默认）替代单文件模式
- 在SSD上运行程序
- 程序启动时添加启动画面提示

---

## 📊 打包结果

### 文件夹模式输出

```
dist/WiFi专业工具/
├── WiFi专业工具.exe          # 主程序 (~50KB)
├── python311.dll             # Python运行时 (~4MB)
├── _internal/                # 依赖库文件夹
│   ├── numpy/
│   ├── matplotlib/
│   ├── pandas/
│   └── ...                   # 其他依赖 (~200-400MB)
├── config.json               # 配置文件
├── signal_history.json       # 数据文件
├── README.md                 # 说明文档
└── 启动WiFi专业工具.bat      # 启动脚本
```

**总大小**: 约250-450MB（取决于依赖版本）

### 单文件模式输出

```
dist/
└── WiFi专业工具.exe          # 独立可执行文件 (~150-250MB)
```

**总大小**: 约150-250MB

---

## 🚀 性能对比

| 模式 | 文件数 | 总大小 | 启动速度 | 分发难度 |
|------|--------|--------|----------|----------|
| **文件夹模式** | 100+ | 250-450MB | 快 (1-2秒) | 中 |
| **单文件模式** | 1 | 150-250MB | 慢 (5-15秒) | 低 |

**推荐**: 文件夹模式（默认），启动速度快，用户体验好

---

## 📦 分发指南

### 方法1: 压缩包分发

```batch
# 打包后压缩dist\WiFi专业工具文件夹
# 使用7-Zip或WinRAR压缩为zip文件

压缩命令示例（7z）:
7z a -tzip WiFi专业工具_v1.6.3.zip "dist\WiFi专业工具\"
```

**优点**: 文件小，下载快  
**缺点**: 用户需手动解压

### 方法2: 安装程序

使用 **Inno Setup** 创建安装程序：

1. 下载安装 [Inno Setup](https://jrsoftware.org/isinfo.php)
2. 创建安装脚本 `installer.iss`
3. 编译生成 `WiFi专业工具_Setup.exe`

**优点**: 专业，可添加桌面快捷方式  
**缺点**: 需要额外工具

### 方法3: 便携版

将整个 `dist\WiFi专业工具` 文件夹复制到U盘：

```
U盘/
└── WiFi专业工具/
    ├── WiFi专业工具.exe
    └── ...
```

**优点**: 即插即用，无需安装  
**缺点**: 文件夹较大

---

## 🔍 验证清单

打包完成后，请验证以下功能：

- [ ] 程序能正常启动（无控制台窗口）
- [ ] 9个功能标签页全部可见
- [ ] WiFi扫描功能正常
- [ ] 图表绘制无中文乱码
- [ ] PDF报告生成正常
- [ ] 配置文件读取正常
- [ ] 日志文件能正常写入
- [ ] 程序关闭后无残留进程
- [ ] 在无Python环境的机器上能运行
- [ ] Windows防火墙授权后网络功能正常

---

## 🛠️ 高级优化

### 1. 添加程序图标

准备 `.ico` 文件并修改spec：

```python
exe = EXE(
    # ...
    icon='wifi_icon.ico',  # 添加图标路径
    # ...
)
```

### 2. 添加版本信息

创建 `version_info.txt`:

```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 6, 3, 0),
    prodvers=(1, 6, 3, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'080404b0',
        [StringStruct(u'CompanyName', u'WiFi Professional Team'),
        StringStruct(u'FileDescription', u'WiFi专业分析工具'),
        StringStruct(u'FileVersion', u'1.6.3.0'),
        StringStruct(u'ProductName', u'WiFi Professional'),
        StringStruct(u'ProductVersion', u'1.6.3.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)
```

修改spec:
```python
exe = EXE(
    # ...
    version='version_info.txt',  # 添加版本信息
    # ...
)
```

### 3. 启动画面（Splash Screen）

创建启动图片 `splash.png` (640x480):

```python
splash = Splash(
    'splash.png',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=(10, 460),
    text_size=12,
    text_color='white',
)

exe = EXE(
    pyz,
    a.scripts,
    splash,  # 添加启动画面
    # ...
)
```

---

## 📝 技术说明

### PyInstaller工作原理

1. **分析阶段**: 扫描主脚本，识别所有import语句
2. **收集阶段**: 收集Python解释器、依赖库、数据文件
3. **打包阶段**: 将所有文件打包为exe + 资源文件
4. **引导阶段**: 创建引导程序，运行时解压并执行Python代码

### 打包后目录结构

```
_internal/
├── base_library.zip      # Python标准库
├── python311.dll         # Python运行时
├── numpy.libs/           # NumPy依赖
├── matplotlib/           # Matplotlib库
├── core/                 # 项目核心模块
└── wifi_modules/         # 功能模块
```

### 依赖处理

- **显式导入**: 自动识别（如 `import numpy`）
- **隐式导入**: 需手动添加到hiddenimports（如插件、动态加载）
- **数据文件**: 需在datas中指定（如字体、配置）

---

## 🐛 调试技巧

### 启用调试模式

临时启用控制台窗口查看错误：

```python
# 修改 wifi_professional.spec
exe = EXE(
    # ...
    console=True,  # 改为True
    # ...
)
```

重新打包后运行，可看到完整错误信息。

### 检查依赖完整性

```python
# 在打包后的程序中测试导入
import sys
print(sys.path)

import numpy
print(numpy.__version__)

import matplotlib
print(matplotlib.__version__)
```

---

## 📞 支持

遇到问题？

1. 查看上方**常见问题解决**章节
2. 检查 `build/` 目录下的构建日志
3. 搜索PyInstaller官方文档
4. 提交Issue到项目仓库

---

**文档版本**: 1.0  
**更新日期**: 2026年2月5日  
**适用版本**: WiFi专业工具 v1.6.3
