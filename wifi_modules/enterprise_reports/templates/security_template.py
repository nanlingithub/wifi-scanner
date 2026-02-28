"""
安全评估报告模板 v2.0
WiFi网络安全评估报告
"""

from typing import Dict, List
from datetime import datetime
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm


class SecurityAssessmentTemplate:
    """安全评估报告模板"""
    
    def __init__(self, styles: Dict):
        self.styles = styles
    
    def get_title(self) -> str:
        return "WiFi网络安全评估报告"
    
    def create_cover(self, data: Dict, company_name: str = "企业名称") -> List:
        """创建封面页"""
        elements = []
        
        title = Paragraph(
            "WiFi网络安全评估报告",
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
        
        security = data.get('security', {})
        
        summary_text = f"""
        <b>安全评分：{security.get('security_score', 0)}/100</b><br/>
        <br/>
        扫描网络总数：<b>{data.get('total_networks', 0)}</b><br/>
        高风险网络：<b>{security.get('high_risk_count', 0)}</b> 个<br/>
        中风险网络：<b>{security.get('medium_risk_count', 0)}</b> 个<br/>
        低风险网络：<b>{security.get('low_risk_count', 0)}</b> 个<br/>
        """
        
        summary = Paragraph(summary_text, self.styles.get('CustomBody', self.styles['Normal']))
        elements.append(summary)
        elements.append(Spacer(1, 1*cm))
        
        return elements
    
    def create_body(self, data: Dict, chart_manager=None) -> List:
        """创建详细分析主体"""
        elements = []
        
        # 1. 加密方式分析
        elements.extend(self._create_encryption_section(data))
        
        # 2. 漏洞分析
        elements.extend(self._create_vulnerability_section(data))
        
        # 3. 风险网络详情
        elements.extend(self._create_risk_networks_section(data))
        
        return elements
    
    def create_recommendations(self, data: Dict) -> List:
        """创建安全建议"""
        elements = []
        
        title = Paragraph(
            "安全加固建议",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        recommendations = data.get('security_recommendations', [
            "禁用所有WEP加密网络",
            "升级到WPA3加密标准",
            "启用强密码策略",
            "定期更新网络设备固件",
            "部署网络访问控制(NAC)"
        ])
        
        for idx, rec in enumerate(recommendations, 1):
            rec_text = Paragraph(
                f"<b>{idx}.</b> {rec}",
                self.styles.get('CustomBody', self.styles['Normal'])
            )
            elements.append(rec_text)
            elements.append(Spacer(1, 0.3*cm))
        
        return elements
    
    def _create_encryption_section(self, data: Dict) -> List:
        """创建加密方式分析章节"""
        elements = []
        
        title = Paragraph(
            "1. 加密方式分析",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        encryption = data.get('encryption_stats', {})
        
        text = f"""
        WPA3: <b>{encryption.get('WPA3', 0)}</b> 个<br/>
        WPA2: <b>{encryption.get('WPA2', 0)}</b> 个<br/>
        WPA: <b>{encryption.get('WPA', 0)}</b> 个<br/>
        WEP: <b>{encryption.get('WEP', 0)}</b> 个 ⚠️<br/>
        开放网络: <b>{encryption.get('Open', 0)}</b> 个 ⚠️⚠️<br/>
        """
        
        desc = Paragraph(text, self.styles.get('CustomBody', self.styles['Normal']))
        elements.append(desc)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_vulnerability_section(self, data: Dict) -> List:
        """创建漏洞分析章节"""
        elements = []
        
        title = Paragraph(
            "2. 漏洞分析",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        vulns = data.get('vulnerabilities', [])
        
        if vulns:
            for vuln in vulns[:5]:  # 显示前5个
                vuln_text = f"""
                <b>漏洞：{vuln.get('name', 'Unknown')}</b><br/>
                严重程度：{vuln.get('severity', 'Medium')}<br/>
                影响网络：{vuln.get('affected_count', 0)} 个<br/>
                """
                desc = Paragraph(vuln_text, self.styles.get('CustomBody', self.styles['Normal']))
                elements.append(desc)
                elements.append(Spacer(1, 0.3*cm))
        else:
            no_vuln = Paragraph(
                "✓ 未发现重大安全漏洞",
                self.styles.get('CustomBody', self.styles['Normal'])
            )
            elements.append(no_vuln)
        
        elements.append(Spacer(1, 0.5*cm))
        return elements
    
    def _create_risk_networks_section(self, data: Dict) -> List:
        """创建风险网络详情章节"""
        elements = []
        
        title = Paragraph(
            "3. 高风险网络详情",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        risk_networks = data.get('risk_networks', [])[:10]
        
        if risk_networks:
            table_data = [['SSID', '风险等级', '加密方式', '漏洞']]
            
            for net in risk_networks:
                table_data.append([
                    net.get('ssid', 'N/A')[:20],
                    net.get('risk_level', 'Medium'),
                    net.get('encryption', 'N/A'),
                    net.get('vulnerability', 'N/A')[:15]
                ])
            
            risk_table = Table(table_data, colWidths=[5*cm, 3*cm, 3*cm, 4*cm])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Chinese'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            elements.append(risk_table)
        
        return elements
