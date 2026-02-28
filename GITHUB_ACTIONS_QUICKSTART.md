# 🚀 快速开始 - GitHub Actions 自动化构建

## ✅ 已完成配置

我已为您配置了完整的 GitHub Actions CI/CD 流程！

### 📂 新增文件
```
.github/
├── workflows/
│   └── build-release.yml    # 主构建流程 ⭐
└── FUNDING.yml              # 赞助配置（可选）

GITHUB_ACTIONS_GUIDE.md      # 详细使用指南
```

---

## 🎯 三种使用方式

### 方式 1: 推送代码自动构建（推荐）

```bash
# 1. 提交您的代码
git add .
git commit -m "Update features"
git push origin main

# 2. GitHub 会自动开始构建
# 访问: https://github.com/你的用户名/仓库名/actions

# 3. 等待 10-15 分钟，构建完成

# 4. 下载构建产物
# Actions → 选择运行 → Artifacts 区域
```

### 方式 2: 手动触发构建

1. 访问 GitHub 仓库
2. 点击 **Actions** 标签页
3. 选择 "Build Multi-Platform Release"
4. 点击 **Run workflow** 按钮
5. 选择分支，点击绿色的 "Run workflow"

### 方式 3: 创建版本发布

```bash
# 1. 创建版本标签
git tag v1.7.3
git push origin v1.7.3

# 2. GitHub Actions 会自动：
#    - 构建 Windows / macOS / Linux 三个版本
#    - 创建 GitHub Release
#    - 上传所有安装包
#    - 生成 Release Notes

# 3. 下载发布版本
# 访问: https://github.com/你的用户名/仓库名/releases
```

---

## 📦 构建产物

### 自动生成的文件

**Windows**:
- `WiFi专业工具.exe` (约 100-150 MB)

**macOS**:
- `WiFi专业工具-macOS.zip` (包含 .app)
- `WiFi专业工具-macOS.dmg` (安装镜像)

**Linux**:
- `wifi-professional` (可执行文件)

### 下载位置

**Actions 页面**（开发版本）:
- 保留 30 天
- Actions → 选择运行 → Artifacts

**Releases 页面**（正式版本）:
- 永久保留
- 自动生成 Release Notes
- https://github.com/你的用户名/仓库名/releases

---

## 🔧 首次使用步骤

### 1. 推送配置文件到 GitHub

```bash
# 添加新文件
git add .github/ GITHUB_ACTIONS_GUIDE.md

# 提交
git commit -m "Add GitHub Actions CI/CD pipeline"

# 推送到 GitHub
git push origin main
```

### 2. 启用 Actions（如果未启用）

1. 访问仓库 → **Settings**
2. 左侧菜单 → **Actions** → **General**
3. 确保 "Allow all actions" 已选中
4. 保存

### 3. 触发首次构建

**自动触发**：推送代码后自动开始

**手动触发**：
1. 访问 **Actions** 标签页
2. 点击 "Build Multi-Platform Release"
3. 点击 "Run workflow"

### 4. 查看构建进度

1. 访问 **Actions** 标签页
2. 点击最新的运行
3. 实时查看构建日志
4. 等待所有步骤完成（✅ 绿色对勾）

### 5. 下载构建产物

1. 滚动到页面底部
2. **Artifacts** 区域
3. 点击下载需要的平台版本

---

## 📊 构建流程

```
推送代码/创建标签
    ↓
GitHub Actions 触发
    ↓
┌─────────────┬─────────────┬─────────────┐
│   Windows   │    macOS    │    Linux    │  ← 并行构建
└─────────────┴─────────────┴─────────────┘
         ↓           ↓           ↓
    上传构建产物（Artifacts）
              ↓
    （如果是标签）创建 GitHub Release
              ↓
          完成！🎉
```

**预计时间**: 10-15 分钟

---

## 🎯 构建状态

构建完成后，您会看到：

### ✅ 成功
```
✅ build-windows
✅ build-macos
✅ build-linux
✅ create-release (仅标签)
```

### 下载产物
- **Windows 用户**: 下载 `WiFi专业工具-Windows`
- **macOS 用户**: 下载 `WiFi专业工具-macOS-DMG`
- **Linux 用户**: 下载 `WiFi专业工具-Linux`

---

## 🔄 版本发布流程

### 发布新版本（推荐）

```bash
# 1. 更新版本号
# 编辑 wifi_professional.py
VERSION = "1.7.3"

# 2. 提交更改
git add wifi_professional.py
git commit -m "Bump version to 1.7.3"
git push origin main

# 3. 创建标签
git tag v1.7.3
git push origin v1.7.3

# 4. 等待 GitHub Actions 完成
# 访问 Actions 查看进度

# 5. 检查 Release
# 访问 Releases 页面
# https://github.com/你的用户名/仓库名/releases

# 6. 完成！
# 用户可以下载 v1.7.3 的所有平台版本
```

---

## 📋 README 徽章（可选）

在 README.md 中添加构建状态徽章：

```markdown
# WiFi专业工具

![Build Status](https://github.com/你的用户名/WiFiProfessional/actions/workflows/build-release.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.7.2-green.svg)

专业的 WiFi 网络分析工具...
```

效果：
- ![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)

---

## 🐛 常见问题

### Q: 构建失败怎么办？

**A**: 查看详细日志
1. Actions → 选择失败的运行
2. 点击失败的步骤（红色 ❌）
3. 查看错误信息
4. 常见问题：
   - 缺少依赖 → 更新 `requirements.txt`
   - 导入错误 → 检查代码语法
   - 权限问题 → 检查 Actions 设置

### Q: 如何只构建某个平台？

**A**: 暂时注释其他平台
```yaml
# 编辑 .github/workflows/build-release.yml
jobs:
  build-windows: ...  # 保留
  # build-macos: ...  # 注释掉
  # build-linux: ...  # 注释掉
```

### Q: 构建时间太长？

**A**: 已启用缓存优化
- pip 依赖缓存
- 并行构建
- 平均 10-15 分钟

### Q: 如何删除旧的 Artifacts？

**A**: 自动清理
- 30 天后自动删除
- 或手动删除：Actions → 选择运行 → Delete workflow run

---

## 💡 下一步

### 立即开始

```bash
# 1. 推送配置
git add .github/ GITHUB_ACTIONS_GUIDE.md
git commit -m "Add CI/CD"
git push origin main

# 2. 查看 Actions
# 访问 https://github.com/你的用户名/仓库名/actions

# 3. 等待构建完成（10-15 分钟）

# 4. 下载测试
```

### 创建首个 Release

```bash
git tag v1.7.2
git push origin v1.7.2

# 访问 Releases 页面查看发布
```

---

## 📖 详细文档

完整使用说明请参阅：**[GITHUB_ACTIONS_GUIDE.md](GITHUB_ACTIONS_GUIDE.md)**

包含内容：
- ✅ 详细构建流程
- ✅ 高级配置
- ✅ 故障排除
- ✅ 最佳实践
- ✅ 代码签名指南

---

## ✅ 配置完成检查清单

- [x] `.github/workflows/build-release.yml` 已创建
- [x] 文档已生成
- [ ] 推送到 GitHub
- [ ] 首次构建成功
- [ ] 下载测试构建产物

---

**GitHub Actions 配置完成！** 🎉

现在执行：
```bash
git add .
git commit -m "Add GitHub Actions CI/CD"
git push origin main
```

然后访问 **Actions** 标签页查看自动构建！ 🚀
