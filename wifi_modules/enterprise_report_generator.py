"""
企业级WiFi报告生成器
支持生成PDF格式的专业网络分析报告和PCI-DSS安全评估报告
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
from typing import Dict, List

class EnterpriseReportGenerator:
    """企业级报告生成器"""
    
    def __init__(self):
        self.setup_fonts()
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
        
    def setup_fonts(self):
        """设置中文字体"""
        try:
            # 尝试注册系统中文字体
            font_paths = [
                'C:/Windows/Fonts/msyh.ttc',  # 微软雅黑
                'C:/Windows/Fonts/simhei.ttf',  # 黑体
                'C:/Windows/Fonts/simsun.ttc',  # 宋体
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('Chinese', font_path))
                        print(f"成功注册字体: {font_path}")
                        break
                    except Exception as font_error:
                        print(f"字体{font_path}注册失败: {font_error}")
                        continue
        except Exception as e:
            print(f"字体注册失败: {e}")
    
    def _create_custom_styles(self):
        """创建自定义样式"""
        custom_styles = {}
        
        # 标题样式
        custom_styles['CustomTitle'] = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontName='Chinese',
            fontSize=24,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # 章节标题
        custom_styles['SectionTitle'] = ParagraphStyle(
            'SectionTitle',
            parent=self.styles['Heading2'],
            fontName='Chinese',
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=20,
            spaceAfter=12,
            borderWidth=0,
            borderPadding=5,
            borderColor=colors.HexColor('#3498db'),
            borderRadius=0,
            backColor=colors.HexColor('#ecf0f1')
        )
        
        # 子标题
        custom_styles['SubTitle'] = ParagraphStyle(
            'SubTitle',
            parent=self.styles['Heading3'],
            fontName='Chinese',
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceBefore=12,
            spaceAfter=8
        )
        
        # 正文
        custom_styles['CustomBody'] = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontName='Chinese',
            fontSize=10,
            leading=16,
            textColor=colors.black,
            alignment=TA_JUSTIFY
        )
        
        # 重点文本
        custom_styles['Emphasis'] = ParagraphStyle(
            'Emphasis',
            parent=self.styles['Normal'],
            fontName='Chinese',
            fontSize=11,
            textColor=colors.HexColor('#c0392b'),
            spaceBefore=6,
            spaceAfter=6
        )
        
        return custom_styles
    
    def generate_signal_analysis_report(self, analysis_data: Dict, output_path: str) -> bool:
        """
        生成信号分析报告
        
        Args:
            analysis_data: 分析数据
            output_path: 输出文件路径
            
        Returns:
            是否成功生成
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            
            # 添加封面
            story.extend(self._create_cover_page(
                "企业级WiFi网络信号分析报告",
                analysis_data.get('scan_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            ))
            
            story.append(PageBreak())
            
            # 添加执行摘要
            story.extend(self._create_executive_summary(analysis_data))
            
            # 添加详细分析章节
            story.extend(self._create_signal_quality_section(analysis_data.get('signal_quality', {})))
            story.extend(self._create_coverage_section(analysis_data.get('coverage_analysis', {})))
            story.extend(self._create_interference_section(analysis_data.get('interference_analysis', {})))
            story.extend(self._create_channel_section(analysis_data.get('channel_analysis', {})))
            
            # 添加网络详情
            story.extend(self._create_network_details(analysis_data.get('networks', [])))
            
            # 添加企业级专业分析章节
            story.extend(self._create_capacity_planning_section(analysis_data))
            story.extend(self._create_roaming_analysis_section(analysis_data))
            story.extend(self._create_network_health_assessment(analysis_data))
            
            # 添加建议
            story.extend(self._create_recommendations_section(analysis_data.get('recommendations', [])))
            
            # 生成PDF
            doc.build(story)
            print(f"信号分析报告已生成: {output_path}")
            return True
            
        except Exception as e:
            print(f"生成信号分析报告失败: {e}")
            return False
    
    def generate_security_assessment_report(self, assessment_data: Dict, output_path: str) -> bool:
        """
        生成PCI-DSS安全评估报告（专业深度版）
        
        Args:
            assessment_data: 评估数据
            output_path: 输出文件路径
            
        Returns:
            是否成功生成
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            
            # 添加封面
            story.extend(self._create_cover_page(
                "PCI-DSS 4.0无线网络安全合规性评估报告",
                assessment_data.get('assessment_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            ))
            
            story.append(PageBreak())
            
            # 第1章：执行摘要
            story.extend(self._create_security_executive_summary(assessment_data))
            story.append(PageBreak())
            
            # 第2章：PCI-DSS标准概述
            story.extend(self._create_pci_dss_overview())
            story.append(PageBreak())
            
            # 第3章：评估方法论
            story.extend(self._create_assessment_methodology())
            
            # 第4章：网络环境概况
            story.extend(self._create_network_environment_overview(assessment_data))
            
            # 第5章：加密与认证分析
            story.extend(self._create_encryption_authentication_analysis(assessment_data))
            
            # 第6章：PCI-DSS合规性检查
            story.extend(self._create_pci_compliance_detailed(assessment_data.get('compliance_status', {})))
            
            # 第7章：风险评估与威胁分析
            story.extend(self._create_risk_threat_analysis(assessment_data.get('risk_assessment', {})))
            
            # 第8章：漏洞扫描与检测
            story.extend(self._create_vulnerability_detailed(assessment_data.get('vulnerability_scan', {})))
            
            # 第9章：安全配置审核
            story.extend(self._create_security_configuration_audit(assessment_data))
            
            # 第10章：补救措施与改进建议
            story.extend(self._create_remediation_recommendations(assessment_data.get('recommendations', [])))
            
            # 第11章：合规路线图
            story.extend(self._create_compliance_roadmap(assessment_data))
            
            # 附录
            story.append(PageBreak())
            story.extend(self._create_pci_appendix())
            
            # 生成PDF
            doc.build(story)
            print(f"安全评估报告已生成: {output_path}")
            return True
            
        except Exception as e:
            print(f"生成安全评估报告失败: {e}")
            return False
    
    def _format_auth_display(self, auth_string):
        """将认证方式格式化为友好的中文显示格式
        
        Args:
            auth_string: 标准化的认证方式字符串 (如 "WPA2-Enterprise")
            
        Returns:
            中文显示格式 (如 "WPA2-企业级(802.1X)")
        """
        if not auth_string or auth_string == '未知' or auth_string == 'N/A':
            return '未知'
        
        # 映射标准格式到中文显示
        auth_map = {
            'WPA3-Enterprise': 'WPA3-企业级(802.1X)',
            'WPA2-Enterprise': 'WPA2-企业级(802.1X)',
            'WPA-Enterprise': 'WPA-企业级(802.1X)',
            'WPA3-Personal': 'WPA3-个人',
            'WPA2-Personal': 'WPA2-个人',
            'WPA-Personal': 'WPA-个人',
            'Open': '开放式(无加密)',
            'WEP': 'WEP(已过时)'
        }
        
        return auth_map.get(auth_string, auth_string)
    
    def _create_cover_page(self, title: str, date: str) -> List:
        """创建封面页"""
        elements = []
        
        # 添加空白
        elements.append(Spacer(1, 3*inch))
        
        # 主标题
        elements.append(Paragraph(title, self.custom_styles['CustomTitle']))
        elements.append(Spacer(1, 0.5*inch))
        
        # 日期
        date_style = ParagraphStyle(
            'DateStyle',
            parent=self.custom_styles['CustomBody'],
            fontSize=12,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(f"生成时间: {date}", date_style))
        elements.append(Spacer(1, 1*inch))
        
        # 报告说明
        company_style = ParagraphStyle(
            'CompanyStyle',
            parent=self.custom_styles['CustomBody'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        elements.append(Paragraph("企业级无线网络专业分析报告", company_style))
        elements.append(Paragraph("基于IEEE 802.11标准与PCI-DSS安全框架", company_style))
        
        return elements
    
    def _create_executive_summary(self, data: Dict) -> List:
        """创建执行摘要（企业级增强版）"""
        elements = []
        
        elements.append(Paragraph("执行摘要", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        # 添加概述段落
        networks = data.get('networks', [])
        signal_quality = data.get('signal_quality', {})
        avg_signal = signal_quality.get('average_signal', 0)
        
        overview_text = f"""
        本次无线网络专业评估覆盖了企业环境中的<b>{len(networks)}个SSID</b>，
        检测到<b>{sum(net.get('ap_count', 1) for net in networks)}个接入点(AP)</b>。
        总体信号强度平均值为<b>{avg_signal:.1f}%</b>（{self._signal_to_dbm(avg_signal):.0f} dBm），
        质量评级为<b>{signal_quality.get('quality_rating', '未知')}</b>。
        评估基于<b>IEEE 802.11</b>无线标准，采用企业级网络管理最佳实践，
        从<b>性能、可靠性、安全性、可扩展性</b>四个维度进行深度分析，
        涵盖信号覆盖、频谱利用、信道规划、漫游性能、容量评估及安全合规等
        关键领域，为企业无线网络优化提供数据支撑和决策依据。
        """
        elements.append(Paragraph(overview_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 16))
        
        # 业务影响评估
        elements.append(Paragraph("业务影响评估", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 8))
        
        business_impact = self._assess_business_impact(data)
        impact_text = f"""
        <b>网络可用性</b>: {business_impact['availability']}<br/>
        <b>用户体验</b>: {business_impact['user_experience']}<br/>
        <b>业务风险</b>: {business_impact['business_risk']}<br/>
        <b>优化紧迫性</b>: {business_impact['urgency']}
        """
        elements.append(Paragraph(impact_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 16))
        
        # 企业级关键指标摘要
        channel_data = data.get('channel_analysis', {})
        interference = data.get('interference_analysis', {})
        
        summary_data = [
            ['评估维度', '指标值', '评级/状态', '企业标准'],
            ['评估时间', data.get('scan_time', 'N/A'), f"耗时{data.get('duration', 0)}秒", '-'],
            ['网络规模', f"{len(networks)}个SSID", f"{sum(net.get('ap_count', 1) for net in networks)}个AP", '≥3个AP（冗余）'],
            ['信号覆盖', f"{avg_signal:.1f}% ({self._signal_to_dbm(avg_signal):.0f} dBm)", signal_quality.get('quality_rating', 'N/A'), '≥70% (≥-67 dBm)'],
            ['频段分布', f"2.4GHz: {sum(1 for n in networks if '2.4' in str(n.get('band', '')))}个 / 5GHz: {sum(1 for n in networks if '5' in str(n.get('band', '')))}个", '双频' if any('5' in str(n.get('band', '')) for n in networks) else '单频', '双频并行部署'],
            ['信道利用率', f"{channel_data.get('avg_utilization', 0):.1f}%", self._get_utilization_status(channel_data.get('avg_utilization', 0)), '<70%（良好）'],
            ['频谱干扰', f"{interference.get('interference_score', 0):.1f}分", interference.get('level', 'N/A'), '<30（低干扰）'],
            ['安全合规', f"{sum(1 for n in networks if 'WPA2' in str(n.get('authentication', '')) or 'WPA3' in str(n.get('authentication', '')))}个安全网络", f"{sum(1 for n in networks if 'WPA2' in str(n.get('authentication', '')) or 'WPA3' in str(n.get('authentication', '')))/len(networks)*100 if networks else 0:.1f}%", '100%（强制）'],
            ['企业级认证', f"{sum(1 for n in networks if 'Enterprise' in str(n.get('authentication', '')) or '企业' in str(n.get('authentication', '')))}个802.1X网络", self._get_enterprise_auth_status(networks), '推荐启用'],
        ]
        
        table = Table(summary_data, colWidths=[3*cm, 4*cm, 3.5*cm, 3.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#ecf0f1')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Chinese'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_signal_quality_section(self, quality_data: Dict) -> List:
        """创建信号质量分析章节"""
        elements = []
        
        elements.append(Paragraph("1. 无线信号质量深度分析", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        # 添加技术说明
        tech_intro = """
        <b>信号强度(RSSI)</b>是衡量WiFi网络性能的关键指标，直接影响连接稳定性、
        数据传输速率和用户体验。本分析基于接收信号强度指示器(RSSI)，
        参考IEEE 802.11标准进行量化评估。信号强度≥-50dBm(约80%)视为优秀，
        -50至-70dBm(60-80%)为良好，低于-70dBm则可能影响服务质量。
        """
        elements.append(Paragraph(tech_intro, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 12))
        
        # 质量统计表
        avg = quality_data.get('average_signal', 0)
        max_sig = quality_data.get('max_signal', 0)
        min_sig = quality_data.get('min_signal', 0)
        
        # 计算RSSI近似值(百分比转dBm)
        # WiFi信号范围: -100dBm(最弱) 到 -30dBm(最强)
        # 转换公式: dBm = (百分比 * 0.7) - 100
        # 修复：确保百分比值在0-100范围内，避免负值或异常值导致错误显示
        avg_safe = max(0, min(100, avg))
        max_safe = max(0, min(100, max_sig))
        min_safe = max(0, min(100, min_sig))
        
        # 同时更新原始值，防止后续使用时出现负数
        avg = avg_safe
        max_sig = max_safe
        min_sig = min_safe
        
        avg_dbm = (avg_safe * 0.7) - 100 if avg_safe > 0 else -100
        max_dbm = (max_safe * 0.7) - 100 if max_safe > 0 else -100
        min_dbm = (min_safe * 0.7) - 100 if min_safe > 0 else -100
        
        stats_data = [
            ['质量指标', '百分比值', 'RSSI(dBm)', '技术评估'],
            ['平均信号强度', f"{avg:.1f}%", f"约{avg_dbm:.0f}dBm", self._get_signal_assessment(avg)],
            ['最强信号', f"{max_sig}%", f"约{max_dbm:.0f}dBm", self._get_signal_assessment(max_sig)],
            ['最弱信号', f"{min_sig}%", f"约{min_dbm:.0f}dBm", self._get_signal_assessment(min_sig)],
            ['信号离散度', f"{max_sig - min_sig}%", f"{max_dbm - min_dbm:.0f}dB", '反映覆盖均匀性'],
        ]
        
        elements.append(Paragraph("<b>信号强度指标:</b>", self.custom_styles['SubTitle']))
        table1 = Table(stats_data, colWidths=[4*cm, 3*cm, 3*cm, 4*cm])
        table1.setStyle(self._get_standard_table_style())
        elements.append(table1)
        elements.append(Spacer(1, 16))
        
        # 信号质量分布
        dist_data = [
            ['质量等级', 'AP数量', '占比', '标准范围'],
            ['优秀(Excellent)', f"{quality_data.get('excellent_count', 0)}个", 
             f"{quality_data.get('excellent_count', 0)/max(sum([quality_data.get('excellent_count', 0), quality_data.get('good_count', 0), quality_data.get('fair_count', 0), quality_data.get('poor_count', 0)]), 1)*100:.1f}%", 
             '≥80% (≥-50dBm)'],
            ['良好(Good)', f"{quality_data.get('good_count', 0)}个", 
             f"{quality_data.get('good_count', 0)/max(sum([quality_data.get('excellent_count', 0), quality_data.get('good_count', 0), quality_data.get('fair_count', 0), quality_data.get('poor_count', 0)]), 1)*100:.1f}%", 
             '60-80% (-70~-50dBm)'],
            ['一般(Fair)', f"{quality_data.get('fair_count', 0)}个", 
             f"{quality_data.get('fair_count', 0)/max(sum([quality_data.get('excellent_count', 0), quality_data.get('good_count', 0), quality_data.get('fair_count', 0), quality_data.get('poor_count', 0)]), 1)*100:.1f}%", 
             '40-60% (-80~-70dBm)'],
            ['较差(Poor)', f"{quality_data.get('poor_count', 0)}个", 
             f"{quality_data.get('poor_count', 0)/max(sum([quality_data.get('excellent_count', 0), quality_data.get('good_count', 0), quality_data.get('fair_count', 0), quality_data.get('poor_count', 0)]), 1)*100:.1f}%", 
             '<40% (<-80dBm)'],
        ]
        
        elements.append(Paragraph("<b>信号质量分布:</b>", self.custom_styles['SubTitle']))
        table2 = Table(dist_data, colWidths=[3.5*cm, 3*cm, 3*cm, 4.5*cm])
        table2.setStyle(self._get_standard_table_style())
        elements.append(table2)
        elements.append(Spacer(1, 12))
        
        # 专业建议
        recommendations = []
        if quality_data.get('poor_count', 0) > 0:
            recommendations.append(f"检测到{quality_data.get('poor_count', 0)}个弱信号AP，建议优化AP位置或增加功率")
        if max_sig - min_sig > 40:
            recommendations.append("信号强度离散度较大，建议重新规划AP布局以实现均匀覆盖")
        if avg < 60:
            recommendations.append("整体信号强度偏低，建议增加AP数量或调整射频参数")
        
        if recommendations:
            elements.append(Paragraph("<b>优化建议:</b>", self.custom_styles['SubTitle']))
            for rec in recommendations:
                elements.append(Paragraph(f"• {rec}", self.custom_styles['CustomBody']))
                elements.append(Spacer(1, 6))
        
        elements.append(Spacer(1, 20))
        return elements
    
    def _get_signal_assessment(self, signal_percent):
        """获取信号质量评估"""
        if signal_percent >= 80:
            return "优秀，适合高带宽应用"
        elif signal_percent >= 60:
            return "良好，一般应用稳定"
        elif signal_percent >= 40:
            return "一般，可能有延迟"
        else:
            return "较差，建议优化"
    
    def _create_coverage_section(self, coverage_data: Dict) -> List:
        """创建覆盖分析章节"""
        elements = []
        
        elements.append(Paragraph("2. 网络覆盖深度分析", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        # 技术背景
        intro_text = """
        <b>WiFi覆盖质量</b>取决于AP密度、频段分布和空间布局。
        根据IEEE 802.11标准，2.4GHz频段穿透性强但带宽有限，
        5GHz频段带宽高但覆盖范围较小。企业级部署应采用双频并发策略，
        合理配置AP密度以实现最佳覆盖与性能平衡。
        """
        elements.append(Paragraph(intro_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 12))
        
        # 详细覆盖统计
        total_ap = coverage_data.get('total_access_points', 0)
        unique_ssid = coverage_data.get('unique_ssids', 0)
        avg_ap = coverage_data.get('avg_aps_per_network', 0)
        count_2_4g = coverage_data.get('frequency_2_4g_count', 0)
        count_5g = coverage_data.get('frequency_5g_count', 0)
        
        coverage_stats = [
            ['覆盖指标', '数值', '技术评估'],
            ['总接入点数量', f"{total_ap}个", self._assess_ap_density(total_ap, unique_ssid)],
            ['独立SSID数量', f"{unique_ssid}个", f"平均每网络{avg_ap:.1f}个AP"],
            ['频段覆盖类型', self._get_band_coverage_type(count_2_4g, count_5g), self._assess_band_coverage(count_2_4g, count_5g)],
            ['2.4GHz AP数量', f"{count_2_4g}个 ({count_2_4g/total_ap*100 if total_ap > 0 else 0:.1f}%)", '传统频段，兼容性好'],
            ['5GHz AP数量', f"{count_5g}个 ({count_5g/total_ap*100 if total_ap > 0 else 0:.1f}%)", '高速频段，干扰少'],
            ['覆盖评级', coverage_data.get('coverage_rating', 'N/A'), self._get_coverage_recommendation(coverage_data)],
        ]
        
        table = Table(coverage_stats, colWidths=[4.5*cm, 4.5*cm, 5*cm])
        table.setStyle(self._get_standard_table_style())
        elements.append(table)
        elements.append(Spacer(1, 16))
        
        # AP密度分析
        if unique_ssid > 0:
            density_text = f"""
            <b>AP密度分析:</b> 当前环境平均每SSID配置{avg_ap:.1f}个AP。
            根据企业级部署最佳实践，单一SSID应配置3-5个AP实现负载均衡和冗余备份。
            {self._get_density_advice(avg_ap)}
            """
            elements.append(Paragraph(density_text, self.custom_styles['CustomBody']))
            elements.append(Spacer(1, 12))
        
        elements.append(Spacer(1, 20))
        return elements
    
    def _assess_ap_density(self, total_ap, unique_ssid):
        """评估AP密度"""
        if unique_ssid == 0:
            return "无数据"
        avg = total_ap / unique_ssid
        if avg >= 5:
            return "高密度部署，冗余好"
        elif avg >= 3:
            return "中等密度，较合理"
        elif avg >= 2:
            return "低密度，容错性差"
        else:
            return "单AP部署，无冗余"
    
    def _get_band_coverage_type(self, count_2_4g, count_5g):
        """获取频段覆盖类型"""
        if count_2_4g > 0 and count_5g > 0:
            return "双频并发"
        elif count_5g > 0:
            return "仅5GHz频段"
        elif count_2_4g > 0:
            return "仅2.4GHz频段"
        else:
            return "未检测到"
    
    def _assess_band_coverage(self, count_2_4g, count_5g):
        """评估频段覆盖"""
        if count_2_4g > 0 and count_5g > 0:
            return "最佳配置，兼顾兼容性与性能"
        elif count_5g > 0:
            return "高性能优先，但可能影响兼容性"
        elif count_2_4g > 0:
            return "兼容性好，但性能有限"
        else:
            return "无数据"
    
    def _get_coverage_recommendation(self, coverage_data):
        """获取覆盖建议"""
        rating = coverage_data.get('coverage_rating', '')
        if '优秀' in rating or '良好' in rating:
            return "覆盖质量佳"
        elif '一般' in rating:
            return "建议优化AP布局"
        else:
            return "需要改进覆盖策略"
    
    def _get_density_advice(self, avg_ap):
        """获取密度建议"""
        if avg_ap >= 5:
            return "当前AP密度充足，具备良好的容错能力。"
        elif avg_ap >= 3:
            return "当前AP密度符合企业级标准。"
        elif avg_ap >= 2:
            return "建议增加AP数量以提高容错性和负载均衡能力。"
        else:
            return "强烈建议增加AP实现冗余部署，避免单点故障。"
    
    def _create_interference_section(self, interference_data: Dict) -> List:
        """创建干扰分析章节"""
        elements = []
        
        elements.append(Paragraph("3. 射频干扰与频谱分析", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        # 技术背景
        tech_text = """
        <b>WiFi干扰</b>是影响网络性能的主要因素。IEEE 802.11标准中，
        2.4GHz频段仅有3个不重叠信道(1,6,11)，而5GHz频段提供更多不重叠信道。
        同频干扰(Co-Channel Interference)和邻道干扰(Adjacent Channel Interference)
        会导致重传增加、吞吐量下降。企业级部署必须进行精细的信道规划。
        """
        elements.append(Paragraph(tech_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 12))
        
        # 干扰等级评估
        interference_level = interference_data.get('interference_level', 'N/A')
        level_color = self._get_interference_color(interference_level)
        
        elements.append(Paragraph(
            f"<b>干扰等级: </b><font color='{level_color}'><b>{interference_level}</b></font>",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 12))
        
        # 最拥挤的信道
        crowded = interference_data.get('most_crowded_channels', [])
        if crowded:
            elements.append(Paragraph("<b>信道拥塞分析:</b>", self.custom_styles['SubTitle']))
            
            crowded_data = [[
'信道', 'AP数量', '频段', '干扰等级', '优化建议']]
            for item in crowded[:5]:
                channel = item.get('channel', 'N/A')
                ap_count = item.get('ap_count', 0)
                band = '2.4GHz' if int(channel) <= 14 else '5GHz' if channel != 'N/A' else 'N/A'
                interference = self._assess_channel_interference(ap_count)
                recommendation = self._get_channel_recommendation(channel, ap_count, band)
                
                crowded_data.append([
                    f"信道 {channel}",
                    f"{ap_count}个AP",
                    band,
                    interference,
                    recommendation
                ])
            
            table = Table(crowded_data, colWidths=[2*cm, 2.5*cm, 2*cm, 2.5*cm, 5*cm])
            table.setStyle(self._get_standard_table_style())
            elements.append(table)
            elements.append(Spacer(1, 12))
        
        # 专业建议
        elements.append(Paragraph("<b>频谱优化建议:</b>", self.custom_styles['SubTitle']))
        suggestions = self._get_interference_recommendations(interference_data)
        for suggestion in suggestions:
            elements.append(Paragraph(f"• {suggestion}", self.custom_styles['CustomBody']))
            elements.append(Spacer(1, 6))
        
        elements.append(Spacer(1, 20))
        return elements
    
    def _get_interference_color(self, level):
        """获取干扰等级颜色"""
        if '低' in level or '良好' in level:
            return '#27ae60'
        elif '中' in level or '一般' in level:
            return '#f39c12'
        elif '高' in level or '严重' in level:
            return '#c0392b'
        else:
            return '#7f8c8d'
    
    def _assess_channel_interference(self, ap_count):
        """评估信道干扰"""
        if ap_count >= 10:
            return "严重拥塞"
        elif ap_count >= 5:
            return "中度拥塞"
        elif ap_count >= 3:
            return "轻度拥塞"
        else:
            return "良好"
    
    def _get_channel_recommendation(self, channel, ap_count, band):
        """获取信道优化建议"""
        if ap_count >= 10:
            if band == '2.4GHz':
                return "建议迁移至5GHz频段"
            else:
                return "建议更换到低负载信道"
        elif ap_count >= 5:
            return "考虑使用其他信道"
        else:
            return "当前信道负载合理"
    
    def _get_interference_recommendations(self, interference_data):
        """获取干扰优化建议"""
        recommendations = []
        crowded = interference_data.get('most_crowded_channels', [])
        
        # 2.4GHz信道优化
        crowded_2_4g = [c for c in crowded if c.get('channel', 99) <= 14]
        if len(crowded_2_4g) > 0:
            recommendations.append(
                "2.4GHz频段：优先使用信道1/6/11，避免邻道干扰，必要时迁移至5GHz"
            )
        
        # 5GHz信道优化
        crowded_5g = [c for c in crowded if c.get('channel', 0) > 14]
        if len(crowded_5g) > 0:
            recommendations.append(
                "5GHz频段：利用DFS信道(52-144)以获取更多频谱资源，降低干扰"
            )
        
        # 通用建议
        if interference_data.get('interference_level') in ['高', '严重']:
            recommendations.append(
                "开启Auto Channel Selection(ACS)功能，让AP自动选择最佳信道"
            )
            recommendations.append(
                "考虑降低AP发射功率，减少同频干扰范围"
            )
        
        if not recommendations:
            recommendations.append("当前干扰水平可接受，保持现有配置")
        
        return recommendations
    
    def _create_channel_section(self, channel_data: Dict) -> List:
        """创建信道分析章节"""
        elements = []
        
        elements.append(Paragraph("4. 信道使用分析", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        # 2.4GHz分析
        data_2_4g = channel_data.get('2.4GHz', {})
        if data_2_4g:
            elements.append(Paragraph("2.4GHz频段:", self.custom_styles['SubTitle']))
            elements.append(Paragraph(
                f"使用的信道: {', '.join(map(str, data_2_4g.get('used_channels', [])))}",
                self.custom_styles['CustomBody']
            ))
            elements.append(Paragraph(
                f"推荐信道: <b>信道 {data_2_4g.get('recommended_channel', 'N/A')}</b>",
                self.custom_styles['CustomBody']
            ))
            elements.append(Spacer(1, 12))
        
        # 5GHz分析
        data_5g = channel_data.get('5GHz', {})
        if data_5g:
            elements.append(Paragraph("5GHz频段:", self.custom_styles['SubTitle']))
            elements.append(Paragraph(
                f"使用的信道: {', '.join(map(str, data_5g.get('used_channels', []))) if data_5g.get('used_channels') else '未检测到'}",
                self.custom_styles['CustomBody']
            ))
            if data_5g.get('recommended_channel'):
                elements.append(Paragraph(
                    f"推荐信道: <b>信道 {data_5g['recommended_channel']}</b>",
                    self.custom_styles['CustomBody']
                ))
        
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_network_details(self, networks: List[Dict]) -> List:
        """创建网络详情章节"""
        elements = []
        
        elements.append(Paragraph("5. 检测网络详细分析", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        # 添加说明
        intro = f"""
        以下是检测到的前10个网络的详细信息，包括信号质量、
        安全配置、AP部署等关键指标。总计检测到<b>{len(networks)}个网络</b>。
        """
        elements.append(Paragraph(intro, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 12))
        
        for i, network in enumerate(networks[:10], 1):
            ssid = network.get('ssid', '未知')
            signal_avg = network.get('signal_avg', 0)
            stability = network.get('signal_stability', 'N/A')
            ap_count = network.get('ap_count', 0)
            encryption = network.get('encryption', '未知')
            auth = network.get('authentication', '未知')
            
            # SSID标题
            elements.append(Paragraph(
                f"5.{i} <b>{ssid}</b>", 
                self.custom_styles['SubTitle']
            ))
            
            # 网络基本信息
            # 确保信号值在合理范围内
            signal_avg_safe = max(0, min(100, signal_avg))
            signal_avg_dbm = (signal_avg_safe * 0.7) - 100 if signal_avg_safe > 0 else -100
            
            network_data = [
                ['指标', '值', '评估'],
                ['平均信号强度', 
                 f"{signal_avg:.1f}% (约{signal_avg_dbm:.0f}dBm)", 
                 self._get_signal_assessment(signal_avg)],
                ['信号稳定性', 
                 stability, 
                 self._assess_stability(stability)],
                ['接入点数量', 
                 f"{ap_count}个AP", 
                 self._assess_ap_redundancy(ap_count)],
                ['加密方式', 
                 encryption, 
                 self._assess_encryption(encryption)],
                ['认证方式', 
                 self._format_auth_display(auth),
                 self._assess_authentication(auth)],
            ]
            
            table = Table(network_data, colWidths=[4*cm, 5*cm, 5*cm])
            table.setStyle(self._get_standard_table_style())
            elements.append(table)
            elements.append(Spacer(1, 12))
        
        if len(networks) > 10:
            elements.append(Paragraph(
                f"<b>注意:</b> 共检测到{len(networks)}个网络，此处仅显示信号最强的前10个。完整数据请参考附录。",
                self.custom_styles['CustomBody']
            ))
        
        elements.append(Spacer(1, 20))
        return elements
    
    def _assess_stability(self, stability):
        """评估信号稳定性"""
        if '稳定' in str(stability) or '优秀' in str(stability):
            return "信号波动小，连接稳定"
        elif '一般' in str(stability) or '良好' in str(stability):
            return "信号有轻微波动"
        elif '不稳定' in str(stability):
            return "信号波动大，可能影响体验"
        else:
            return "数据不足"
    
    def _assess_ap_redundancy(self, ap_count):
        """评估AP冗余性"""
        if ap_count >= 5:
            return "高冗余，容错性强"
        elif ap_count >= 3:
            return "中等冗余，较合理"
        elif ap_count >= 2:
            return "低冗余，建议增加"
        else:
            return "无冗余，单点故障风险"
    
    def _assess_encryption(self, encryption):
        """评估加密方式"""
        if 'CCMP' in encryption or 'AES' in encryption:
            return "安全，AES加密"
        elif 'TKIP' in encryption:
            return "较弱，建议升级到AES"
        elif '无' in encryption or 'None' in encryption:
            return "无加密，安全风险高"
        else:
            return "未知加密方式"
    
    def _assess_authentication(self, auth):
        """评估认证方式"""
        if 'WPA3' in auth:
            return "最高安全级别"
        elif 'Enterprise' in auth or '802.1X' in auth or '企业' in auth:
            return "企业级，集中式管理"
        elif 'WPA2' in auth:
            return "安全，个人用户适用"
        elif 'WPA' in auth:
            return "较弱，建议升级"
        elif 'Open' in auth or '开放' in auth:
            return "无认证，安全风险高"
        else:
            return "未知认证方式"
    
    def _create_recommendations_section(self, recommendations: List[str]) -> List:
        """创建优化建议章节"""
        elements = []
        
        elements.append(Paragraph("6. 专业优化建议", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        # 添加说明
        intro_text = """
        基于本次WiFi网络深度分析，结合IEEE 802.11标准和企业级部署最佳实践，
        提供以下专业优化建议以提升网络性能、可靠性和安全性：
        """
        elements.append(Paragraph(intro_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 12))
        
        if not recommendations or len(recommendations) == 0:
            # 如果没有建议，添加默认建议
            recommendations = [
                "网络配置良好，建议定期监控和维护",
                "持续关注新的WiFi标准（如WiFi 6E/7）的技术发展",
                "定期进行网络安全审计，确保符合企业安全标准"
            ]
        
        # 分类显示建议
        for i, rec in enumerate(recommendations, 1):
            # 判断建议类型并添加图标
            priority_icon = ""
            if any(word in rec for word in ['严重', '紧急', '关键', '强烈']):
                priority_icon = "🔴 [高优先级] "
            elif any(word in rec for word in ['建议', '推荐', '应该']):
                priority_icon = "🟡 [中优先级] "
            else:
                priority_icon = "🟢 [低优先级] "
            
            elements.append(Paragraph(
                f"<b>{i}. {priority_icon}</b>{rec}", 
                self.custom_styles['CustomBody']
            ))
            elements.append(Spacer(1, 10))
        
        # 添加通用最佳实践
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("<b>企业级WiFi部署最佳实践:</b>", self.custom_styles['SubTitle']))
        
        best_practices = [
            "定期进行网络扫描和性能评估（建议每月一次）",
            "保持AP固件更新，及时应用安全补丁",
            "实施网络分段，将访客网络与内部网络隔离",
            "配置802.11k/v/r协议支持快速漫游",
            "部署网络监控系统，实时监控性能指标",
            "建立完善的故障响应和应急预案"
        ]
        
        for practice in best_practices:
            elements.append(Paragraph(f"• {practice}", self.custom_styles['CustomBody']))
            elements.append(Spacer(1, 6))
        
        return elements
    
    def _create_security_summary(self, data: Dict) -> List:
        """创建安全摘要"""
        elements = []
        
        elements.append(Paragraph("安全评估摘要", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        # 总体评分
        score = data.get('overall_score', 0)
        compliance = data.get('compliance_level', '未知')
        
        score_color = self._get_score_color(score)
        
        summary_text = f"""
        <para align=center>
            <font size=16><b>总体安全得分: </b></font>
            <font size=20 color='{score_color}'><b>{score}</b></font><font size=16><b>/100</b></font><br/>
            <font size=14>合规等级: <b>{compliance}</b></font>
        </para>
        """
        
        elements.append(Paragraph(summary_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 20))
        
        # 快速统计
        quick_stats = [
            ['评估项目', '数值'],
            ['评估时间', data.get('assessment_time', 'N/A')],
            ['评估网络总数', f"{data.get('total_networks', 0)}个"],
            ['安全网络比例', f"{data.get('encryption_analysis', {}).get('secure_percentage', 0):.1f}%"],
            ['合规检查通过率', f"{data.get('compliance_status', {}).get('compliance_percentage', 0):.1f}%"],
            ['发现的风险', f"{data.get('risk_assessment', {}).get('summary', {}).get('critical', 0) + data.get('risk_assessment', {}).get('summary', {}).get('high', 0)}个（关键+高）"],
        ]
        
        table = Table(quick_stats, colWidths=[7*cm, 7*cm])
        table.setStyle(self._get_standard_table_style())
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _assess_business_impact(self, data: Dict) -> Dict:
        """评估业务影响"""
        networks = data.get('networks', [])
        signal_quality = data.get('signal_quality', {})
        avg_signal = signal_quality.get('average_signal', 0)
        
        # 网络可用性评估
        if avg_signal >= 70:
            availability = "优秀 - 网络覆盖良好，支持关键业务应用"
        elif avg_signal >= 50:
            availability = "良好 - 基本满足业务需求，部分区域可能存在弱信号"
        elif avg_signal >= 30:
            availability = "一般 - 存在明显覆盖盲区，影响移动办公体验"
        else:
            availability = "较差 - 覆盖严重不足，业务连续性面临风险"
        
        # 用户体验评估
        secure_networks = sum(1 for n in networks if 'WPA2' in str(n.get('authentication', '')) or 'WPA3' in str(n.get('authentication', '')))
        security_rate = secure_networks / len(networks) * 100 if networks else 0
        
        if avg_signal >= 70 and security_rate >= 90:
            user_experience = "优秀 - 快速连接、稳定传输、安全可靠"
        elif avg_signal >= 50 and security_rate >= 70:
            user_experience = "良好 - 正常使用，偶有延迟或掉线"
        elif avg_signal >= 30:
            user_experience = "一般 - 频繁掉线、速度慢，影响工作效率"
        else:
            user_experience = "较差 - 连接困难、严重影响用户满意度"
        
        # 业务风险评估
        if security_rate < 50:
            business_risk = "高风险 - 存在严重安全隐患，可能导致数据泄露或合规问题"
        elif security_rate < 80 or avg_signal < 40:
            business_risk = "中风险 - 部分业务受影响，需优先改进"
        elif avg_signal < 60:
            business_risk = "低风险 - 可正常运营，建议持续优化"
        else:
            business_risk = "极低 - 网络状态健康，符合企业标准"
        
        # 优化紧迫性
        if avg_signal < 30 or security_rate < 50:
            urgency = "紧急 - 建议立即启动优化项目"
        elif avg_signal < 50 or security_rate < 80:
            urgency = "高 - 建议30天内完成改进"
        elif avg_signal < 70:
            urgency = "中 - 建议90天内纳入规划"
        else:
            urgency = "低 - 定期维护即可"
        
        return {
            'availability': availability,
            'user_experience': user_experience,
            'business_risk': business_risk,
            'urgency': urgency
        }
    
    def _get_utilization_status(self, utilization: float) -> str:
        """获取信道利用率状态"""
        if utilization < 30:
            return "低负载（优秀）"
        elif utilization < 50:
            return "正常负载（良好）"
        elif utilization < 70:
            return "中等负载（一般）"
        elif utilization < 85:
            return "高负载（需优化）"
        else:
            return "过载（紧急）"
    
    def _get_enterprise_auth_status(self, networks: List) -> str:
        """获取企业级认证状态"""
        enterprise_count = sum(1 for n in networks if 'Enterprise' in str(n.get('authentication', '')) or '企业' in str(n.get('authentication', '')))
        if enterprise_count == 0:
            return "未部署"
        elif enterprise_count < len(networks) // 2:
            return "部分部署"
        else:
            return "已广泛部署"
    
    def _signal_to_dbm(self, signal_percent: float) -> float:
        """信号百分比转dBm
        
        WiFi信号转换标准:
        百分比范围: 0-100%
        dBm范围: -100dBm(最弱) 到 -30dBm(最强)
        转换公式: dBm = (百分比 * 0.7) - 100
        """
        # 确保百分比在0-100范围内
        signal_percent = max(0, min(100, signal_percent))
        return (signal_percent * 0.7) - 100
    
    def _create_capacity_planning_section(self, data: Dict) -> List:
        """创建容量规划章节"""
        elements = []
        
        elements.append(Paragraph("7. 容量规划与负载分析", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        networks = data.get('networks', [])
        total_aps = sum(net.get('ap_count', 1) for net in networks)
        
        capacity_intro = f"""
        <para align=justify>
        容量规划是企业无线网络设计的核心环节。本章节基于当前检测到的<b>{total_aps}个AP</b>，
        从用户密度、带宽需求、AP覆盖范围等维度进行容量评估，并提供扩容建议。
        </para>
        """
        elements.append(Paragraph(capacity_intro, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 12))
        
        # 容量评估表
        elements.append(Paragraph("7.1 当前容量评估", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 8))
        
        # 假设每个AP支持25-30用户（标准办公负载）
        estimated_capacity_low = total_aps * 25
        estimated_capacity_high = total_aps * 30
        
        capacity_data = [
            ['评估项', '当前值', '推荐范围', '状态'],
            ['AP总数', f"{total_aps}个", '-', '-'],
            ['理论容量（轻负载）', f"{estimated_capacity_low}-{estimated_capacity_high}用户", '25-30用户/AP', '标准配置'],
            ['高密度容量（会议室）', f"{total_aps * 15}用户", '≤15用户/AP', '需专项设计'],
            ['频段利用', self._analyze_band_distribution(networks), '双频并行', self._get_band_status(networks)],
            ['AP冗余度', f"{total_aps}个（冗余：{max(0, total_aps-2)}）", '≥3个（N+1）', '需评估' if total_aps < 3 else '充足'],
        ]
        
        table = Table(capacity_data, colWidths=[4*cm, 4*cm, 3.5*cm, 2.5*cm])
        table.setStyle(self._get_standard_table_style())
        elements.append(table)
        elements.append(Spacer(1, 15))
        
        # 容量规划建议
        elements.append(Paragraph("7.2 容量规划建议", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 8))
        
        # 短期建议
        elements.append(Paragraph("<b>短期建议（0-6个月）</b>", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("• 监控当前AP负载和客户端分布，识别高负载AP（>50客户端或>70%信道利用率）", self.custom_styles['CustomBody']))
        elements.append(Paragraph("• 对高密度区域（会议室、开放办公区）进行专项勘测和AP加密部署", self.custom_styles['CustomBody']))
        elements.append(Paragraph("• 启用负载均衡和band steering，优化客户端分布", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        # 中期规划
        elements.append(Paragraph("<b>中期规划（6-12个月）</b>", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("• 根据业务增长预测用户数，按1.3倍冗余系数规划AP数量", self.custom_styles['CustomBody']))
        elements.append(Paragraph("• 升级核心交换机支持PoE+（802.3at）或PoE++（802.3bt）为WiFi 6 AP供电", self.custom_styles['CustomBody']))
        elements.append(Paragraph("• 部署网络管理平台实现AP统一管理、配置推送、性能监控", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        # 长期战略
        elements.append(Paragraph("<b>长期战略（1-3年）</b>", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("• 制定WiFi 6/6E升级路线图，支持更高用户密度和IoT设备接入", self.custom_styles['CustomBody']))
        elements.append(Paragraph("• 规划6GHz频段应用（WiFi 6E），为AR/VR等高带宽应用预留容量", self.custom_styles['CustomBody']))
        elements.append(Paragraph("• 建立容量管理流程，每季度评估容量使用率和扩容需求", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_roaming_analysis_section(self, data: Dict) -> List:
        """创建漫游性能分析章节"""
        elements = []
        
        elements.append(Paragraph("8. 漫游性能与移动办公支持", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        roaming_intro = """
        <para align=justify>
        无缝漫游是企业移动办公的关键要求。本章节评估网络的漫游性能，
        包括AP覆盖重叠度、漫游协议支持、切换延迟等关键指标。
        </para>
        """
        elements.append(Paragraph(roaming_intro, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 12))
        
        # 漫游协议支持
        elements.append(Paragraph("8.1 漫游协议支持评估", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 8))
        
        roaming_protocols = [
            ['协议', '功能', '标准延迟', '企业推荐', '检测结果'],
            ['802.11k (RRM)', '邻居报告、信道扫描优化', '-', '必须启用', '需设备验证'],
            ['802.11v (BSS-TM)', 'BSS过渡管理、负载均衡', '-', '强烈推荐', '需设备验证'],
            ['802.11r (FT)', '快速BSS过渡', '<50ms', 'VoIP必需', '需设备验证'],
            ['OKC/PMK缓存', '预认证加速', '<100ms', '推荐启用', '802.1X环境'],
        ]
        
        table = Table(roaming_protocols, colWidths=[2.5*cm, 3.5*cm, 2.5*cm, 2.5*cm, 3*cm])
        table.setStyle(self._get_standard_table_style())
        elements.append(table)
        elements.append(Spacer(1, 15))
        
        # 漫游优化建议
        elements.append(Paragraph("8.2 漫游优化建议", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 8))
        
        elements.append(Paragraph("<b>覆盖重叠设计</b>: AP间信号重叠20-30%（-70至-75dBm），支持提前切换而非断开重连", self.custom_styles['CustomBody']))
        elements.append(Paragraph("<b>RSSI阈值</b>: 设置漫游触发阈值为-70dBm，去关联阈值-80dBm，避免粘性客户端问题", self.custom_styles['CustomBody']))
        elements.append(Paragraph("<b>快速漫游</b>: 启用802.11r减少重新认证时间，VoIP/视频会议场景必须支持", self.custom_styles['CustomBody']))
        elements.append(Paragraph("<b>负载均衡</b>: 使用802.11v引导客户端向低负载AP漫游，避免单AP过载", self.custom_styles['CustomBody']))
        elements.append(Paragraph("<b>频段引导</b>: 优先引导5GHz capable设备连接5GHz频段，释放2.4GHz容量", self.custom_styles['CustomBody']))
        elements.append(Paragraph("<b>测试验证</b>: 使用WiFi分析仪或移动终端进行漫游测试，验证切换延迟<50ms", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_network_health_assessment(self, data: Dict) -> List:
        """创建网络健康度评估章节"""
        elements = []
        
        elements.append(Paragraph("9. 网络健康度综合评估", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        health_intro = """
        <para align=justify>
        网络健康度是衡量无线网络整体运行状态的综合指标。本章节从性能、可靠性、
        安全性、可扩展性四个维度进行评分，并给出改进优先级排序。
        </para>
        """
        elements.append(Paragraph(health_intro, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 12))
        
        # 计算健康度评分
        networks = data.get('networks', [])
        signal_quality = data.get('signal_quality', {})
        avg_signal = signal_quality.get('average_signal', 0)
        
        # 性能评分 (40分)
        perf_score = min(40, (avg_signal / 100) * 40)
        
        # 可靠性评分 (20分) - 基于AP数量和频段分布
        total_aps = sum(net.get('ap_count', 1) for net in networks)
        has_5ghz = any('5' in str(n.get('band', '')) for n in networks)
        reliability_score = min(20, (total_aps / 5) * 10 + (10 if has_5ghz else 0))
        
        # 安全性评分 (30分)
        secure_networks = sum(1 for n in networks if 'WPA2' in str(n.get('authentication', '')) or 'WPA3' in str(n.get('authentication', '')))
        security_score = (secure_networks / len(networks) * 30) if networks else 0
        
        # 可扩展性评分 (10分) - 基于企业级认证和技术先进性
        enterprise_count = sum(1 for n in networks if 'Enterprise' in str(n.get('authentication', '')) or '企业' in str(n.get('authentication', '')))
        scalability_score = min(10, (enterprise_count / max(1, len(networks))) * 10)
        
        total_health_score = perf_score + reliability_score + security_score + scalability_score
        
        # 健康度评分表
        elements.append(Paragraph("9.1 健康度评分", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 8))
        
        health_data = [
            ['评估维度', '得分', '满分', '等级', '权重'],
            ['性能指标', f"{perf_score:.1f}", '40', self._get_score_level(perf_score, 40), '40%'],
            ['可靠性', f"{reliability_score:.1f}", '20', self._get_score_level(reliability_score, 20), '20%'],
            ['安全性', f"{security_score:.1f}", '30', self._get_score_level(security_score, 30), '30%'],
            ['可扩展性', f"{scalability_score:.1f}", '10', self._get_score_level(scalability_score, 10), '10%'],
            ['综合健康度', f"{total_health_score:.1f}", '100', self._get_score_level(total_health_score, 100), '100%'],
        ]
        
        table = Table(health_data, colWidths=[3.5*cm, 2*cm, 2*cm, 3*cm, 2.5*cm])
        table.setStyle(self._get_standard_table_style())
        elements.append(table)
        elements.append(Spacer(1, 15))
        
        # 健康度解读
        elements.append(Paragraph("9.2 健康度解读与改进方向", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 8))
        
        if total_health_score >= 85:
            health_status = "优秀（A级）- 网络状态健康，符合企业级标准，建议保持并持续优化"
        elif total_health_score >= 70:
            health_status = "良好（B级）- 基本满足需求，存在改进空间，建议定期评估和优化"
        elif total_health_score >= 55:
            health_status = "一般（C级）- 存在明显问题，需制定改进计划并在90天内完成"
        else:
            health_status = "较差（D级）- 严重影响业务，建议立即启动优化项目"
        
        elements.append(Paragraph(f"<b>综合评价</b>: {health_status}", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("<b>优先改进领域</b>:", self.custom_styles['CustomBody']))
        
        if perf_score < 30:
            elements.append(Paragraph("• 性能优化：信号覆盖和信道规划需加强", self.custom_styles['CustomBody']))
        if reliability_score < 15:
            elements.append(Paragraph("• 可靠性提升：增加AP数量和双频覆盖", self.custom_styles['CustomBody']))
        if security_score < 20:
            elements.append(Paragraph("• 安全加固：升级加密协议和认证方式", self.custom_styles['CustomBody']))
        if scalability_score < 5:
            elements.append(Paragraph("• 架构升级：部署企业级认证和管理平台", self.custom_styles['CustomBody']))
        if total_health_score >= 85:
            elements.append(Paragraph("• 当前网络状态良好，建议定期维护", self.custom_styles['CustomBody']))
        
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _analyze_band_distribution(self, networks: List) -> str:
        """分析频段分布"""
        band_24 = sum(1 for n in networks if '2.4' in str(n.get('band', '')))
        band_5 = sum(1 for n in networks if '5' in str(n.get('band', '')))
        return f"2.4GHz: {band_24}个 / 5GHz: {band_5}个"
    
    def _get_band_status(self, networks: List) -> str:
        """获取频段部署状态"""
        band_5 = sum(1 for n in networks if '5' in str(n.get('band', '')))
        if band_5 == 0:
            return "仅2.4GHz"
        elif band_5 >= len(networks) // 2:
            return "双频均衡"
        else:
            return "以2.4GHz为主"
    
    def _get_score_level(self, score: float, max_score: float) -> str:
        """获取评分等级"""
        percentage = (score / max_score) * 100
        if percentage >= 85:
            return "优秀"
        elif percentage >= 70:
            return "良好"
        elif percentage >= 55:
            return "一般"
        else:
            return "需改进"
    
    def _get_score_color(self, score: int) -> str:
        """根据分数获取颜色"""
        if score >= 90:
            return '#27ae60'  # 绿色
        elif score >= 75:
            return '#f39c12'  # 橙色
        elif score >= 60:
            return '#e67e22'  # 深橙色
        else:
            return '#c0392b'  # 红色
    
    def _create_compliance_section(self, compliance_data: Dict) -> List:
        """创建合规性章节"""
        elements = []
        
        elements.append(Paragraph("PCI-DSS合规性检查", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        # 合规状态
        status = compliance_data.get('overall_status', '未知')
        status_color = '#27ae60' if status == 'COMPLIANT' else '#c0392b'
        
        elements.append(Paragraph(
            f"总体状态: <font color='{status_color}'><b>{status}</b></font>",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 12))
        
        # 检查详情
        checks = compliance_data.get('checks', {})
        if checks:
            check_data = [['要求编号', '要求描述', '状态', '详情']]
            
            for req_id, check in checks.items():
                status_text = '✓ 通过' if check['status'] == 'PASS' else '✗ 失败'
                check_data.append([
                    req_id,
                    check.get('requirement', ''),
                    status_text,
                    check.get('details', '')
                ])
            
            table = Table(check_data, colWidths=[2*cm, 4*cm, 2*cm, 6*cm])
            table.setStyle(self._get_standard_table_style())
            elements.append(table)
        
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_risk_section(self, risk_data: Dict) -> List:
        """创建风险评估章节"""
        elements = []
        
        elements.append(Paragraph("风险评估", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        # 风险摘要
        summary = risk_data.get('summary', {})
        risk_summary = [
            ['风险等级', '数量'],
            ['关键风险', f"{summary.get('critical', 0)}个"],
            ['高风险', f"{summary.get('high', 0)}个"],
            ['中等风险', f"{summary.get('medium', 0)}个"],
            ['低风险', f"{summary.get('low', 0)}个"],
        ]
        
        table = Table(risk_summary, colWidths=[7*cm, 7*cm])
        table.setStyle(self._get_standard_table_style())
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # 风险详情（仅显示关键和高风险）
        details = risk_data.get('details', {})
        for level in ['critical', 'high']:
            risks = details.get(level, [])
            if risks:
                level_name = '关键风险' if level == 'critical' else '高风险'
                elements.append(Paragraph(f"{level_name}详情:", self.custom_styles['SubTitle']))
                
                for i, risk in enumerate(risks, 1):
                    elements.append(Paragraph(
                        f"<b>{i}. {risk.get('ssid', 'N/A')}</b>",
                        self.custom_styles['CustomBody']
                    ))
                    elements.append(Paragraph(
                        f"问题: {risk.get('issue', '')}",
                        self.custom_styles['CustomBody']
                    ))
                    elements.append(Paragraph(
                        f"影响: {risk.get('impact', '')}",
                        self.custom_styles['CustomBody']
                    ))
                    elements.append(Paragraph(
                        f"修复建议: {risk.get('remediation', '')}",
                        self.custom_styles['Emphasis']
                    ))
                    elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_vulnerability_section(self, vuln_data: Dict) -> List:
        """创建漏洞扫描章节"""
        elements = []
        
        elements.append(Paragraph("漏洞扫描结果", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        # 漏洞统计
        by_severity = vuln_data.get('by_severity', {})
        vuln_stats = [
            ['严重程度', '数量'],
            ['关键', f"{by_severity.get('critical', 0)}个"],
            ['高', f"{by_severity.get('high', 0)}个"],
            ['中', f"{by_severity.get('medium', 0)}个"],
            ['低', f"{by_severity.get('low', 0)}个"],
        ]
        
        table = Table(vuln_stats, colWidths=[7*cm, 7*cm])
        table.setStyle(self._get_standard_table_style())
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_encryption_section(self, encryption_data: Dict) -> List:
        """创建加密分析章节"""
        elements = []
        
        elements.append(Paragraph("加密方式分析", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        stats = encryption_data.get('statistics', {})
        if stats:
            enc_data = [['加密类型', 'AP数量', '占比', '安全评级']]
            
            for enc_type, data in stats.items():
                rating = data.get('rating', {})
                enc_data.append([
                    enc_type,
                    f"{data.get('count', 0)}个",
                    f"{data.get('percentage', 0):.1f}%",
                    rating.get('level', 'N/A')
                ])
            
            table = Table(enc_data, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
            table.setStyle(self._get_standard_table_style())
            elements.append(table)
        
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            f"安全加密比例: <b>{encryption_data.get('secure_percentage', 0):.1f}%</b>",
            self.custom_styles['CustomBody']
        ))
        
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_security_recommendations(self, recommendations: List[Dict]) -> List:
        """创建安全建议章节"""
        elements = []
        
        elements.append(Paragraph("安全改进建议", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        # 按优先级排序
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        sorted_recs = sorted(
            recommendations,
            key=lambda x: priority_order.get(x.get('priority', 'LOW'), 999)
        )
        
        for i, rec in enumerate(sorted_recs, 1):
            priority = rec.get('priority', 'N/A')
            priority_color = {
                'CRITICAL': '#c0392b',
                'HIGH': '#e67e22',
                'MEDIUM': '#f39c12',
                'LOW': '#3498db'
            }.get(priority, '#000000')
            
            elements.append(Paragraph(
                f"<b>{i}. {rec.get('title', '')}</b> "
                f"<font color='{priority_color}'>[{priority}]</font>",
                self.custom_styles['SubTitle']
            ))
            
            elements.append(Paragraph(
                f"类别: {rec.get('category', 'N/A')}",
                self.custom_styles['CustomBody']
            ))
            
            elements.append(Paragraph(
                f"描述: {rec.get('description', '')}",
                self.custom_styles['CustomBody']
            ))
            
            elements.append(Paragraph(
                f"建议措施: <b>{rec.get('action', '')}</b>",
                self.custom_styles['Emphasis']
            ))
            
            elements.append(Paragraph(
                f"相关PCI-DSS要求: {rec.get('pci_requirement', 'N/A')}",
                self.custom_styles['CustomBody']
            ))
            
            elements.append(Spacer(1, 15))
        
        return elements
    
    # ========== PCI-DSS专业报告章节（新增）==========
    
    def _create_security_executive_summary(self, data: Dict) -> List:
        """第1章：执行摘要（深度版）"""
        elements = []
        
        elements.append(Paragraph("第一章 执行摘要", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        # 评估概述
        elements.append(Paragraph(
            "本报告基于<b>PCI-DSS 4.0标准</b>（Payment Card Industry Data Security Standard）"
            "对企业无线网络环境进行了全面的安全合规性评估。PCI-DSS是由PCI安全标准委员会（PCI SSC）"
            "制定的行业安全标准，旨在保护持卡人数据，确保支付卡交易的安全性。",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "无线网络作为现代企业IT基础设施的重要组成部分，同时也是安全防护的薄弱环节。"
            "本次评估采用<b>深度安全审计方法</b>，包括网络扫描、配置审核、风险评估和合规性检查，"
            "全面审视无线网络的安全态势，识别潜在的安全风险和合规性差距。",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 15))
        
        # 关键发现
        elements.append(Paragraph("1.1 关键发现", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        score = data.get('overall_score', 0)
        compliance = data.get('compliance_level', '未知')
        score_color = self._get_score_color(score)
        
        risk_summary = data.get('risk_assessment', {}).get('summary', {})
        critical_count = risk_summary.get('critical', 0)
        high_count = risk_summary.get('high', 0)
        total_networks = data.get('total_networks', 0)
        
        findings_text = f"""
        <para align=justify>
        • <b>总体安全得分</b>: <font color='{score_color}'><b>{score}/100</b></font> - {self._get_score_interpretation(score)}<br/>
        • <b>合规等级</b>: <font color='{score_color}'><b>{compliance}</b></font><br/>
        • <b>评估网络</b>: {total_networks}个无线网络<br/>
        • <b>关键风险</b>: {critical_count}个<br/>
        • <b>高风险</b>: {high_count}个<br/>
        • <b>需要立即关注</b>: {critical_count + high_count}项安全问题
        </para>
        """
        elements.append(Paragraph(findings_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 15))
        
        # 主要风险领域
        elements.append(Paragraph("1.2 主要风险领域", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        risk_areas = self._identify_risk_areas(data)
        for i, area in enumerate(risk_areas, 1):
            elements.append(Paragraph(
                f"<b>{i}. {area['title']}</b>: {area['description']}",
                self.custom_styles['CustomBody']
            ))
            elements.append(Spacer(1, 8))
        
        # 合规性状态
        elements.append(Paragraph("1.3 合规性状态摘要", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        compliance_data = data.get('compliance_status', {})
        compliance_pct = compliance_data.get('compliance_percentage', 0)
        
        compliance_text = f"""
        <para align=justify>
        经评估，当前无线网络环境的<b>PCI-DSS合规率为{compliance_pct:.1f}%</b>。
        {"已基本满足" if compliance_pct >= 90 else "尚未完全满足" if compliance_pct >= 70 else "存在较大差距于"}
        PCI-DSS 4.0对无线网络安全的要求。关键需改进领域包括加密强度、认证机制、
        访问控制和安全监控等方面。
        </para>
        """
        elements.append(Paragraph(compliance_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_pci_dss_overview(self) -> List:
        """第2章：PCI-DSS标准概述"""
        elements = []
        
        elements.append(Paragraph("第二章 PCI-DSS 4.0标准概述", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        # 标准介绍
        elements.append(Paragraph(
            "<b>PCI-DSS（Payment Card Industry Data Security Standard）</b>是支付卡行业数据安全标准，"
            "由Visa、MasterCard、American Express、Discover和JCB等主要支付卡品牌联合创建的PCI安全标准委员会"
            "（PCI Security Standards Council）制定和维护。",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "PCI-DSS 4.0版本于2022年3月发布，2024年3月31日起强制实施，引入了更严格的安全控制要求，"
            "特别加强了对无线网络、云环境和新兴技术的安全规范。",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 15))
        
        # 六大安全目标
        elements.append(Paragraph("2.1 六大安全目标", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        goals = [
            ['目标', '描述', '相关要求'],
            ['建立和维护安全网络', '保护持卡人数据环境的网络安全', 'Req 1, 2'],
            ['保护持卡人数据', '确保敏感数据的保密性和完整性', 'Req 3, 4'],
            ['维护漏洞管理程序', '持续识别和修复安全漏洞', 'Req 5, 6'],
            ['实施强访问控制措施', '限制对数据的访问权限', 'Req 7, 8, 9'],
            ['定期监控和测试网络', '持续监控安全状态', 'Req 10, 11'],
            ['维护信息安全政策', '建立全员安全意识', 'Req 12'],
        ]
        
        table = Table(goals, colWidths=[4*cm, 6*cm, 3*cm])
        table.setStyle(self._get_standard_table_style())
        elements.append(table)
        elements.append(Spacer(1, 15))
        
        # 无线网络特定要求
        elements.append(Paragraph("2.2 无线网络安全要求重点", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        elements.append(Paragraph("PCI-DSS对无线网络有严格的安全要求，主要包括：", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph("<b>要求1.2.3</b> - 安装防火墙并限制与不受信任网络的连接", self.custom_styles['CustomBody']))
        elements.append(Paragraph("<b>要求2.1.1</b> - 更改所有无线设备的默认配置参数", self.custom_styles['CustomBody']))
        elements.append(Paragraph("<b>要求4.1</b> - 使用强加密和安全协议保护传输中的持卡人数据", self.custom_styles['CustomBody']))
        elements.append(Paragraph("<b>要求11.2</b> - 每季度执行一次无线网络扫描和检测", self.custom_styles['CustomBody']))
        elements.append(Paragraph("<b>要求11.3</b> - 定期进行渗透测试", self.custom_styles['CustomBody']))
        elements.append(Paragraph("<b>要求12.3</b> - 制定关键技术的安全使用策略", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("<b>最低加密要求</b>: WPA2-AES或WPA3，禁止使用WEP和WPA-TKIP", self.custom_styles['CustomBody']))
        elements.append(Paragraph("<b>企业级认证</b>: 对于处理持卡人数据的环境，推荐使用802.1X企业认证", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_assessment_methodology(self) -> List:
        """第3章：评估方法论"""
        elements = []
        
        elements.append(Paragraph("第三章 评估方法论", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        method_text = """
        <para align=justify>
        本次PCI-DSS无线网络安全评估采用多层次、系统化的评估方法，确保全面覆盖所有关键安全控制点。
        评估方法论基于PCI SSC发布的《无线网络指南》和《渗透测试指南》，结合行业最佳实践。
        </para>
        """
        elements.append(Paragraph(method_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 15))
        
        # 评估流程
        elements.append(Paragraph("3.1 评估流程", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        phases = [
            ['阶段', '活动', '输出'],
            ['1. 信息收集', '网络扫描、设备清单、配置审查', 'WiFi网络拓扑图、设备清单'],
            ['2. 漏洞识别', '加密分析、认证审核、配置检查', '漏洞清单、风险等级评估'],
            ['3. 合规性测试', 'PCI-DSS要求逐项验证', '合规性检查清单'],
            ['4. 风险评估', 'CVSS评分、威胁建模', '风险矩阵、优先级排序'],
            ['5. 报告编制', '综合分析、建议制定', '评估报告、改进路线图'],
        ]
        
        table = Table(phases, colWidths=[3*cm, 6*cm, 5*cm])
        table.setStyle(self._get_standard_table_style())
        elements.append(table)
        elements.append(Spacer(1, 15))
        
        # 评估工具和技术
        elements.append(Paragraph("3.2 评估工具和技术", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        tools_text = """
        <para align=justify>
        <b>网络扫描</b>: 使用Windows netsh命令进行无线网络发现和信号质量分析<br/>
        <b>配置审核</b>: 检查SSID、加密类型、认证方式、信道配置等关键参数<br/>
        <b>安全分析</b>: 基于IEEE 802.11标准和PCI-DSS要求进行安全性评估<br/>
        <b>风险评分</b>: 采用CVSS 3.1评分系统量化安全风险<br/>
        <b>合规验证</b>: 对照PCI-DSS 4.0控制要求进行逐项检查
        </para>
        """
        elements.append(Paragraph(tools_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 15))
        
        # 评估范围
        elements.append(Paragraph("3.3 评估范围", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        elements.append(Paragraph(
            "本次评估涵盖企业环境中所有可检测到的无线网络，包括但不限于：<br/>"
            "• 企业内部WiFi网络（员工网络、访客网络、IoT网络）<br/>"
            "• 2.4GHz和5GHz频段的所有网络<br/>"
            "• WPA2/WPA3企业级和个人级认证网络<br/>"
            "• 开放式和加密式网络",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "<b>注意</b>: 本评估为非侵入式被动扫描，不进行主动渗透测试或密码破解。",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_network_environment_overview(self, data: Dict) -> List:
        """第4章：网络环境概况"""
        elements = []
        
        elements.append(Paragraph("第四章 无线网络环境概况", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        total_networks = data.get('total_networks', 0)
        
        overview_text = f"""
        <para align=justify>
        本次评估在企业环境中共检测到<b>{total_networks}个无线网络</b>，涵盖多种网络类型、
        加密方式和认证机制。以下对网络环境的关键特征进行深入分析。
        </para>
        """
        elements.append(Paragraph(overview_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 15))
        
        # 网络分布统计
        elements.append(Paragraph("4.1 网络类型分布", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        auth_analysis = data.get('authentication_analysis', {})
        auth_stats = auth_analysis.get('statistics', {})
        
        if auth_stats:
            dist_data = [['认证类型', '网络数量', '占比', '安全等级']]
            for auth_type, auth_data in auth_stats.items():
                count = auth_data.get('count', 0)
                percentage = auth_data.get('percentage', 0)
                security = self._get_auth_security_level(auth_type)
                dist_data.append([
                    self._format_auth_display(auth_type),
                    f"{count}个",
                    f"{percentage:.1f}%",
                    security
                ])
            
            table = Table(dist_data, colWidths=[4*cm, 3*cm, 3*cm, 4*cm])
            table.setStyle(self._get_standard_table_style())
            elements.append(table)
        
        elements.append(Spacer(1, 15))
        
        # 频段分布
        elements.append(Paragraph("4.2 频段使用分析", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        band_text = """
        <para align=justify>
        无线网络频段分布对网络性能和安全性都有重要影响。2.4GHz频段穿透力强但易受干扰，
        5GHz频段速度快且信道多但覆盖范围较小。
        </para>
        """
        elements.append(Paragraph(band_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 15))
        
        # 信号强度分布
        elements.append(Paragraph("4.3 信号强度分布", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        signal_text = """
        <para align=justify>
        <b>信号强度分析</b>对于评估物理安全风险至关重要。过强的WiFi信号可能导致信号
        泄露到企业边界之外，增加未授权访问的风险。PCI-DSS要求将无线信号限制在必要的
        物理范围内。
        </para>
        """
        elements.append(Paragraph(signal_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_encryption_authentication_analysis(self, data: Dict) -> List:
        """第5章：加密与认证深度分析"""
        elements = []
        
        elements.append(Paragraph("第五章 加密与认证机制分析", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        # 加密标准深度解析
        elements.append(Paragraph("5.1 加密协议安全性评估", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        enc_intro = """
        <para align=justify>
        无线网络加密是保护数据传输安全的第一道防线。PCI-DSS明确要求使用强加密算法
        保护持卡人数据，禁止使用已知存在漏洞的过时加密协议。
        </para>
        """
        elements.append(Paragraph(enc_intro, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        # 加密技术对比
        enc_comparison = [
            ['加密类型', '安全性', 'PCI-DSS合规', '技术特点', '建议'],
            ['WPA3-AES', '优秀', '✓ 合规', 'SAE认证、前向保密', '推荐使用'],
            ['WPA2-AES(CCMP)', '良好', '✓ 合规', 'AES-128加密、CCMP协议', '可接受'],
            ['WPA2-TKIP', '较弱', '✗ 不合规', '存在已知漏洞、易攻击', '必须升级'],
            ['WPA-TKIP', '极弱', '✗ 不合规', 'RC4加密、严重漏洞', '禁止使用'],
            ['WEP', '极弱', '✗ 不合规', '已完全破解、无安全性', '立即禁用'],
            ['Open(无加密)', '无', '✗ 不合规', '明文传输、无防护', '严禁使用'],
        ]
        
        table = Table(enc_comparison, colWidths=[3*cm, 2*cm, 2.5*cm, 4*cm, 2.5*cm])
        table.setStyle(self._get_standard_table_style())
        elements.append(table)
        elements.append(Spacer(1, 15))
        
        # 当前环境加密分析
        elements.append(Paragraph("5.2 当前环境加密状况", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        enc_data = data.get('encryption_analysis', {})
        enc_stats = enc_data.get('statistics', {})
        secure_pct = enc_data.get('secure_percentage', 0)
        
        current_enc_text = f"""
        <para align=justify>
        经检测，当前环境中<b>安全加密比例为{secure_pct:.1f}%</b>。
        {"达到" if secure_pct >= 95 else "接近" if secure_pct >= 85 else "未达到"}
        PCI-DSS对加密强度的要求（要求100%使用强加密）。
        </para>
        """
        elements.append(Paragraph(current_enc_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 15))
        
        # 认证机制分析
        elements.append(Paragraph("5.3 认证机制安全性分析", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        elements.append(Paragraph(
            "<b>企业级认证(802.1X)</b>相比个人级认证提供了更强的安全保障，包括：<br/>"
            "• 集中式用户认证和授权管理<br/>"
            "• 支持多因素认证(MFA)<br/>"
            "• 用户级审计和追溯能力<br/>"
            "• 动态密钥管理(PMK缓存)<br/>"
            "• 与企业目录服务(LDAP/AD)集成",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "<b>PCI-DSS建议</b>: 对于处理或传输持卡人数据的无线网络，强烈推荐使用企业级认证。",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_pci_compliance_detailed(self, compliance_data: Dict) -> List:
        """第6章：PCI-DSS合规性详细检查"""
        elements = []
        
        elements.append(Paragraph("第六章 PCI-DSS合规性检查详情", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        # 合规性总览
        overall_status = compliance_data.get('overall_status', '未知')
        compliance_pct = compliance_data.get('compliance_percentage', 0)
        
        status_color = '#27ae60' if overall_status == 'COMPLIANT' else '#c0392b'
        
        overview_text = f"""
        <para align=justify>
        根据PCI-DSS 4.0标准对无线网络的相关要求进行逐项检查，
        总体合规率为<b><font color='{status_color}'>{compliance_pct:.1f}%</font></b>，
        合规状态: <b><font color='{status_color}'>{overall_status}</font></b>。
        </para>
        """
        elements.append(Paragraph(overview_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 15))
        
        # 详细检查清单
        elements.append(Paragraph("6.1 控制要求检查清单", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        checks = compliance_data.get('checks', {})
        if checks:
            check_data = [['要求ID', '要求描述', '测试程序', '状态', '发现']]
            
            for req_id, check in sorted(checks.items()):
                status = check.get('status', 'UNKNOWN')
                status_text = '✓ 通过' if status == 'PASS' else '✗ 失败' if status == 'FAIL' else '△ 部分'
                status_color_cell = colors.HexColor('#d4edda') if status == 'PASS' else colors.HexColor('#f8d7da')
                
                check_data.append([
                    req_id,
                    check.get('requirement', '')[:60],
                    check.get('test_procedure', '')[:80],
                    status_text,
                    check.get('finding', '')[:100]
                ])
            
            table = Table(check_data, colWidths=[1.5*cm, 3.5*cm, 4*cm, 1.5*cm, 3.5*cm])
            table.setStyle(self._get_standard_table_style())
            elements.append(table)
        
        elements.append(Spacer(1, 15))
        
        # 关键发现
        elements.append(Paragraph("6.2 合规性差距分析", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        gaps_text = """
        <para align=justify>
        根据检查结果，识别出以下主要合规性差距需要优先处理：<br/>
        <b>• 加密强度不足</b>: 部分网络使用过时加密协议<br/>
        <b>• 默认配置未更改</b>: 检测到使用默认SSID或配置的AP<br/>
        <b>• 访问控制薄弱</b>: 缺少企业级认证和网络隔离<br/>
        <b>• 监控机制缺失</b>: 未实施持续的无线网络安全监控
        </para>
        """
        elements.append(Paragraph(gaps_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_risk_threat_analysis(self, risk_data: Dict) -> List:
        """第7章：风险评估与威胁分析"""
        elements = []
        
        elements.append(Paragraph("第七章 风险评估与威胁分析", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        # 风险评分方法
        elements.append(Paragraph("7.1 风险评分方法论", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        elements.append(Paragraph(
            "本评估采用<b>CVSS 3.1(Common Vulnerability Scoring System)</b>标准对识别的"
            "安全风险进行量化评分。CVSS是业界广泛认可的漏洞评分系统，考虑了漏洞的可利用性、"
            "影响范围和复杂度等多个维度。",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "<b>风险等级划分</b>:<br/>"
            "• <b>关键(Critical)</b>: CVSS 9.0-10.0 - 严重威胁，需立即处理<br/>"
            "• <b>高(High)</b>: CVSS 7.0-8.9 - 重大风险，应优先修复<br/>"
            "• <b>中(Medium)</b>: CVSS 4.0-6.9 - 中等风险，计划修复<br/>"
            "• <b>低(Low)</b>: CVSS 0.1-3.9 - 低风险，可延后处理",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 15))
        
        # 风险统计
        elements.append(Paragraph("7.2 风险分布统计", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        summary = risk_data.get('summary', {})
        total_risks = sum(summary.values())
        
        risk_dist = [
            ['风险等级', '数量', '占比', 'CVSS范围'],
            ['关键风险', f"{summary.get('critical', 0)}个", 
             f"{summary.get('critical', 0)/total_risks*100 if total_risks>0 else 0:.1f}%", '9.0-10.0'],
            ['高风险', f"{summary.get('high', 0)}个",
             f"{summary.get('high', 0)/total_risks*100 if total_risks>0 else 0:.1f}%", '7.0-8.9'],
            ['中等风险', f"{summary.get('medium', 0)}个",
             f"{summary.get('medium', 0)/total_risks*100 if total_risks>0 else 0:.1f}%", '4.0-6.9'],
            ['低风险', f"{summary.get('low', 0)}个",
             f"{summary.get('low', 0)/total_risks*100 if total_risks>0 else 0:.1f}%", '0.1-3.9'],
        ]
        
        table = Table(risk_dist, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
        table.setStyle(self._get_standard_table_style())
        elements.append(table)
        elements.append(Spacer(1, 15))
        
        # 威胁场景分析
        elements.append(Paragraph("7.3 典型威胁场景", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        elements.append(Paragraph("基于当前网络环境，识别出以下典型威胁场景：", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 8))
        
        elements.append(Paragraph("<b>1. 中间人攻击(MITM)</b>", self.custom_styles['CustomBody']))
        elements.append(Paragraph("弱加密或开放网络易受MITM攻击，攻击者可截获敏感数据包括持卡人信息。", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 6))
        
        elements.append(Paragraph("<b>2. 邪恶双子(Evil Twin)攻击</b>", self.custom_styles['CustomBody']))
        elements.append(Paragraph("攻击者设置同名恶意AP，诱导用户连接并窃取凭据和数据。", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 6))
        
        elements.append(Paragraph("<b>3. 暴力破解攻击</b>", self.custom_styles['CustomBody']))
        elements.append(Paragraph("弱密码的WPA2-PSK网络易被离线破解，导致网络被完全渗透。", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 6))
        
        elements.append(Paragraph("<b>4. 拒绝服务(DoS)攻击</b>", self.custom_styles['CustomBody']))
        elements.append(Paragraph("通过去认证攻击或信道干扰导致网络不可用，影响业务连续性。", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 6))
        
        elements.append(Paragraph("<b>5. 侧信道攻击</b>", self.custom_styles['CustomBody']))
        elements.append(Paragraph("通过信号分析、流量模式等侧信道获取敏感信息。", self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_vulnerability_detailed(self, vuln_data: Dict) -> List:
        """第8章：漏洞扫描与检测详情"""
        elements = []
        
        elements.append(Paragraph("第八章 漏洞扫描与安全检测", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        # 漏洞检测方法
        vuln_intro = """
        <para align=justify>
        漏洞扫描是识别系统安全弱点的关键步骤。本次评估通过自动化扫描和人工审核相结合，
        全面检查无线网络配置、加密强度、认证机制等方面的潜在漏洞。
        </para>
        """
        elements.append(Paragraph(vuln_intro, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 15))
        
        # 漏洞统计
        elements.append(Paragraph("8.1 漏洞严重性分布", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        by_severity = vuln_data.get('by_severity', {})
        total_vulns = sum(by_severity.values())
        
        vuln_stats = [
            ['严重程度', '数量', '占比', '响应时限'],
            ['关键', f"{by_severity.get('critical', 0)}个",
             f"{by_severity.get('critical', 0)/total_vulns*100 if total_vulns>0 else 0:.1f}%", '立即(24小时内)'],
            ['高', f"{by_severity.get('high', 0)}个",
             f"{by_severity.get('high', 0)/total_vulns*100 if total_vulns>0 else 0:.1f}%", '紧急(7天内)'],
            ['中', f"{by_severity.get('medium', 0)}个",
             f"{by_severity.get('medium', 0)/total_vulns*100 if total_vulns>0 else 0:.1f}%", '计划(30天内)'],
            ['低', f"{by_severity.get('low', 0)}个",
             f"{by_severity.get('low', 0)/total_vulns*100 if total_vulns>0 else 0:.1f}%", '正常(90天内)'],
        ]
        
        table = Table(vuln_stats, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
        table.setStyle(self._get_standard_table_style())
        elements.append(table)
        elements.append(Spacer(1, 15))
        
        # 漏洞类型分析
        elements.append(Paragraph("8.2 漏洞类型分类", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        by_type = vuln_data.get('by_type', {})
        if by_type:
            type_data = [['漏洞类型', '数量', '典型CVE示例']]
            for vuln_type, count in by_type.items():
                type_data.append([
                    vuln_type,
                    f"{count}个",
                    self._get_cve_example(vuln_type)
                ])
            
            table = Table(type_data, colWidths=[5*cm, 3*cm, 6*cm])
            table.setStyle(self._get_standard_table_style())
            elements.append(table)
        
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_security_configuration_audit(self, data: Dict) -> List:
        """第9章：安全配置审核"""
        elements = []
        
        elements.append(Paragraph("第九章 安全配置审核", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        audit_intro = """
        <para align=justify>
        安全配置审核确保无线网络按照PCI-DSS要求和行业最佳实践进行配置。
        不当的配置是导致安全漏洞的主要原因之一。
        </para>
        """
        elements.append(Paragraph(audit_intro, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 15))
        
        # 配置项检查
        elements.append(Paragraph("9.1 关键配置项检查", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        config_checks = [
            ['配置项', 'PCI-DSS要求', '当前状态', '合规'],
            ['SSID广播', '可启用（需其他控制配合）', '已启用', '✓'],
            ['默认SSID', '必须更改', '部分未更改', '✗'],
            ['管理密码', '必须更改默认密码', '需人工验证', '△'],
            ['WPS功能', '建议禁用', '需人工验证', '△'],
            ['802.11w(PMF)', '推荐启用', '需设备支持', '△'],
            ['快速漫游(FT)', '可选启用', '部分支持', '✓'],
        ]
        
        table = Table(config_checks, colWidths=[3*cm, 4*cm, 3*cm, 2*cm])
        table.setStyle(self._get_standard_table_style())
        elements.append(table)
        elements.append(Spacer(1, 15))
        
        # 网络隔离检查
        elements.append(Paragraph("9.2 网络隔离与分段", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        elements.append(Paragraph(
            "<b>PCI-DSS要求</b>: 持卡人数据环境(CDE)必须与其他网络进行逻辑隔离。"
            "无线网络应实施VLAN分段，将不同安全级别的网络隔离。",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "<b>推荐配置</b>:<br/>"
            "• 员工网络、访客网络、IoT网络分别使用不同VLAN<br/>"
            "• CDE访问通过专用SSID和强认证<br/>"
            "• 实施防火墙规则限制跨VLAN流量<br/>"
            "• 使用802.1X动态VLAN分配",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_remediation_recommendations(self, recommendations: List[Dict]) -> List:
        """第10章：补救措施与改进建议（深度版）"""
        elements = []
        
        elements.append(Paragraph("第十章 补救措施与改进建议", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        remedy_intro = """
        <para align=justify>
        基于评估发现的安全风险和合规性差距，制定以下详细的补救措施和改进建议。
        建议按照优先级和时间表逐步实施，确保在合理时间内达到PCI-DSS合规要求。
        </para>
        """
        elements.append(Paragraph(remedy_intro, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 15))
        
        # 按优先级分组
        elements.append(Paragraph("10.1 紧急措施（立即执行）", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        critical_recs = [rec for rec in recommendations if rec.get('priority') == 'CRITICAL']
        if critical_recs:
            for i, rec in enumerate(critical_recs, 1):
                self._add_recommendation_detail(elements, i, rec)
        else:
            elements.append(Paragraph("✓ 无需立即处理的关键问题", self.custom_styles['CustomBody']))
        
        elements.append(Spacer(1, 15))
        
        # 高优先级建议
        elements.append(Paragraph("10.2 重要措施（7-30天内完成）", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        high_recs = [rec for rec in recommendations if rec.get('priority') == 'HIGH']
        if high_recs:
            for i, rec in enumerate(high_recs[:5], 1):  # 显示前5个
                self._add_recommendation_detail(elements, i, rec)
        
        elements.append(Spacer(1, 15))
        
        # 中等优先级
        elements.append(Paragraph("10.3 计划性改进（30-90天内完成）", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        medium_recs = [rec for rec in recommendations if rec.get('priority') == 'MEDIUM']
        if medium_recs:
            medium_summary = f"共{len(medium_recs)}项中等优先级改进建议，包括配置优化、监控增强、流程改进等。"
            elements.append(Paragraph(medium_summary, self.custom_styles['CustomBody']))
        
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_compliance_roadmap(self, data: Dict) -> List:
        """第11章：合规路线图"""
        elements = []
        
        elements.append(Paragraph("第十一章 PCI-DSS合规路线图", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        roadmap_intro = """
        <para align=justify>
        根据当前评估结果，制定分阶段的PCI-DSS合规实施路线图，确保系统性、
        可管理地达到合规要求。
        </para>
        """
        elements.append(Paragraph(roadmap_intro, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 15))
        
        # 实施阶段
        phases = [
            ['阶段', '时间框架', '主要任务', '预期成果'],
            ['第一阶段\n紧急修复', '0-30天', 
             '• 禁用WEP/WPA-TKIP\n• 更改默认配置\n• 实施访问控制',
             '消除关键风险\n合规率提升至60%'],
            ['第二阶段\n系统加固', '30-90天',
             '• 部署企业认证\n• 实施网络隔离\n• 增强监控机制',
             '完成主要控制\n合规率达到85%'],
            ['第三阶段\n持续优化', '90-180天',
             '• 实施自动化监控\n• 建立审计机制\n• 人员培训',
             '达到完全合规\n建立持续改进'],
        ]
        
        table = Table(phases, colWidths=[2.5*cm, 2.5*cm, 5*cm, 4*cm])
        table.setStyle(self._get_standard_table_style())
        elements.append(table)
        elements.append(Spacer(1, 15))
        
        # 资源需求
        elements.append(Paragraph("11.1 所需资源", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        elements.append(Paragraph(
            "<b>技术资源</b>:<br/>"
            "• 802.1X认证服务器（RADIUS）<br/>"
            "• 网络访问控制(NAC)系统<br/>"
            "• 无线入侵防御系统(WIPS)<br/>"
            "• SIEM安全信息与事件管理平台",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "<b>人力资源</b>:<br/>"
            "• 网络安全工程师（实施和配置）<br/>"
            "• 系统管理员（日常运维）<br/>"
            "• 安全审计人员（合规检查）",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_pci_appendix(self) -> List:
        """附录：PCI-DSS参考资料"""
        elements = []
        
        elements.append(Paragraph("附录 PCI-DSS参考资料", self.custom_styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        # 参考文档
        elements.append(Paragraph("A. 参考标准与文档", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        elements.append(Paragraph(
            "1. <b>PCI DSS v4.0</b> - Payment Card Industry Data Security Standard<br/>"
            "   PCI Security Standards Council, March 2022",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            "2. <b>Wireless Guideline</b> - Information Supplement to PCI DSS<br/>"
            "   PCI Security Standards Council",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            "3. <b>IEEE 802.11</b> - Wireless LAN Medium Access Control and Physical Layer Specifications",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            "4. <b>NIST SP 800-97</b> - Establishing Wireless Robust Security Networks:<br/>"
            "   A Guide to IEEE 802.11i",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            "5. <b>CVSS v3.1</b> - Common Vulnerability Scoring System Specification<br/>"
            "   FIRST.org",
            self.custom_styles['CustomBody']
        ))
        elements.append(Spacer(1, 15))
        
        # 术语表
        elements.append(Paragraph("B. 缩略语表", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        acronyms = [
            ['缩略语', '全称', '中文'],
            ['PCI-DSS', 'Payment Card Industry Data Security Standard', '支付卡行业数据安全标准'],
            ['AP', 'Access Point', '无线接入点'],
            ['SSID', 'Service Set Identifier', '服务集标识符'],
            ['WPA', 'Wi-Fi Protected Access', 'WiFi保护访问'],
            ['AES', 'Advanced Encryption Standard', '高级加密标准'],
            ['CCMP', 'Counter Mode with CBC-MAC Protocol', '计数器模式与CBC-MAC协议'],
            ['802.1X', 'IEEE 802.1X', 'IEEE端口认证标准'],
            ['RADIUS', 'Remote Authentication Dial-In User Service', '远程认证拨号用户服务'],
            ['CVSS', 'Common Vulnerability Scoring System', '通用漏洞评分系统'],
            ['CDE', 'Cardholder Data Environment', '持卡人数据环境'],
        ]
        
        table = Table(acronyms, colWidths=[2*cm, 6*cm, 5*cm])
        table.setStyle(self._get_standard_table_style())
        elements.append(table)
        elements.append(Spacer(1, 15))
        
        # 联系信息
        elements.append(Paragraph("C. 技术支持与咨询", self.custom_styles['SubTitle']))
        elements.append(Spacer(1, 10))
        
        contact_text = """
        <para align=justify>
        如需关于本报告或PCI-DSS合规性的进一步咨询，请联系：<br/>
        <b>技术支持</b>: support@company.com<br/>
        <b>安全团队</b>: security@company.com<br/>
        <b>合规咨询</b>: compliance@company.com
        </para>
        """
        elements.append(Paragraph(contact_text, self.custom_styles['CustomBody']))
        elements.append(Spacer(1, 20))
        
        return elements
    
    # 辅助方法
    def _get_score_interpretation(self, score: int) -> str:
        """解释分数含义"""
        if score >= 90:
            return "优秀，符合PCI-DSS要求"
        elif score >= 75:
            return "良好，有少量改进空间"
        elif score >= 60:
            return "一般，需要显著改进"
        else:
            return "不合格，存在严重安全隐患"
    
    def _identify_risk_areas(self, data: Dict) -> List[Dict]:
        """识别主要风险领域"""
        risk_areas = []
        
        # 加密风险
        enc_data = data.get('encryption_analysis', {})
        if enc_data.get('secure_percentage', 100) < 95:
            risk_areas.append({
                'title': '加密强度不足',
                'description': '部分网络使用过时或弱加密协议，无法满足PCI-DSS要求'
            })
        
        # 认证风险
        auth_data = data.get('authentication_analysis', {})
        auth_stats = auth_data.get('statistics', {})
        open_count = auth_stats.get('Open', {}).get('count', 0)
        if open_count > 0:
            risk_areas.append({
                'title': '开放网络风险',
                'description': f'检测到{open_count}个无加密网络，存在数据泄露风险'
            })
        
        # 配置风险
        risk_data = data.get('risk_assessment', {})
        if risk_data.get('summary', {}).get('high', 0) > 0:
            risk_areas.append({
                'title': '配置安全风险',
                'description': '存在高风险的配置问题，如默认设置、弱密码等'
            })
        
        return risk_areas
    
    def _get_auth_security_level(self, auth_type: str) -> str:
        """获取认证类型的安全等级"""
        if 'WPA3' in auth_type:
            return '优秀'
        elif 'Enterprise' in auth_type or '企业' in auth_type:
            return '良好'
        elif 'WPA2' in auth_type:
            return '一般'
        elif 'Open' in auth_type or '开放' in auth_type:
            return '极差'
        else:
            return '较差'
    
    def _get_cve_example(self, vuln_type: str) -> str:
        """获取漏洞类型的CVE示例"""
        cve_map = {
            'WPS PIN暴力破解': 'CVE-2011-5053 (Reaver)',
            'KRACK攻击': 'CVE-2017-13077 (WPA2密钥重装)',
            '弱加密算法': 'CVE-2001-0819 (WEP破解)',
            '弱加密': 'CVE-2017-13077 (KRACK攻击)',
            '认证缺陷': 'CVE-2018-14526 (WPA2漏洞)',
            '配置错误': 'CWE-16 (配置安全)',
            '信息泄露': 'CWE-200 (信息暴露)',
            '开放网络': 'CWE-319 (明文传输)',
        }
        return cve_map.get(vuln_type, 'N/A')
    
    def _add_recommendation_detail(self, elements: List, index: int, rec: Dict):
        """添加详细建议内容"""
        priority = rec.get('priority', 'N/A')
        priority_color = {
            'CRITICAL': '#c0392b',
            'HIGH': '#e67e22',
            'MEDIUM': '#f39c12',
            'LOW': '#3498db'
        }.get(priority, '#000000')
        
        elements.append(Paragraph(
            f"<b>{index}. {rec.get('title', '')}</b> "
            f"<font color='{priority_color}'>[{priority}]</font>",
            self.custom_styles['SubTitle']
        ))
        
        elements.append(Paragraph(
            f"<b>类别</b>: {rec.get('category', 'N/A')}",
            self.custom_styles['CustomBody']
        ))
        
        elements.append(Paragraph(
            f"<b>问题描述</b>: {rec.get('description', '')}",
            self.custom_styles['CustomBody']
        ))
        
        elements.append(Paragraph(
            f"<b>改进措施</b>: {rec.get('action', '')}",
            self.custom_styles['Emphasis']
        ))
        
        elements.append(Paragraph(
            f"<b>预期效果</b>: {rec.get('expected_outcome', '提升安全性和合规性')}",
            self.custom_styles['CustomBody']
        ))
        
        elements.append(Paragraph(
            f"<b>相关PCI-DSS要求</b>: {rec.get('pci_requirement', 'N/A')}",
            self.custom_styles['CustomBody']
        ))
        
        elements.append(Spacer(1, 12))
    
    def _get_standard_table_style(self) -> TableStyle:
        """获取标准表格样式"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Chinese'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
        ])
    
    # 兼容方法：与GUI界面调用匹配
    def generate_enterprise_report(self, analysis_data: Dict, filepath: str, company_name: str = None) -> bool:
        """
        生成企业报告（兼容方法）
        
        Args:
            analysis_data: 分析数据
            filepath: 输出路径
            company_name: 公司名称（可选）
            
        Returns:
            是否成功
        """
        return self.generate_signal_analysis_report(analysis_data, filepath)
    
    def generate_pci_dss_report(self, assessment_data: Dict, filepath: str, company_name: str = None) -> bool:
        """
        生成PCI-DSS报告（兼容方法）
        
        Args:
            assessment_data: 评估数据
            filepath: 输出路径
            company_name: 公司名称（可选）
            
        Returns:
            是否成功
        """
        return self.generate_security_assessment_report(assessment_data, filepath)

