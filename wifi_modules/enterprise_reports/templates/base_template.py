"""
报告模板基类
定义标准报告结构协议
"""

from typing import Dict, List, Protocol


class ReportTemplate(Protocol):
    """报告模板协议"""
    
    def create_cover(self, data: Dict, company_name: str = "企业名称") -> List:
        """
        创建封面页
        
        Args:
            data: 报告数据
            company_name: 公司名称
            
        Returns:
            List: ReportLab元素列表
        """
        ...
    
    def create_summary(self, data: Dict) -> List:
        """
        创建执行摘要
        
        Args:
            data: 报告数据
            
        Returns:
            List: ReportLab元素列表
        """
        ...
    
    def create_body(self, data: Dict, chart_manager=None) -> List:
        """
        创建详细分析主体
        
        Args:
            data: 报告数据
            chart_manager: 图表管理器
            
        Returns:
            List: ReportLab元素列表
        """
        ...
    
    def create_recommendations(self, data: Dict) -> List:
        """
        创建优化建议
        
        Args:
            data: 报告数据
            
        Returns:
            List: ReportLab元素列表
        """
        ...
    
    def get_title(self) -> str:
        """获取报告标题"""
        ...
