# WiFi专业分析工具 - 模块结构文档

## 📊 模块职责清单

本文档明确定义各功能模块的职责边界，避免功能重复。

---

## 🎯 核心模块 (core/)

### WiFiAnalyzer (core/wifi_analyzer.py)
**职责**:  
- WiFi网络扫描（Windows netsh命令封装）
- 网络数据解析（SSID、BSSID、信号强度、频道等）
- 适配器管理和检测

**接口**:
- `scan_networks()` - 扫描WiFi网络
- `get_adapters()` - 获取网络适配器列表
- `get_current_wifi_info()` - 获取当前连接信息

**使用者**: 所有标签页模块

---

## 🏷️ 标签页模块 (wifi_modules/)

### 1. 网络概览 (network_overview.py)
**核心职责**:
- WiFi网络列表展示
- 基本信号信息显示（SSID、BSSID、信号强度、频道）
- 网络连接/断开操作
- 信号罗盘测向（12方向RSSI扫描）
- 优化的12等分雷达图

**禁止功能**:
- ❌ 信道分析（由channel_analysis负责）
- ❌ 实时监控（由realtime_monitor负责）
- ❌ 热力图生成（由heatmap负责）

**数据导出**: 使用 `export_utils.DataExporter`

---

### 2. 信道分析 (channel_analysis.py)
**核心职责**:
- 2.4GHz/5GHz/6GHz全频段信道分析
- 信道利用率计算（IEEE 802.11干扰算法）
- 信道拥塞检测和推荐
- 全球8个地区信道规范
- DFS信道识别
- 信道绑定分析（20/40/80/160/320MHz）

**可视化**: 信道利用率柱状图、频谱分布图

**数据导出**: 信道分析报告（文本格式）

---

### 3. 实时监控 (realtime_monitor_optimized.py)
**核心职责**:
- 周期性WiFi扫描（可配置间隔）
- 信号强度实时追踪
- 频谱图可视化
- 信号趋势分析
- 信号警报管理（阈值检测）

**可视化**: 
- 使用 `visualization_utils.SpectrumVisualizer` 绘制频谱图
- 时间序列趋势图

**数据导出**: 使用 `export_utils.DataExporter.export_monitoring_data()`

**性能优化**:
- 数据队列缓冲
- Pandas DataFrame存储
- Blitting技术绘图优化

---

### 4. 信号热力图 (heatmap.py)
**核心职责**:
- 测量点数据采集（手动/网格/快速）
- 信号强度插值（RBF/Kriging/IDW）
- 2D热力图可视化
- 3D曲面图
- 多频段支持（2.4G/5G/6G/最佳信号）
- AP位置标注
- 障碍物绘制

**可视化**: 
- 使用 `visualization_utils.HeatmapVisualizer` 生成热力图
- 质量分级颜色映射

**数据导出**: 使用 `export_utils.DataExporter.export_heatmap_data()`

**特殊功能**:
- 信号传播动画
- 历史对比分析
- 场景化优化（办公室/医院/工厂等）

---

### 5. 部署优化 (deployment.py)
**核心职责**:
- 平面图上传和显示
- 交互式测量点添加（点击画布）
- AP位置规划和推荐（KMeans聚类）
- 障碍物绘制（墙体/门）
- 信号传播模型（路径损耗计算）
- 覆盖率分析

**可视化**: 
- 使用 `visualization_utils.HeatmapVisualizer` 生成覆盖热力图
- 平面图叠加显示

**优化算法**:
- KMeans聚类（推荐AP位置）
- RBF插值（信号预测）
- 差分进化（AP位置优化）

---

### 6. 安全检测 (security_tab.py)
**核心职责**:
- WPS漏洞扫描（CVE数据库）
- Evil Twin检测（BSSID相似度）
- 密码强度分析
- 安全风险评分（0-100）
- DNS劫持检测

**安全模块** (wifi_modules/security/):
- `vulnerability.py` - 漏洞检测器
- `password.py` - 密码分析器
- `scoring.py` - 评分计算器
- `dns_enhanced.py` - DNS检测器

**数据导出**: 安全评估报告（文本格式）

---

### 7. 企业报告 (enterprise_report_tab.py)
**核心职责**:
- 多点位信号采集
- 综合信号质量分析
- 企业级PDF报告生成
- PCI-DSS合规性评估

**分析引擎** (enterprise_signal_analyzer.py):
- 信号分布统计
- 覆盖质量分析
- 干扰评估
- 容量规划建议

**报告生成器** (enterprise_pdf_generator.py):
- PDF格式输出
- 多图表嵌入
- 专业排版

**禁止功能**:
- ❌ 自己实现信道分析（调用channel_analysis API）

---

### 8. WiFi 6/6E 分析器 (wifi6_analyzer_tab.py)
**核心职责**:
- WiFi 6特性检测（OFDMA、BSS Color、TWT、MU-MIMO）
- HE能力分析
- WiFi 6E 6GHz频段支持
- WiFi 6网络综合评分

**分析引擎** (wifi6_analyzer.py):
- OFDMA效率分析
- BSS颜色冲突检测
- TWT节能评估
- MU-MIMO性能预测

**数据导出**: 使用 `export_utils.DataExporter.export_wifi6_analysis()`

**独特功能**: 无其他模块重叠

---

### 9. 智能干扰定位器 (interference_locator_tab.py)
**核心职责**:
- RSSI三角定位
- 干扰源类型识别（6种：微波炉/蓝牙/电话/摄像头/ZigBee/WiFi）
- 干扰严重程度评估（5级）
- 缓解策略生成
- 干扰强度热力图

**定位引擎** (interference_locator.py):
- 对数距离路径损耗模型
- Trilateration算法
- 频率特征分析

**可视化**:
- 2D定位地图（Matplotlib）
- 干扰热力图

**数据导出**: 使用 `export_utils.DataExporter.export_interference_report()`

**独特功能**: 无其他模块重叠

---

## 🛠️ 工具模块 (wifi_modules/)

### 可视化工具 (visualization_utils.py) ✨新增
**职责**:
- 热力图绘制（RBF/Kriging/IDW插值）
- 频谱图绘制（现代/经典风格）
- 雷达图绘制（极坐标投影）

**类**:
- `HeatmapVisualizer` - 热力图生成器
- `SpectrumVisualizer` - 频谱图生成器
- `RadarVisualizer` - 雷达图生成器

**使用者**:
- heatmap.py
- deployment.py
- realtime_monitor_optimized.py
- network_overview.py（雷达图）

---

### 数据导出工具 (export_utils.py) ✨新增
**职责**:
- CSV导出（通用格式）
- JSON导出（通用格式）
- 专用导出方法（监控数据、热力图、WiFi6、干扰报告）

**类**:
- `DataExporter` - 统一导出接口

**方法**:
- `export_to_csv()` - 通用CSV导出
- `export_to_json()` - 通用JSON导出
- `export_monitoring_data()` - 监控数据专用
- `export_heatmap_data()` - 热力图项目专用
- `export_wifi6_analysis()` - WiFi 6报告专用
- `export_interference_report()` - 干扰报告专用

**使用者**: 所有需要导出功能的模块

---

## ⚠️ 已识别的重复功能（待处理）

### ✅ 已完成优化 (3/7)

#### P0-1: 统一信号可视化工具
- 状态: ✅ 已完成
- 创建: `wifi_modules/visualization_utils.py` (500行)
- 影响模块: heatmap.py, deployment.py
- 代码减少: ~400行

#### P0-2: 统一WiFi扫描接口
- 状态: ✅ 已完成
- 修改: wifi_modules/wifi6_analyzer.py
- 核心API: core.wifi_analyzer.WiFiAnalyzer.scan_wifi_networks()
- 影响:
  * wifi6_analyzer.py: 移除_scan_windows/_scan_linux/_scan_macos (减少~200行)
  * network_overview.py: 已使用统一API ✓
  * realtime_monitor_optimized.py: 已使用统一API ✓
  * interference_locator.py: 不需要修改(测量点模式)
- 优势:
  * 统一跨平台扫描逻辑
  * 自动缓存与重试机制
  * 线程安全保证
- 代码减少: ~200行

#### P1-2: 统一数据导出工具
- 状态: ✅ 已完成
- 创建: `wifi_modules/export_utils.py` (280行)
- 影响模块: 所有需要导出的模块
- 代码减少: ~250行（待集成）

### 🔴 高优先级 (待处理)

1. **信道分析** - 3个模块重复实现
   - **解决方案**: 保留 `channel_analysis.py`，其他调用其API
   - **待修改**: network_overview._show_channel_analysis() 删除，enterprise_report 调用API
   - 预计减少: ~300行

### 🟡 中优先级 (待处理)

2. **频率/信道转换** - 3处重复
   - **解决方案**: 统一到 `core/utils.py`
   - **待修改**: wifi6_analyzer.py, test_utils.py
   - 预计减少: ~80行

3. **频段识别** - 多模块重复
   - **解决方案**: `core/utils.py` 添加 `get_frequency_band()`
   - 预计减少: ~50行

---

## 📈 优化成果总结

### 已完成 (3/7任务, 43%)
- **总计减少代码**: ~600行重复代码
  * P0-1可视化工具: ~400行
  * P0-2 WiFi扫描统一: ~200行
  * P1-2导出工具: 已创建基础设施

### 待完成 (4/7任务)
- **预计减少代码**: ~430行
  * P1-1信道分析: ~300行
  * P2-2频率转换: ~80行
  * P2-3频段识别: ~50行

### 完成后预期
- **总计减少**: ~1030行重复代码
- **代码复用率**: 提升约35%
- **维护成本**: 降低约40%

---

## 📝 版本历史

### v2.0 (2026-02-05)
- ✅ 创建 `visualization_utils.py` - 统一可视化工具
- ✅ 创建 `export_utils.py` - 统一导出工具
- ✅ 优化 `heatmap.py` 和 `deployment.py` 使用新工具
- ✅ 统一WiFi扫描接口到 `core/wifi_analyzer.py`
- ✅ 重构 `wifi6_analyzer.py` 移除平台特定扫描代码
- ✅ 清理备份文件
- ✅ 创建本文档明确模块职责

### 待实施
- ⏳ 整合信道分析功能
- ⏳ 创建频率/信道转换工具
- ⏳ 统一频段识别逻辑

---

## 🎯 开发原则

1. **单一职责**: 每个模块只负责一个核心功能领域
2. **避免重复**: 优先使用工具模块，不重复实现相同逻辑
3. **清晰边界**: 模块间通过明确API通信，不直接访问内部实现
4. **统一接口**: 相同功能使用相同工具类（如可视化、导出）

---

## 📧 联系方式

**开发者**: NL@China_SZ  
**版本**: WiFi Professional Tool v1.6.3  
**最后更新**: 2026年2月5日
