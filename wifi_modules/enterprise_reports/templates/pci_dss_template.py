"""
PCI-DSS合规性评估报告模板 v2.0
支付卡行业数据安全标准评估
"""

from typing import Dict, List
from datetime import datetime
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm


class PCIDSSTemplate:
    """PCI-DSS合规性评估报告模板"""
    
    def __init__(self, styles: Dict):
        self.styles = styles
    
    def get_title(self) -> str:
        return "PCI-DSS无线网络安全合规性评估报告"
    
    def create_cover(self, data: Dict, company_name: str = "企业名称") -> List:
        """创建封面页"""
        elements = []
        
        title = Paragraph(
            "PCI-DSS无线网络安全<br/>合规性评估报告",
            self.styles.get('CustomTitle', self.styles['Heading1'])
        )
        elements.append(title)
        elements.append(Spacer(1, 1*cm))
        
        company = Paragraph(
            f"<b>{company_name}</b>",
            self.styles.get('CustomBody', self.styles['Normal'])
        )
        elements.append(company)
        elements.append(Spacer(1, 0.5*cm))
        
        scan_time = data.get('scan_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        time_text = Paragraph(
            f"评估时间: {scan_time}",
            self.styles.get('CustomBody', self.styles['Normal'])
        )
        elements.append(time_text)
        elements.append(Spacer(1, 0.5*cm))
        
        standard = Paragraph(
            "<b>评估标准：PCI-DSS v4.0</b>",
            self.styles.get('Emphasis', self.styles['Normal'])
        )
        elements.append(standard)
        
        return elements
    
    def create_summary(self, data: Dict) -> List:
        """创建执行摘要"""
        elements = []
        
        title = Paragraph(
            "执行摘要",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        pci = data.get('pci_dss', {})
        
        summary_text = f"""
        <b>合规性评分：{pci.get('compliance_score', 0)}/100</b><br/>
        <br/>
        合规项目：<b>{pci.get('compliant_items', 0)}</b> 项<br/>
        不合规项目：<b>{pci.get('non_compliant_items', 0)}</b> 项<br/>
        需改进项目：<b>{pci.get('needs_improvement', 0)}</b> 项<br/>
        <br/>
        <b>总体评估：{pci.get('overall_status', '部分合规')}</b>
        """
        
        summary = Paragraph(summary_text, self.styles.get('CustomBody', self.styles['Normal']))
        elements.append(summary)
        elements.append(Spacer(1, 1*cm))
        
        return elements
    
    def create_body(self, data: Dict, chart_manager=None) -> List:
        """创建详细分析主体"""
        elements = []
        
        # 1. 合规性检查清单
        elements.extend(self._create_compliance_checklist(data))
        
        # 2. 不合规项详情
        elements.extend(self._create_non_compliance_details(data))
        
        # 3. 风险评估
        elements.extend(self._create_risk_assessment(data))
        
        return elements
    
    def create_recommendations(self, data: Dict) -> List:
        """创建整改建议"""
        elements = []
        
        title = Paragraph(
            "整改建议和行动计划",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        recommendations = data.get('pci_recommendations', [
            "【高优先级】禁用所有不安全的加密协议（WEP、WPA）",
            "【高优先级】实施强制访问控制(MAC地址过滤)",
            "【中优先级】部署无线入侵检测系统(WIDS)",
            "【中优先级】定期进行渗透测试和安全审计",
            "【低优先级】建立完善的无线网络安全策略文档"
        ])
        
        for idx, rec in enumerate(recommendations, 1):
            rec_text = Paragraph(
                f"<b>{idx}.</b> {rec}",
                self.styles.get('CustomBody', self.styles['Normal'])
            )
            elements.append(rec_text)
            elements.append(Spacer(1, 0.3*cm))
        
        return elements
    
    def _create_compliance_checklist(self, data: Dict) -> List:
        """创建合规性检查清单"""
        elements = []
        
        title = Paragraph(
            "1. PCI-DSS合规性检查清单",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        checklist = data.get('compliance_checklist', [
            {'requirement': '2.1.1 更改默认密码', 'status': '合规', 'score': 100},
            {'requirement': '4.1.1 使用强加密', 'status': '部分合规', 'score': 75},
            {'requirement': '11.1.2 无线网络检测', 'status': '合规', 'score': 100},
            {'requirement': '12.3 可接受使用策略', 'status': '需改进', 'score': 50}
        ])
        
        table_data = [['要求编号', '检查项', '状态', '评分']]
        
        for item in checklist:
            table_data.append([
                item.get('requirement', '')[:20],
                item.get('description', item.get('requirement', ''))[:30],
                item.get('status', 'N/A'),
                f"{item.get('score', 0)}/100"
            ])
        
        checklist_table = Table(table_data, colWidths=[3*cm, 6*cm, 3*cm, 3*cm])
        checklist_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5490')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Chinese'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        elements.append(checklist_table)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_non_compliance_details(self, data: Dict) -> List:
        """创建不合规项详情"""
        elements = []
        
        title = Paragraph(
            "2. 不合规项详情",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        non_compliant = data.get('non_compliant_items_details', [])
        
        if non_compliant:
            for item in non_compliant[:5]:
                item_text = f"""
                <b>不合规项：{item.get('requirement', 'Unknown')}</b><br/>
                严重程度：{item.get('severity', 'Medium')}<br/>
                发现详情：{item.get('details', 'N/A')}<br/>
                整改建议：{item.get('remediation', 'N/A')}<br/>
                """
                desc = Paragraph(item_text, self.styles.get('CustomBody', self.styles['Normal']))
                elements.append(desc)
                elements.append(Spacer(1, 0.3*cm))
        else:
            compliant_text = Paragraph(
                "✓ 所有检查项均已合规",
                self.styles.get('CustomBody', self.styles['Normal'])
            )
            elements.append(compliant_text)
        
        elements.append(Spacer(1, 0.5*cm))
        return elements
    
    def _create_risk_assessment(self, data: Dict) -> List:
        """创建风险评估"""
        elements = []
        
        title = Paragraph(
            "3. 风险评估",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        risk = data.get('risk_assessment', {})
        
        text = f"""
        <b>总体风险等级：{risk.get('overall_risk', '中等')}</b><br/>
        <br/>
        高风险项：<b>{risk.get('high_risk_count', 0)}</b> 个<br/>
        中风险项：<b>{risk.get('medium_risk_count', 0)}</b> 个<br/>
        低风险项：<b>{risk.get('low_risk_count', 0)}</b> 个<br/>
        <br/>
        建议在 <b>{risk.get('remediation_timeline', '30天')}</b> 内完成整改。
        """
        
        desc = Paragraph(text, self.styles.get('CustomBody', self.styles['Normal']))
        elements.append(desc)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
