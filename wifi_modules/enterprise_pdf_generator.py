#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
企业级WiFi报告PDF生成器
版本: 1.6
功能: 生成专业的PDF格式WiFi分析报告
"""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, KeepTogether
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("[警告] ReportLab未安装，PDF导出功能不可用")


class EnterprisePDFReportGenerator:
    """企业级PDF报告生成器"""
    
    def __init__(self):
        self.setup_fonts()
        self.styles = self._create_styles()
    
    def setup_fonts(self):
        """设置中文字体"""
        if not REPORTLAB_AVAILABLE:
            return
        
        try:
            # 尝试注册中文字体
            font_paths = [
                'C:/Windows/Fonts/simhei.ttf',  # 黑体
                'C:/Windows/Fonts/msyh.ttc',     # 微软雅黑
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',  # Linux
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Chinese', font_path))
                    break
        except Exception as e:
            print(f"[警告] 中文字体注册失败: {e}")
    
    def _create_styles(self) -> Dict:
        """创建样式"""
        if not REPORTLAB_AVAILABLE:
            return {}
        
        styles = getSampleStyleSheet()
        
        # 自定义样式
        custom_styles = {
            'Title': ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                textColor=colors.HexColor('#1a5490'),
                spaceAfter=30,
                alignment=TA_CENTER
            ),
            'Heading1': ParagraphStyle(
                'CustomHeading1',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#2c5aa0'),
                spaceAfter=12,
                spaceBefore=12
            ),
            'Heading2': ParagraphStyle(
                'CustomHeading2',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#3d6bb3'),
                spaceAfter=10,
                spaceBefore=10
            ),
            'Normal': ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6
            ),
            'BodyText': ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=10,
                alignment=TA_JUSTIFY
            )
        }
        
        return custom_styles
    
    def generate_enterprise_report(
        self, 
        analysis_data: Dict,
        output_path: str,
        company_name: str = "企业名称",
        report_type: str = "WiFi网络信号分析报告"
    ) -> bool:
        """
        生成企业级信号分析报告
        
        Args:
            analysis_data: 分析数据
            output_path: 输出文件路径
            company_name: 公司名称
            report_type: 报告类型
            
        Returns:
            是否成功
        """
        if not REPORTLAB_AVAILABLE:
            print("[错误] ReportLab未安装，无法生成PDF报告")
            return False
        
        try:
            # 创建PDF文档
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
            story.extend(self._create_cover_page(company_name, report_type, analysis_data))
            story.append(PageBreak())
            
            # 执行摘要
            story.extend(self._create_executive_summary(analysis_data))
            story.append(PageBreak())
            
            # 详细分析
            story.extend(self._create_detailed_analysis(analysis_data))
            story.append(PageBreak())
            
            # 建议措施
            story.extend(self._create_recommendations(analysis_data))
            
            # 生成PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"生成PDF报告失败: {e}")
            return False
    
    def generate_pci_dss_report(
        self,
        assessment_data: Dict,
        output_path: str,
        company_name: str = "企业名称"
    ) -> bool:
        """
        生成PCI-DSS评估报告
        
        Args:
            assessment_data: 评估数据
            output_path: 输出文件路径
            company_name: 公司名称
            
        Returns:
            是否成功
        """
        if not REPORTLAB_AVAILABLE:
            print("[错误] ReportLab未安装，无法生成PDF报告")
            return False
        
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
            story.extend(self._create_pci_cover_page(company_name, assessment_data))
            story.append(PageBreak())
            
            # 执行摘要
            story.extend(self._create_pci_executive_summary(assessment_data))
            story.append(PageBreak())
            
            # 合规状态
            story.extend(self._create_compliance_status(assessment_data))
            story.append(PageBreak())
            
            # 详细发现
            story.extend(self._create_findings_section(assessment_data))
            story.append(PageBreak())
            
            # 整改建议
            story.extend(self._create_pci_recommendations(assessment_data))
            
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"生成PCI-DSS报告失败: {e}")
            return False
    
    def _create_cover_page(self, company_name: str, report_type: str, data: Dict) -> List:
        """创建封面页"""
        elements = []
        
        # 标题
        title = Paragraph(
            f"<b>{report_type}</b>",
            self.styles['Title']
        )
        elements.append(Spacer(1, 2*inch))
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # 公司名称
        company = Paragraph(
            f"<b>{company_name}</b>",
            ParagraphStyle('Company', fontSize=18, alignment=TA_CENTER)
        )
        elements.append(company)
        elements.append(Spacer(1, 1*inch))
        
        # 报告信息
        timestamp = data.get('timestamp', datetime.now().isoformat())
        report_date = datetime.fromisoformat(timestamp).strftime('%Y年%m月%d日')
        
        info_text = f"""
        <para align=center>
        报告日期: {report_date}<br/>
        网络总数: {data.get('total_networks', 0)}<br/>
        报告版本: v1.6<br/>
        </para>
        """
        
        info = Paragraph(info_text, self.styles['Normal'])
        elements.append(info)
        
        return elements
    
    def _create_executive_summary(self, data: Dict) -> List:
        """创建执行摘要"""
        elements = []
        
        # 标题
        elements.append(Paragraph("<b>执行摘要</b>", self.styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        # 概述
        coverage = data.get('coverage_quality', {})
        security = data.get('security_analysis', {})
        
        summary_text = f"""
        本报告对企业无线网络进行了全面的信号分析和安全评估。
        共扫描到 {data.get('total_networks', 0)} 个无线网络。
        
        <b>关键发现:</b><br/>
        • 信号质量评级: {coverage.get('rating', 'N/A')}<br/>
        • 质量评分: {coverage.get('quality_score', 0)}/100<br/>
        • 安全评分: {security.get('security_score', 0)}/100<br/>
        • 脆弱网络数: {security.get('vulnerable_networks', 0)}<br/>
        • 优化建议数: {len(data.get('recommendations', []))}<br/>
        """
        
        elements.append(Paragraph(summary_text, self.styles['BodyText']))
        elements.append(Spacer(1, 0.3*inch))
        
        # 关键指标表格
        metrics_data = [
            ['指标', '数值', '评级'],
            ['网络总数', str(data.get('total_networks', 0)), '-'],
            ['信号质量', f"{coverage.get('quality_score', 0)}/100", coverage.get('rating', 'N/A')],
            ['安全评分', f"{security.get('security_score', 0)}/100", self._get_security_rating(security.get('security_score', 0))],
            ['强信号比例', f"{coverage.get('strong_signal_percentage', 0)}%", '-'],
            ['弱信号比例', f"{coverage.get('weak_signal_percentage', 0)}%", '-']
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch, 1.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(metrics_table)
        
        return elements
    
    def _create_detailed_analysis(self, data: Dict) -> List:
        """创建详细分析"""
        elements = []
        
        elements.append(Paragraph("<b>详细分析</b>", self.styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        # 1. 信号分布分析
        elements.append(Paragraph("<b>1. 信号强度分布</b>", self.styles['Heading2']))
        signal_dist = data.get('signal_distribution', {})
        
        signal_data = [
            ['信号等级', '网络数量', '百分比'],
            ['优秀 (≥-50dBm)', str(signal_dist.get('excellent', 0)), 
             f"{signal_dist.get('excellent', 0) / max(data.get('total_networks', 1), 1) * 100:.1f}%"],
            ['良好 (-50~-60dBm)', str(signal_dist.get('good', 0)),
             f"{signal_dist.get('good', 0) / max(data.get('total_networks', 1), 1) * 100:.1f}%"],
            ['一般 (-60~-70dBm)', str(signal_dist.get('fair', 0)),
             f"{signal_dist.get('fair', 0) / max(data.get('total_networks', 1), 1) * 100:.1f}%"],
            ['较差 (-70~-80dBm)', str(signal_dist.get('poor', 0)),
             f"{signal_dist.get('poor', 0) / max(data.get('total_networks', 1), 1) * 100:.1f}%"],
            ['很差 (<-80dBm)', str(signal_dist.get('very_poor', 0)),
             f"{signal_dist.get('very_poor', 0) / max(data.get('total_networks', 1), 1) * 100:.1f}%"]
        ]
        
        signal_table = Table(signal_data, colWidths=[3*inch, 2*inch, 1.5*inch])
        signal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(signal_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # 2. 信道利用率
        elements.append(Paragraph("<b>2. 信道利用率分析</b>", self.styles['Heading2']))
        channel_util = data.get('channel_utilization', {})
        
        channel_text = f"""
        检测到 {channel_util.get('total_channels_used', 0)} 个信道正在使用。
        拥塞信道数: {len(channel_util.get('congested_channels', []))}
        最拥塞信道: {channel_util.get('most_congested', 'N/A')}
        """
        
        elements.append(Paragraph(channel_text, self.styles['BodyText']))
        elements.append(Spacer(1, 0.2*inch))
        
        # 3. 安全分析
        elements.append(Paragraph("<b>3. 安全性分析</b>", self.styles['Heading2']))
        security = data.get('security_analysis', {})
        sec_dist = security.get('distribution', {})
        
        security_data = [
            ['加密类型', '网络数量'],
            ['WPA3', str(sec_dist.get('WPA3', 0))],
            ['WPA2', str(sec_dist.get('WPA2', 0))],
            ['WPA', str(sec_dist.get('WPA', 0))],
            ['WEP', str(sec_dist.get('WEP', 0))],
            ['开放网络', str(sec_dist.get('Open', 0))]
        ]
        
        security_table = Table(security_data, colWidths=[3*inch, 3.5*inch])
        security_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(security_table)
        
        return elements
    
    def _create_recommendations(self, data: Dict) -> List:
        """创建建议措施"""
        elements = []
        
        elements.append(Paragraph("<b>优化建议</b>", self.styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        recommendations = data.get('recommendations', [])
        
        for i, rec in enumerate(recommendations, 1):
            rec_text = f"""
            <b>{i}. [{rec['priority']}] {rec['category']}</b><br/>
            <b>问题:</b> {rec['issue']}<br/>
            <b>建议:</b> {rec['recommendation']}<br/>
            <b>影响:</b> {rec['impact']}<br/>
            """
            
            elements.append(Paragraph(rec_text, self.styles['BodyText']))
            elements.append(Spacer(1, 0.15*inch))
        
        return elements
    
    def _create_pci_cover_page(self, company_name: str, data: Dict) -> List:
        """创建PCI-DSS封面页"""
        elements = []
        
        title = Paragraph(
            "<b>PCI-DSS无线网络安全评估报告</b>",
            self.styles['Title']
        )
        elements.append(Spacer(1, 2*inch))
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        company = Paragraph(
            f"<b>{company_name}</b>",
            ParagraphStyle('Company', fontSize=18, alignment=TA_CENTER)
        )
        elements.append(company)
        elements.append(Spacer(1, 1*inch))
        
        timestamp = data.get('timestamp', datetime.now().isoformat())
        report_date = datetime.fromisoformat(timestamp).strftime('%Y年%m月%d日')
        
        info_text = f"""
        <para align=center>
        评估日期: {report_date}<br/>
        PCI-DSS版本: {data.get('pci_dss_version', 'N/A')}<br/>
        合规状态: {data.get('compliance_score', 0) >= 80 and '合规' or '不合规'}<br/>
        合规分数: {data.get('compliance_score', 0)}/100<br/>
        风险级别: {data.get('risk_level', 'Unknown')}<br/>
        </para>
        """
        
        elements.append(Paragraph(info_text, self.styles['Normal']))
        
        return elements
    
    def _create_pci_executive_summary(self, data: Dict) -> List:
        """创建PCI-DSS执行摘要"""
        elements = []
        
        elements.append(Paragraph("<b>执行摘要</b>", self.styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        findings = data.get('findings', [])
        critical = len([f for f in findings if f['severity'] == 'Critical'])
        high = len([f for f in findings if f['severity'] == 'High'])
        medium = len([f for f in findings if f['severity'] == 'Medium'])
        
        summary_text = f"""
        本报告基于PCI-DSS {data.get('pci_dss_version', 'N/A')} 标准对企业无线网络进行了安全评估。
        
        <b>评估结果:</b><br/>
        • 合规分数: {data.get('compliance_score', 0)}/100<br/>
        • 合规状态: {data.get('compliance_score', 0) >= 80 and '<font color="green">合规</font>' or '<font color="red">不合规</font>'}<br/>
        • 风险级别: {self._get_risk_color(data.get('risk_level', 'Unknown'))}<br/>
        <br/>
        <b>发现统计:</b><br/>
        • 严重 (Critical): {critical}<br/>
        • 高 (High): {high}<br/>
        • 中 (Medium): {medium}<br/>
        """
        
        elements.append(Paragraph(summary_text, self.styles['BodyText']))
        
        return elements
    
    def _create_compliance_status(self, data: Dict) -> List:
        """创建合规状态"""
        elements = []
        
        elements.append(Paragraph("<b>合规状态评估</b>", self.styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        requirements = data.get('requirements', {})
        
        req_data = [['要求', '标题', '状态', '分数']]
        
        for req_key, req_info in requirements.items():
            status_color = 'green' if req_info['status'] == 'Pass' else 'red'
            req_data.append([
                req_key,
                req_info['title'],
                f'<font color="{status_color}">{req_info["status"]}</font>',
                f"{req_info['score']}/100"
            ])
        
        req_table = Table(req_data, colWidths=[1.5*inch, 3*inch, 1*inch, 1*inch])
        req_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(req_table)
        
        return elements
    
    def _create_findings_section(self, data: Dict) -> List:
        """创建发现章节"""
        elements = []
        
        elements.append(Paragraph("<b>详细发现</b>", self.styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        findings = data.get('findings', [])
        
        for i, finding in enumerate(findings, 1):
            severity_color = {
                'Critical': 'red',
                'High': 'orange',
                'Medium': 'yellow',
                'Low': 'blue',
                'Info': 'gray'
            }.get(finding['severity'], 'black')
            
            finding_text = f"""
            <b>{i}. [{finding['requirement']}] <font color="{severity_color}">{finding['severity']}</font></b><br/>
            <b>问题:</b> {finding['issue']}<br/>
            <b>详情:</b> {finding['details']}<br/>
            <b>整改建议:</b> {finding['remediation']}<br/>
            <b>PCI-DSS参考:</b> {finding['pci_reference']}<br/>
            """
            
            elements.append(Paragraph(finding_text, self.styles['BodyText']))
            elements.append(Spacer(1, 0.15*inch))
        
        return elements
    
    def _create_pci_recommendations(self, data: Dict) -> List:
        """创建PCI-DSS整改建议"""
        elements = []
        
        elements.append(Paragraph("<b>整改建议</b>", self.styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        recommendations = data.get('recommendations', [])
        
        for i, rec in enumerate(recommendations, 1):
            rec_text = f"""
            <b>{i}. [{rec['priority']}] {rec['category']}</b><br/>
            <b>措施:</b> {rec['action']}<br/>
            <b>描述:</b> {rec['description']}<br/>
            <b>实施步骤:</b><br/>
            """
            
            for step in rec['steps']:
                rec_text += f"{step}<br/>"
            
            rec_text += f"<b>时间要求:</b> {rec['timeline']}<br/>"
            
            elements.append(Paragraph(rec_text, self.styles['BodyText']))
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _get_security_rating(self, score: float) -> str:
        """获取安全评级"""
        if score >= 90:
            return '优秀'
        elif score >= 80:
            return '良好'
        elif score >= 60:
            return '一般'
        else:
            return '较差'
    
    def _get_risk_color(self, risk_level: str) -> str:
        """获取风险级别颜色标记"""
        colors_map = {
            'Critical': '<font color="red">严重</font>',
            'High': '<font color="orange">高</font>',
            'Medium': '<font color="yellow">中</font>',
            'Low': '<font color="green">低</font>'
        }
        return colors_map.get(risk_level, risk_level)
