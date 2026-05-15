#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨Domain查询引擎 - 智能查询多个domain并组合元素
核心功能：根据用户意图自动识别需要的domains，智能查询和组合
"""

import sqlite3
import json
import sys
import os
from typing import Dict, List, Optional, Set, Any

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.variable_sampler import SQLiteVariableSampler
from intelligent_generator import IntelligentGenerator


class CrossDomainQueryEngine:
    """跨Domain智能查询引擎"""

    def __init__(self, db_path: str = "extracted_results/elements.db"):
        """
        初始化跨domain查询引擎

        Args:
            db_path: 数据库路径
        """
        self.db = sqlite3.connect(db_path)
        self.cursor = self.db.cursor()
        self.sampler = SQLiteVariableSampler(db_path)
        self.generator = IntelligentGenerator(db_path)

    def query_by_intent(self, intent: Dict) -> Dict[str, List[Dict]]:
        """
        根据用户意图跨domain查询元素

        Args:
            intent: 用户意图字典

        Returns:
            按domain分组的元素字典
            {
                'portrait': [element1, element2, ...],
                'video': [element3, ...],
                'art': [element4, ...],
                'common': [element5, ...]
            }
        """
        # 1. 分析需要哪些domains
        required_domains = self.analyze_required_domains(intent)
        print(f"📊 分析结果：需要 {len(required_domains)} 个domain: {', '.join(required_domains)}")

        # 2. 构建跨domain SQL查询计划
        query_plan = self.build_query_plan(intent, required_domains)

        # 3. 执行查询，从多个domains获取元素
        elements = {}
        for domain, categories in query_plan.items():
            print(f"  🔍 查询 {domain} domain: {', '.join(categories)}")
            elements[domain] = self.query_domain(domain, categories, intent)

        # 4. 应用变量采样（如果元素有变量）
        sampled_elements = {}
        for domain, domain_elements in elements.items():
            sampled_elements[domain] = []
            for elem in domain_elements:
                # 检查是否有变量
                try:
                    result = self.sampler.sample_element_with_variables(
                        elem['element_id'],
                        style_context=intent.get('visual_style')
                    )
                    # 如果有变量，使用采样后的结果
                    if result['variables']:
                        elem_copy = elem.copy()
                        elem_copy['template'] = result['result']
                        elem_copy['sampled_variables'] = result['variables']
                        sampled_elements[domain].append(elem_copy)
                    else:
                        sampled_elements[domain].append(elem)
                except:
                    # 没有变量或采样失败，使用原始元素
                    sampled_elements[domain].append(elem)

        return sampled_elements

    def analyze_required_domains(self, intent: Dict) -> List[str]:
        """
        分析意图需要哪些domains

        Args:
            intent: 用户意图字典

        Returns:
            需要的domain列表
        """
        domains = set()

        # 有人物 → portrait
        if 'subject' in intent:
            domains.add('portrait')

        # 有动作/能量/运动 → video
        video_keywords = ['action', 'pose', 'energy', 'movement', 'motion', 'dynamic']
        if any(k in intent for k in video_keywords):
            domains.add('video')

        # 检查特殊动作关键词
        raw_input = intent.get('raw_input', '').lower()
        if any(kw in raw_input for kw in ['kamehameha', '龟派气功', '能量', 'energy', '气息']):
            domains.add('video')

        # 有艺术风格 → art
        if 'art_style' in intent or 'visual_style' in intent:
            visual_style = intent.get('visual_style', {})
            if isinstance(visual_style, dict):
                art_style = visual_style.get('art_style', '')
            else:
                art_style = str(visual_style)

            # 特殊艺术风格需要art domain
            art_keywords = ['3d', 'wax', '蜡像', 'holographic', 'sculpture', 'rendering']
            if any(kw in art_style.lower() for kw in art_keywords):
                domains.add('art')

        # 有设计需求 → design
        design_keywords = ['layout', 'composition', 'typography', 'poster', 'card']
        if any(k in intent for k in design_keywords):
            domains.add('design')

        # 有产品 → product
        if 'product' in intent:
            domains.add('product')

        # 始终包含common（光影、技术参数）
        domains.add('common')

        return list(domains)

    def build_query_plan(self, intent: Dict, domains: List[str]) -> Dict[str, List[str]]:
        """
        构建查询计划

        Args:
            intent: 用户意图
            domains: 需要查询的domain列表

        Returns:
            查询计划字典 {domain: [categories]}
        """
        query_plan = {}

        for domain in domains:
            if domain == 'portrait':
                query_plan['portrait'] = [
                    'gender', 'age_range', 'ethnicity',
                    'eye_types', 'face_shapes', 'skin_tones',
                    'makeup_styles', 'hair_styles', 'hair_colors',
                    'expressions', 'poses'
                ]

            elif domain == 'video':
                query_plan['video'] = [
                    'scene_types',      # 能量气息、动态场景
                    'motion_effects',   # 动态效果
                    'camera_movements'  # 镜头运动
                ]

            elif domain == 'art':
                query_plan['art'] = [
                    'art_styles',        # 3D渲染、蜡像质感
                    'special_effects'    # 全息、粒子效果
                ]

            elif domain == 'design':
                query_plan['design'] = [
                    'layout_types',
                    'visual_styles',
                    'composition_techniques'
                ]

            elif domain == 'product':
                query_plan['product'] = [
                    'photography_styles',
                    'lighting_setups'
                ]

            elif domain == 'common':
                query_plan['common'] = [
                    'lighting_techniques',
                    'photography_techniques',
                    'poses',
                    'technical_quality'
                ]

        return query_plan

    def query_domain(self, domain: str, categories: List[str], intent: Dict) -> List[Dict]:
        """
        查询单个domain的元素

        Args:
            domain: domain ID
            categories: 要查询的category列表
            intent: 用户意图（用于关键词提取）

        Returns:
            元素列表
        """
        elements = []

        for category in categories:
            # 从intent提取该category的关键词
            keywords = self.extract_keywords_from_intent(intent, category)

            # 获取候选元素
            candidates = self.get_all_elements_by_category(domain, category)

            if not candidates:
                continue

            # 使用ElementSelector选择最佳元素
            from framework_loader import ElementSelector

            best_elem, score = ElementSelector.select_best_element(
                candidates=candidates,
                user_keywords=keywords,
                user_intent=intent,
                field_name=f"{domain}.{category}",
                debug=False
            )

            if best_elem and score > 20:  # 分数阈值
                elements.append(best_elem)

        return elements

    def extract_keywords_from_intent(self, intent: Dict, category: str) -> List[str]:
        """
        从intent中提取特定category的关键词

        Args:
            intent: 用户意图
            category: category ID

        Returns:
            关键词列表
        """
        keywords = []
        raw_input = intent.get('raw_input', '')

        # 根据category提取不同的关键词
        if category == 'scene_types':
            # 场景类型：能量、气息、氛围
            scene_keywords = ['energy', 'aura', 'atmosphere', 'power', '能量', '气息', '氛围']
            keywords.extend([kw for kw in scene_keywords if kw in raw_input.lower()])

        elif category == 'motion_effects':
            # 动态效果：动作、运动
            motion_keywords = ['motion', 'movement', 'action', 'dynamic', '动作', '运动', '动态']
            keywords.extend([kw for kw in motion_keywords if kw in raw_input.lower()])

        elif category == 'art_styles':
            # 艺术风格
            visual_style = intent.get('visual_style', {})
            if isinstance(visual_style, dict):
                art_style = visual_style.get('art_style', '')
                if art_style:
                    keywords.append(art_style)
            # 从raw_input提取
            art_keywords = ['3d', 'wax', '蜡像', 'holographic', 'realistic', 'rendering']
            keywords.extend([kw for kw in art_keywords if kw in raw_input.lower()])

        elif category == 'special_effects':
            # 特效
            effect_keywords = ['glow', 'particle', 'holographic', 'energy', '发光', '粒子', '全息']
            keywords.extend([kw for kw in effect_keywords if kw in raw_input.lower()])

        elif category == 'lighting_techniques':
            # 光影技术
            lighting = intent.get('lighting', 'natural')
            if lighting:
                keywords.append(lighting)

        # 如果没有关键词，使用空列表（会选择评分最高的）
        return keywords if keywords else []

    def get_all_elements_by_category(self, domain: str, category: str) -> List[Dict]:
        """
        从数据库获取该category的所有元素

        Args:
            domain: domain ID
            category: category ID

        Returns:
            元素列表
        """
        return self.generator.get_all_elements_by_category(domain, category)

    def close(self):
        """关闭数据库连接"""
        self.sampler.close()
        self.generator.close()
        self.db.close()


def test_cross_domain_query():
    """测试跨domain查询"""
    print("=" * 80)
    print("测试跨Domain查询引擎")
    print("=" * 80)

    engine = CrossDomainQueryEngine()

    # 测试案例：龙珠悟空打龟派气功
    print("\n【测试案例】龙珠悟空打龟派气功的蜡像3D感\n")

    intent = {
        'raw_input': '龙珠动漫的蜡像3D感悟空打出龟派气功',
        'subject': {
            'gender': 'male',
            'ethnicity': 'East_Asian',
            'character': 'Son Goku'
        },
        'action': 'kamehameha',
        'energy': 'blue_energy_blast',
        'visual_style': {
            'art_style': 'wax_figure_3d'
        },
        'render': '3d_realistic'
    }

    # 执行跨domain查询
    results = engine.query_by_intent(intent)

    # 显示结果
    print("\n📋 查询结果：")
    total_elements = 0
    for domain, elements in results.items():
        if elements:
            print(f"\n  【{domain} domain】({len(elements)}个元素)")
            for elem in elements[:3]:  # 只显示前3个
                print(f"    - {elem['chinese_name']} ({elem['category']})")
            total_elements += len(elements)

    print(f"\n✅ 共获取 {total_elements} 个元素，来自 {len(results)} 个domain")

    engine.close()


if __name__ == '__main__':
    test_cross_domain_query()
