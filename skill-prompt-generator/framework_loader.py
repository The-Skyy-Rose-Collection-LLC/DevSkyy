#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
框架加载器和框架驱动的提示词生成器
Framework Loader and Framework-Driven Prompt Generator
"""

import yaml
import os
from typing import Dict, List, Optional, Any


class FrameworkLoader:
    """框架加载器"""

    @staticmethod
    def load(framework_path: str = "prompt_framework.yaml") -> Dict:
        """
        加载框架配置文件

        参数:
            framework_path: 框架配置文件路径

        返回:
            框架配置字典
        """
        if not os.path.exists(framework_path):
            raise FileNotFoundError(f"框架配置文件不存在: {framework_path}")

        with open(framework_path, 'r', encoding='utf-8') as f:
            framework = yaml.safe_load(f)

        print(f"✓ 加载框架: {framework['description']}")
        print(f"  版本: {framework['framework_version']}")
        print(f"  类别数: {len(framework['categories'])}")

        return framework

    @staticmethod
    def get_all_fields(framework: Dict) -> Dict[str, Dict]:
        """
        获取框架中所有的字段定义

        返回:
            {
                'subject.gender': {...},
                'styling.makeup': {...},
                ...
            }
        """
        all_fields = {}

        for category_name, category_config in framework['categories'].items():
            for field_name, field_config in category_config['fields'].items():
                full_field_name = f"{category_name}.{field_name}"
                all_fields[full_field_name] = {
                    'category': category_name,
                    'field': field_name,
                    **field_config
                }

        return all_fields

    @staticmethod
    def get_required_fields(framework: Dict) -> List[str]:
        """获取所有必选字段"""
        required = []

        for category_name, category_config in framework['categories'].items():
            if category_config.get('required'):
                for field_name, field_config in category_config['fields'].items():
                    if field_config.get('required'):
                        required.append(f"{category_name}.{field_name}")

        return required

    @staticmethod
    def apply_dependencies(intent: Dict, framework: Dict) -> Dict:
        """
        应用框架的依赖规则

        参数:
            intent: 原始intent
            framework: 框架配置

        返回:
            应用规则后的intent
        """
        updated_intent = intent.copy()

        dependencies = framework.get('dependencies', [])

        for rule in dependencies:
            # 检查条件是否满足
            if 'when' in rule:
                conditions_met = True

                for condition_field, condition_value in rule['when'].items():
                    category, field = condition_field.split('.')
                    actual_value = updated_intent.get(category, {}).get(field)

                    if actual_value != condition_value:
                        conditions_met = False
                        break

                # 如果条件满足，应用then规则
                if conditions_met and 'then' in rule:
                    print(f"✓ 应用依赖规则: {rule.get('name', '未命名')}")

                    for then_field, then_value in rule['then'].items():
                        category, field = then_field.split('.')

                        if category not in updated_intent:
                            updated_intent[category] = {}

                        updated_intent[category][field] = then_value
                        print(f"  → 设置 {then_field} = {then_value}")

        return updated_intent

    @staticmethod
    def validate_intent(intent: Dict, framework: Dict) -> List[Dict]:
        """
        验证intent的完整性和一致性

        返回:
            问题列表
        """
        issues = []

        validation = framework.get('validation', {})

        # 检查必选字段
        required_fields = validation.get('required_fields', [])
        for req in required_fields:
            field_path = req['field']
            category, field = field_path.split('.')

            if category not in intent or field not in intent[category]:
                issues.append({
                    'type': 'missing_required',
                    'field': field_path,
                    'severity': 'error',
                    'message': req['error_message']
                })

        # 检查一致性
        consistency_checks = validation.get('consistency_checks', [])
        for check in consistency_checks:
            if 'when' in check:
                # 检查条件
                for condition_field, condition_values in check['when'].items():
                    category, field = condition_field.split('.')
                    actual_value = intent.get(category, {}).get(field)

                    # 如果值在条件列表中，说明有问题
                    if isinstance(condition_values, list):
                        if actual_value in condition_values:
                            issues.append({
                                'type': 'consistency_check',
                                'name': check['name'],
                                'severity': check['severity'],
                                'message': check['message'],
                                'suggestion': check.get('suggestion', '')
                            })
                    else:
                        if actual_value == condition_values:
                            # 检查其他条件字段
                            pass

        return issues


class FrameworkDrivenGenerator:
    """框架驱动的生成器"""

    def __init__(self, db_path: str = "extracted_results/elements.db",
                 framework_path: str = "prompt_framework.yaml"):
        """
        初始化

        参数:
            db_path: 数据库路径
            framework_path: 框架配置文件路径
        """
        # 加载框架
        self.framework = FrameworkLoader.load(framework_path)

        # 加载IntelligentGenerator（用于数据库查询）
        from intelligent_generator import IntelligentGenerator
        self.generator = IntelligentGenerator(db_path)

    def generate_by_framework(self, intent: Dict) -> Dict:
        """
        根据框架和intent生成提示词

        参数:
            intent: 用户意图（可能不完整）

        返回:
            {
                'intent': 完整的intent,
                'elements': 查询到的元素列表,
                'prompt': 最终提示词,
                'issues': 问题列表,
                'fixes': 修正说明
            }
        """
        print("\n" + "="*80)
        print("框架驱动生成")
        print("="*80)

        # 步骤1：应用依赖规则，补全intent
        print("\n📋 步骤1：应用框架依赖规则")
        print("-"*80)

        complete_intent = FrameworkLoader.apply_dependencies(intent, self.framework)

        # 步骤2：验证intent
        print("\n✓ 步骤2：验证Intent")
        print("-"*80)

        validation_issues = FrameworkLoader.validate_intent(complete_intent, self.framework)

        if validation_issues:
            print(f"⚠️ 发现 {len(validation_issues)} 个验证问题:")
            for issue in validation_issues:
                print(f"  - [{issue['severity']}] {issue['message']}")
        else:
            print("✓ Intent验证通过")

        # 步骤3：根据框架查询数据库
        print("\n🔍 步骤3：根据框架查询数据库")
        print("-"*80)

        elements = self.query_by_framework(complete_intent)

        print(f"✓ 查询到 {len(elements)} 个元素")

        # 步骤4：一致性检查
        print("\n✓ 步骤4：一致性检查")
        print("-"*80)

        consistency_issues = self.generator.check_consistency(elements)

        fixes_applied = []
        if consistency_issues:
            print(f"⚠️ 发现 {len(consistency_issues)} 个一致性问题")
            elements, fixes_applied = self.generator.resolve_conflicts(elements, consistency_issues)
            for fix in fixes_applied:
                print(f"  {fix}")
        else:
            print("✓ 没有发现一致性问题")

        # 步骤5：生成提示词
        print("\n✨ 步骤5：生成最终提示词")
        print("-"*80)

        prompt = self.generator.compose_prompt(elements, mode='auto', keywords_limit=3)

        # 步骤6：完整性检查
        print("\n🎯 步骤6：完整性检查")
        print("-"*80)

        completeness_issues = self.generator.check_completeness(complete_intent, prompt)

        if completeness_issues:
            print(f"⚠️ 发现 {len(completeness_issues)} 个缺失的需求:")
            for item in completeness_issues:
                print(f"  - {item['description']}")
        else:
            print("✓ 提示词满足所有用户要求")

        return {
            'intent': complete_intent,
            'elements': elements,
            'prompt': prompt,
            'validation_issues': validation_issues,
            'consistency_issues': consistency_issues,
            'completeness_issues': completeness_issues,
            'fixes': fixes_applied
        }

    def query_all_candidates_by_framework(self, intent: Dict) -> Dict[str, List[Dict]]:
        """
        查询所有候选元素（供SKILL分析选择）

        返回:
            {
                'makeup': [所有makeup元素列表],
                'lighting': [所有lighting元素列表],
                ...
            }
        """
        candidates = {}

        # 遍历框架的所有category
        for category_name, category_config in self.framework['categories'].items():

            # 跳过不需要查询数据库的category
            if category_name in ['subject', 'expression', 'scene', 'technical']:
                continue

            # 获取该category的intent值
            category_intent = intent.get(category_name, {})

            # 遍历该category的所有字段
            for field_name, field_config in category_config['fields'].items():

                # 获取字段值
                field_value = category_intent.get(field_name, field_config.get('default'))

                # 如果该字段有db_category（需要查询数据库）
                if 'db_category' in field_config:

                    db_category = field_config['db_category']
                    field_key = f"{category_name}.{field_name}"

                    # 查询该类别的所有元素
                    all_elements = self.generator.get_all_elements_by_category('portrait', db_category)

                    if all_elements:
                        candidates[field_key] = all_elements
                        print(f"✓ {field_key}: 查询到 {len(all_elements)} 个候选元素")

        # 查询subject相关的候选
        subject = intent.get('subject', {})

        if 'ethnicity' in subject:
            # 眼睛候选
            eye_candidates = self.generator.get_all_elements_by_category('portrait', 'eye_types')
            if eye_candidates:
                candidates['facial.eyes'] = eye_candidates
                print(f"✓ facial.eyes: 查询到 {len(eye_candidates)} 个候选元素")

            # 发色候选
            hair_candidates = self.generator.get_all_elements_by_category('portrait', 'hair_colors')
            if hair_candidates:
                candidates['styling.hair_color'] = hair_candidates
                print(f"✓ styling.hair_color: 查询到 {len(hair_candidates)} 个候选元素")

        return candidates

    def query_by_framework(self, intent: Dict) -> List[Dict]:
        """
        根据框架遍历查询所有字段

        这是核心方法：代码不需要知道有哪些字段，只遍历框架
        """
        elements = []

        # 1. 处理主体属性（特殊处理）
        subject = intent.get('subject', {})

        if 'gender' in subject:
            elem = self.generator.get_element_by_category('portrait', 'gender', subject['gender'])
            if elem:
                elements.append(elem)

        if 'ethnicity' in subject:
            elem = self.generator.get_element_by_category('portrait', 'ethnicity', subject['ethnicity'])
            if elem:
                elements.append(elem)

                # 自动选择匹配人种的眼睛和头发
                ethnicity_name = subject['ethnicity']

                if ethnicity_name == 'East_Asian':
                    eye_elem = self.generator.get_element_by_category('portrait', 'eye_types', 'almond')
                else:
                    eye_elem = self.generator.get_element_by_category('portrait', 'eye_types')

                if eye_elem:
                    elements.append(eye_elem)

                typical_hair = self.generator.knowledge['ethnicity_typical_hair'].get(ethnicity_name, ['black'])
                hair_color_elem = self.generator.get_element_by_category('portrait', 'hair_colors', typical_hair[0])
                if hair_color_elem:
                    elements.append(hair_color_elem)

        if 'age_range' in subject:
            elem = self.generator.get_element_by_category('portrait', 'age_range')
            if elem:
                elements.append(elem)

        # 2. 遍历框架的所有category（除了subject和expression）
        for category_name, category_config in self.framework['categories'].items():

            # 跳过已处理的
            if category_name in ['subject', 'expression', 'scene', 'technical']:
                continue

            # 获取该category的intent值
            category_intent = intent.get(category_name, {})

            # 遍历该category的所有字段
            for field_name, field_config in category_config['fields'].items():

                # 获取字段值
                field_value = category_intent.get(field_name, field_config.get('default'))

                # 如果该字段有db_category（需要查询数据库）
                if 'db_category' in field_config and field_value:

                    # 跳过默认值或auto
                    if field_value in ['modern', 'natural', 'auto', 'none']:
                        continue

                    db_category = field_config['db_category']

                    # 获取搜索关键词
                    keywords_map = field_config.get('search_keywords', {})
                    keywords = keywords_map.get(field_value, [field_value])

                    # 查询数据库
                    elem = None
                    for kw in keywords:
                        elem = self.generator.get_element_by_category('portrait', db_category, kw)
                        if elem:
                            print(f"✓ {category_name}.{field_name} = '{field_value}' → 找到: '{elem['chinese_name']}'（关键词: {kw}）")
                            elements.append(elem)
                            break

                    if not elem:
                        print(f"⚠️ {category_name}.{field_name} = '{field_value}' → 未找到元素")

        # 3. 处理其他固定类别
        for attr in ['skin_tones', 'skin_textures', 'face_shapes', 'expressions', 'poses']:
            elem = self.generator.get_element_by_category('portrait', attr)
            if elem:
                elements.append(elem)

        # 4. 处理风格关键词
        style_keywords = []

        # 从scene收集关键词
        scene = intent.get('scene', {})
        if 'atmosphere' in scene and scene['atmosphere']:
            style_keywords.append(scene['atmosphere'])

        if 'director_style' in scene and scene['director_style']:
            style_keywords.append(scene['director_style'])

            # 应用导演风格的关键词扩展
            director_keywords = {
                'tsui_hark': ['wuxia', 'martial arts', 'flowing', 'dynamic'],
                'zhang_yimou': ['traditional', 'red', 'gold', 'period drama'],
                'wong_kar_wai': ['nostalgic', 'atmospheric', 'saturated colors']
            }
            if scene['director_style'] in director_keywords:
                style_keywords.extend(director_keywords[scene['director_style']])

        # 从era收集关键词
        if 'era' in scene and scene['era'] != 'modern':
            style_keywords.append(scene['era'])
            if scene['era'] == 'ancient':
                style_keywords.extend(['traditional', 'period', 'classical'])

        if style_keywords:
            style_elements = self.generator.search_style_elements(style_keywords)
            elements.extend(style_elements)

        return elements

    def close(self):
        """关闭数据库连接"""
        self.generator.close()


class ElementSelector:
    """
    元素选择器 - 实现全局最优选择策略

    功能：
    - 从候选元素列表中选择最匹配用户需求的元素
    - 使用多维度评分机制（关键词匹配 + 质量评分 + 语义一致性）
    - 替代简单的贪心策略（第一个匹配就选）
    """

    @staticmethod
    def calculate_match_score(
        element: Dict,
        user_keywords: List[str],
        user_intent: Dict,
        field_name: str = ""
    ) -> float:
        """
        计算元素与用户需求的匹配度

        参数:
            element: 候选元素
            user_keywords: 用户需求关键词列表（如 ['round', 'plump', 'full']）
            user_intent: 用户完整意图（用于语义一致性检查）
            field_name: 字段名（如 'facial.face_shape'）

        返回:
            匹配度评分（0-100）

        评分维度：
            1. 关键词匹配度（60%）- 用户关键词在元素中出现的比例
            2. 元素质量评分（30%）- 元素的reusability_score
            3. 语义一致性（10%）- 检测是否有语义冲突
        """
        score = 0.0

        # 获取元素的关键词和模板
        elem_keywords_raw = element.get('keywords', '')
        elem_template = element.get('ai_prompt_template', '')
        elem_name = element.get('name', '')

        # 处理keywords字段（可能是字符串或列表）
        if isinstance(elem_keywords_raw, list):
            elem_keywords_str = ' '.join(elem_keywords_raw)
        elif isinstance(elem_keywords_raw, str):
            try:
                import json
                keywords_list = json.loads(elem_keywords_raw)
                elem_keywords_str = ' '.join(keywords_list)
            except:
                elem_keywords_str = elem_keywords_raw
        else:
            elem_keywords_str = str(elem_keywords_raw)

        # 转为小写便于匹配
        elem_keywords_lower = elem_keywords_str.lower()
        elem_template_lower = elem_template.lower() if elem_template else ''
        elem_name_lower = elem_name.lower() if elem_name else ''

        # 维度1：关键词匹配度（60分）
        if user_keywords:
            matched_count = 0
            total_keywords = len(user_keywords)

            for user_kw in user_keywords:
                user_kw_lower = user_kw.lower()

                # 检查是否在关键词、模板或名称中出现
                if (user_kw_lower in elem_keywords_lower or
                    user_kw_lower in elem_template_lower or
                    user_kw_lower in elem_name_lower):
                    matched_count += 1

            keyword_match_rate = matched_count / total_keywords
            score += keyword_match_rate * 60

        # 维度2：元素质量评分（30分）
        reusability = element.get('reusability_score', 0.0)
        if reusability > 0:
            score += (reusability / 10.0) * 30

        # 维度3：语义一致性检查（±10分）
        # 检测语义冲突并扣分
        consistency_penalty = ElementSelector._check_semantic_consistency(
            element, user_keywords, user_intent, field_name
        )
        score += consistency_penalty

        return max(0.0, min(100.0, score))  # 限制在0-100范围

    @staticmethod
    def _check_semantic_consistency(
        element: Dict,
        user_keywords: List[str],
        user_intent: Dict,
        field_name: str
    ) -> float:
        """
        检查语义一致性，返回加分或扣分

        返回:
            分数调整值（-20 到 +10）
        """
        penalty = 0.0

        # 处理keywords字段
        elem_keywords_raw = element.get('keywords', '')
        if isinstance(elem_keywords_raw, list):
            elem_keywords_str = ' '.join(elem_keywords_raw)
        elif isinstance(elem_keywords_raw, str):
            try:
                import json
                keywords_list = json.loads(elem_keywords_raw)
                elem_keywords_str = ' '.join(keywords_list)
            except:
                elem_keywords_str = elem_keywords_raw
        else:
            elem_keywords_str = str(elem_keywords_raw)

        elem_keywords_lower = elem_keywords_str.lower()
        elem_template = element.get('ai_prompt_template', '')
        elem_template_lower = elem_template.lower() if elem_template else ''

        # 规则1：婴儿肥 vs 精致
        # 如果用户要求婴儿肥（plump/chubby/full），但元素是精致的（refined/delicate）→ 扣分
        baby_fat_keywords = ['plump', 'chubby', 'full', 'baby fat', 'rounded']
        refined_keywords = ['refined', 'delicate', 'classical', 'sculpted', 'elegant']

        user_wants_baby_fat = any(kw in ' '.join(user_keywords).lower() for kw in baby_fat_keywords)
        elem_is_refined = any(kw in elem_keywords_lower or kw in elem_template_lower for kw in refined_keywords)

        if user_wants_baby_fat and elem_is_refined:
            penalty -= 20  # 严重冲突，大幅扣分

        # 规则2：奖励完美匹配
        # 如果用户关键词都在元素中出现 → 加分
        if user_keywords:
            all_matched = all(
                kw.lower() in elem_keywords_lower or kw.lower() in elem_template_lower
                for kw in user_keywords
            )
            if all_matched:
                penalty += 10  # 完美匹配，加分

        return penalty

    @staticmethod
    def select_best_element(
        candidates: List[Dict],
        user_keywords: List[str],
        user_intent: Dict = None,
        field_name: str = "",
        debug: bool = False
    ) -> tuple:
        """
        从候选列表中选择最佳元素（全局最优策略）

        参数:
            candidates: 候选元素列表
            user_keywords: 用户需求关键词
            user_intent: 用户完整意图（可选）
            field_name: 字段名（可选，用于调试）
            debug: 是否输出调试信息

        返回:
            (最佳元素, 最佳得分)
        """
        if not candidates:
            return None, 0.0

        if user_intent is None:
            user_intent = {}

        best_element = None
        best_score = 0.0

        if debug:
            print(f"\n{'='*80}")
            print(f"🎯 全局最优选择：{field_name}")
            print(f"{'='*80}")
            print(f"候选数量：{len(candidates)}")
            print(f"用户关键词：{user_keywords}")
            print()

        # 遍历所有候选，计算每个的匹配度
        scores = []
        for i, elem in enumerate(candidates):
            score = ElementSelector.calculate_match_score(
                elem, user_keywords, user_intent, field_name
            )
            scores.append((elem, score))

            if debug:
                print(f"{i+1}. {elem.get('chinese_name', elem.get('name'))}")
                print(f"   得分：{score:.1f}")
                print(f"   关键词：{elem.get('keywords', 'N/A')[:60]}...")
                print()

            # 更新最佳
            if score > best_score:
                best_score = score
                best_element = elem

        if debug and best_element:
            print(f"✅ 最佳选择：{best_element.get('chinese_name', best_element.get('name'))}")
            print(f"   得分：{best_score:.1f}")
            print(f"{'='*80}\n")

        return best_element, best_score

    @staticmethod
    def select_from_candidates_dict(
        candidates_dict: Dict[str, List[Dict]],
        intent: Dict,
        keywords_map: Dict[str, List[str]],
        debug: bool = False
    ) -> Dict[str, Dict]:
        """
        从多个字段的候选中批量选择最佳元素

        参数:
            candidates_dict: {field_name: [候选列表]}
            intent: 用户完整意图
            keywords_map: {field_name: [关键词列表]}
            debug: 是否输出调试信息

        返回:
            {field_name: 最佳元素}
        """
        selected = {}

        for field_name, candidates in candidates_dict.items():
            keywords = keywords_map.get(field_name, [])

            best_elem, score = ElementSelector.select_best_element(
                candidates, keywords, intent, field_name, debug
            )

            if best_elem:
                selected[field_name] = best_elem

        return selected
