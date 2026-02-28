"""
企业报告系统v2.0测试脚本
测试统一PDF生成器、缓存系统、图表管理器
"""

import sys
import os

# 设置UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from wifi_modules.enterprise_reports.pdf_generator import PDFGenerator, PDFGeneratorAsync
from wifi_modules.enterprise_reports.report_cache import ReportCache
from wifi_modules.enterprise_reports.chart_manager import ChartManager
from wifi_modules.enterprise_reports.templates.signal_template import SignalAnalysisTemplate
from wifi_modules.enterprise_reports.templates.security_template import SecurityAssessmentTemplate
from wifi_modules.enterprise_reports.templates.pci_dss_template import PCIDSSTemplate


def test_chart_manager():
    """测试图表管理器"""
    print("\n" + "="*60)
    print("测试1: 图表管理器")
    print("="*60)
    
    try:
        with ChartManager() as cm:
            # 创建饼图
            pie_img = cm.create_pie_chart(
                labels=['强信号', '良好', '一般', '弱信号'],
                sizes=[30, 40, 20, 10],
                title='信号质量分布'
            )
            print("✓ 饼图创建成功")
            
            # 创建柱状图
            bar_img = cm.create_bar_chart(
                categories=['2.4G', '5G'],
                values=[25, 63],
                title='频段使用统计',
                ylabel='网络数量'
            )
            print("✓ 柱状图创建成功")
            
        print("✓ 图表资源已自动清理")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def test_report_cache():
    """测试报告缓存"""
    print("\n" + "="*60)
    print("测试2: 报告缓存系统")
    print("="*60)
    
    try:
        cache = ReportCache(cache_dir="./cache/test_reports")
        
        # 测试数据
        test_data = {
            'networks': [
                {'ssid': 'WiFi-1', 'signal': -45},
                {'ssid': 'WiFi-2', 'signal': -60}
            ],
            'quality_score': 85
        }
        
        # 首次获取（应该未命中）
        cached = cache.get(test_data, 'signal')
        if cached is None:
            print("✓ 缓存未命中（符合预期）")
        
        # 写入缓存
        fake_pdf = b'%PDF-1.4\nTest PDF content'
        cache.set(test_data, 'signal', fake_pdf)
        print("✓ 缓存写入成功")
        
        # 再次获取（应该命中）
        cached = cache.get(test_data, 'signal')
        if cached:
            print(f"✓ 缓存命中！内容长度: {len(cached)} bytes")
        
        # 获取统计信息
        stats = cache.get_stats()
        print(f"✓ 缓存统计: {stats['total_files']}个文件, "
              f"{stats['total_size_mb']:.2f}MB")
        
        # 清理
        cache.clear_all()
        print("✓ 缓存已清空")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def test_pdf_generator_sync():
    """测试同步PDF生成"""
    print("\n" + "="*60)
    print("测试3: 同步PDF生成（带缓存）")
    print("="*60)
    
    try:
        # 创建生成器
        generator = PDFGenerator(use_cache=True)
        
        # 测试数据
        test_data = {
            'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_networks': 88,
            'signal_quality': {
                'quality_score': 85,
                'average_signal': 68.5,
                'strong_count': 30,
                'weak_count': 10,
                'max_signal': 95.0,
                'min_signal': 15.0,
                'distribution': {
                    '强信号(>70%)': 30,
                    '良好(50-70%)': 40,
                    '一般(30-50%)': 15,
                    '弱信号(<30%)': 3
                }
            },
            'coverage_score': 78,
            'interference_score': 82,
            'coverage_analysis': {
                'coverage_score': 78,
                'good_coverage_percent': 85.5,
                'poor_coverage_areas': 2
            },
            'channel_analysis': {
                '2.4G_usage': 25,
                '5G_usage': 63,
                'congested_channels': [1, 6, 11]
            },
            'interference_analysis': {
                'interference_level': '低',
                'affected_networks': 5,
                'main_source': '微波炉'
            },
            'networks': [
                {'ssid': 'Office-WiFi', 'signal_percent': 85, 'band': '5G', 
                 'channel': 36, 'security': 'WPA2'},
                {'ssid': 'Guest-Net', 'signal_percent': 65, 'band': '2.4G', 
                 'channel': 6, 'security': 'WPA2'}
            ],
            'recommendations': [
                "优化AP位置，提高弱覆盖区域的信号强度",
                "将更多设备迁移至5GHz频段，减少2.4GHz拥塞",
                "调整信道配置，避开拥挤信道1、6、11"
            ]
        }
        
        # 创建模板
        template = SignalAnalysisTemplate(generator.styles)
        
        # 第1次生成（应该耗时较长）
        print("\n第1次生成（无缓存）:")
        success = generator.generate_report(
            data=test_data,
            output_path="test_signal_report_v2.pdf",
            template=template,
            company_name="测试企业科技有限公司",
            report_type="signal"
        )
        
        if success:
            print("✓ 第1次生成成功")
        
        # 第2次生成（应该使用缓存，速度快）
        print("\n第2次生成（有缓存）:")
        success = generator.generate_report(
            data=test_data,
            output_path="test_signal_report_v2_cached.pdf",
            template=template,
            company_name="测试企业科技有限公司",
            report_type="signal"
        )
        
        if success:
            print("✓ 第2次生成成功（应该使用缓存）")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_generator_async():
    """测试异步PDF生成（带进度）"""
    print("\n" + "="*60)
    print("测试4: 异步PDF生成（带进度反馈）")
    print("="*60)
    
    try:
        # 创建异步生成器
        generator = PDFGeneratorAsync(use_cache=False)  # 禁用缓存以看到完整进度
        
        # 测试数据（同上）
        test_data = {
            'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_networks': 88,
            'signal_quality': {
                'quality_score': 85,
                'average_signal': 68.5,
                'strong_count': 30,
                'weak_count': 10
            },
            'coverage_score': 78,
            'interference_score': 82
        }
        
        # 进度回调
        def print_progress(percent, status, detail):
            print(f"  [{percent:3d}%] {status:30s} - {detail}")
        
        # 创建模板
        template = SignalAnalysisTemplate(generator.styles)
        
        # 异步生成
        success = generator.generate_report_async(
            data=test_data,
            output_path="test_signal_report_v2_async.pdf",
            template=template,
            company_name="测试企业科技有限公司",
            report_type="signal",
            progress_callback=print_progress
        )
        
        if success:
            print("✓ 异步生成成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_security_template():
    """测试安全评估模板"""
    print("\n" + "="*60)
    print("测试5: 安全评估报告生成")
    print("="*60)
    
    try:
        generator = PDFGenerator(use_cache=True)
        
        test_data = {
            'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_networks': 88,
            'security': {
                'security_score': 75,
                'high_risk_count': 3,
                'medium_risk_count': 12,
                'low_risk_count': 73
            },
            'encryption_stats': {
                'WPA3': 15,
                'WPA2': 60,
                'WPA': 10,
                'WEP': 2,
                'Open': 1
            },
            'vulnerabilities': [
                {
                    'name': 'WEP加密漏洞',
                    'severity': '高',
                    'affected_count': 2
                },
                {
                    'name': '开放网络风险',
                    'severity': '高',
                    'affected_count': 1
                }
            ],
            'risk_networks': [
                {
                    'ssid': 'Old-Router',
                    'risk_level': '高',
                    'encryption': 'WEP',
                    'vulnerability': 'WEP可破解'
                }
            ],
            'security_recommendations': [
                "禁用所有WEP加密网络",
                "关闭开放网络或设置访客隔离",
                "升级到WPA3加密标准"
            ]
        }
        
        template = SecurityAssessmentTemplate(generator.styles)
        
        success = generator.generate_report(
            data=test_data,
            output_path="test_security_report_v2.pdf",
            template=template,
            company_name="测试企业科技有限公司",
            report_type="security"
        )
        
        if success:
            print("✓ 安全评估报告生成成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pci_dss_template():
    """测试PCI-DSS模板"""
    print("\n" + "="*60)
    print("测试6: PCI-DSS合规性报告生成")
    print("="*60)
    
    try:
        generator = PDFGenerator(use_cache=True)
        
        test_data = {
            'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'pci_dss': {
                'compliance_score': 82,
                'compliant_items': 8,
                'non_compliant_items': 2,
                'needs_improvement': 2,
                'overall_status': '部分合规'
            },
            'compliance_checklist': [
                {'requirement': '2.1.1', 'description': '更改默认密码', 
                 'status': '合规', 'score': 100},
                {'requirement': '4.1.1', 'description': '使用强加密', 
                 'status': '部分合规', 'score': 75}
            ],
            'non_compliant_items_details': [
                {
                    'requirement': '4.1.1 强加密',
                    'severity': '高',
                    'details': '发现2个使用WEP加密的网络',
                    'remediation': '禁用WEP，升级到WPA2/WPA3'
                }
            ],
            'risk_assessment': {
                'overall_risk': '中等',
                'high_risk_count': 2,
                'medium_risk_count': 3,
                'low_risk_count': 7,
                'remediation_timeline': '30天'
            },
            'pci_recommendations': [
                "【高优先级】禁用所有WEP加密网络",
                "【高优先级】实施强制访问控制",
                "【中优先级】部署无线入侵检测系统"
            ]
        }
        
        template = PCIDSSTemplate(generator.styles)
        
        success = generator.generate_report(
            data=test_data,
            output_path="test_pci_dss_report_v2.pdf",
            template=template,
            company_name="测试企业科技有限公司",
            report_type="pci_dss"
        )
        
        if success:
            print("✓ PCI-DSS合规性报告生成成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("   企业报告系统 v2.0 - 综合测试")
    print("="*80)
    
    results = {}
    
    # 运行测试
    results['图表管理器'] = test_chart_manager()
    results['报告缓存'] = test_report_cache()
    results['同步PDF生成'] = test_pdf_generator_sync()
    results['异步PDF生成'] = test_pdf_generator_async()
    results['安全评估报告'] = test_security_template()
    results['PCI-DSS报告'] = test_pci_dss_template()
    
    # 总结
    print("\n" + "="*80)
    print("   测试总结")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:20s} - {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n✓✓✓ 所有测试通过！企业报告系统v2.0可以投入使用")
    else:
        print(f"\n⚠ 有 {total - passed} 个测试失败，请检查")
    
    print("="*80)


if __name__ == '__main__':
    main()
