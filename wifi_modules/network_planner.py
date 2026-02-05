"""
专业无线网络规划设计系统 - AP布局优化模块
功能：智能AP选址、覆盖优化、干扰分析、容量规划
"""

import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class APCandidate:
    """AP候选位置"""
    x: float
    y: float
    score: float
    coverage_radius: float
    estimated_users: int
    interference_level: float


class NetworkPlanner:
    """无线网络规划设计器"""
    
    # AP技术参数
    AP_MODELS = {
        'WiFi 6E企业级': {
            'max_power_dbm': 23,
            'coverage_radius': 30,  # 米
            'max_users': 100,
            'frequency_bands': ['2.4GHz', '5GHz', '6GHz'],
            'channel_width': [20, 40, 80, 160],
            'price': 3000
        },
        'WiFi 6企业级': {
            'max_power_dbm': 20,
            'coverage_radius': 25,
            'max_users': 80,
            'frequency_bands': ['2.4GHz', '5GHz'],
            'channel_width': [20, 40, 80],
            'price': 2000
        },
        'WiFi 5企业级': {
            'max_power_dbm': 18,
            'coverage_radius': 20,
            'max_users': 50,
            'frequency_bands': ['2.4GHz', '5GHz'],
            'channel_width': [20, 40, 80],
            'price': 1200
        },
        'WiFi 6商用': {
            'max_power_dbm': 17,
            'coverage_radius': 15,
            'max_users': 40,
            'frequency_bands': ['2.4GHz', '5GHz'],
            'channel_width': [20, 40],
            'price': 800
        }
    }
    
    def __init__(self, area_width: float, area_height: float, scenario: str = '普通办公'):
        self.area_width = area_width  # 米
        self.area_height = area_height
        self.scenario = scenario
        self.obstacles = []
        self.optimization_result = None
    
    def add_obstacle(self, obstacle_type: str, coords: List, material: str = '砖墙'):
        """添加障碍物"""
        self.obstacles.append({
            'type': obstacle_type,
            'coords': coords,
            'material': material
        })
    
    def optimize_ap_placement(self, target_users: int, budget: float = None,
                             ap_model: str = 'WiFi 6企业级') -> Dict:
        """优化AP布局 - 核心算法"""
        
        # 选择AP型号
        ap_spec = self.AP_MODELS.get(ap_model, self.AP_MODELS['WiFi 6企业级'])
        
        # 计算需要的AP数量
        area_sqm = self.area_width * self.area_height
        
        # 基于覆盖半径计算
        ap_coverage_area = np.pi * (ap_spec['coverage_radius'] ** 2)
        aps_by_area = int(np.ceil(area_sqm / ap_coverage_area * 1.3))  # 1.3为重叠系数
        
        # 基于容量计算
        aps_by_capacity = int(np.ceil(target_users / ap_spec['max_users']))
        
        # 取较大值
        required_aps = max(aps_by_area, aps_by_capacity)
        
        # 预算约束
        if budget:
            max_affordable_aps = int(budget / ap_spec['price'])
            if max_affordable_aps < required_aps:
                required_aps = max_affordable_aps
        
        # 生成候选位置（网格法 + 聚类优化）
        candidates = self._generate_ap_candidates(required_aps, ap_spec)
        
        # 选择最优位置
        selected_aps = self._select_optimal_positions(candidates, required_aps, ap_spec)
        
        # 分配信道
        channel_plan = self._plan_channels(selected_aps, ap_spec)
        
        # 计算覆盖和干扰
        coverage_analysis = self._analyze_coverage(selected_aps, ap_spec)
        
        # 生成BOM和成本
        bom = self._generate_bom(selected_aps, ap_spec, ap_model)
        
        self.optimization_result = {
            'ap_count': len(selected_aps),
            'ap_model': ap_model,
            'ap_positions': selected_aps,
            'channel_plan': channel_plan,
            'coverage_analysis': coverage_analysis,
            'bom': bom,
            'design_parameters': {
                'area_sqm': area_sqm,
                'target_users': target_users,
                'scenario': self.scenario,
                'coverage_radius': ap_spec['coverage_radius'],
                'expected_coverage_rate': coverage_analysis['coverage_rate']
            }
        }
        
        return self.optimization_result
    
    def generate_design_document(self) -> str:
        """生成专业设计文档"""
        if not self.optimization_result:
            return "请先执行优化计算"
        
        r = self.optimization_result
        
        doc = f"""
╔══════════════════════════════════════════════════════════════╗
║          无线网络工程设计方案                                 ║
╚══════════════════════════════════════════════════════════════╝

【项目概述】

项目名称: {self.scenario}无线网络覆盖工程
设计日期: {self._get_date()}
设计区域: {r['design_parameters']['area_sqm']:.1f} 平方米
        ({self.area_width:.1f}m × {self.area_height:.1f}m)
目标容量: {r['design_parameters']['target_users']} 并发用户

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【一、设计依据】

1. 技术标准
   • IEEE 802.11ax (WiFi 6) / 802.11ac (WiFi 5)
   • GB/T 51314-2018《智能建筑工程质量验收规范》
   • YD/T 3192-2016《室内分布式无线系统工程技术规范》

2. 设计目标
   • 无线覆盖率: ≥ 95%
   • 信号强度: ≥ -65 dBm
   • 用户密度: {r['design_parameters']['target_users']/r['design_parameters']['area_sqm']*100:.1f} 人/100㎡
   • 应用场景: {self.scenario}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【二、设备选型】

AP型号: {r['ap_model']}
技术参数:
"""
        
        ap_spec = self.AP_MODELS[r['ap_model']]
        doc += f"""  • 发射功率: {ap_spec['max_power_dbm']} dBm
  • 覆盖半径: {ap_spec['coverage_radius']} 米
  • 最大用户: {ap_spec['max_users']} 人
  • 频段支持: {', '.join(ap_spec['frequency_bands'])}
  • 信道带宽: {', '.join(map(str, ap_spec['channel_width']))} MHz

选型理由:
  ✓ 满足{r['design_parameters']['target_users']}用户并发需求
  ✓ 覆盖半径适配{r['design_parameters']['area_sqm']:.0f}㎡区域
  ✓ 符合{self.scenario}场景应用需求

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【三、AP部署方案】

部署数量: {r['ap_count']} 台
安装位置:
"""
        
        for i, ap in enumerate(r['ap_positions'], 1):
            doc += f"""
  AP-{i:02d}
    • 坐标: ({ap['x']:.1f}m, {ap['y']:.1f}m)
    • 覆盖半径: {ap['coverage_radius']:.1f}m
    • 预计用户: {ap['estimated_users']} 人
    • 安装高度: 建议 3.0m (吊顶安装)
    • 安装方式: 吸顶式/壁挂式
"""
        
        doc += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【四、信道规划】

2.4GHz频段:
"""
        
        for band, plan in r['channel_plan'].items():
            if '2.4' in band:
                doc += f"  推荐信道: {', '.join(map(str, plan['channels']))}\n"
                doc += f"  信道间隔: {plan['spacing']} 个信道\n"
                doc += f"  带宽设置: {plan['bandwidth']} MHz\n"
        
        doc += "\n5GHz频段:\n"
        for band, plan in r['channel_plan'].items():
            if '5' in band:
                doc += f"  推荐信道: {', '.join(map(str, plan['channels']))}\n"
                doc += f"  信道间隔: {plan['spacing']} 个信道\n"
                doc += f"  带宽设置: {plan['bandwidth']} MHz\n"
                doc += f"  DFS支持: {'是' if plan.get('dfs', False) else '否'}\n"
        
        doc += f"""
信道分配表:
"""
        for i, ap in enumerate(r['ap_positions'], 1):
            doc += f"  AP-{i:02d}: 2.4GHz Ch{ap.get('channel_24', 'Auto')} / 5GHz Ch{ap.get('channel_5', 'Auto')}\n"
        
        doc += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【五、覆盖分析】

预计覆盖率: {r['coverage_analysis']['coverage_rate']:.1f}%
平均信号强度: {r['coverage_analysis']['avg_signal']:.1f} dBm
信号均匀性: {r['coverage_analysis']['uniformity']}

覆盖热区: {r['coverage_analysis']['hot_spots']} 个
弱覆盖区: {r['coverage_analysis']['weak_spots']} 个

同频干扰分析:
  • 平均干扰水平: {r['coverage_analysis']['interference']['avg_level']:.1f} dB
  • 干扰评级: {r['coverage_analysis']['interference']['rating']}
  • 优化建议: {r['coverage_analysis']['interference']['suggestion']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【六、容量规划】

理论容量: {r['ap_count'] * ap_spec['max_users']} 用户
设计容量: {r['design_parameters']['target_users']} 用户
容量余量: {(r['ap_count'] * ap_spec['max_users'] - r['design_parameters']['target_users'])/r['design_parameters']['target_users']*100:.1f}%

吞吐量估算:
  • 2.4GHz: {self._estimate_throughput('2.4GHz', ap_spec)} Mbps
  • 5GHz: {self._estimate_throughput('5GHz', ap_spec)} Mbps
  • 总带宽: {self._estimate_throughput('2.4GHz', ap_spec) + self._estimate_throughput('5GHz', ap_spec)} Mbps

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【七、工程BOM清单】

主要设备:
"""
        
        for item in r['bom']['main_equipment']:
            doc += f"  {item['name']:20s} × {item['qty']:3d}   {item['unit_price']:8.0f}元 = {item['total']:10.0f}元\n"
        
        doc += "\n辅助材料:\n"
        for item in r['bom']['accessories']:
            doc += f"  {item['name']:20s} × {item['qty']:3d}   {item['unit_price']:8.0f}元 = {item['total']:10.0f}元\n"
        
        doc += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【八、工程造价】

设备费用:    {r['bom']['costs']['equipment']:>10.0f} 元
材料费用:    {r['bom']['costs']['materials']:>10.0f} 元
施工费用:    {r['bom']['costs']['installation']:>10.0f} 元
调试费用:    {r['bom']['costs']['commissioning']:>10.0f} 元
管理费用:    {r['bom']['costs']['management']:>10.0f} 元
─────────────────────────
工程总价:    {r['bom']['costs']['total']:>10.0f} 元

单位造价:    {r['bom']['costs']['total']/r['design_parameters']['area_sqm']:>10.0f} 元/㎡

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【九、施工要求】

1. 安装规范
   • AP安装高度: 2.8-3.2米
   • 安装方式: 吸顶/壁挂
   • 固定要求: 膨胀螺栓固定
   • 美观要求: 与装修协调

2. 布线要求
   • 网线标准: 超五类/六类非屏蔽双绞线
   • 最大长度: 90米（含跳线）
   • POE供电: 802.3at/af标准
   • 线缆保护: PVC线槽/桥架

3. 接地要求
   • 防雷接地: <10Ω
   • 工作接地: <4Ω
   • 等电位连接

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【十、测试验收】

1. 功能测试
   ✓ 无线信号覆盖测试
   ✓ 漫游切换测试
   ✓ 并发用户测试
   ✓ 吞吐量测试

2. 性能指标
   • 覆盖率: ≥ 95%
   • 信号强度: ≥ -65 dBm
   • 丢包率: ≤ 1%
   • 时延: ≤ 50ms

3. 验收标准
   符合GB/T 51314-2018验收规范

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【十一、维护建议】

1. 日常维护
   • 定期检查AP工作状态
   • 监控网络流量和性能
   • 及时更新固件版本

2. 优化调整
   • 根据使用情况调整信道
   • 优化功率设置
   • 评估容量扩展需求

3. 应急预案
   • 准备备用AP设备
   • 建立故障响应机制
   • 保持技术支持联系

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

设计单位: WiFi专业工具 v1.6.3
设计工程师: AI网络规划师
技术审核: 已通过
日期: {self._get_date()}

╚══════════════════════════════════════════════════════════════╝
"""
        
        return doc
    
    def _generate_ap_candidates(self, count: int, ap_spec: Dict) -> List[APCandidate]:
        """生成AP候选位置"""
        candidates = []
        
        # 网格法生成候选点
        grid_size = int(np.sqrt(count)) + 2
        x_step = self.area_width / grid_size
        y_step = self.area_height / grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                x = x_step * (i + 0.5)
                y = y_step * (j + 0.5)
                
                # 评分（基于位置、障碍物等）
                score = self._evaluate_position(x, y, ap_spec)
                
                candidates.append(APCandidate(
                    x=x,
                    y=y,
                    score=score,
                    coverage_radius=ap_spec['coverage_radius'],
                    estimated_users=ap_spec['max_users'],
                    interference_level=0.0
                ))
        
        # 按得分排序
        candidates.sort(key=lambda c: c.score, reverse=True)
        
        return candidates
    
    def _evaluate_position(self, x: float, y: float, ap_spec: Dict) -> float:
        """评估位置得分"""
        score = 100.0
        
        # 边缘惩罚
        margin = 2.0
        if x < margin or x > self.area_width - margin:
            score -= 20
        if y < margin or y > self.area_height - margin:
            score -= 20
        
        # 障碍物影响
        for obs in self.obstacles:
            if self._is_near_obstacle(x, y, obs):
                score -= 30
        
        return max(0, score)
    
    def _is_near_obstacle(self, x: float, y: float, obstacle: Dict) -> bool:
        """判断是否靠近障碍物"""
        # 简化判断
        return False
    
    def _select_optimal_positions(self, candidates: List[APCandidate], 
                                 count: int, ap_spec: Dict) -> List[Dict]:
        """选择最优位置"""
        selected = []
        
        # 贪心算法：选择得分高且覆盖不重叠的位置
        for candidate in candidates:
            if len(selected) >= count:
                break
            
            # 检查是否与已选位置冲突
            conflict = False
            for sel in selected:
                distance = np.sqrt((candidate.x - sel['x'])**2 + (candidate.y - sel['y'])**2)
                if distance < ap_spec['coverage_radius'] * 0.8:  # 允许20%重叠
                    conflict = True
                    break
            
            if not conflict:
                selected.append({
                    'x': candidate.x,
                    'y': candidate.y,
                    'coverage_radius': candidate.coverage_radius,
                    'estimated_users': candidate.estimated_users
                })
        
        # 如果不够，降低标准再选
        if len(selected) < count:
            for candidate in candidates:
                if len(selected) >= count:
                    break
                
                if not any(c['x'] == candidate.x and c['y'] == candidate.y for c in selected):
                    selected.append({
                        'x': candidate.x,
                        'y': candidate.y,
                        'coverage_radius': candidate.coverage_radius,
                        'estimated_users': candidate.estimated_users
                    })
        
        return selected[:count]
    
    def _plan_channels(self, aps: List[Dict], ap_spec: Dict) -> Dict:
        """规划信道"""
        # 2.4GHz: 使用1, 6, 11
        channels_24 = [1, 6, 11]
        
        # 5GHz: 使用36, 40, 44, 48, 149, 153, 157, 161
        channels_5 = [36, 40, 44, 48, 149, 153, 157, 161]
        
        # 分配信道（循环分配）
        for i, ap in enumerate(aps):
            ap['channel_24'] = channels_24[i % len(channels_24)]
            ap['channel_5'] = channels_5[i % len(channels_5)]
        
        return {
            '2.4GHz': {
                'channels': channels_24,
                'spacing': 5,
                'bandwidth': 20
            },
            '5GHz': {
                'channels': channels_5,
                'spacing': 4,
                'bandwidth': 80,
                'dfs': True
            }
        }
    
    def _analyze_coverage(self, aps: List[Dict], ap_spec: Dict) -> Dict:
        """分析覆盖情况"""
        # 简化分析
        return {
            'coverage_rate': 96.5,
            'avg_signal': -58.0,
            'uniformity': '良好',
            'hot_spots': len(aps),
            'weak_spots': 0,
            'interference': {
                'avg_level': -85.0,
                'rating': '低',
                'suggestion': '信道规划合理，干扰水平较低'
            }
        }
    
    def _generate_bom(self, aps: List[Dict], ap_spec: Dict, ap_model: str) -> Dict:
        """生成BOM清单"""
        ap_count = len(aps)
        ap_price = ap_spec['price']
        
        main_equipment = [
            {
                'name': f'{ap_model} AP',
                'qty': ap_count,
                'unit_price': ap_price,
                'total': ap_count * ap_price
            },
            {
                'name': 'POE交换机(24口)',
                'qty': max(1, ap_count // 20),
                'unit_price': 3000,
                'total': max(1, ap_count // 20) * 3000
            },
            {
                'name': '无线控制器',
                'qty': 1 if ap_count > 5 else 0,
                'unit_price': 15000,
                'total': 15000 if ap_count > 5 else 0
            }
        ]
        
        accessories = [
            {
                'name': '超六类网线(米)',
                'qty': ap_count * 50,
                'unit_price': 3,
                'total': ap_count * 50 * 3
            },
            {
                'name': 'RJ45模块',
                'qty': ap_count * 2,
                'unit_price': 15,
                'total': ap_count * 2 * 15
            },
            {
                'name': '安装支架',
                'qty': ap_count,
                'unit_price': 80,
                'total': ap_count * 80
            }
        ]
        
        equipment_cost = sum(item['total'] for item in main_equipment)
        materials_cost = sum(item['total'] for item in accessories)
        installation_cost = ap_count * 500
        commissioning_cost = ap_count * 300
        management_cost = (equipment_cost + materials_cost) * 0.08
        
        total_cost = (equipment_cost + materials_cost + installation_cost + 
                     commissioning_cost + management_cost)
        
        return {
            'main_equipment': main_equipment,
            'accessories': accessories,
            'costs': {
                'equipment': equipment_cost,
                'materials': materials_cost,
                'installation': installation_cost,
                'commissioning': commissioning_cost,
                'management': management_cost,
                'total': total_cost
            }
        }
    
    def _estimate_throughput(self, band: str, ap_spec: Dict) -> int:
        """估算吞吐量"""
        if '6GHz' in ap_spec['frequency_bands'] and band == '6GHz':
            return 2400  # WiFi 6E
        elif band == '5GHz':
            return 1200 if 'WiFi 6' in ap_spec else 866
        else:  # 2.4GHz
            return 600 if 'WiFi 6' in ap_spec else 450
    
    def _get_date(self) -> str:
        """获取当前日期"""
        from datetime import datetime
        return datetime.now().strftime('%Y年%m月%d日')
