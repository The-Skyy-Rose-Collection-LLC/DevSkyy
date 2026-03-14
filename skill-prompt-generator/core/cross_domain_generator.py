#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨Domain生成器 - 统一的提示词生成入口
自动识别需求类型，智能路由到对应生成器
"""

import sys
import os
import re
from typing import Dict, List, Optional

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cross_domain_query import CrossDomainQueryEngine
from core.design_bridge import DesignVariableBridge
from intelligent_generator import IntelligentGenerator


class CrossDomainGenerator:
    """统一的跨Domain生成器"""

    def __init__(self, db_path: str = "extracted_results/elements.db",
                 yaml_dir: str = "variables"):
        """
        初始化跨domain生成器

        Args:
            db_path: SQLite数据库路径
            yaml_dir: YAML变量文件目录
        """
        self.query_engine = CrossDomainQueryEngine(db_path)
        self.design_bridge = DesignVariableBridge(db_path, yaml_dir)
        self.portrait_generator = IntelligentGenerator(db_path)

    def generate(self, user_input: str, generation_type: str = 'auto') -> Dict:
        """
        统一生成入口

        Args:
            user_input: 用户输入（自然语言）
            generation_type: 生成类型
                - 'portrait': 人像（仅SQLite portrait domain）
                - 'design': 设计（SQLite + YAML）
                - 'cross_domain': 跨domain（SQLite多domain）
                - 'auto': 自动识别

        Returns:
            生成结果字典
            {
                'prompt': '完整提示词',
                'type': '生成类型',
                'metadata': {...}
            }
        """
        # 1. 解析用户输入为Intent
        intent = self.parse_user_input(user_input)

        # 2. 自动识别生成类型
        if generation_type == 'auto':
            generation_type = self.classify_generation_type(intent)

        print(f"📌 生成类型: {generation_type}")

        # 3. 路由到对应生成器
        if generation_type == 'portrait':
            # 纯人像 → 只用portrait domain（向后兼容）
            return self.generate_portrait(intent)

        elif generation_type == 'design':
            # 设计海报/卡片 → SQLite基础 + YAML设计
            return self.generate_design(intent)

        elif generation_type == 'cross_domain':
            # 复杂场景 → SQLite跨domain
            return self.generate_cross_domain(intent)

        else:
            raise ValueError(f"Unknown generation type: {generation_type}")

    def parse_user_input(self, user_input: str) -> Dict:
        """
        解析用户输入为结构化Intent

        Args:
            user_input: 用户输入字符串

        Returns:
            Intent字典
        """
        intent = {
            'raw_input': user_input,
            'subject': {},
            'action': None,
            'visual_style': {},
            'atmosphere': {},
            'design_style': None,
            'lighting': 'natural'
        }

        user_lower = user_input.lower()

        # 识别人物
        if any(kw in user_lower for kw in ['女', 'woman', 'female', '女性', '少女']):
            intent['subject']['gender'] = 'female'
        elif any(kw in user_lower for kw in ['男', 'man', 'male', '男性', '悟空', 'goku']):
            intent['subject']['gender'] = 'male'

        # 识别人种
        if any(kw in user_input for kw in ['东亚', 'East_Asian', '中国', '日本', '韩国']):
            intent['subject']['ethnicity'] = 'East_Asian'

        # 识别年龄
        if any(kw in user_input for kw in ['年轻', 'young', '少女']):
            intent['subject']['age_range'] = 'young_adult'
        elif any(kw in user_input for kw in ['儿童', 'child', '孩子']):
            intent['subject']['age_range'] = 'child'

        # 识别动作（特殊识别龟派气功）
        if any(kw in user_input for kw in ['龟派气功', 'kamehameha', '能量波']):
            intent['action'] = 'kamehameha'
            intent['energy'] = 'blue_energy_blast'

        # 识别艺术风格
        if any(kw in user_input for kw in ['3d', '3D', '蜡像', 'wax']):
            intent['visual_style']['art_style'] = 'wax_figure_3d'
        elif any(kw in user_input for kw in ['动漫', 'anime']):
            intent['visual_style']['art_style'] = 'anime'

        # 识别设计风格
        if any(kw in user_input for kw in ['温馨可爱', '可爱', 'cute', 'warm']):
            intent['design_style'] = '温馨可爱'
        elif any(kw in user_input for kw in ['现代简约', '简约', 'minimal', 'modern']):
            intent['design_style'] = '现代简约'

        # 识别设计需求
        if any(kw in user_input for kw in ['海报', 'poster', '卡片', 'card']):
            intent['design_requirement'] = True

        # 识别光影
        if any(kw in user_input for kw in ['电影', 'cinematic', '电影级']):
            intent['lighting'] = 'cinematic'
        elif any(kw in user_input for kw in ['自然', 'natural']):
            intent['lighting'] = 'natural'

        return intent

    def classify_generation_type(self, intent: Dict) -> str:
        """
        自动分类生成类型

        Args:
            intent: 解析的Intent

        Returns:
            生成类型字符串
        """
        # 检查是否是设计需求
        if intent.get('design_style') or intent.get('design_requirement'):
            return 'design'

        # 检查是否需要多个domain
        need_multiple_domains = False

        # 有动作/能量/特效 → 需要video/art domain
        if intent.get('action') or intent.get('energy'):
            need_multiple_domains = True

        # 有特殊艺术风格（3D、蜡像） → 需要art domain
        visual_style = intent.get('visual_style', {})
        art_style = visual_style.get('art_style', '')
        if any(kw in art_style for kw in ['3d', 'wax', 'holographic']):
            need_multiple_domains = True

        if need_multiple_domains:
            return 'cross_domain'

        # 默认：如果有人物，就是portrait
        if intent.get('subject'):
            return 'portrait'

        # 没有人物，也不是设计，默认cross_domain
        return 'cross_domain'

    def generate_portrait(self, intent: Dict) -> Dict:
        """
        生成纯人像提示词（向后兼容）

        Args:
            intent: 用户意图

        Returns:
            生成结果
        """
        print("  → 使用 portrait 生成器（向后兼容）")

        # 使用原有的intelligent_generator
        elements = self.portrait_generator.select_elements_by_intent(intent)

        # 检查一致性
        issues = self.portrait_generator.check_consistency(elements)
        if issues:
            elements, fixes = self.portrait_generator.resolve_conflicts(elements, issues)

        # 生成提示词
        prompt = self.portrait_generator.compose_prompt(elements, mode='auto')

        return {
            'prompt': prompt,
            'type': 'portrait',
            'metadata': {
                'element_count': len(elements),
                'issues_fixed': len(issues)
            }
        }

    def generate_design(self, intent: Dict) -> Dict:
        """
        生成设计提示词（SQLite + YAML）

        Args:
            intent: 用户意图

        Returns:
            生成结果
        """
        print("  → 使用 design 生成器（SQLite + YAML）")

        result = self.design_bridge.generate_design_prompt(intent)

        return {
            'prompt': result['prompt'],
            'type': 'design',
            'metadata': result['metadata'],
            'yaml_variables': result['yaml_variables']
        }

    def generate_cross_domain(self, intent: Dict) -> Dict:
        """
        生成跨domain提示词（SQLite多domain + intelligent_generator完整流程）

        修复版：跨域查询后，复用intelligent_generator的核心能力
        - 一致性检查
        - 冲突解决
        - 智能组装

        Args:
            intent: 用户意图

        Returns:
            生成结果
        """
        print("  → 使用 cross_domain 生成器（SQLite多domain + 智能组装）")

        # 1. 跨domain查询获取候选元素
        elements_by_domain = self.query_engine.query_by_intent(intent)

        # 2. 合并所有domain的元素为统一列表
        all_elements = []
        for domain, elements in elements_by_domain.items():
            for elem in elements:
                # 确保元素有必要的字段
                if 'template' not in elem:
                    elem['template'] = elem.get('ai_prompt_template', '')
                if 'category' not in elem:
                    elem['category'] = elem.get('category_id', 'unknown')
                # 标记来源domain
                elem['source_domain'] = domain
                all_elements.append(elem)

        print(f"  📊 合并了 {len(all_elements)} 个元素来自 {len(elements_by_domain)} 个domain")

        # 3. 如果元素太少，补充基于intent的智能选择
        if len(all_elements) < 5:
            print("  ⚠️  元素较少，使用intelligent_generator补充...")
            extra_elements = self.portrait_generator.select_elements_by_intent(intent)
            # 合并，避免重复
            existing_ids = {e.get('element_id') for e in all_elements}
            for elem in extra_elements:
                if elem.get('element_id') not in existing_ids:
                    elem['source_domain'] = 'portrait_supplement'
                    all_elements.append(elem)
            print(f"  📊 补充后共 {len(all_elements)} 个元素")

        # 4. 使用intelligent_generator检查一致性
        issues = self.portrait_generator.check_consistency(all_elements)
        if issues:
            print(f"  🔍 发现 {len(issues)} 个一致性问题，正在修复...")
            all_elements, fixes = self.portrait_generator.resolve_conflicts(all_elements, issues)
            for fix in fixes:
                print(f"     {fix}")

        # 5. 基于raw_input增强prompt（提取用户原始描述中的关键信息）
        enhanced_parts = self._extract_scene_description(intent)
        
        # 6. 使用intelligent_generator的智能组装
        base_prompt = self.portrait_generator.compose_prompt(all_elements, mode='auto')
        
        # 7. 组合最终提示词：增强描述 + 数据库元素
        if enhanced_parts:
            final_prompt = f"{enhanced_parts}, {base_prompt}"
        else:
            final_prompt = base_prompt

        return {
            'prompt': final_prompt,
            'type': 'cross_domain',
            'metadata': {
                'domains_used': list(elements_by_domain.keys()),
                'element_count': len(all_elements),
                'issues_fixed': len(issues) if issues else 0,
                'enhanced': bool(enhanced_parts)
            }
        }

    def _extract_scene_description(self, intent: Dict) -> str:
        """
        从用户原始输入提取场景描述，生成增强的英文描述
        
        这是cross_domain的关键增强：将用户的自然语言描述转换为结构化的英文prompt
        """
        raw_input = intent.get('raw_input', '')
        if not raw_input:
            return ''
        
        parts = []
        raw_lower = raw_input.lower()
        
        # 场景类型识别
        scene_mappings = {
            # 古代/历史场景
            ('秦', '宫殿', '大殿'): 'ancient Chinese Qin Dynasty palace hall, grand imperial architecture',
            ('战国', '秦国'): 'Warring States period, ancient Chinese military setting',
            ('古代', '古装'): 'ancient Chinese historical setting',
            ('宫廷', '皇宫'): 'Chinese imperial palace, ornate traditional architecture',
            ('战场', '战争'): 'epic battlefield, war scene',
            
            # 动作场景
            ('比武', '对决', '决斗'): 'intense combat duel, martial arts battle',
            ('剑术', '剑', '刀'): 'sword fighting, blade combat, weapon clash',
            ('武术', '功夫'): 'martial arts, kung fu action',
            ('打斗', '格斗'): 'fighting scene, combat action',
            
            # 人物类型
            ('武将', '将军', '将领'): 'powerful military general, armored warrior',
            ('武士', '剑客'): 'skilled swordsman, warrior',
            ('王', '皇帝', '君主'): 'noble king, imperial ruler',
            
            # 氛围
            ('史诗', '壮观'): 'epic cinematic scene, grand scale',
            ('电影级', '大片'): 'blockbuster movie quality, cinematic composition',
            ('激烈', '紧张'): 'intense dramatic action, high tension',
        }
        
        for keywords, english_desc in scene_mappings.items():
            if any(kw in raw_input for kw in keywords):
                parts.append(english_desc)
        
        # 特定人物识别
        character_mappings = {
            '赢稷': 'King Yingji of Qin',
            '秦王': 'King of Qin',
            '白起': 'General Baiqi, legendary military commander',
            '项羽': 'Xiang Yu, mighty warrior king',
            '刘邦': 'Liu Bang, founder of Han Dynasty',
            '韩信': 'Han Xin, brilliant military strategist',
            '悟空': 'Son Goku, powerful martial artist',
        }
        
        for cn_name, en_name in character_mappings.items():
            if cn_name in raw_input:
                parts.append(en_name)
        
        # 视觉风格增强
        if any(kw in raw_lower for kw in ['电影', 'cinematic', '史诗']):
            parts.append('dramatic lighting, dust particles in the air')
        
        if any(kw in raw_lower for kw in ['古代', '战国', '秦']):
            parts.append('elaborate period costume with intricate bronze patterns')
        
        # 去重并返回
        seen = set()
        unique_parts = []
        for part in parts:
            if part not in seen:
                seen.add(part)
                unique_parts.append(part)
        
        return ', '.join(unique_parts)

    def close(self):
        """关闭资源"""
        self.query_engine.close()
        self.design_bridge.close()
        self.portrait_generator.close()


def test_cross_domain_generator():
    """测试CrossDomainGenerator"""
    print("=" * 80)
    print("测试CrossDomainGenerator统一接口")
    print("=" * 80)

    generator = CrossDomainGenerator()

    # 测试1：纯人像（向后兼容）
    print("\n【测试1】纯人像：生成一个年轻女性肖像\n")
    result1 = generator.generate("生成一个年轻女性肖像")
    print(f"\n类型: {result1['type']}")
    print(f"元素数: {result1['metadata']['element_count']}")
    print(f"提示词长度: {len(result1['prompt'])} 字符")

    # 测试2：跨domain复杂场景
    print("\n\n【测试2】跨domain：龙珠悟空打龟派气功的蜡像3D感\n")
    result2 = generator.generate("龙珠动漫的蜡像3D感悟空打出龟派气功")
    print(f"\n类型: {result2['type']}")
    print(f"使用domain: {', '.join(result2['metadata']['domains_used'])}")
    print(f"元素数: {result2['metadata']['element_count']}")
    print(f"\n提示词预览: {result2['prompt'][:200]}...")

    # 测试3：设计海报（SQLite + YAML）
    print("\n\n【测试3】设计：温馨可爱的儿童教育海报\n")
    result3 = generator.generate("温馨可爱风格的儿童教育海报")
    print(f"\n类型: {result3['type']}")
    print(f"风格: {result3['metadata']['design_style']}")
    if 'yaml_variables' in result3:
        print(f"配色: {result3['yaml_variables'].get('colors', {}).get('scheme_name')}")
    print(f"\n提示词: {result3['prompt']}")

    generator.close()
    print("\n\n✅ 所有测试完成")


if __name__ == '__main__':
    test_cross_domain_generator()
