# WiFi专业工具 - macOS 快速入门 🚀

## 3 步快速开始

### 第 1 步：环境准备 ⚙️

```bash
# 打开终端，进入项目目录
cd WiFiProfessional

# 运行安装脚本
python3 setup_macos.py
```

安装脚本会自动完成：
- ✅ 检查系统环境（macOS 10.13+）
- ✅ 检查 Python 版本（3.8+）
- ✅ 安装所有依赖包
- ✅ 创建启动脚本
- ✅ 检查 WiFi 扫描工具

---

### 第 2 步：运行程序 🎯

**方式一：双击运行（推荐）**
```
双击 "启动WiFi专业工具.command"
```

**方式二：命令行运行**
```bash
python3 wifi_professional.py
```

**方式三：完整权限运行**
```bash
sudo python3 wifi_professional.py
```

---

### 第 3 步：授予权限 🔐

首次运行时，系统会提示：

1. **位置服务权限**
   - 系统偏好设置 → 安全性与隐私 → 隐私 → 位置服务
   - 勾选 "WiFi专业工具" 或 "Terminal"

2. **网络访问权限**
   - 点击"允许"即可

---

## 打包为 .app 应用 📦

如果想打包成独立应用：

```bash
# 添加执行权限
chmod +x build_macos.sh create_icns_icon.sh

# 执行打包
./build_macos.sh
```

打包完成后：
- 应用位置：`dist/WiFi专业工具.app`
- 拖到"应用程序"文件夹即可使用

---

## 功能预览 ✨

### 1️⃣ 网络概览
- WiFi 网络扫描
- 信号强度监控
- 设备厂商识别

### 2️⃣ 信道分析
- 2.4/5/6 GHz 分析
- 干扰源检测
- 信道优化建议

### 3️⃣ 实时监控
- 信号强度曲线
- 连接质量监控
- 网络性能评估

### 4️⃣ 热力图
- 信号覆盖可视化
- 多点位数据采集
- 3D 热力图展示

### 5️⃣ 部署优化
- AP 位置规划
- 覆盖率分析
- 智能推荐方案

### 6️⃣ 安全检测
- 开放网络检测
- WPS 漏洞扫描
- 钓鱼热点识别

### 7️⃣ 企业报告
- 专业 PDF 报告
- PCI-DSS 评估
- 多点位对比

---

## 常见问题 ❓

### Q: 扫描不到 WiFi？
**A:** 检查位置服务权限，或使用 `sudo` 运行

### Q: 应用提示"已损坏"？
**A:** 运行命令移除隔离属性：
```bash
sudo xattr -cr /Applications/WiFi专业工具.app
```

### Q: Apple Silicon (M1/M2) 兼容性？
**A:** 使用 Python 3.9+ Universal2 版本，或通过 Rosetta 2 运行：
```bash
arch -x86_64 python3 wifi_professional.py
```

---

## 系统要求 💻

| 项目 | 要求 |
|-----|------|
| 系统 | macOS 10.13 (High Sierra) + |
| 处理器 | Intel / Apple Silicon (M1/M2) |
| 内存 | 4GB+ |
| Python | 3.8+ |

---

## 获取帮助 🆘

- 📖 详细文档：`README_MACOS.md`
- 🔧 打包指南：`MACOS_BUILD_GUIDE.md`
- 📧 问题反馈：提交 GitHub Issue

---

## 使用技巧 💡

1. **首次扫描慢？**
   - 正常现象，首次扫描需要初始化
   - 后续会使用缓存机制加速

2. **获取更多信息？**
   - 使用 `sudo` 运行可获取完整权限
   - 某些高级功能需要管理员权限

3. **生成专业报告？**
   - 使用"企业级报告"标签页
   - 支持导出 PDF 和 Excel

4. **多点位采集？**
   - 在热力图标签页添加测量点
   - 支持导入/导出 CSV 数据

---

**准备好了吗？开始使用 WiFi 专业工具吧！** 🎉

```bash
python3 wifi_professional.py
```
