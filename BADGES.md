# 测试徽章使用指南

## 📊 测试结果展示

为了直观展示项目测试状态，可以在README.md顶部添加测试徽章：

### 1. Codecov覆盖率徽章

```markdown
[![codecov](https://codecov.io/gh/YOUR_USERNAME/WiFiProfessional/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/WiFiProfessional)
```

### 2. GitHub Actions测试状态

```markdown
[![Tests](https://github.com/YOUR_USERNAME/WiFiProfessional/actions/workflows/test.yml/badge.svg)](https://github.com/YOUR_USERNAME/WiFiProfessional/actions/workflows/test.yml)
```

### 3. Python版本支持

```markdown
[![Python Versions](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
```

### 4. 测试用例数量

```markdown
[![Tests](https://img.shields.io/badge/tests-238%20passed-brightgreen)](https://github.com/YOUR_USERNAME/WiFiProfessional)
```

### 5. 代码覆盖率（本地生成）

```markdown
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)](test_reports/coverage/index.html)
```

### 6. License徽章

```markdown
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
```

---

## 📝 完整示例

在README.md顶部添加所有徽章：

```markdown
# WiFi专业分析工具

[![Tests](https://github.com/YOUR_USERNAME/WiFiProfessional/actions/workflows/test.yml/badge.svg)](https://github.com/YOUR_USERNAME/WiFiProfessional/actions)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/WiFiProfessional/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/WiFiProfessional)
[![Python Versions](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-238%20passed-brightgreen)](#)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)](#)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

专业的WiFi网络分析工具...
```

---

## 🔧 设置Codecov（可选）

1. 访问 https://codecov.io
2. 使用GitHub账号登录
3. 添加WiFiProfessional仓库
4. GitHub Actions会自动上传覆盖率数据

---

## 📈 动态徽章更新

测试徽章会在每次CI运行后自动更新：
- ✅ 测试通过 → 绿色徽章
- ❌ 测试失败 → 红色徽章
- ⚠️ 部分失败 → 黄色徽章

---

**注意**: 将 `YOUR_USERNAME` 替换为实际的GitHub用户名
