# WiFi专业分析工具 - macOS 版本

## 📱 系统要求

- **操作系统**: macOS 10.13 (High Sierra) 或更高版本
- **处理器**: Intel 或 Apple Silicon (M1/M2)
- **内存**: 4GB RAM 或以上
- **磁盘空间**: 500MB 可用空间
- **权限**: 需要授予位置服务权限（用于WiFi扫描）

## 🚀 快速开始

### 方式一：使用打包好的 .app 应用

1. **下载应用**
   - 从发布页面下载 `WiFi专业工具.app` 或 `WiFi专业工具.dmg`

2. **安装应用**
   - 如果是 DMG 文件：双击打开，将应用拖到"应用程序"文件夹
   - 如果是 .app 文件：直接拖到"应用程序"文件夹

3. **首次运行**
   ```
   右键点击应用 → 选择"打开" → 点击"打开"确认
   ```
   （macOS Gatekeeper 会阻止未签名的应用，需要手动确认）

4. **授予权限**
   - 系统会提示授予"位置服务"权限
   - 进入 系统偏好设置 → 安全性与隐私 → 隐私 → 位置服务
   - 勾选 WiFi专业工具

### 方式二：从源代码运行

1. **安装依赖**
   ```bash
   # 克隆仓库
   git clone https://github.com/yourusername/WiFiProfessional.git
   cd WiFiProfessional
   
   # 创建虚拟环境
   python3 -m venv venv
   source venv/bin/activate
   
   # 安装依赖
   pip install -r requirements.txt
   ```

2. **运行程序**
   ```bash
   python3 wifi_professional.py
   ```

## 🔨 自行打包

### 方法一：使用打包脚本（推荐）

```bash
# 给脚本添加执行权限
chmod +x build_macos.sh

# 执行打包脚本
./build_macos.sh
```

脚本会自动：
- 创建虚拟环境
- 安装依赖
- 执行打包
- 生成 .app 应用
- 可选创建 DMG 镜像

### 方法二：手动打包

```bash
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 执行打包
pyinstaller build_macos.spec

# 3. 检查结果
open dist/
```

### 创建图标文件

如果需要自定义图标：

```bash
# 从 PNG 创建 ICNS（需要 PNG 图片，推荐 1024x1024）
mkdir wifi_icon.iconset
sips -z 16 16     wifi_icon.png --out wifi_icon.iconset/icon_16x16.png
sips -z 32 32     wifi_icon.png --out wifi_icon.iconset/icon_16x16@2x.png
sips -z 32 32     wifi_icon.png --out wifi_icon.iconset/icon_32x32.png
sips -z 64 64     wifi_icon.png --out wifi_icon.iconset/icon_32x32@2x.png
sips -z 128 128   wifi_icon.png --out wifi_icon.iconset/icon_128x128.png
sips -z 256 256   wifi_icon.png --out wifi_icon.iconset/icon_128x128@2x.png
sips -z 256 256   wifi_icon.png --out wifi_icon.iconset/icon_256x256.png
sips -z 512 512   wifi_icon.png --out wifi_icon.iconset/icon_256x256@2x.png
sips -z 512 512   wifi_icon.png --out wifi_icon.iconset/icon_512x512.png
sips -z 1024 1024 wifi_icon.png --out wifi_icon.iconset/icon_512x512@2x.png
iconutil -c icns wifi_icon.iconset
rm -rf wifi_icon.iconset
```

## 📊 功能说明

### ✅ 完全支持的功能

- ✅ WiFi 网络扫描
- ✅ 信号强度监控
- ✅ 信道分析
- ✅ 实时监控
- ✅ 热力图生成
- ✅ 部署优化
- ✅ 安全检测
- ✅ 企业级报告

### ⚠️ 功能限制

由于 macOS 系统限制：

1. **WiFi 扫描**
   - 使用 `airport` 命令（系统内置）
   - 信息相对 Windows 版本略少（无 dBm 值）
   - 需要位置服务权限

2. **管理员权限**
   - 某些高级功能可能需要 sudo 权限
   - 使用命令行运行时需要 `sudo python3 wifi_professional.py`

3. **实时监控**
   - macOS 对 WiFi API 访问有限制
   - 刷新速度可能比 Windows 版本慢

## 🔧 macOS 特定配置

### WiFi 扫描命令

macOS 使用内置的 `airport` 命令：

```bash
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s
```

### 授予位置权限

如果扫描失败，检查位置服务：

```bash
# 检查位置服务状态
sudo launchctl list | grep locationd

# 如果服务未运行
sudo launchctl load /System/Library/LaunchDaemons/com.apple.locationd.plist
```

### 常见问题

**Q: 无法打开应用，提示"已损坏"**

A: 这是 Gatekeeper 的安全限制，执行：
```bash
sudo xattr -cr /Applications/WiFi专业工具.app
```

**Q: 扫描不到 WiFi 网络**

A: 检查位置服务权限：
- 系统偏好设置 → 安全性与隐私 → 隐私 → 位置服务
- 确保勾选了 WiFi专业工具

**Q: 应用闪退**

A: 查看崩溃日志：
```bash
# 查看应用日志
log show --predicate 'process == "WiFi专业工具"' --last 1h

# 或查看崩溃报告
open ~/Library/Logs/DiagnosticReports/
```

**Q: Apple Silicon (M1/M2) 兼容性**

A: 
- 推荐使用 Python 3.9+ (Universal2 版本)
- 如果遇到问题，尝试使用 Rosetta 2 运行
```bash
arch -x86_64 python3 wifi_professional.py
```

## 🔐 代码签名（可选）

如果要分发给其他用户，建议进行代码签名：

```bash
# 1. 生成开发者证书（需要付费开发者账户）
# 在 Xcode → Preferences → Accounts 中添加

# 2. 对应用签名
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/WiFi专业工具.app

# 3. 验证签名
codesign --verify --verbose dist/WiFi专业工具.app
spctl -a -t exec -vv dist/WiFi专业工具.app

# 4. 公证（Notarization，macOS 10.15+）
# 创建 dmg 后提交给 Apple
xcrun notarytool submit dist/WiFi专业工具.dmg --apple-id your@email.com --password xxxx-xxxx-xxxx-xxxx --team-id TEAMID
```

## 📦 发布清单

打包完成后应包含：

```
dist/
├── WiFi专业工具.app          # macOS 应用程序
│   ├── Contents/
│   │   ├── MacOS/
│   │   │   └── WiFi专业工具  # 可执行文件
│   │   ├── Resources/
│   │   │   └── wifi_icon.icns # 图标
│   │   └── Info.plist        # 应用信息
└── WiFi专业工具_v1.7.2.dmg   # 安装镜像（可选）
```

## 🌐 跨平台兼容性

| 功能 | Windows | macOS | Linux |
|-----|---------|-------|-------|
| WiFi 扫描 | ✅ 完整 | ✅ 基础 | ✅ 基础 |
| 信号强度 | ✅ dBm | ⚠️ 百分比 | ✅ dBm |
| 信道分析 | ✅ | ✅ | ✅ |
| 热力图 | ✅ | ✅ | ✅ |
| 安全检测 | ✅ | ✅ | ✅ |
| 企业报告 | ✅ | ✅ | ✅ |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

特别关注 macOS 平台的改进：
- 更详细的 WiFi 信息获取
- 性能优化
- UI/UX 改进

## 📄 许可证

本项目采用 MIT 许可证

## 📧 联系方式

- 开发者: NL@China_SZ
- 版本: 1.7.2
- 更新日期: 2026-02-28

---

**注意**: 本工具仅供合法网络管理和测试使用，请勿用于非法目的。
