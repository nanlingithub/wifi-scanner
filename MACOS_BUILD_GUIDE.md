# macOS 打包快速指南

## 🚀 快速开始（3步）

### 1. 环境准备

```bash
# 在 macOS 终端中执行
cd WiFiProfessional
python3 setup_macos.py
```

这会自动：
- ✅ 检查系统环境
- ✅ 安装依赖包
- ✅ 创建启动脚本
- ✅ 检查权限配置

### 2. 运行测试

```bash
# 方式一：使用启动脚本（推荐）
./启动WiFi专业工具.command

# 方式二：直接运行
python3 wifi_professional.py

# 方式三：使用 sudo 获取完整权限
sudo python3 wifi_professional.py
```

### 3. 打包应用

```bash
# 给打包脚本添加执行权限
chmod +x build_macos.sh

# 执行打包
./build_macos.sh
```

打包完成后，应用位于 `dist/WiFi专业工具.app`

---

## 📋 详细说明

### 系统要求

| 项目 | 要求 |
|-----|------|
| 系统版本 | macOS 10.13+ |
| Python | 3.8+ |
| 内存 | 4GB+ |
| 磁盘空间 | 500MB+ |

### 权限配置

macOS WiFi 扫描需要**位置服务权限**：

1. **系统偏好设置** → **安全性与隐私** → **隐私**
2. 选择左侧 **位置服务**
3. 勾选 **WiFi专业工具**

如果没有权限，扫描功能将无法使用。

### 依赖包安装

```bash
# 核心依赖
pip3 install tkinter psutil pandas numpy matplotlib scipy

# 可选依赖（增强功能）
pip3 install scikit-learn pykrige reportlab openpyxl

# 打包工具
pip3 install pyinstaller
```

或直接安装 requirements.txt：

```bash
pip3 install -r requirements.txt
```

### 图标文件

如果需要自定义图标，准备 1024x1024 的 PNG 图片：

```bash
# 创建 ICNS 图标
./create_icns_icon.sh wifi_icon.png
```

或参考 README_MACOS.md 中的详细步骤。

---

## 🔧 打包选项

### 选项 1：单文件模式（推荐）

```bash
pyinstaller --onefile \
  --windowed \
  --name "WiFi专业工具" \
  --icon wifi_icon.icns \
  wifi_professional.py
```

优点：单个可执行文件，便于分发
缺点：启动稍慢（需解压）

### 选项 2：目录模式（使用 spec 文件）

```bash
pyinstaller build_macos.spec
```

优点：
- ✅ 启动快速
- ✅ 完整配置
- ✅ 生成 .app 包

这是推荐的方式！

### 选项 3：使用 py2app（原生打包）

```bash
# 安装 py2app
pip3 install py2app

# 生成 setup.py
py2applet --make-setup wifi_professional.py

# 打包
python3 setup.py py2app
```

---

## 📦 打包后的文件结构

```
dist/
└── WiFi专业工具.app/
    ├── Contents/
    │   ├── MacOS/
    │   │   └── WiFi专业工具          # 可执行文件
    │   ├── Resources/
    │   │   ├── wifi_icon.icns        # 应用图标
    │   │   ├── config/               # 配置文件
    │   │   └── ...                   # 其他资源
    │   ├── Frameworks/               # Python 框架和库
    │   └── Info.plist                # 应用信息
```

应用大小：约 100-150 MB（包含 Python 运行时）

---

## 🐛 常见问题

### Q1: 打包失败 - ModuleNotFoundError

**问题**: 提示找不到某个模块

**解决**:
```bash
# 检查依赖是否安装
pip3 list | grep <模块名>

# 重新安装依赖
pip3 install -r requirements.txt --force-reinstall
```

### Q2: 应用无法打开 - "已损坏"

**问题**: 双击应用提示"已损坏无法打开"

**解决**:
```bash
# 移除隔离属性
sudo xattr -cr /Applications/WiFi专业工具.app

# 或者允许运行未签名应用
sudo spctl --master-disable
```

### Q3: WiFi 扫描失败

**问题**: 扫描结果为空或报错

**解决**:
1. 检查位置服务权限
2. 尝试使用 sudo 运行
3. 确认 WiFi 已开启

```bash
# 测试 airport 命令
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s
```

### Q4: Apple Silicon (M1/M2) 兼容性

**问题**: M1/M2 Mac 上运行报错

**解决**:
```bash
# 使用 Universal2 Python
# 或使用 Rosetta 2 运行
arch -x86_64 python3 wifi_professional.py

# 打包时指定架构
pyinstaller --target-arch universal2 build_macos.spec
```

### Q5: 启动慢

**问题**: 应用启动需要 5-10 秒

**原因**: PyInstaller 单文件模式需要解压

**解决**: 使用目录模式（build_macos.spec）

---

## 🔐 代码签名（可选）

如果要分发给其他用户或上架 Mac App Store：

### 1. 获取开发者证书

- 注册 Apple Developer Program（$99/年）
- 在 Xcode 中下载证书

### 2. 签名应用

```bash
# 查看可用证书
security find-identity -v -p codesigning

# 签名
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name (TEAM_ID)" \
  dist/WiFi专业工具.app

# 验证签名
codesign --verify --deep --strict dist/WiFi专业工具.app
spctl -a -v dist/WiFi专业工具.app
```

### 3. 公证（Notarization）

macOS 10.15+ 需要：

```bash
# 创建 DMG
hdiutil create -volname "WiFi专业工具" \
  -srcfolder dist/WiFi专业工具.app \
  -ov -format UDZO \
  dist/WiFi专业工具.dmg

# 提交公证
xcrun notarytool submit dist/WiFi专业工具.dmg \
  --apple-id your@email.com \
  --password xxxx-xxxx-xxxx-xxxx \
  --team-id TEAM_ID \
  --wait

# 装订公证凭证
xcrun stapler staple dist/WiFi专业工具.dmg
```

---

## 📱 分发方式

### 方式 1: DMG 镜像（推荐）

```bash
# build_macos.sh 脚本会询问是否创建 DMG
# 或手动创建：
hdiutil create -volname "WiFi专业工具" \
  -srcfolder dist/WiFi专业工具.app \
  -ov -format UDZO \
  dist/WiFi专业工具_v1.7.2.dmg
```

用户只需：
1. 下载 DMG
2. 双击打开
3. 拖到应用程序文件夹

### 方式 2: ZIP 压缩包

```bash
cd dist
zip -r ../WiFi专业工具_v1.7.2_macOS.zip WiFi专业工具.app
```

### 方式 3: PKG 安装包

使用 `pkgbuild` 和 `productbuild` 创建安装程序。

---

## 📊 性能优化

### 减小应用体积

```python
# 在 build_macos.spec 中排除不需要的模块
excludes = [
    'pytest', 'sphinx', 'setuptools', 'pip',
    'tkinter.test', 'unittest', 'email'
]
```

### 加快启动速度

- ✅ 使用目录模式（非 onefile）
- ✅ 延迟导入大型库
- ✅ 优化 Python 代码

---

## 🆘 获取帮助

如果遇到问题：

1. 查看日志文件：`logs/wifi_professional.log`
2. 查看系统日志：
   ```bash
   log show --predicate 'process == "WiFi专业工具"' --last 1h
   ```
3. 提交 Issue（附带错误日志）

---

## ✅ 完成检查清单

打包前确认：

- [ ] Python 3.8+ 已安装
- [ ] 所有依赖已安装
- [ ] 图标文件已准备
- [ ] 位置服务权限已配置
- [ ] 测试运行正常
- [ ] 打包脚本有执行权限

打包后确认：

- [ ] .app 文件生成成功
- [ ] 应用可以双击打开
- [ ] WiFi 扫描功能正常
- [ ] 所有标签页加载正常
- [ ] 报告生成功能正常

---

**准备好了吗？开始打包吧！** 🚀

```bash
./build_macos.sh
```
