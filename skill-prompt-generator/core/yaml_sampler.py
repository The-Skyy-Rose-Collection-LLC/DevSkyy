#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML变量采样器 - 从prompt-crafter的YAML配置中采样设计变量
支持温馨可爱、现代简约等风格的配色、边框、装饰采样
"""

import yaml
import random
import time
from typing import Dict, List, Optional, Any
from pathlib import Path


class YAMLVariableSampler:
    """YAML变量采样器（读取prompt-crafter的YAML配置）"""

    def __init__(self, yaml_dir: str = "variables"):
        """
        初始化YAML变量采样器

        Args:
            yaml_dir: YAML文件目录路径
        """
        self.yaml_dir = Path(yaml_dir)
        self.history = []
        self.max_history = 100

        # 加载YAML配置
        self.colors = self._load_yaml('colors.yaml')
        self.borders = self._load_yaml('borders.yaml')
        self.decorations = self._load_yaml('decorations.yaml')

    def _load_yaml(self, filename: str) -> Dict:
        """加载YAML文件"""
        filepath = self.yaml_dir / filename
        if not filepath.exists():
            print(f"⚠️ YAML文件不存在: {filepath}")
            return {}

        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def sample_variables(self, style: str = '温馨可爱',
                        variable_types: Optional[List[str]] = None) -> Dict:
        """
        采样设计变量

        Args:
            style: 风格名称（温馨可爱、现代简约）
            variable_types: 要采样的变量类型列表（如：['colors', 'borders']），None表示全部

        Returns:
            采样的设计变量字典
            {
                'colors': {'scheme_name': '珊瑚粉色系', 'variants': [...]},
                'borders': {'style': '大圆角', 'config': {...}},
                'decorations': {'type': '星星', 'config': {...}}
            }
        """
        if variable_types is None:
            variable_types = ['colors', 'borders', 'decorations']

        sampled = {}

        if 'colors' in variable_types and self.colors:
            sampled['colors'] = self._sample_colors(style)

        if 'borders' in variable_types and self.borders:
            sampled['borders'] = self._sample_borders(style)

        if 'decorations' in variable_types and self.decorations:
            sampled['decorations'] = self._sample_decorations(style)

        # 记录历史
        self.history.append({
            'style': style,
            'sampled': sampled,
            'timestamp': time.time()
        })

        # 限制历史长度
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        return sampled

    def _sample_colors(self, style: str) -> Dict:
        """采样配色方案"""
        if style not in self.colors:
            # 风格不存在，使用第一个可用风格
            style = list(self.colors.keys())[0] if self.colors else None
            if not style:
                return {}

        color_schemes = self.colors[style]

        # 过滤出非文字色/背景色的主色系
        main_schemes = {
            name: data for name, data in color_schemes.items()
            if '文字' not in name and '背景' not in name and isinstance(data, dict)
        }

        if not main_schemes:
            return {}

        # 避免最近使用的
        recent_schemes = self._get_recent_values('colors', n=2)
        available = [name for name in main_schemes.keys() if name not in recent_schemes]

        if not available:
            available = list(main_schemes.keys())

        # 随机选择一个色系
        scheme_name = random.choice(available)
        scheme_data = main_schemes[scheme_name]

        # 从variants中随机选择一个颜色
        variants = scheme_data.get('variants', [])
        selected_variant = random.choice(variants) if variants else None

        return {
            'scheme_name': scheme_name,
            'scheme_data': scheme_data,
            'selected_variant': selected_variant,
            'style': style
        }

    def _sample_borders(self, style: str) -> Dict:
        """采样边框样式"""
        if style not in self.borders:
            # 风格不存在，使用第一个可用风格
            style = list(self.borders.keys())[0] if self.borders else None
            if not style:
                return {}

        border_styles = self.borders[style]

        if not border_styles:
            return {}

        # 避免最近使用的
        recent_borders = self._get_recent_values('borders', n=2)
        available = [name for name in border_styles.keys() if name not in recent_borders]

        if not available:
            available = list(border_styles.keys())

        # 随机选择一个边框样式
        border_name = random.choice(available)
        border_config = border_styles[border_name]

        return {
            'border_name': border_name,
            'border_config': border_config,
            'style': style
        }

    def _sample_decorations(self, style: str) -> Dict:
        """采样装饰元素"""
        if style not in self.decorations:
            # 风格不存在，使用第一个可用风格
            style = list(self.decorations.keys())[0] if self.decorations else None
            if not style:
                return {}

        decoration_options = self.decorations[style]

        if not decoration_options:
            return {}

        # 避免最近使用的
        recent_decorations = self._get_recent_values('decorations', n=2)
        available = [name for name in decoration_options.keys() if name not in recent_decorations]

        if not available:
            available = list(decoration_options.keys())

        # 随机选择一个装饰元素
        decoration_name = random.choice(available)
        decoration_config = decoration_options[decoration_name]

        return {
            'decoration_name': decoration_name,
            'decoration_config': decoration_config,
            'style': style
        }

    def _get_recent_values(self, variable_type: str, n: int = 2) -> List[str]:
        """获取最近使用过的值"""
        recent = []
        for record in reversed(self.history):
            if variable_type in record['sampled']:
                sampled_data = record['sampled'][variable_type]
                # 提取名称
                if variable_type == 'colors':
                    name = sampled_data.get('scheme_name')
                elif variable_type == 'borders':
                    name = sampled_data.get('border_name')
                elif variable_type == 'decorations':
                    name = sampled_data.get('decoration_name')
                else:
                    continue

                if name and name not in recent:
                    recent.append(name)

                if len(recent) >= n:
                    break

        return recent

    def get_prompt_description(self, sampled: Dict) -> str:
        """
        将采样的变量转换为提示词描述

        Args:
            sampled: 采样的变量字典

        Returns:
            提示词描述字符串
        """
        parts = []

        # 配色描述
        if 'colors' in sampled:
            colors_data = sampled['colors']
            scheme_name = colors_data.get('scheme_name', '')
            variant = colors_data.get('selected_variant')
            if variant:
                parts.append(f"Color palette: {scheme_name}, primary color {variant['name']} ({variant['hex']})")

        # 边框描述
        if 'borders' in sampled:
            borders_data = sampled['borders']
            border_name = borders_data.get('border_name', '')
            border_config = borders_data.get('border_config', {})
            radius = border_config.get('radius', '')
            if radius:
                parts.append(f"Border style: {border_name}, radius {radius}")

        # 装饰描述
        if 'decorations' in sampled:
            deco_data = sampled['decorations']
            deco_name = deco_data.get('decoration_name', '')
            parts.append(f"Decorative elements: {deco_name}")

        return ', '.join(parts)


def test_yaml_sampler():
    """测试YAML变量采样器"""
    print("=" * 80)
    print("测试YAML变量采样器")
    print("=" * 80)

    sampler = YAMLVariableSampler()

    # 测试1：采样温馨可爱风格
    print("\n【测试1】采样温馨可爱风格")
    sampled1 = sampler.sample_variables(style='温馨可爱')

    print(f"  配色: {sampled1.get('colors', {}).get('scheme_name')}")
    if 'colors' in sampled1:
        variant = sampled1['colors'].get('selected_variant')
        if variant:
            print(f"    主色: {variant['name']} ({variant['hex']})")

    print(f"  边框: {sampled1.get('borders', {}).get('border_name')}")
    print(f"  装饰: {sampled1.get('decorations', {}).get('decoration_name')}")

    # 测试2：再次采样（应避免重复）
    print("\n【测试2】再次采样温馨可爱（应避免重复）")
    sampled2 = sampler.sample_variables(style='温馨可爱')

    print(f"  配色: {sampled2.get('colors', {}).get('scheme_name')}")
    print(f"  边框: {sampled2.get('borders', {}).get('border_name')}")
    print(f"  装饰: {sampled2.get('decorations', {}).get('decoration_name')}")

    # 测试3：采样现代简约风格
    print("\n【测试3】采样现代简约风格")
    sampled3 = sampler.sample_variables(style='现代简约')

    print(f"  配色: {sampled3.get('colors', {}).get('scheme_name')}")
    print(f"  边框: {sampled3.get('borders', {}).get('border_name')}")
    print(f"  装饰: {sampled3.get('decorations', {}).get('decoration_name')}")

    # 测试4：生成提示词描述
    print("\n【测试4】生成提示词描述")
    prompt_desc = sampler.get_prompt_description(sampled1)
    print(f"  {prompt_desc}")

    print("\n✅ 测试完成")


if __name__ == '__main__':
    test_yaml_sampler()
