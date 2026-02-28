# WiFi专业工具 - 自动化测试文档

## 📋 目录

- [快速开始](#快速开始)
- [测试运行方式](#测试运行方式)
- [测试类型](#测试类型)
- [覆盖率报告](#覆盖率报告)
- [CI/CD集成](#cicd集成)
- [测试编写指南](#测试编写指南)
- [故障排除](#故障排除)

---

## 🚀 快速开始

### 1. 安装测试依赖

```bash
pip install pytest pytest-cov pytest-html pytest-xdist
```

### 2. 运行所有测试

```bash
# 方式1: 使用Python脚本
python run_tests.py

# 方式2: 使用批处理脚本（Windows）
运行测试.bat

# 方式3: 直接使用pytest
pytest -v
```

### 3. 查看报告

测试完成后，报告生成在 `test_reports/` 目录：
- **HTML测试报告**: `test_reports/report_*.html`
- **覆盖率报告**: `test_reports/coverage/index.html`
- **JUnit XML**: `test_reports/junit.xml`

---

## 🧪 测试运行方式

### 基础用法

```bash
# 运行所有测试（带覆盖率和HTML报告）
python run_tests.py

# 快速测试（跳过慢速测试）
python run_tests.py --quick

# 显示测试摘要
python run_tests.py --summary

# 列出所有测试
python run_tests.py --list
```

### 高级用法

```bash
# 运行特定测试文件
python run_tests.py --file test_wifi6_analyzer.py

# 运行特定测试函数
python run_tests.py --file test_wifi6_analyzer.py::test_scan_wifi6_networks

# 按标记运行测试
python run_tests.py --marker integration
python run_tests.py --marker performance
python run_tests.py --marker slow

# 重新运行失败的测试
python run_tests.py --failed

# CI模式（完整报告）
python run_tests.py --ci

# 不生成覆盖率报告
python run_tests.py --no-coverage

# 不生成HTML报告
python run_tests.py --no-html
```

### 直接使用pytest

```bash
# 基础运行
pytest

# 详细输出
pytest -v

# 显示print输出
pytest -s

# 并行运行（需要pytest-xdist）
pytest -n auto

# 运行最慢的10个测试
pytest --durations=10

# 代码覆盖率
pytest --cov=core --cov=wifi_modules --cov-report=html

# 生成HTML报告
pytest --html=report.html --self-contained-html
```

---

## 🏷️ 测试类型

项目中的测试按以下标记分类：

### 1. admin_required
需要管理员权限的测试

```bash
# 运行需要管理员权限的测试
python run_tests.py --marker admin_required
```

**示例**:
- WiFi扫描测试
- 网络连接测试

### 2. integration
集成测试（测试多个模块协作）

```bash
python run_tests.py --marker integration
```

**示例**:
- WiFi扫描 + 数据解析
- 热力图生成 + 可视化
- 企业报告生成

### 3. performance
性能测试（测试执行时间和资源消耗）

```bash
python run_tests.py --marker performance
```

**示例**:
- 大量网络扫描性能
- 热力图插值算法性能
- 内存使用测试

### 4. slow
慢速测试（运行时间 > 5秒）

```bash
# 运行慢速测试
python run_tests.py --marker slow

# 跳过慢速测试
python run_tests.py --quick
# 或
pytest -m "not slow"
```

---

## 📊 覆盖率报告

### 查看覆盖率

测试运行后，覆盖率报告自动生成：

```bash
# 在浏览器中打开HTML报告
start test_reports/coverage/index.html  # Windows
open test_reports/coverage/index.html   # macOS
xdg-open test_reports/coverage/index.html  # Linux
```

### 覆盖率目标

| 模块类型 | 目标覆盖率 | 当前覆盖率 |
|---------|----------|----------|
| 核心模块 (core/) | ≥ 80% | 📊 待测试 |
| WiFi模块 (wifi_modules/) | ≥ 70% | 📊 待测试 |
| 工具模块 (utils) | ≥ 90% | 📊 待测试 |

### 提升覆盖率

```bash
# 查看未覆盖的代码行
pytest --cov=core --cov=wifi_modules --cov-report=term-missing

# 生成详细覆盖率报告
python run_tests.py --coverage-only
```

---

## 🔄 CI/CD集成

### GitHub Actions

项目已配置GitHub Actions自动化测试工作流（`.github/workflows/test.yml`）：

**触发条件**:
- Push到 `main` 或 `develop` 分支
- Pull Request
- 每日定时运行（北京时间08:00）
- 手动触发

**测试矩阵**:
- **操作系统**: Windows, Ubuntu, macOS
- **Python版本**: 3.9, 3.10, 3.11, 3.12

**工作流包含**:
1. ✅ 单元测试
2. 📊 覆盖率报告（上传到Codecov）
3. 🔍 代码质量检查（Pylint, Black, Flake8）
4. 🔒 安全扫描（Bandit）
5. ⚡ 性能测试

### 本地CI模拟

```bash
# 运行完整CI测试套件
python run_tests.py --ci
```

这将执行与CI/CD相同的测试流程。

---

## ✍️ 测试编写指南

### 测试文件结构

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试模块名称
测试 xxx 功能
"""

import pytest
from wifi_modules.xxx import XXX


@pytest.fixture
def sample_data():
    """测试数据fixture"""
    return {...}


class TestXXX:
    """XXX类测试"""
    
    def test_basic_function(self):
        """测试基本功能"""
        # Arrange
        obj = XXX()
        
        # Act
        result = obj.method()
        
        # Assert
        assert result is not None
    
    @pytest.mark.integration
    def test_integration(self, sample_data):
        """集成测试"""
        # ...
    
    @pytest.mark.slow
    def test_performance(self):
        """性能测试"""
        import time
        start = time.time()
        # ...
        elapsed = time.time() - start
        assert elapsed < 5.0  # 应在5秒内完成
```

### 使用标记

```python
import pytest

# 标记为集成测试
@pytest.mark.integration
def test_integration():
    pass

# 标记为需要管理员权限
@pytest.mark.admin_required
def test_admin_function():
    pass

# 标记为慢速测试
@pytest.mark.slow
def test_slow_operation():
    pass

# 标记为性能测试
@pytest.mark.performance
def test_performance():
    pass

# 组合标记
@pytest.mark.integration
@pytest.mark.slow
def test_complex_integration():
    pass
```

### 测试命名规范

- **测试文件**: `test_<module_name>.py`
- **测试类**: `Test<ClassName>`
- **测试函数**: `test_<function_name>`

示例:
```
tests/
├── test_wifi_analyzer.py
│   ├── TestWiFiAnalyzer
│   │   ├── test_scan_networks()
│   │   ├── test_get_adapters()
│   │   └── test_parse_network_info()
│   └── TestNetworkInfo
│       ├── test_signal_strength()
│       └── test_frequency_band()
```

### 使用Fixtures

```python
@pytest.fixture
def wifi_analyzer():
    """WiFi分析器fixture"""
    from core.wifi_analyzer import WiFiAnalyzer
    analyzer = WiFiAnalyzer()
    yield analyzer
    # 清理代码
    analyzer.cleanup()

def test_scan(wifi_analyzer):
    """使用fixture的测试"""
    networks = wifi_analyzer.scan_networks()
    assert len(networks) > 0
```

### Mock外部依赖

```python
from unittest.mock import Mock, patch

@patch('subprocess.run')
def test_with_mock(mock_run):
    """使用Mock测试"""
    # 设置mock返回值
    mock_run.return_value = Mock(
        returncode=0,
        stdout="SSID : TestWiFi"
    )
    
    # 执行测试
    result = my_function()
    
    # 验证
    assert result == expected
    mock_run.assert_called_once()
```

---

## 🐛 故障排除

### 常见问题

#### 1. ModuleNotFoundError

**问题**: `ModuleNotFoundError: No module named 'xxx'`

**解决方案**:
```bash
# 安装缺失的依赖
pip install -r requirements.txt

# 如果是测试依赖
pip install pytest pytest-cov pytest-html
```

#### 2. 权限错误

**问题**: WiFi扫描测试失败（权限不足）

**解决方案**:
```bash
# Windows: 以管理员身份运行
# 或跳过需要管理员权限的测试
pytest -m "not admin_required"
```

#### 3. 测试超时

**问题**: 测试运行时间过长

**解决方案**:
```bash
# 使用快速测试模式
python run_tests.py --quick

# 并行运行测试
pytest -n auto
```

#### 4. 覆盖率报告未生成

**问题**: 找不到覆盖率HTML报告

**解决方案**:
```bash
# 确保安装了pytest-cov
pip install pytest-cov

# 重新生成覆盖率报告
python run_tests.py --coverage-only
```

### 调试技巧

```bash
# 1. 进入pdb调试器（遇到失败时）
pytest --pdb

# 2. 显示完整traceback
pytest --tb=long

# 3. 显示print输出
pytest -s

# 4. 只运行失败的测试
pytest --lf

# 5. 详细输出 + 显示慢速测试
pytest -v --durations=10
```

---

## 📈 测试统计

### 当前测试覆盖

| 模块 | 测试文件 | 测试数量 | 状态 |
|------|---------|---------|------|
| core/wifi_analyzer.py | test_wifi_analyzer.py | ~15个 | ✅ |
| wifi_modules/wifi6_analyzer.py | test_wifi6_analyzer.py | ~12个 | ✅ |
| wifi_modules/heatmap.py | test_heatmap.py | ~25个 | ✅ |
| wifi_modules/security/ | test_security_scoring.py | ~8个 | ✅ |
| core/utils.py | test_utils.py | ~10个 | ✅ |

**总测试数**: ~70个

### 测试运行时间

| 测试类型 | 平均时间 | 备注 |
|---------|---------|------|
| 快速测试 | ~30秒 | 跳过慢速测试 |
| 完整测试 | ~2分钟 | 包含所有测试 |
| CI完整测试 | ~3分钟 | 包含覆盖率+报告生成 |

---

## 🔗 相关资源

- **Pytest文档**: https://docs.pytest.org/
- **Coverage.py文档**: https://coverage.readthedocs.io/
- **pytest-html**: https://pytest-html.readthedocs.io/
- **测试最佳实践**: https://docs.python-guide.org/writing/tests/

---

## 📞 联系与支持

如有测试相关问题，请参考：
- [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md) - 优化报告
- [MODULE_STRUCTURE.md](MODULE_STRUCTURE.md) - 模块结构
- [README.md](README.md) - 项目主文档

---

**文档版本**: 1.0  
**最后更新**: 2026年2月5日  
**维护者**: NL@China_SZ
