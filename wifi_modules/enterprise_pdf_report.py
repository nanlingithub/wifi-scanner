#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WiFi企业级PDF报告生成器
功能：生成专业的WiFi网络分析和安全评估PDF报告
版本：1.6
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
import io


class EnterprisePDFReport:
    """企业级PDF报告生成器"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.page_width, self.page_height = A4
        
    def _setup_custom_styles(self):
        """设置自定义样式"""
        # 标题样式
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # 章节标题
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=20,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        # 子标题
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#34495e'),
            spaceBefore=10,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        # 正文
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#2c3e50')
        ))
        
        # 高亮文本
        self.styles.add(ParagraphStyle(
            name='Highlight',
            parent=self.styles['BodyText'],
            fontSize=11,
            textColor=colors.HexColor('#e74c3c'),
            fontName='Helvetica-Bold'
        ))
    
    def generate_signal_analysis_report(self, 
                                       analysis_data: Dict,
                                       output_path: str) -> bool:
        """
        生成信号分析PDF报告
        
        Args:
            analysis_data: 来自EnterpriseSignalReport的分析数据
            output_path: PDF输出路径
            
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
            
            # 封面
            story.extend(self._create_cover_page(
                "WiFi企业级网络信号分析报告",
                analysis_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            ))
            
            story.append(PageBreak())
            
            # 执行摘要
            story.extend(self._create_executive_summary(analysis_data))
            story.append(Spacer(1, 0.5*cm))
            
            # 信号质量分析
            story.extend(self._create_signal_quality_section(analysis_data))
            story.append(Spacer(1, 0.5*cm))
            
            # 覆盖率评估
            story.extend(self._create_coverage_section(analysis_data))
            story.append(Spacer(1, 0.5*cm))
            
            # 信道利用率
            story.extend(self._create_channel_section(analysis_data))
            story.append(PageBreak())
            
            # 干扰分析
            story.extend(self._create_interference_section(analysis_data))
            story.append(Spacer(1, 0.5*cm))
            
            # 安全状态
            story.extend(self._create_security_section(analysis_data))
            story.append(PageBreak())
            
            # 优化建议
            story.extend(self._create_recommendations_section(analysis_data))
            
            # 生成PDF
            doc.build(story, onFirstPage=self._add_page_number,
                     onLaterPages=self._add_page_number)
            
            return True
            
        except Exception as e:
            print(f"生成信号分析报告失败: {e}")
            return False
    
    def generate_security_assessment_report(self,
                                           assessment_data: Dict,
                                           output_path: str) -> bool:
        """
        生成PCI-DSS安全评估PDF报告
        
        Args:
            assessment_data: 来自PCIDSSSecurityAssessment的评估数据
            output_path: PDF输出路径
            
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
            
            # 封面
            story.extend(self._create_cover_page(
                "PCI-DSS无线网络安全风险评估报告",
                assessment_data.get('assessment_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            ))
            
            story.append(PageBreak())
            
            # 评估总览
            story.extend(self._create_security_overview(assessment_data))
            story.append(Spacer(1, 0.5*cm))
            
            # 风险评分仪表盘
            story.extend(self._create_risk_dashboard(assessment_data))
            story.append(PageBreak())
            
            # PCI-DSS合规性检查
            story.extend(self._create_compliance_checklist(assessment_data))
            story.append(PageBreak())
            
            # 详细安全风险
            story.extend(self._create_detailed_risks(assessment_data))
            story.append(PageBreak())
            
            # 修复建议
            story.extend(self._create_remediation_plan(assessment_data))
            
            # 生成PDF
            doc.build(story, onFirstPage=self._add_page_number,
                     onLaterPages=self._add_page_number)
            
            return True
            
        except Exception as e:
            print(f"生成安全评估报告失败: {e}")
            return False
    
    def _create_cover_page(self, title: str, timestamp: str) -> List:
        """创建封面"""
        elements = []
        
        elements.append(Spacer(1, 3*cm))
        elements.append(Paragraph(title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 1*cm))
        
        # 报告信息
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#7f8c8d'),
            alignment=TA_CENTER
        )
        
        elements.append(Paragraph(f"生成时间: {timestamp}", info_style))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph("WiFi专业分析工具 v1.6", info_style))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph("NL@China_SZ", info_style))
        
        return elements
    
    def _create_executive_summary(self, data: Dict) -> List:
        """创建执行摘要"""
        elements = []
        
        elements.append(Paragraph("执行摘要", self.styles['SectionTitle']))
        
        # 总体评分表
        summary_data = [
            ['评估维度', '评分', '等级'],
            ['信号质量', 
             f"{data.get('signal_quality', {}).get('quality_score', 0)}/100",
             self._get_score_color(data.get('signal_quality', {}).get('quality_score', 0))],
            ['覆盖率', 
             f"{data.get('coverage_assessment', {}).get('coverage_score', 0)}/100",
             self._get_score_color(data.get('coverage_assessment', {}).get('coverage_score', 0))],
            ['干扰控制', 
             f"{data.get('interference_sources', {}).get('interference_score', 0)}/100",
             self._get_score_color(data.get('interference_sources', {}).get('interference_score', 0))],
            ['安全性', 
             f"{data.get('security_status', {}).get('security_score', 0)}/100",
             self._get_score_color(data.get('security_status', {}).get('security_score', 0))],
        ]
        
        table = Table(summary_data, colWidths=[8*cm, 4*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_signal_quality_section(self, data: Dict) -> List:
        """创建信号质量分析章节"""
        elements = []
        
        elements.append(Paragraph("1. 信号质量分析", self.styles['SectionTitle']))
        
        signal_data = data.get('signal_quality', {})
        distribution = signal_data.get('distribution', {})
        
        # 信号分布饼图
        if distribution:
            chart_img = self._create_pie_chart(
                list(distribution.keys()),
                list(distribution.values()),
                "信号质量分布"
            )
            if chart_img:
                elements.append(chart_img)
                elements.append(Spacer(1, 0.3*cm))
        
        # 统计信息（修复：使用正确的百分比单位）
        avg_signal = signal_data.get('average_signal', 0)
        avg_dbm = signal_data.get('average_dbm', -100)  # 新增：从分析结果获取dBm值
        max_signal = signal_data.get('max_signal', signal_data.get('strongest_signal', 0))
        min_signal = signal_data.get('min_signal', signal_data.get('weakest_signal', 0))
        
        stats_text = f"""
        <b>平均信号强度:</b> {avg_signal:.1f}% ({avg_dbm:.1f} dBm)<br/>
        <b>最强信号:</b> {max_signal:.0f}%<br/>
        <b>最弱信号:</b> {min_signal:.0f}%<br/>
        <b>信号方差:</b> {signal_data.get('signal_variance', 0)}<br/>
        <b>质量评分:</b> {signal_data.get('quality_score', signal_data.get('average_score', 0))}/100
        """
        
        elements.append(Paragraph(stats_text, self.styles['CustomBody']))
        
        return elements
    
    def _create_coverage_section(self, data: Dict) -> List:
        """创建覆盖率评估章节"""
        elements = []
        
        elements.append(Paragraph("2. 覆盖率评估", self.styles['SectionTitle']))
        
        coverage_data = data.get('coverage_assessment', {})
        
        coverage_table_data = [
            ['指标', '数值'],
            ['接入点总数', str(coverage_data.get('total_access_points', 0))],
            ['可用AP数', str(coverage_data.get('available_aps', 0))],
            ['覆盖评分', f"{coverage_data.get('coverage_score', 0)}/100"],
            ['覆盖等级', coverage_data.get('coverage_level', 'N/A')],
        ]
        
        table = Table(coverage_table_data, colWidths=[10*cm, 6*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_channel_section(self, data: Dict) -> List:
        """创建信道利用率章节"""
        elements = []
        
        elements.append(Paragraph("3. 信道利用率分析", self.styles['SectionTitle']))
        
        channel_data = data.get('channel_utilization', {})
        
        info_text = f"""
        <b>使用的信道数:</b> {channel_data.get('total_channels_used', 0)}<br/>
        <b>最拥挤信道:</b> 信道 {channel_data.get('most_congested_channel', 0)} 
        ({channel_data.get('max_networks_on_channel', 0)} 个网络)<br/>
        <b>拥堵等级:</b> {channel_data.get('congestion_level', 'N/A')}
        """
        
        elements.append(Paragraph(info_text, self.styles['CustomBody']))
        
        return elements
    
    def _create_interference_section(self, data: Dict) -> List:
        """创建干扰分析章节"""
        elements = []
        
        elements.append(Paragraph("4. 干扰源分析", self.styles['SectionTitle']))
        
        interference_data = data.get('interference_sources', {})
        risks = interference_data.get('risk_details', [])
        
        if risks:
            for risk in risks:
                risk_text = f"""
                <b>干扰类型:</b> {risk['type']}<br/>
                <b>严重程度:</b> {risk['severity'].upper()}<br/>
                <b>描述:</b> {risk['description']}<br/>
                """
                if 'recommendation' in risk:
                    risk_text += f"<b>建议:</b> {risk['recommendation']}<br/>"
                
                elements.append(Paragraph(risk_text, self.styles['CustomBody']))
                elements.append(Spacer(1, 0.3*cm))
        else:
            elements.append(Paragraph("未检测到明显干扰源", self.styles['CustomBody']))
        
        return elements
    
    def _create_security_section(self, data: Dict) -> List:
        """创建安全状态章节"""
        elements = []
        
        elements.append(Paragraph("5. 安全状态评估", self.styles['SectionTitle']))
        
        security_data = data.get('security_status', {})
        distribution = security_data.get('security_distribution', {})
        
        # 安全类型分布表
        sec_table_data = [['加密类型', '数量']]
        for sec_type, count in distribution.items():
            sec_table_data.append([sec_type, str(count)])
        
        table = Table(sec_table_data, colWidths=[10*cm, 6*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*cm))
        
        summary = f"""
        <b>安全评分:</b> {security_data.get('security_score', 0)}/100<br/>
        <b>脆弱网络数:</b> {security_data.get('vulnerable_networks', 0)}<br/>
        <b>安全等级:</b> {security_data.get('security_level', 'N/A')}
        """
        elements.append(Paragraph(summary, self.styles['CustomBody']))
        
        return elements
    
    def _create_recommendations_section(self, data: Dict) -> List:
        """创建优化建议章节"""
        elements = []
        
        elements.append(Paragraph("6. 优化建议", self.styles['SectionTitle']))
        
        recommendations = data.get('optimization_recommendations', [])
        
        if recommendations:
            # 按优先级分组
            high_priority = [r for r in recommendations if r['priority'] == 'high']
            medium_priority = [r for r in recommendations if r['priority'] == 'medium']
            
            if high_priority:
                elements.append(Paragraph("高优先级", self.styles['SubTitle']))
                for i, rec in enumerate(high_priority, 1):
                    rec_text = f"""
                    <b>{i}. [{rec['category']}]</b><br/>
                    问题: {rec['issue']}<br/>
                    建议: {rec['suggestion']}
                    """
                    elements.append(Paragraph(rec_text, self.styles['CustomBody']))
                    elements.append(Spacer(1, 0.3*cm))
            
            if medium_priority:
                elements.append(Paragraph("中等优先级", self.styles['SubTitle']))
                for i, rec in enumerate(medium_priority, 1):
                    rec_text = f"""
                    <b>{i}. [{rec['category']}]</b><br/>
                    问题: {rec['issue']}<br/>
                    建议: {rec['suggestion']}
                    """
                    elements.append(Paragraph(rec_text, self.styles['CustomBody']))
                    elements.append(Spacer(1, 0.3*cm))
        else:
            elements.append(Paragraph("网络状态良好，暂无优化建议", self.styles['CustomBody']))
        
        return elements
    
    def _create_security_overview(self, data: Dict) -> List:
        """创建安全评估总览"""
        elements = []
        
        elements.append(Paragraph("安全评估总览", self.styles['SectionTitle']))
        
        overview_text = f"""
        <b>检测网络总数:</b> {data.get('total_networks_detected', 0)}<br/>
        <b>风险评分:</b> {data.get('overall_risk_score', 0)}/100<br/>
        <b>风险等级:</b> {data.get('risk_level', 'N/A')}<br/>
        <b>检测到的安全问题:</b> {len(data.get('detailed_risks', []))}个
        """
        
        elements.append(Paragraph(overview_text, self.styles['CustomBody']))
        
        return elements
    
    def _create_risk_dashboard(self, data: Dict) -> List:
        """创建风险仪表盘"""
        elements = []
        
        elements.append(Paragraph("风险评分", self.styles['SectionTitle']))
        
        # 创建仪表盘图表
        risk_score = data.get('overall_risk_score', 0)
        gauge_img = self._create_gauge_chart(risk_score, "风险评分 (分数越高越安全)")
        
        if gauge_img:
            elements.append(gauge_img)
        
        return elements
    
    def _create_compliance_checklist(self, data: Dict) -> List:
        """创建PCI-DSS合规性检查清单"""
        elements = []
        
        elements.append(Paragraph("PCI-DSS合规性检查", self.styles['SectionTitle']))
        
        compliance = data.get('compliance_check', {})
        checks = compliance.get('compliance_checks', {})
        
        # 合规性表格
        check_data = [['PCI-DSS要求', '状态', '详情']]
        
        for check_id, check_info in checks.items():
            status_symbol = '✓' if check_info['status'] == 'compliant' else '✗'
            check_data.append([
                check_info['requirement'],
                status_symbol,
                check_info['details']
            ])
        
        table = Table(check_data, colWidths=[9*cm, 2*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        summary_text = f"""
        <b>总体状态:</b> {compliance.get('overall_status', 'N/A').upper()}<br/>
        <b>合规率:</b> {compliance.get('compliance_rate', 0)}%<br/>
        <b>通过检查:</b> {compliance.get('compliant_checks', 0)}/{compliance.get('total_checks', 0)}
        """
        elements.append(Paragraph(summary_text, self.styles['CustomBody']))
        
        return elements
    
    def _create_detailed_risks(self, data: Dict) -> List:
        """创建详细安全风险章节"""
        elements = []
        
        elements.append(Paragraph("详细安全风险", self.styles['SectionTitle']))
        
        risks = data.get('detailed_risks', [])
        
        if risks:
            for i, risk in enumerate(risks, 1):
                severity_color = {
                    'critical': '#e74c3c',
                    'high': '#e67e22',
                    'medium': '#f39c12',
                    'low': '#95a5a6'
                }.get(risk['severity'], '#95a5a6')
                
                risk_text = f"""
                <b>风险 {i}: [{risk['severity'].upper()}] {risk['category']}</b><br/>
                <font color="{severity_color}">相关要求: {risk['requirement']}</font><br/>
                <b>发现:</b> {risk['finding']}<br/>
                <b>修复建议:</b> {risk['remediation']}
                """
                
                elements.append(Paragraph(risk_text, self.styles['CustomBody']))
                elements.append(Spacer(1, 0.5*cm))
        else:
            elements.append(Paragraph("未检测到明显安全风险", self.styles['CustomBody']))
        
        return elements
    
    def _create_remediation_plan(self, data: Dict) -> List:
        """创建修复计划"""
        elements = []
        
        elements.append(Paragraph("修复行动计划", self.styles['SectionTitle']))
        
        risks = data.get('detailed_risks', [])
        critical_risks = [r for r in risks if r['severity'] == 'critical']
        high_risks = [r for r in risks if r['severity'] == 'high']
        
        if critical_risks or high_risks:
            plan_text = "<b>建议按以下优先级处理:</b><br/><br/>"
            
            if critical_risks:
                plan_text += f"<b>1. 紧急处理 ({len(critical_risks)}个严重风险):</b><br/>"
                for risk in critical_risks:
                    plan_text += f"   • {risk['category']}: {risk['remediation']}<br/>"
                plan_text += "<br/>"
            
            if high_risks:
                plan_text += f"<b>2. 优先处理 ({len(high_risks)}个高风险):</b><br/>"
                for risk in high_risks:
                    plan_text += f"   • {risk['category']}: {risk['remediation']}<br/>"
            
            elements.append(Paragraph(plan_text, self.styles['CustomBody']))
        else:
            elements.append(Paragraph("无需立即修复的问题，建议定期复查", self.styles['CustomBody']))
        
        return elements
    
    def _create_pie_chart(self, labels: List, values: List, title: str) -> Optional[Image]:
        """创建饼图"""
        try:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.set_title(title)
            
            # 保存到内存
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return Image(img_buffer, width=10*cm, height=7*cm)
        except Exception as e:
            print(f"创建饼图失败: {e}")
            return None
    
    def _create_gauge_chart(self, score: int, title: str) -> Optional[Image]:
        """创建仪表盘图表"""
        try:
            fig, ax = plt.subplots(figsize=(6, 3))
            
            # 绘制半圆仪表盘
            colors_map = ['#e74c3c', '#e67e22', '#f39c12', '#2ecc71']
            wedges = []
            for i in range(4):
                wedge = Wedge((0.5, 0), 0.4, i*45, (i+1)*45, 
                            facecolor=colors_map[i], edgecolor='white', linewidth=2)
                ax.add_patch(wedge)
            
            # 绘制指针
            angle = score * 1.8  # 0-100 映射到 0-180度
            angle_rad = np.deg2rad(180 - angle)
            ax.arrow(0.5, 0, 0.35*np.cos(angle_rad), 0.35*np.sin(angle_rad),
                    head_width=0.03, head_length=0.05, fc='black', ec='black')
            
            # 设置
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 0.5)
            ax.axis('off')
            ax.text(0.5, -0.1, f'{score}/100', ha='center', fontsize=14, weight='bold')
            ax.set_title(title)
            
            # 保存
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return Image(img_buffer, width=10*cm, height=5*cm)
        except Exception as e:
            print(f"创建仪表盘失败: {e}")
            return None
    
    def _get_score_color(self, score: int) -> str:
        """根据评分获取等级"""
        if score >= 90:
            return '优秀'
        elif score >= 75:
            return '良好'
        elif score >= 60:
            return '一般'
        else:
            return '需改进'
    
    def _add_page_number(self, canvas_obj, doc):
        """添加页码"""
        page_num = canvas_obj.getPageNumber()
        text = f"第 {page_num} 页"
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.drawRightString(
            doc.pagesize[0] - 2*cm,
            1*cm,
            text
        )


# 修复numpy导入问题
try:
    import numpy as np
except ImportError:
    np = None
