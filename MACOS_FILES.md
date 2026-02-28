# WiFi专业工具 macOS 版本 - 文件清单

## 📋 新增文件列表

本次为 macOS 平台适配新增的文件：

### 1. 打包配置文件

#### `build_macos.spec` ⭐
- **用途**: PyInstaller 打包配置文件（macOS 专用）
- **功能**: 
  - 定义打包参数
  - 配置依赖模块
  - 设置应用信息
  - 生成 .app 包
- **使用**: `pyinstaller build_macos.spec`

#### `build_macos.sh` ⭐
- **用途**: macOS 自动打包脚本
- **功能**:
  - 环境检查
  - 依赖安装
  - 自动打包
  - 生成 DMG 镜像
- **使用**: `./build_macos.sh`

### 2. 安装和设置脚本

#### `setup_macos.py` ⭐
- **用途**: macOS 环境配置助手
- **功能**:
  - 检查系统版本
  - 验证 Python 版本
  - 安装依赖包
  - 创建启动脚本
  - 检查权限配置
- **使用**: `python3 setup_macos.py`

#### `create_icns_icon.sh`
- **用途**: 图标格式转换工具
- **功能**: 将 PNG 图片转换为 macOS ICNS 图标
- **使用**: `./create_icns_icon.sh wifi_icon.png`

### 3. 文档文件

#### `README_MACOS.md` 📖
- **用途**: macOS 版本详细说明
- **内容**:
  - 系统要求
  - 安装步骤
  - 功能说明
  - 常见问题
  - 代码签名指南

#### `MACOS_BUILD_GUIDE.md` 📖
- **用途**: 打包详细指南
- **内容**:
  - 打包流程
  - 配置选项
  - 故障排除
  - 性能优化
  - 分发方法

#### `MACOS_QUICKSTART.md` 📖
- **用途**: 快速入门指南
- **内容**:
  - 3 步开始
  - 功能预览
  - 使用技巧
  - 快速问题解答

#### `MACOS_FILES.md` 📖
- **用途**: 文件清单（本文件）
- **内容**: 所有新增文件的说明

### 4. 修改的现有文件

#### `core/wifi_analyzer.py` ✏️
- **修改内容**: 增强 macOS WiFi 扫描功能
- **改进**:
  - 完善 `_parse_mac_wifi_scan()` 方法
  - 支持解析 RSSI、信道、加密等信息
  - 添加更详细的日志

#### `core/admin_utils.py` ✏️
- **修改内容**: 跨平台权限检测
- **改进**:
  - `is_admin()` 支持 macOS/Linux
  - `restart_as_admin()` 支持 osascript 提权
  - `check_admin_rights()` 平台化提示
  - `get_admin_status_text()` 跨平台文本

---

## 📂 完整目录结构

```
WiFiProfessional/
├── 📄 build_macos.spec           # macOS 打包配置 ⭐
├── 📄 build_macos.sh             # macOS 打包脚本 ⭐
├── 📄 setup_macos.py             # macOS 安装助手 ⭐
├── 📄 create_icns_icon.sh        # 图标转换工具
│
├── 📖 README_MACOS.md            # macOS 说明文档 ⭐
├── 📖 MACOS_BUILD_GUIDE.md       # 打包详细指南 ⭐
├── 📖 MACOS_QUICKSTART.md        # 快速入门指南 ⭐
├── 📖 MACOS_FILES.md             # 文件清单（本文件）
│
├── 📄 wifi_professional.py       # 主程序
├── 📄 requirements.txt           # 依赖列表
├── 📄 config.json                # 配置文件
│
├── 📁 core/                      # 核心模块
│   ├── wifi_analyzer.py          # ✏️ 增强 macOS 支持
│   ├── admin_utils.py            # ✏️ 跨平台权限
│   ├── connectivity.py
│   ├── memory_monitor.py
│   └── ...
│
├── 📁 wifi_modules/              # 功能模块
│   ├── network_overview.py
│   ├── channel_analysis.py
│   ├── heatmap.py
│   └── ...
│
└── 📁 dist/                      # 打包输出（运行后生成）
    └── WiFi专业工具.app          # macOS 应用
```

---

## 🎯 文件用途对照表

| 使用场景 | 相关文件 |
|---------|---------|
| **首次安装** | `setup_macos.py` → `README_MACOS.md` |
| **快速运行** | `启动WiFi专业工具.command` → `MACOS_QUICKSTART.md` |
| **打包应用** | `build_macos.sh` → `build_macos.spec` → `MACOS_BUILD_GUIDE.md` |
| **创建图标** | `create_icns_icon.sh` |
| **问题排查** | `README_MACOS.md` 常见问题章节 |
| **深入了解** | `MACOS_BUILD_GUIDE.md` 详细说明 |

---

## 🚀 使用流程

### 新用户推荐流程

```
1. 阅读 MACOS_QUICKSTART.md（3分钟）
   ↓
2. 运行 setup_macos.py（自动配置）
   ↓
3. 双击 启动WiFi专业工具.command（开始使用）
   ↓
4. 如有问题，查看 README_MACOS.md
```

### 开发者/打包流程

```
1. 阅读 MACOS_BUILD_GUIDE.md（了解打包）
   ↓
2. 准备图标：create_icns_icon.sh wifi_icon.png
   ↓
3. 配置：编辑 build_macos.spec（可选）
   ↓
4. 打包：./build_macos.sh
   ↓
5. 测试：dist/WiFi专业工具.app
   ↓
6. 分发：创建 DMG 或签名
```

---

## ⚙️ 文件权限

需要执行权限的脚本：

```bash
# 添加执行权限
chmod +x build_macos.sh
chmod +x create_icns_icon.sh
chmod +x 启动WiFi专业工具.command
```

---

## 📝 版本信息

- **创建日期**: 2026-02-28
- **版本**: 1.7.2
- **平台**: macOS（兼容 Windows/Linux）
- **Python**: 3.8+

---

## 🔄 与 Windows 版本的差异

| 项目 | Windows | macOS |
|-----|---------|-------|
| 打包配置 | `wifi_professional.spec` | `build_macos.spec` |
| 打包脚本 | `build_exe.bat` | `build_macos.sh` |
| 启动脚本 | `启动WiFi专业工具.bat` | `启动WiFi专业工具.command` |
| 图标格式 | `.ico` | `.icns` |
| WiFi扫描 | `netsh wlan` | `airport -s` |
| 权限检测 | `IsUserAnAdmin()` | `os.geteuid()` |
| 应用格式 | `.exe` | `.app` |
| 分发格式 | `.exe` / `.zip` | `.app` / `.dmg` |

---

## 📦 打包产物

运行 `./build_macos.sh` 后生成：

```
dist/
├── WiFi专业工具.app/          # macOS 应用包
│   └── Contents/
│       ├── MacOS/              # 可执行文件
│       ├── Resources/          # 资源文件
│       ├── Frameworks/         # Python 运行时
│       └── Info.plist          # 应用信息
│
└── WiFi专业工具_v1.7.2.dmg    # 安装镜像（可选）
```

应用大小：约 100-150 MB

---

## ✅ 完整性检查

确认所有文件是否存在：

```bash
# 检查必需文件
ls -l build_macos.spec
ls -l build_macos.sh
ls -l setup_macos.py
ls -l README_MACOS.md
ls -l MACOS_BUILD_GUIDE.md
ls -l MACOS_QUICKSTART.md

# 检查修改的文件
ls -l core/wifi_analyzer.py
ls -l core/admin_utils.py
```

---

## 🆘 问题报告

如果遇到问题，请提供：

1. **系统信息**
   ```bash
   sw_vers
   python3 --version
   ```

2. **错误日志**
   ```bash
   cat logs/wifi_professional.log
   ```

3. **使用的文件**
   - 说明使用了哪个脚本
   - 提供错误截图

---

**文件清单完成！** ✨

现在您可以：
- 📖 阅读 `MACOS_QUICKSTART.md` 快速开始
- 🔧 使用 `setup_macos.py` 配置环境
- 📦 运行 `build_macos.sh` 打包应用
