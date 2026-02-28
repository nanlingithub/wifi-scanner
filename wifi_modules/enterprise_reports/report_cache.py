"""
报告缓存系统 v2.0
智能缓存PDF报告，加速生成速度
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, Optional


class ReportCache:
    """✅ 报告生成缓存"""
    
    # 缓存有效期（秒）
    DEFAULT_TTL = 1800  # 30分钟
    
    def __init__(self, cache_dir: str = "./cache/reports", ttl: int = DEFAULT_TTL):
        """
        初始化缓存系统
        
        Args:
            cache_dir: 缓存目录
            ttl: 缓存有效期（秒）
        """
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        
        # 创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 清理过期缓存
        self._cleanup_expired()
    
    def _compute_hash(self, data: Dict) -> str:
        """
        计算数据哈希值
        
        Args:
            data: 报告数据
            
        Returns:
            str: MD5哈希值
        """
        # 移除时间戳等变化字段
        stable_data = {
            k: v for k, v in data.items() 
            if k not in ['timestamp', 'scan_time', 'report_time', 'generated_at']
        }
        
        # 序列化为JSON（排序键确保一致性）
        data_str = json.dumps(stable_data, sort_keys=True, ensure_ascii=False)
        
        # 计算MD5哈希
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, cache_key: str, report_type: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{report_type}_{cache_key}.pdf"
    
    def _get_meta_path(self, cache_key: str, report_type: str) -> Path:
        """获取元数据文件路径"""
        return self.cache_dir / f"{report_type}_{cache_key}.meta"
    
    def get(self, data: Dict, report_type: str) -> Optional[bytes]:
        """
        获取缓存的报告
        
        Args:
            data: 报告数据
            report_type: 报告类型（signal/security/pci_dss）
            
        Returns:
            Optional[bytes]: PDF内容（缓存命中）或None（缓存未命中）
        """
        cache_key = self._compute_hash(data)
        cache_file = self._get_cache_path(cache_key, report_type)
        meta_file = self._get_meta_path(cache_key, report_type)
        
        # 检查文件是否存在
        if not cache_file.exists() or not meta_file.exists():
            return None
        
        # 读取元数据
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            
            # 检查缓存是否过期
            cache_time = meta.get('created_at', 0)
            if time.time() - cache_time > self.ttl:
                # 缓存过期，删除文件
                cache_file.unlink(missing_ok=True)
                meta_file.unlink(missing_ok=True)
                return None
            
            # 读取PDF内容
            with open(cache_file, 'rb') as f:
                pdf_content = f.read()
            
            print(f"✓ 缓存命中: {report_type}_{cache_key[:8]}... (生成时间: <0.1秒)")
            return pdf_content
            
        except Exception as e:
            print(f"✗ 读取缓存失败: {e}")
            return None
    
    def set(self, data: Dict, report_type: str, pdf_content: bytes):
        """
        缓存报告
        
        Args:
            data: 报告数据
            report_type: 报告类型
            pdf_content: PDF内容
        """
        cache_key = self._compute_hash(data)
        cache_file = self._get_cache_path(cache_key, report_type)
        meta_file = self._get_meta_path(cache_key, report_type)
        
        try:
            # 写入PDF内容
            with open(cache_file, 'wb') as f:
                f.write(pdf_content)
            
            # 写入元数据
            meta = {
                'created_at': time.time(),
                'report_type': report_type,
                'cache_key': cache_key,
                'data_size': len(json.dumps(data))
            }
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2)
            
            print(f"✓ 报告已缓存: {report_type}_{cache_key[:8]}...")
            
        except Exception as e:
            print(f"✗ 缓存写入失败: {e}")
    
    def invalidate(self, data: Dict, report_type: str):
        """
        使缓存失效
        
        Args:
            data: 报告数据
            report_type: 报告类型
        """
        cache_key = self._compute_hash(data)
        cache_file = self._get_cache_path(cache_key, report_type)
        meta_file = self._get_meta_path(cache_key, report_type)
        
        cache_file.unlink(missing_ok=True)
        meta_file.unlink(missing_ok=True)
        
        print(f"✓ 缓存已清除: {report_type}_{cache_key[:8]}...")
    
    def clear_all(self):
        """清空所有缓存"""
        count = 0
        for file in self.cache_dir.glob('*.pdf'):
            file.unlink()
            count += 1
        for file in self.cache_dir.glob('*.meta'):
            file.unlink()
        
        print(f"✓ 已清空所有缓存 ({count}个文件)")
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_count = 0
        
        for meta_file in self.cache_dir.glob('*.meta'):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                
                # 检查是否过期
                cache_time = meta.get('created_at', 0)
                if current_time - cache_time > self.ttl:
                    # 删除PDF和元数据
                    pdf_file = meta_file.with_suffix('.pdf')
                    pdf_file.unlink(missing_ok=True)
                    meta_file.unlink()
                    expired_count += 1
                    
            except Exception:
                # 元数据损坏，删除
                meta_file.unlink(missing_ok=True)
        
        if expired_count > 0:
            print(f"✓ 已清理{expired_count}个过期缓存")
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        pdf_files = list(self.cache_dir.glob('*.pdf'))
        total_size = sum(f.stat().st_size for f in pdf_files)
        
        return {
            'total_files': len(pdf_files),
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir),
            'ttl_minutes': self.ttl / 60
        }


# 使用示例
if __name__ == '__main__':
    # 创建缓存实例
    cache = ReportCache()
    
    # 模拟报告数据
    test_data = {
        'networks': [
            {'ssid': 'WiFi-1', 'signal': -45},
            {'ssid': 'WiFi-2', 'signal': -60}
        ],
        'quality_score': 85,
        'timestamp': '2026-02-05 12:00:00'  # 会被忽略
    }
    
    # 测试缓存
    report_type = 'signal'
    
    # 首次生成（缓存未命中）
    cached = cache.get(test_data, report_type)
    if cached is None:
        print("✗ 缓存未命中，需要生成新报告")
        # 模拟PDF内容
        fake_pdf = b'%PDF-1.4\nFake PDF content'
        cache.set(test_data, report_type, fake_pdf)
    
    # 再次获取（缓存命中）
    cached = cache.get(test_data, report_type)
    if cached:
        print(f"✓ 缓存命中！内容长度: {len(cached)} bytes")
    
    # 获取统计信息
    stats = cache.get_stats()
    print(f"\n缓存统计:")
    print(f"  文件数: {stats['total_files']}")
    print(f"  总大小: {stats['total_size_mb']:.2f} MB")
    print(f"  有效期: {stats['ttl_minutes']:.0f} 分钟")
    
    # 清理测试
    cache.clear_all()
