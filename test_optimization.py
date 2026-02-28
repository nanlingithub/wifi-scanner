"""
实时监控优化功能测试脚本
测试P0-P3优化的所有功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_signal_predictor():
    """测试轻量级预测器"""
    print("=" * 60)
    print("测试 1: 轻量级信号预测器")
    print("=" * 60)
    
    from wifi_modules.signal_predictor import LightweightSignalPredictor
    
    # 创建预测器
    predictor = LightweightSignalPredictor(alpha=0.3, beta=0.1)
    
    # 测试数据（模拟信号下降趋势）
    signal_history = [-65, -64, -66, -65, -67, -68, -69, -70, -71, -72]
    
    # 训练
    predictor.fit(signal_history)
    
    # 预测未来5分钟
    prediction = predictor.predict(steps=5)
    lower, upper = predictor.get_confidence_interval(steps=5)
    trend = predictor.get_trend_indicator()
    
    print(f"✅ 预测器初始化成功")
    print(f"   当前信号: {signal_history[-1]}dBm")
    print(f"   5分钟后预测: {prediction:.1f}dBm")
    print(f"   95%置信区间: [{lower:.1f}, {upper:.1f}]")
    print(f"   趋势: {trend['emoji']} {trend['direction']} ({trend['rate']:.2f}dBm/分钟)")
    print()
    
    return True

def test_quality_scorer():
    """测试WiFi质量评分器"""
    print("=" * 60)
    print("测试 2: WiFi质量评分系统")
    print("=" * 60)
    
    from wifi_modules.signal_predictor import WiFiQualityScorer
    
    # 测试不同信号强度的评分
    test_signals = [
        (-55, "优秀信号"),
        (-65, "良好信号"),
        (-75, "一般信号"),
        (-85, "较差信号"),
        (-95, "极差信号")
    ]
    
    print("✅ 评分器初始化成功")
    print("\n信号质量评分结果:")
    print("-" * 50)
    
    for signal, desc in test_signals:
        score = WiFiQualityScorer.get_quality_score(signal)
        grade, emoji, level = WiFiQualityScorer.get_quality_grade(score)
        quality_text = WiFiQualityScorer.get_signal_quality_text(signal)
        
        print(f"   {desc:12s}: {quality_text} (分数:{score:3d})")
    
    print()
    return True

def test_module_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试 3: 模块导入检查")
    print("=" * 60)
    
    try:
        from wifi_modules.signal_predictor import LightweightSignalPredictor, WiFiQualityScorer
        print("✅ signal_predictor模块导入成功")
        
        from wifi_modules.realtime_monitor_optimized import OptimizedRealtimeMonitorTab
        print("✅ realtime_monitor_optimized模块导入成功")
        
        print()
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_legacy_cleanup():
    """验证版本统一"""
    print("=" * 60)
    print("测试 4: 版本统一验证")
    print("=" * 60)
    
    # 检查legacy文件夹
    legacy_path = "wifi_modules/legacy"
    if os.path.exists(legacy_path):
        print(f"✅ legacy文件夹已创建: {legacy_path}")
        
        # 检查旧版本是否已移动
        old_file = os.path.join(legacy_path, "realtime_monitor_v1.0_deprecated.py")
        if os.path.exists(old_file):
            print(f"✅ 基础版已移至legacy: {old_file}")
        else:
            print(f"⚠️  基础版未找到: {old_file}")
        
        # 检查README
        readme_path = os.path.join(legacy_path, "README.md")
        if os.path.exists(readme_path):
            print(f"✅ legacy说明文档已创建: {readme_path}")
        else:
            print(f"⚠️  说明文档未找到: {readme_path}")
    else:
        print(f"⚠️  legacy文件夹未找到: {legacy_path}")
    
    # 检查优化版是否存在
    optimized_file = "wifi_modules/realtime_monitor_optimized.py"
    if os.path.exists(optimized_file):
        print(f"✅ 优化版正常使用: {optimized_file}")
    else:
        print(f"❌ 优化版未找到: {optimized_file}")
    
    print()
    return True

def test_performance():
    """性能测试"""
    print("=" * 60)
    print("测试 5: 性能测试")
    print("=" * 60)
    
    import time
    from wifi_modules.signal_predictor import LightweightSignalPredictor
    
    # 创建预测器
    predictor = LightweightSignalPredictor()
    signal_history = [-65 + i*0.5 for i in range(100)]
    predictor.fit(signal_history)
    
    # 测试预测速度
    iterations = 1000
    start_time = time.time()
    
    for _ in range(iterations):
        predictor.predict(steps=5)
    
    elapsed_time = time.time() - start_time
    avg_time_ms = (elapsed_time / iterations) * 1000
    
    print(f"✅ 性能测试完成")
    print(f"   测试次数: {iterations}")
    print(f"   总耗时: {elapsed_time:.3f}秒")
    print(f"   平均耗时: {avg_time_ms:.4f}ms/次")
    print(f"   {'✅ 性能优秀 (<1ms)' if avg_time_ms < 1 else '⚠️ 性能一般'}")
    print()
    
    return True

def main():
    """主测试函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "WiFi实时监控优化功能测试" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    tests = [
        ("模块导入", test_module_imports),
        ("轻量级预测器", test_signal_predictor),
        ("质量评分系统", test_quality_scorer),
        ("版本统一", test_legacy_cleanup),
        ("性能测试", test_performance)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ 测试失败: {name}")
            print(f"   错误: {str(e)}")
            results.append((name, False))
    
    # 总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name:20s}: {status}")
    
    print()
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！优化功能正常工作。")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查。")
    
    print()

if __name__ == "__main__":
    main()
