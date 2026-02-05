# WiFi专业分析工具 (独立版)

## 概述
专业的WiFi网络分析工具，提供网络扫描、信号监控、热力图生成、AP部署规划、PCI-DSS安全评估等企业级功能。

## 功能特点
- ✅ WiFi网络扫描与分析
- ✅ 信道分析与可视化
- ✅ 实时信号监控
- ✅ WiFi覆盖热力图
- ✅ AP部署规划优化
- ✅ PCI-DSS安全评估
- ✅ 企业级PDF报告
- ✅ WiFi性能基准测试
- ✅ 信号罗盘测向

## 依赖的Core模块
此独立版本包含以下3个核心模块：

- `core/wifi_analyzer.py` - WiFi分析引擎 (包含OUI厂商识别数据库)
- `core/admin_utils.py` - 权限检测工具
- `core/memory_monitor.py` - 内存监控

## WiFi功能模块 (38个)
完整的 `wifi_modules/` 目录，包括：

### 主要标签页
- `network_overview.py` - 网络概览
- `channel_analysis.py` - 信道分析
- `realtime_monitor_optimized.py` - 实时监控
- `heatmap.py` - 热力图生成
- `deployment.py` - AP部署规划
- `security_tab.py` - 安全评估
- `enterprise_report_tab.py` - 企业报告

### 支持模块
- `theme.py` - ModernTheme亮/暗色主题
- `icon_system.py` - 专业图标系统
- `performance_window.py` - 性能测试窗口
- `pci_dss_security_assessment.py` - PCI-DSS评估
- `enterprise_pdf_generator.py` - PDF报告生成器
- 以及其他30+个支持模块

## 运行方式

### Windows
双击 `启动WiFi专业工具.bat`

### 命令行
```bash
cd WiFiProfessional
python wifi_professional.py
```

## 系统要求
- Windows 7/8/10/11
- Python 3.6+
- **需要管理员权限** (WiFi扫描需要)

## 依赖库
```
psutil>=5.9.0
pandas>=1.3.0
numpy>=1.21.0
matplotlib>=3.5.0
scipy>=1.9.0
scikit-learn>=1.0.0
reportlab>=3.6.0
```

安装依赖：
```bash
pip install -r requirements.txt
```

## 独立性说明
此版本是**完全独立**的，包含了：
- 所有必要的core模块
- 完整的wifi_modules目录
- 独立的配置文件

可以单独复制此文件夹到其他位置运行，无需依赖项目根目录。

## OUI厂商识别
内置336条WiFi设备厂商OUI数据库，识别率97.6%：
- 华为、小米、TP-Link、Cisco等主流厂商
- 三级查询架构：本地缓存 → LRU缓存 → 在线API
- 查询速度 < 1ms

## 版本信息
- 版本：v1.6
- 开发者：NL@China_SZ
- 最后更新：2026-02-05

## 功能亮点
- 🎨 现代化UI设计（亮/暗色主题）
- 📊 专业级数据可视化
- 🔒 PCI-DSS安全合规检查
- 📈 实时性能监控
- 🗺️ 智能热力图生成
- 📋 企业级PDF报告
