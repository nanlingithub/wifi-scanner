"""
信号分析报告模板 v2.0
企业级WiFi信号质量分析报告
"""

from typing import Dict, List
from datetime import datetime
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm


class SignalAnalysisTemplate:
    """信号分析报告模板"""
    
    def __init__(self, styles: Dict):
        """
        初始化模板
        
        Args:
            styles: PDF样式字典
        """
        self.styles = styles
    
    def get_title(self) -> str:
        """获取报告标题"""
        return "企业级WiFi网络信号分析报告"
    
    def create_cover(self, data: Dict, company_name: str = "企业名称") -> List:
        """
        创建封面页
        
        Args:
            data: 报告数据
            company_name: 公司名称
            
        Returns:
            List: ReportLab元素列表
        """
        elements = []
        
        # 大标题
        title = Paragraph(
            "企业级WiFi网络信号分析报告",
            self.styles.get('CustomTitle', self.styles['Heading1'])
        )
        elements.append(title)
        elements.append(Spacer(1, 1*cm))
        
        # 公司名称
        company = Paragraph(
            f"<b>{company_name}</b>",
            self.styles.get('CustomBody', self.styles['Normal'])
        )
        elements.append(company)
        elements.append(Spacer(1, 0.5*cm))
        
        # 报告时间
        scan_time = data.get('scan_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        time_text = Paragraph(
            f"报告生成时间: {scan_time}",
            self.styles.get('CustomBody', self.styles['Normal'])
        )
        elements.append(time_text)
        elements.append(Spacer(1, 0.5*cm))
        
        # 报告编号
        report_id = f"WIFI-SIG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        id_text = Paragraph(
            f"报告编号: {report_id}",
            self.styles.get('CustomBody', self.styles['Normal'])
        )
        elements.append(id_text)
        elements.append(Spacer(1, 2*cm))
        
        # 机密性声明
        confidential = Paragraph(
            "<b>机密文件 | Confidential</b><br/>"
            "本报告包含企业网络敏感信息，请妥善保管",
            self.styles.get('Emphasis', self.styles['Normal'])
        )
        elements.append(confidential)
        
        return elements
    
    def create_summary(self, data: Dict) -> List:
        """
        创建执行摘要
        
        Args:
            data: 报告数据
            
        Returns:
            List: ReportLab元素列表
        """
        elements = []
        
        # 章节标题
        title = Paragraph(
            "执行摘要",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        # 总体评分
        signal = data.get('signal_quality', {})
        quality_score = signal.get('quality_score', 0)
        
        summary_text = f"""
        <b>总体评分：{quality_score}/100</b><br/>
        <br/>
        本次分析共扫描到 <b>{data.get('total_networks', 0)}</b> 个WiFi网络，
        平均信号强度为 <b>{signal.get('average_signal', 0):.1f}%</b>。
        其中强信号网络 <b>{signal.get('strong_count', 0)}</b> 个，
        弱信号网络 <b>{signal.get('weak_count', 0)}</b> 个。
        """
        
        summary = Paragraph(
            summary_text,
            self.styles.get('CustomBody', self.styles['Normal'])
        )
        elements.append(summary)
        elements.append(Spacer(1, 0.5*cm))
        
        # 评分表
        score_data = [
            ['评估项', '得分', '等级'],
            ['信号质量', f"{quality_score}/100", self._get_grade(quality_score)],
            ['覆盖率', f"{data.get('coverage_score', 0)}/100", 
             self._get_grade(data.get('coverage_score', 0))],
            ['干扰控制', f"{data.get('interference_score', 0)}/100",
             self._get_grade(data.get('interference_score', 0))]
        ]
        
        score_table = Table(score_data, colWidths=[6*cm, 4*cm, 3*cm])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Chinese'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(score_table)
        elements.append(Spacer(1, 1*cm))
        
        return elements
    
    def create_body(self, data: Dict, chart_manager=None) -> List:
        """
        创建详细分析主体
        
        Args:
            data: 报告数据
            chart_manager: 图表管理器
            
        Returns:
            List: ReportLab元素列表
        """
        elements = []
        
        # 1. 信号质量分析
        elements.extend(self._create_signal_quality_section(data, chart_manager))
        
        # 2. 覆盖率评估
        elements.extend(self._create_coverage_section(data))
        
        # 3. 信道利用率
        elements.extend(self._create_channel_section(data))
        
        # 4. 干扰源分析
        elements.extend(self._create_interference_section(data))
        
        # 5. 网络详情
        elements.extend(self._create_network_details(data))
        
        return elements
    
    def create_recommendations(self, data: Dict) -> List:
        """
        创建优化建议
        
        Args:
            data: 报告数据
            
        Returns:
            List: ReportLab元素列表
        """
        elements = []
        
        # 章节标题
        title = Paragraph(
            "优化建议",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        # 建议列表
        recommendations = data.get('recommendations', [
            "优化AP位置，提高覆盖率",
            "调整信道配置，减少干扰",
            "升级设备支持WiFi 6标准",
            "部署5GHz频段网络"
        ])
        
        for idx, rec in enumerate(recommendations, 1):
            rec_text = Paragraph(
                f"<b>{idx}.</b> {rec}",
                self.styles.get('CustomBody', self.styles['Normal'])
            )
            elements.append(rec_text)
            elements.append(Spacer(1, 0.3*cm))
        
        return elements
    
    def _create_signal_quality_section(self, data: Dict, chart_manager=None) -> List:
        """创建信号质量分析章节"""
        elements = []
        
        # 章节标题
        title = Paragraph(
            "1. 信号质量分析",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        signal = data.get('signal_quality', {})
        
        # 文字描述
        text = f"""
        信号质量是WiFi网络性能的核心指标。本次扫描发现：<br/>
        <br/>
        • 平均信号强度：<b>{signal.get('average_signal', 0):.1f}%</b><br/>
        • 最强信号：<b>{signal.get('max_signal', 0):.1f}%</b><br/>
        • 最弱信号：<b>{signal.get('min_signal', 0):.1f}%</b><br/>
        • 强信号网络（>70%）：<b>{signal.get('strong_count', 0)}</b> 个<br/>
        • 弱信号网络（<30%）：<b>{signal.get('weak_count', 0)}</b> 个<br/>
        """
        
        desc = Paragraph(
            text,
            self.styles.get('CustomBody', self.styles['Normal'])
        )
        elements.append(desc)
        elements.append(Spacer(1, 0.5*cm))
        
        # 如果有图表管理器，添加饼图
        if chart_manager and signal.get('distribution'):
            dist = signal['distribution']
            labels = list(dist.keys())
            sizes = list(dist.values())
            
            pie_img = chart_manager.create_pie_chart(
                labels=labels,
                sizes=sizes,
                title='信号质量分布',
                colors=['#2ecc71', '#3498db', '#f39c12', '#e74c3c']
            )
            
            from reportlab.platypus import Image
            img = Image(pie_img, width=12*cm, height=8*cm)
            elements.append(img)
            elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_coverage_section(self, data: Dict) -> List:
        """创建覆盖率评估章节"""
        elements = []
        
        title = Paragraph(
            "2. 覆盖率评估",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        coverage = data.get('coverage_analysis', {})
        score = coverage.get('coverage_score', 0)
        
        text = f"""
        网络覆盖评分：<b>{score}/100</b><br/>
        <br/>
        覆盖良好区域占比：<b>{coverage.get('good_coverage_percent', 0):.1f}%</b><br/>
        需要改善区域：<b>{coverage.get('poor_coverage_areas', 0)}</b> 个<br/>
        """
        
        desc = Paragraph(text, self.styles.get('CustomBody', self.styles['Normal']))
        elements.append(desc)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_channel_section(self, data: Dict) -> List:
        """创建信道利用率章节"""
        elements = []
        
        title = Paragraph(
            "3. 信道利用率分析",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        channel = data.get('channel_analysis', {})
        
        text = f"""
        2.4GHz频段使用：<b>{channel.get('2.4G_usage', 0)}</b> 个网络<br/>
        5GHz频段使用：<b>{channel.get('5G_usage', 0)}</b> 个网络<br/>
        拥挤信道：<b>{', '.join(map(str, channel.get('congested_channels', [])))}</b><br/>
        """
        
        desc = Paragraph(text, self.styles.get('CustomBody', self.styles['Normal']))
        elements.append(desc)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_interference_section(self, data: Dict) -> List:
        """创建干扰源分析章节"""
        elements = []
        
        title = Paragraph(
            "4. 干扰源分析",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        interference = data.get('interference_analysis', {})
        
        text = f"""
        干扰等级：<b>{interference.get('interference_level', '低')}</b><br/>
        受干扰网络数：<b>{interference.get('affected_networks', 0)}</b> 个<br/>
        主要干扰源：<b>{interference.get('main_source', '无')}</b><br/>
        """
        
        desc = Paragraph(text, self.styles.get('CustomBody', self.styles['Normal']))
        elements.append(desc)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_network_details(self, data: Dict) -> List:
        """创建网络详情章节"""
        elements = []
        
        title = Paragraph(
            "5. 网络详情列表",
            self.styles.get('SectionTitle', self.styles['Heading2'])
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        networks = data.get('networks', [])[:10]  # 只显示前10个
        
        if networks:
            table_data = [['SSID', '信号', '频段', '信道', '加密']]
            
            for net in networks:
                table_data.append([
                    net.get('ssid', 'N/A')[:20],
                    f"{net.get('signal_percent', 0):.0f}%",
                    net.get('band', 'N/A'),
                    str(net.get('channel', 'N/A')),
                    net.get('security', 'N/A')
                ])
            
            net_table = Table(table_data, colWidths=[6*cm, 2*cm, 2*cm, 2*cm, 3*cm])
            net_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Chinese'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            elements.append(net_table)
        
        return elements
    
    def _get_grade(self, score: float) -> str:
        """根据分数获取等级"""
        if score >= 90:
            return "A (优秀)"
        elif score >= 80:
            return "B (良好)"
        elif score >= 70:
            return "C (一般)"
        elif score >= 60:
            return "D (及格)"
        else:
            return "F (不及格)"
