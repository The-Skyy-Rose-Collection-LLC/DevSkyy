#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设计变量桥接器 - 连接SQLite元素和YAML设计变量
智能融合两者生成完整的设计提示词
"""

import sys
import os
from typing import Dict, List, Optional

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cross_domain_query import CrossDomainQueryEngine
from core.yaml_sampler import YAMLVariableSampler


class DesignVariableBridge:
    """连接 SQLite元素 和 YAML设计变量的桥接器"""

    def __init__(self, db_path: str = "extracted_results/elements.db",
                 yaml_dir: str = "variables"):
        """
        初始化设计变量桥接器

        Args:
            db_path: SQLite数据库路径
            yaml_dir: YAML变量文件目录
        """
        self.sqlite_engine = CrossDomainQueryEngine(db_path)
        self.yaml_sampler = YAMLVariableSampler(yaml_dir)

    def generate_design_prompt(self, intent: Dict) -> Dict:
        """
        生成完整设计提示词（SQLite + YAML）

        Args:
            intent: 用户意图字典

        Returns:
            包含完整提示词和元数据的字典
            {
                'prompt': '完整提示词',
                'sqlite_elements': {...},
                'yaml_variables': {...},
                'metadata': {...}
            }
        """
        # 1. 从SQLite获取基础元素（人物、场景、光影）
        sqlite_elements = self.sqlite_engine.query_by_intent(intent)
        print(f"📊 SQLite元素: {sum(len(elems) for elems in sqlite_elements.values())} 个")

        # 2. 从YAML获取设计变量（配色、边框、装饰）
        design_style = intent.get('design_style', '温馨可爱')
        yaml_variables = self.yaml_sampler.sample_variables(style=design_style)
        print(f"🎨 YAML变量: 风格={design_style}")

        # 3. 融合两者
        merged = self.merge_elements_and_variables(
            sqlite_elements,
            yaml_variables,
            intent
        )

        # 4. 应用设计逻辑（可选）
        # design_logic = self.load_design_logic(design_style)

        # 5. 生成最终提示词
        prompt = self.build_final_prompt(merged)

        return {
            'prompt': prompt,
            'sqlite_elements': sqlite_elements,
            'yaml_variables': yaml_variables,
            'metadata': {
                'design_style': design_style,
                'element_count': sum(len(elems) for elems in sqlite_elements.values()),
                'domains_used': list(sqlite_elements.keys())
            }
        }

    def merge_elements_and_variables(self, sqlite_elements: Dict[str, List[Dict]],
                                    yaml_variables: Dict,
                                    intent: Dict) -> Dict:
        """
        智能融合SQLite元素和YAML变量

        Args:
            sqlite_elements: SQLite查询的元素（按domain分组）
            yaml_variables: YAML采样的变量
            intent: 用户意图

        Returns:
            融合后的结构化数据
        """
        merged = {
            'content': [],       # SQLite元素（主体内容）
            'design': [],        # YAML变量（设计规范）
            'technical': []      # 技术参数
        }

        # 处理SQLite元素
        for domain, elements in sqlite_elements.items():
            for elem in elements:
                category = elem.get('category', '')

                # 分类元素
                if domain in ['portrait', 'video', 'art']:
                    # 主体内容
                    merged['content'].append({
                        'domain': domain,
                        'category': category,
                        'template': elem.get('template', ''),
                        'chinese_name': elem.get('chinese_name', '')
                    })
                elif domain == 'common':
                    # 技术参数（光影、摄影技术）
                    if 'lighting' in category or 'photography' in category:
                        merged['technical'].append({
                            'domain': domain,
                            'category': category,
                            'template': elem.get('template', ''),
                            'chinese_name': elem.get('chinese_name', '')
                        })

        # 处理YAML变量（设计规范）
        if 'colors' in yaml_variables:
            colors_data = yaml_variables['colors']
            scheme_name = colors_data.get('scheme_name', '')
            variant = colors_data.get('selected_variant')
            if variant:
                merged['design'].append({
                    'type': 'color',
                    'description': f"Color scheme: {scheme_name}, primary color {variant['name']} ({variant['hex']})"
                })

        if 'borders' in yaml_variables:
            borders_data = yaml_variables['borders']
            border_name = borders_data.get('border_name', '')
            border_config = borders_data.get('border_config', {})
            radius = border_config.get('radius', '')
            if radius:
                merged['design'].append({
                    'type': 'border',
                    'description': f"Border style: {border_name}, border-radius: {radius}"
                })

        if 'decorations' in yaml_variables:
            deco_data = yaml_variables['decorations']
            deco_name = deco_data.get('decoration_name', '')
            merged['design'].append({
                'type': 'decoration',
                'description': f"Decorative elements: {deco_name}"
            })

        return merged

    def build_final_prompt(self, merged: Dict) -> str:
        """
        构建最终提示词

        Args:
            merged: 融合后的结构化数据

        Returns:
            完整提示词字符串
        """
        parts = []

        # 1. 主体内容（SQLite元素）
        for item in merged['content']:
            template = item['template']
            if template:
                parts.append(template)

        # 2. 设计规范（YAML变量）
        for item in merged['design']:
            description = item['description']
            if description:
                parts.append(description)

        # 3. 技术参数（光影、摄影）
        for item in merged['technical']:
            template = item['template']
            if template:
                parts.append(template)

        return ', '.join(parts)

    def load_design_logic(self, design_style: str) -> Optional[Dict]:
        """
        加载设计逻辑（可选）

        Args:
            design_style: 设计风格名称

        Returns:
            设计逻辑配置字典
        """
        # 从design-logic目录加载对应风格的规则
        # 这部分可以后续扩展
        return None

    def close(self):
        """关闭资源"""
        self.sqlite_engine.close()


def test_design_bridge():
    """测试设计变量桥接器"""
    print("=" * 80)
    print("测试设计变量桥接器")
    print("=" * 80)

    bridge = DesignVariableBridge()

    # 测试案例：温馨可爱的儿童教育海报
    print("\n【测试案例】温馨可爱的儿童教育海报\n")

    intent = {
        'raw_input': '温馨可爱风格的儿童教育海报',
        'design_style': '温馨可爱',
        'subject': {
            'age_range': 'child',
            'gender': 'female'
        },
        'atmosphere': {
            'theme': 'educational',
            'mood': 'warm'
        },
        'lighting': 'soft'
    }

    # 生成设计提示词
    result = bridge.generate_design_prompt(intent)

    # 显示结果
    print("\n📋 生成结果：")
    print(f"\n风格: {result['metadata']['design_style']}")
    print(f"元素数: {result['metadata']['element_count']}")
    print(f"使用domain: {', '.join(result['metadata']['domains_used'])}")

    print(f"\n✨ 完整提示词：")
    print("─" * 80)
    print(result['prompt'])
    print("─" * 80)

    # 显示YAML变量
    if result['yaml_variables']:
        print(f"\n🎨 设计变量：")
        for var_type, var_data in result['yaml_variables'].items():
            if var_type == 'colors':
                print(f"  配色: {var_data.get('scheme_name')}")
            elif var_type == 'borders':
                print(f"  边框: {var_data.get('border_name')}")
            elif var_type == 'decorations':
                print(f"  装饰: {var_data.get('decoration_name')}")

    bridge.close()
    print("\n✅ 测试完成")


if __name__ == '__main__':
    test_design_bridge()
