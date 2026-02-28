"""
统一PDF生成器 v2.0
消除代码重复，支持异步生成和智能缓存
"""

import os
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .chart_manager import ChartManager
from .report_cache import ReportCache
from .templates.base_template import ReportTemplate


class PDFGenerator:
    """✅ 统一PDF生成器（消除重复）"""
    
    def __init__(self, use_cache: bool = True):
        """
        初始化PDF生成器
        
        Args:
            use_cache: 是否启用缓存
        """
        self.setup_fonts()
        self.styles = self._create_styles()
        self.cache = ReportCache() if use_cache else None
    
    def setup_fonts(self):
        """设置中文字体"""
        try:
            font_paths = [
                'C:/Windows/Fonts/msyh.ttc',  # 微软雅黑
                'C:/Windows/Fonts/simhei.ttf',  # 黑体
                'C:/Windows/Fonts/simsun.ttc',  # 宋体
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('Chinese', font_path))
                        print(f"✓ 成功注册字体: {font_path}")
                        break
                    except Exception as e:
                        continue
        except Exception as e:
            print(f"✗ 字体注册失败: {e}")
    
    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """创建自定义样式"""
        base_styles = getSampleStyleSheet()
        custom_styles = {}
        
        # 复制基础样式
        for key in base_styles.byName.keys():
            custom_styles[key] = base_styles[key]
        
        # 标题样式
        custom_styles['CustomTitle'] = ParagraphStyle(
            'CustomTitle',
            parent=base_styles['Heading1'],
            fontName='Chinese',
            fontSize=24,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # 章节标题
        custom_styles['SectionTitle'] = ParagraphStyle(
            'SectionTitle',
            parent=base_styles['Heading2'],
            fontName='Chinese',
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=20,
            spaceAfter=12,
            backColor=colors.HexColor('#ecf0f1'),
            borderPadding=5
        )
        
        # 子标题
        custom_styles['SubTitle'] = ParagraphStyle(
            'SubTitle',
            parent=base_styles['Heading3'],
            fontName='Chinese',
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceBefore=12,
            spaceAfter=8
        )
        
        # 正文
        custom_styles['CustomBody'] = ParagraphStyle(
            'CustomBody',
            parent=base_styles['Normal'],
            fontName='Chinese',
            fontSize=10,
            leading=16,
            textColor=colors.black,
            alignment=TA_JUSTIFY
        )
        
        # 重点文本
        custom_styles['Emphasis'] = ParagraphStyle(
            'Emphasis',
            parent=base_styles['Normal'],
            fontName='Chinese',
            fontSize=11,
            textColor=colors.HexColor('#c0392b'),
            spaceBefore=6,
            spaceAfter=6
        )
        
        return custom_styles
    
    def generate_report(self, 
                       data: Dict,
                       output_path: str,
                       template: ReportTemplate,
                       company_name: str = "企业名称",
                       report_type: str = "signal") -> bool:
        """
        生成报告（自动缓存）
        
        Args:
            data: 报告数据
            output_path: 输出路径
            template: 报告模板
            company_name: 公司名称
            report_type: 报告类型（signal/security/pci_dss）
            
        Returns:
            bool: 生成是否成功
        """
        start_time = time.time()
        
        # ✅ 尝试从缓存获取
        if self.cache:
            cached_pdf = self.cache.get(data, report_type)
            if cached_pdf:
                with open(output_path, 'wb') as f:
                    f.write(cached_pdf)
                elapsed = time.time() - start_time
                print(f"✓ 使用缓存报告（生成时间: {elapsed:.2f}秒）")
                return True
        
        # 缓存未命中，生成新报告
        temp_path = output_path + ".tmp"
        
        try:
            success = self._generate_pdf_internal(
                data, temp_path, template, company_name
            )
            
            if success:
                # ✅ 写入缓存
                if self.cache:
                    with open(temp_path, 'rb') as f:
                        pdf_content = f.read()
                    self.cache.set(data, report_type, pdf_content)
                
                # 移动到目标位置
                if os.path.exists(output_path):
                    os.remove(output_path)
                os.rename(temp_path, output_path)
                
                elapsed = time.time() - start_time
                print(f"✓ 新报告已生成并缓存（生成时间: {elapsed:.2f}秒）")
                return True
            
            return False
            
        except Exception as e:
            print(f"✗ 生成报告失败: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
    
    def _generate_pdf_internal(self,
                               data: Dict,
                               output_path: str,
                               template: ReportTemplate,
                               company_name: str) -> bool:
        """
        内部PDF生成方法
        
        Args:
            data: 报告数据
            output_path: 输出路径
            template: 报告模板
            company_name: 公司名称
            
        Returns:
            bool: 生成是否成功
        """
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
        
        # 使用ChartManager管理图表资源
        with ChartManager() as chart_manager:
            # 1. 封面页
            story.extend(template.create_cover(data, company_name))
            story.append(PageBreak())
            
            # 2. 执行摘要
            story.extend(template.create_summary(data))
            story.append(PageBreak())
            
            # 3. 详细分析主体
            story.extend(template.create_body(data, chart_manager))
            story.append(PageBreak())
            
            # 4. 优化建议
            story.extend(template.create_recommendations(data))
            
            # 生成PDF
            doc.build(story)
            # ChartManager会在退出with块时自动清理资源
        
        return True


class PDFGeneratorAsync(PDFGenerator):
    """✅ 异步PDF生成器（带进度反馈）"""
    
    def generate_report_async(self,
                              data: Dict,
                              output_path: str,
                              template: ReportTemplate,
                              company_name: str = "企业名称",
                              report_type: str = "signal",
                              progress_callback: Optional[Callable[[int, str, str], None]] = None) -> bool:
        """
        异步生成报告
        
        Args:
            data: 报告数据
            output_path: 输出路径
            template: 报告模板
            company_name: 公司名称
            report_type: 报告类型
            progress_callback: 进度回调 callback(percent, status, detail)
            
        Returns:
            bool: 生成是否成功
        """
        start_time = time.time()
        
        try:
            # 阶段1: 准备数据 (0-10%)
            if progress_callback:
                progress_callback(5, "准备报告数据...", "初始化PDF文档")
            
            # 检查缓存
            if self.cache:
                cached_pdf = self.cache.get(data, report_type)
                if cached_pdf:
                    if progress_callback:
                        progress_callback(50, "使用缓存报告...", "正在写入文件")
                    
                    with open(output_path, 'wb') as f:
                        f.write(cached_pdf)
                    
                    if progress_callback:
                        elapsed = time.time() - start_time
                        progress_callback(100, "生成完成！", 
                                        f"已保存到: {output_path}（{elapsed:.2f}秒）")
                    return True
            
            # 创建PDF文档
            if progress_callback:
                progress_callback(10, "初始化文档...", "设置页面布局")
            
            doc = SimpleDocTemplate(
                output_path + ".tmp",
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            
            with ChartManager() as chart_manager:
                # 阶段2: 生成封面 (10-20%)
                if progress_callback:
                    progress_callback(15, "生成封面...", "创建报告标题页")
                story.extend(template.create_cover(data, company_name))
                story.append(PageBreak())
                
                # 阶段3: 生成摘要 (20-35%)
                if progress_callback:
                    progress_callback(25, "生成执行摘要...", "分析关键指标")
                story.extend(template.create_summary(data))
                story.append(PageBreak())
                
                # 阶段4: 生成主体 (35-80%)
                if progress_callback:
                    progress_callback(40, "生成详细分析...", "创建图表和表格")
                
                body_elements = template.create_body(data, chart_manager)
                
                # 分段添加主体内容，提供细粒度进度
                if isinstance(body_elements, list):
                    total_elements = len(body_elements)
                    for idx, element in enumerate(body_elements):
                        story.append(element)
                        if progress_callback and total_elements > 0:
                            progress = 40 + int((idx + 1) / total_elements * 40)
                            progress_callback(
                                progress,
                                f"生成详细分析... ({idx+1}/{total_elements})",
                                f"处理内容元素"
                            )
                else:
                    story.append(body_elements)
                
                story.append(PageBreak())
                
                # 阶段5: 生成建议 (80-90%)
                if progress_callback:
                    progress_callback(85, "生成优化建议...", "整理改进方案")
                story.extend(template.create_recommendations(data))
                
                # 阶段6: 编译PDF (90-100%)
                if progress_callback:
                    progress_callback(95, "编译PDF文档...", "正在写入文件")
                
                doc.build(story)
            
            # 写入缓存
            if self.cache:
                with open(output_path + ".tmp", 'rb') as f:
                    pdf_content = f.read()
                self.cache.set(data, report_type, pdf_content)
            
            # 移动到目标位置
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(output_path + ".tmp", output_path)
            
            # 完成
            if progress_callback:
                elapsed = time.time() - start_time
                progress_callback(100, "生成完成！", 
                                f"已保存到: {output_path}（{elapsed:.2f}秒）")
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(0, "生成失败", f"错误: {str(e)}")
            
            # 清理临时文件
            temp_file = output_path + ".tmp"
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            print(f"✗ 生成报告失败: {e}")
            return False


# 使用示例
if __name__ == '__main__':
    from templates.signal_template import SignalAnalysisTemplate
    
    # 测试数据
    test_data = {
        'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_networks': 88,
        'signal_quality': {
            'quality_score': 85,
            'average_signal': 68.5,
            'strong_count': 30,
            'weak_count': 10
        }
    }
    
    # 方式1: 同步生成（带缓存）
    generator = PDFGenerator(use_cache=True)
    template = SignalAnalysisTemplate(generator.styles)
    
    success = generator.generate_report(
        data=test_data,
        output_path="test_report_sync.pdf",
        template=template,
        company_name="测试企业",
        report_type="signal"
    )
    
    print(f"同步生成: {'成功' if success else '失败'}")
    
    # 方式2: 异步生成（带进度）
    async_generator = PDFGeneratorAsync(use_cache=True)
    
    def print_progress(percent, status, detail):
        print(f"[{percent:3d}%] {status} - {detail}")
    
    success = async_generator.generate_report_async(
        data=test_data,
        output_path="test_report_async.pdf",
        template=template,
        company_name="测试企业",
        report_type="signal",
        progress_callback=print_progress
    )
    
    print(f"异步生成: {'成功' if success else '失败'}")
