# GitHub Actions 自动化构建指南

## 🚀 概述

已为本项目配置了完整的 GitHub Actions 工作流，支持：
- ✅ **自动化跨平台构建**（Windows / macOS / Linux）
- ✅ **自动测试**（多 Python 版本）
- ✅ **自动发布**（创建 GitHub Release）
- ✅ **构建产物下载**（30 天保留期）

---

## 📂 配置文件

### `.github/workflows/build-release.yml` ⭐
**主构建流程**，包含 5 个 Job：

1. **build-windows** - 构建 Windows EXE
2. **build-macos** - 构建 macOS APP + DMG
3. **build-linux** - 构建 Linux 可执行文件
4. **create-release** - 创建 GitHub Release（仅标签触发）
5. **build-summary** - 生成构建摘要

### `.github/workflows/test.yml`
**自动测试流程**：
- 多操作系统（Ubuntu / Windows / macOS）
- 多 Python 版本（3.8 / 3.9 / 3.10 / 3.11）
- 代码覆盖率报告

---

## 🔧 如何使用

### 方式 1：推送代码自动构建

```bash
# 提交代码
git add .
git commit -m "Update features"
git push origin main

# GitHub Actions 会自动：
# 1. 开始构建（3个平台并行）
# 2. 上传构建产物
# 3. 在 Actions 标签页查看进度
```

**查看结果**：
- 访问 GitHub 仓库 → Actions 标签页
- 点击最新的工作流运行
- 下载 Artifacts（构建产物）

### 方式 2：手动触发构建

1. 访问 GitHub 仓库 → **Actions** 标签页
2. 选择 "Build Multi-Platform Release"
3. 点击 **Run workflow** 按钮
4. 选择分支，点击 "Run workflow"

### 方式 3：创建版本发布

```bash
# 创建版本标签
git tag v1.7.3
git push origin v1.7.3

# GitHub Actions 会自动：
# 1. 构建所有平台
# 2. 创建 GitHub Release
# 3. 上传所有安装包
# 4. 生成 Release Notes
```

**发布产物**：
- `WiFi专业工具-Windows-v1.7.3.zip`
- `WiFi专业工具-macOS-v1.7.3.zip`
- `WiFi专业工具-macOS-v1.7.3.dmg`
- `WiFi专业工具-Linux-v1.7.3.tar.gz`

---

## 📊 构建流程详解

### Windows 构建流程

```yaml
1. 检出代码
2. 设置 Python 3.11
3. 安装依赖（requirements.txt + pyinstaller）
4. 执行打包（wifi_professional.spec）
5. 检查构建结果
6. 上传 WiFi专业工具.exe
```

**输出**：`WiFi专业工具.exe`（约 100-150 MB）

### macOS 构建流程

```yaml
1. 检出代码
2. 设置 Python 3.11
3. 安装依赖
4. 自动创建 ICNS 图标（如需要）
5. 执行打包（build_macos.spec）
6. 压缩为 ZIP
7. 创建 DMG 镜像
8. 上传两种格式
```

**输出**：
- `WiFi专业工具-macOS.zip`
- `WiFi专业工具-macOS.dmg`

### Linux 构建流程

```yaml
1. 检出代码
2. 设置 Python 3.11
3. 安装系统依赖（python3-tk）
4. 安装 Python 依赖
5. 执行打包（onefile 模式）
6. 添加执行权限
7. 上传可执行文件
```

**输出**：`wifi-professional`（Linux ELF 可执行文件）

---

## 🎯 触发条件

### 自动触发

| 事件 | 触发条件 | 执行内容 |
|-----|---------|---------|
| **push** | 推送到 main/master 分支 | 构建所有平台 |
| **push tag** | 推送版本标签（v*） | 构建 + 创建 Release |
| **pull_request** | PR 到 main/master | 构建测试 |

### 手动触发

- `workflow_dispatch`：在 Actions 页面手动运行

---

## 📥 下载构建产物

### 从 Actions 页面下载

1. 访问仓库 → **Actions** 标签页
2. 点击最新的成功构建
3. 滚动到底部查看 **Artifacts**
4. 下载需要的平台版本：
   - `WiFi专业工具-Windows`
   - `WiFi专业工具-macOS-ZIP`
   - `WiFi专业工具-macOS-DMG`
   - `WiFi专业工具-Linux`

**保留期**：30 天

### 从 Release 下载

1. 访问仓库 → **Releases** 标签页
2. 选择版本（如 v1.7.3）
3. 下载对应平台的安装包
4. 查看 Release Notes

---

## 🔐 密钥配置（可选）

### 代码签名（macOS）

如需对 macOS 应用进行代码签名和公证：

```yaml
# 在仓库 Settings → Secrets 中添加：
APPLE_CERTIFICATE: base64 编码的证书
APPLE_CERTIFICATE_PASSWORD: 证书密码
APPLE_ID: Apple ID
APPLE_APP_PASSWORD: 应用专用密码
APPLE_TEAM_ID: 团队 ID
```

然后在工作流中添加签名步骤。

### Codecov（代码覆盖率）

```yaml
# 添加 Secret：
CODECOV_TOKEN: your-codecov-token
```

---

## 🐛 故障排除

### 构建失败排查

1. **查看日志**
   - Actions → 选择失败的运行 → 点击失败的步骤
   - 查看详细错误信息

2. **常见问题**

   **问题**: `ModuleNotFoundError`
   ```yaml
   # 解决：检查 requirements.txt 是否包含所有依赖
   pip freeze > requirements.txt
   git add requirements.txt
   git commit -m "Update requirements"
   ```

   **问题**: macOS 图标创建失败
   ```yaml
   # 解决：确保仓库中有 wifi_icon.png 或 wifi_icon.icns
   ```

   **问题**: Windows 打包超时
   ```yaml
   # 解决：增加 timeout-minutes
   - name: 构建
     timeout-minutes: 30  # 默认 360 分钟
   ```

3. **本地测试**
   ```bash
   # 在推送前本地测试构建
   # Windows
   .\build_exe.bat
   
   # macOS
   ./build_macos.sh
   ```

### 检查构建状态

**徽章**：在 README.md 中添加状态徽章

```markdown
![Build Status](https://github.com/yourusername/WiFiProfessional/actions/workflows/build-release.yml/badge.svg)
```

---

## 📈 优化建议

### 1. 缓存依赖

已启用 pip 缓存：
```yaml
- uses: actions/setup-python@v5
  with:
    cache: 'pip'  # 缓存 pip 依赖
```

### 2. 并行构建

所有平台并行构建，节省时间：
```
Windows  ─┐
macOS    ─┼─→ create-release
Linux    ─┘
```

### 3. 条件执行

仅标签推送时创建 Release：
```yaml
if: startsWith(github.ref, 'refs/tags/v')
```

---

## 📦 发布流程

### 完整发布流程

```bash
# 1. 更新版本号
# 修改 wifi_professional.py 中的 VERSION

# 2. 更新 CHANGELOG
echo "## v1.7.3 - 2026-02-28" >> CHANGELOG.md

# 3. 提交更改
git add .
git commit -m "Release v1.7.3"
git push origin main

# 4. 创建标签
git tag v1.7.3
git push origin v1.7.3

# 5. 等待 GitHub Actions 完成
# 访问 Actions 页面查看进度（约 10-15 分钟）

# 6. 检查 Release
# 访问 Releases 页面，确认自动创建的发布

# 7. 编辑 Release Notes（可选）
# 添加更详细的更新说明
```

---

## 🎨 自定义配置

### 修改构建触发条件

编辑 `.github/workflows/build-release.yml`：

```yaml
on:
  push:
    branches: [ main, develop ]  # 添加 develop 分支
    paths-ignore:             # 忽略某些文件
      - '**.md'
      - 'docs/**'
```

### 添加构建步骤

```yaml
- name: 🧪 运行测试
  run: pytest tests/ -v

- name: 📝 生成文档
  run: |
    pip install sphinx
    sphinx-build docs/ dist/docs/
```

### 修改 Python 版本

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'  # 使用 Python 3.12
```

---

## 💡 最佳实践

1. **版本管理**
   - 使用语义化版本（v1.2.3）
   - 每次发布前更新 CHANGELOG

2. **测试**
   - 推送前本地测试
   - 保持测试覆盖率 > 80%

3. **文档**
   - 更新 README 和相关文档
   - Release Notes 清晰明了

4. **构建产物**
   - 定期清理旧的 Artifacts
   - 重要版本创建 Release

---

## ✅ 验证清单

部署前确认：

- [ ] `.github/workflows/` 文件已创建
- [ ] `requirements.txt` 包含所有依赖
- [ ] 打包配置文件正确（`.spec` 文件）
- [ ] 图标文件已准备（`.ico`, `.icns`）
- [ ] 代码已推送到 GitHub
- [ ] Actions 已启用（Settings → Actions）
- [ ] 首次运行成功

---

## 🆘 获取帮助

- **查看日志**: Actions 标签页 → 选择运行 → 查看详细日志
- **查看文档**: [GitHub Actions 官方文档](https://docs.github.com/en/actions)
- **常见问题**: 参考本文档的故障排除章节

---

## 📊 当前配置总结

```
✅ 自动化构建：Windows / macOS / Linux
✅ 自动测试：多版本 Python
✅ 自动发布：GitHub Release
✅ 构建缓存：加速构建
✅ 并行执行：节省时间
✅ 错误处理：详细日志
✅ 产物保留：30 天

预计构建时间：10-15 分钟
```

---

**GitHub Actions 已配置完成！** 🎉

现在只需：
```bash
git add .github/
git commit -m "Add GitHub Actions CI/CD"
git push origin main
```

然后访问仓库的 Actions 标签页，查看首次自动构建！
