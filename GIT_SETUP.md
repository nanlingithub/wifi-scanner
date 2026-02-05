# Git版本管理设置指南

## 📦 安装Git后的初始化步骤

### 1. 验证Git安装
```powershell
git --version
```

### 2. 配置Git用户信息
```powershell
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
```

### 3. 初始化Git仓库
```powershell
cd d:\AI_code\github_copiloit\Net_check_tools_APP\WiFiProfessional
git init
```

### 4. 添加所有文件到暂存区
```powershell
git add .
```

### 5. 创建初始提交
```powershell
git commit -m "初始提交: WiFi专业分析工具 v1.6"
```

## 📋 常用Git命令

### 查看状态
```powershell
git status                  # 查看当前状态
git log --oneline          # 查看提交历史
```

### 提交更改
```powershell
git add .                   # 添加所有更改
git add 文件名              # 添加指定文件
git commit -m "提交说明"    # 提交更改
```

### 分支管理
```powershell
git branch                  # 查看分支
git branch dev              # 创建开发分支
git checkout dev            # 切换到开发分支
git checkout -b feature/新功能  # 创建并切换到新分支
git merge dev               # 合并分支
```

### 版本回退
```powershell
git log                     # 查看提交历史
git reset --hard HEAD^      # 回退到上一个版本
git reset --hard 提交ID     # 回退到指定版本
```

### 差异对比
```powershell
git diff                    # 查看未暂存的更改
git diff --cached           # 查看已暂存的更改
git diff HEAD               # 查看所有更改
```

## 🏷️ 推荐的Git工作流

### 主分支策略
```
main (master)     → 生产版本 (v1.6, v1.7...)
├─ dev            → 开发分支
   ├─ feature/信号监控优化
   ├─ feature/新增厂商识别
   └─ bugfix/修复扫描超时
```

### 提交信息规范
```
feat: 新增WiFi 6E支持
fix: 修复信道分析崩溃问题
perf: 优化扫描性能 (15s → 5s)
docs: 更新README文档
style: 代码格式化
refactor: 重构网络概览模块
test: 添加单元测试
chore: 更新依赖包版本
```

## 🔄 日常开发流程示例

```powershell
# 1. 更新代码前先查看状态
git status

# 2. 创建功能分支
git checkout -b feature/热力图优化

# 3. 修改代码...

# 4. 查看更改
git diff

# 5. 暂存更改
git add wifi_modules/heatmap.py

# 6. 提交
git commit -m "feat: 优化热力图渲染性能"

# 7. 切换回主分支
git checkout main

# 8. 合并功能分支
git merge feature/热力图优化
```

## 📊 版本标签管理

```powershell
# 创建标签
git tag -a v1.6 -m "WiFi专业分析工具 v1.6"

# 查看所有标签
git tag

# 查看标签信息
git show v1.6

# 推送标签到远程（如果有远程仓库）
git push origin v1.6
```

## ⚠️ 注意事项

1. **敏感信息保护**
   - 不要提交密码、API密钥等敏感信息
   - 使用 `.gitignore` 忽略配置文件

2. **大文件处理**
   - 避免提交大于100MB的文件
   - 日志文件、数据文件应添加到 `.gitignore`

3. **提交频率**
   - 每完成一个小功能就提交
   - 提交信息要清晰描述更改内容

4. **分支清理**
   - 合并后删除不需要的分支
   ```powershell
   git branch -d feature/已完成的功能
   ```

## 🔗 远程仓库配置（可选）

如需同步到GitHub/Gitee：

```powershell
# 添加远程仓库
git remote add origin https://github.com/你的用户名/WiFiProfessional.git

# 推送到远程
git push -u origin main

# 拉取远程更改
git pull origin main
```

---

**文档生成时间**: 2026-02-05
**项目版本**: v1.6
