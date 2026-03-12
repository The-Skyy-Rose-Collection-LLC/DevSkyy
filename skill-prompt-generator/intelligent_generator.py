#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能提示词生成器 - 配合Claude Skill使用
具备语义理解、常识推理、一致性检查能力
"""

import sqlite3
import json
from typing import Dict, List, Optional, Tuple


class IntelligentGenerator:
    """智能提示词生成器 - 理解意图，检查一致性"""

    def __init__(self, db_path: str = "extracted_results/elements.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        # 加载常识知识库
        self.knowledge = self.load_knowledge()

    def load_knowledge(self) -> Dict:
        """加载元素关系和常识约束"""
        return {
            # 人种 → 典型眼睛颜色
            'ethnicity_typical_eyes': {
                'East_Asian': ['black', 'dark brown', 'brown'],
                'Southeast_Asian': ['dark brown', 'brown', 'black'],
                'South_Asian': ['dark brown', 'brown', 'black'],
                'European': ['blue', 'green', 'brown', 'hazel', 'grey'],
                'African': ['dark brown', 'black', 'brown'],
                'Middle_Eastern': ['brown', 'dark brown', 'hazel', 'black'],
                'Latin_American': ['brown', 'dark brown', 'hazel', 'green'],
            },

            # 人种 → 典型发色
            'ethnicity_typical_hair': {
                'East_Asian': ['black', 'dark brown'],
                'Southeast_Asian': ['black', 'dark brown'],
                'South_Asian': ['black', 'dark brown'],
                'European': ['blonde', 'brown', 'black', 'red', 'auburn'],
                'African': ['black', 'dark brown'],
                'Middle_Eastern': ['black', 'dark brown', 'brown'],
                'Latin_American': ['black', 'dark brown', 'brown'],
            },

            # 风格类型定义
            'style_types': {
                'anime': {'type': 'art_style', 'affects': 'rendering', 'description': '动漫绘画风格'},
                'manga': {'type': 'art_style', 'affects': 'rendering', 'description': '漫画绘画风格'},
                'realistic': {'type': 'art_style', 'affects': 'rendering', 'description': '写实绘画风格'},
                'illustration': {'type': 'art_style', 'affects': 'rendering', 'description': '插画绘画风格'},

                'cyberpunk': {'type': 'atmosphere', 'affects': 'scene', 'description': '赛博朋克场景氛围'},
                'fantasy': {'type': 'atmosphere', 'affects': 'scene', 'description': '奇幻场景氛围'},
                'vintage': {'type': 'atmosphere', 'affects': 'scene', 'description': '复古场景氛围'},

                'neon': {'type': 'lighting', 'affects': 'lighting', 'description': '霓虹灯光'},
                'dramatic': {'type': 'lighting', 'affects': 'lighting', 'description': '戏剧性灯光'},
            },

            # 导演/风格 → 光影需求映射
            'director_lighting_styles': {
                'zhang_yimou': {
                    'description': '张艺谋电影风格',
                    'lighting_keywords': ['dramatic', 'shadow', 'rim', 'contrast', 'chiaroscuro', 'volumetric'],
                    'required_elements': ['dramatic shadows', 'rim lighting'],
                },
                'cinematic': {
                    'description': '电影级',
                    'lighting_keywords': ['dramatic', 'cinematic', 'rim', 'contrast'],
                    'required_elements': ['dramatic lighting', 'rim lighting'],
                },
                'film_noir': {
                    'description': '黑色电影',
                    'lighting_keywords': ['shadow', 'contrast', 'chiaroscuro', 'low key'],
                    'required_elements': ['dramatic shadows', 'high contrast'],
                },
            },

            # 人物属性类别（不应该被style关键词覆盖）
            'subject_attribute_categories': {
                'gender', 'age_range', 'ethnicity', 'skin_tones',
                'eye_types', 'hair_colors', 'hair_styles',
                'face_shapes', 'nose_types', 'lip_types'
            }
        }

    def get_element_by_category(self, domain: str, category: str,
                                value_filter: Optional[str] = None) -> Optional[Dict]:
        """从数据库获取元素"""
        query = """
            SELECT element_id, name, chinese_name, ai_prompt_template,
                   keywords, reusability_score, category_id
            FROM elements
            WHERE domain_id = ? AND category_id = ?
        """
        params = [domain, category]

        if value_filter:
            query += " AND (ai_prompt_template LIKE ? OR keywords LIKE ?)"
            params.extend([f"%{value_filter}%", f"%{value_filter}%"])

        query += " ORDER BY reusability_score DESC LIMIT 1"

        self.cursor.execute(query, params)
        row = self.cursor.fetchone()

        if not row:
            return None

        # 验证name是否匹配value_filter（避免子串误匹配，如female被male匹配）
        if value_filter and row[1].lower() != value_filter.lower():
            # 如果不匹配，尝试直接用name精确匹配
            query_exact = """
                SELECT element_id, name, chinese_name, ai_prompt_template,
                       keywords, reusability_score, category_id
                FROM elements
                WHERE domain_id = ? AND category_id = ? AND name = ?
                ORDER BY reusability_score DESC LIMIT 1
            """
            self.cursor.execute(query_exact, [domain, category, value_filter])
            row = self.cursor.fetchone()
            if not row:
                return None

        keywords = None
        if row[4]:
            try:
                keywords = json.loads(row[4])
            except:
                pass

        return {
            'element_id': row[0],
            'name': row[1],
            'chinese_name': row[2],
            'template': row[3],
            'keywords': keywords,
            'reusability': row[5],
            'category': row[6]
        }

    def get_all_elements_by_category(self, domain: str, category: str,
                                     value_filter: Optional[str] = None) -> List[Dict]:
        """从数据库获取该类别的所有元素（用于SKILL分析）"""
        query = """
            SELECT element_id, name, chinese_name, ai_prompt_template,
                   keywords, reusability_score, category_id
            FROM elements
            WHERE domain_id = ? AND category_id = ?
        """
        params = [domain, category]

        if value_filter:
            query += " AND (ai_prompt_template LIKE ? OR keywords LIKE ?)"
            params.extend([f"%{value_filter}%", f"%{value_filter}%"])

        query += " ORDER BY reusability_score DESC"

        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()

        elements = []
        for row in rows:
            keywords = None
            if row[4]:
                try:
                    keywords = json.loads(row[4])
                except:
                    pass

            elements.append({
                'element_id': row[0],
                'name': row[1],
                'chinese_name': row[2],
                'template': row[3],
                'keywords': keywords,
                'reusability': row[5],
                'category': row[6]
            })

        return elements

    def select_elements_by_intent(self, intent: Dict) -> List[Dict]:
        """
        基于解析的意图从数据库选择元素

        intent格式:
        {
            'subject': {
                'gender': 'female',
                'ethnicity': 'East_Asian',
                'age_range': 'young_adult'
            },
            'visual_style': {
                'art_style': 'anime'
            },
            'atmosphere': {
                'theme': 'cyberpunk'
            }
        }
        """
        elements = []

        # 1. 选择人物属性
        subject = intent.get('subject', {})

        if 'gender' in subject:
            elem = self.get_element_by_category('portrait', 'gender', subject['gender'])
            if elem:
                elements.append(elem)

        if 'age_range' in subject:
            elem = self.get_element_by_category('portrait', 'age_range')
            if elem:
                elements.append(elem)

        if 'ethnicity' in subject:
            ethnicity_name = subject['ethnicity']
            elem = self.get_element_by_category('portrait', 'ethnicity', ethnicity_name)
            if elem:
                elements.append(elem)

            # 自动选择匹配人种的眼睛
            # 对于东亚人，选择almond/large expressive类型（避免green/blue）
            if ethnicity_name == 'East_Asian':
                eye_elem = self.get_element_by_category('portrait', 'eye_types', 'almond')
            else:
                eye_elem = self.get_element_by_category('portrait', 'eye_types')

            if eye_elem:
                elements.append(eye_elem)

            # 自动选择匹配人种的发色
            typical_hair = self.knowledge['ethnicity_typical_hair'].get(ethnicity_name, ['black'])
            hair_color_elem = self.get_element_by_category('portrait', 'hair_colors', typical_hair[0])
            if hair_color_elem:
                elements.append(hair_color_elem)

        # 2. 根据intent选择服装和发型（优先使用intent指定的）
        clothing = intent.get('clothing', 'modern')
        hairstyle = intent.get('hairstyle', 'modern')

        # 服装关键词映射（灵活搜索）
        clothing_keywords_map = {
            'traditional_chinese': ['traditional', 'chinese', 'hanfu', 'period'],
            'kimono': ['kimono', 'japanese'],
            'business': ['business', 'suit', 'formal'],
            'casual': ['casual'],
            'formal': ['formal', 'evening']
        }

        # 搜索服装元素
        if clothing != 'modern':  # 如果非默认，搜索特定服装
            search_keywords = clothing_keywords_map.get(clothing, [clothing])
            clothing_elem = None
            # 尝试用每个关键词搜索
            for kw in search_keywords:
                clothing_elem = self.get_element_by_category('portrait', 'clothing_styles', kw)
                if clothing_elem:
                    print(f"✓ 找到服装元素: '{clothing_elem['chinese_name']}'（搜索关键词: {kw}）")
                    elements.append(clothing_elem)
                    break

            # 如果没找到，记录信息
            if not clothing_elem:
                print(f"⚠️ 未找到'{clothing}'服装元素，将通过风格关键词搜索")
        else:
            # 默认选择一个现代服装
            elem = self.get_element_by_category('portrait', 'clothing_styles')
            if elem:
                elements.append(elem)

        # 发型关键词映射（灵活搜索）
        hairstyle_keywords_map = {
            'ancient_chinese': ['traditional', 'classical', 'bun', 'updo'],
            'traditional_japanese': ['traditional', 'japanese'],
        }

        # 搜索发型元素（如果指定了特殊发型）
        if hairstyle != 'modern':
            search_keywords = hairstyle_keywords_map.get(hairstyle, [hairstyle])
            hair_style_elem = None
            # 尝试用每个关键词搜索
            for kw in search_keywords:
                hair_style_elem = self.get_element_by_category('portrait', 'hair_styles', kw)
                if hair_style_elem:
                    print(f"✓ 找到发型元素: '{hair_style_elem['chinese_name']}'（搜索关键词: {kw}）")
                    elements.append(hair_style_elem)
                    break

            # 如果没找到，记录信息
            if not hair_style_elem:
                print(f"⚠️ 未找到'{hairstyle}'发型元素，将通过风格关键词搜索")
        else:
            # 默认选择一个现代发型
            elem = self.get_element_by_category('portrait', 'hair_styles')
            if elem:
                elements.append(elem)

        # 3. 选择其他人物属性
        for attr in ['skin_tones', 'skin_textures', 'face_shapes',
                     'makeup_styles', 'expressions', 'poses']:
            elem = self.get_element_by_category('portrait', attr)
            if elem:
                elements.append(elem)

        # 4. 添加风格元素（lighting, era, director_style等）
        visual_style = intent.get('visual_style', {})
        atmosphere = intent.get('atmosphere', {})
        era = intent.get('era', 'modern')
        lighting = intent.get('lighting', 'natural')

        # 收集所有风格关键词
        style_keywords = []

        # 添加服装关键词（补充搜索）
        if clothing != 'modern':
            clothing_search_kws = clothing_keywords_map.get(clothing, [])
            style_keywords.extend(clothing_search_kws)
            print(f"✓ 添加服装搜索关键词: {', '.join(clothing_search_kws)}")

        # 添加发型关键词（补充搜索）
        if hairstyle != 'modern':
            hairstyle_search_kws = hairstyle_keywords_map.get(hairstyle, [])
            style_keywords.extend(hairstyle_search_kws)
            print(f"✓ 添加发型搜索关键词: {', '.join(hairstyle_search_kws)}")

        # 添加艺术风格
        if 'art_style' in visual_style:
            style_keywords.append(visual_style['art_style'])

        # 添加氛围主题
        if 'theme' in atmosphere:
            style_keywords.append(atmosphere['theme'])

        # 添加光影关键词
        if lighting:
            style_keywords.append(lighting)

        # 添加时代背景关键词
        if era != 'modern':
            style_keywords.append(era)
            # 古代时期添加相关词
            if era == 'ancient':
                style_keywords.extend(['traditional', 'period', 'classical'])

        # 检查导演风格，添加特定关键词
        director_style = atmosphere.get('director_style')
        if director_style:
            # 检查是否在知识库中（用于光影扩展）
            if director_style in self.knowledge.get('director_lighting_styles', {}):
                lighting_config = self.knowledge['director_lighting_styles'][director_style]
                style_keywords.extend(lighting_config['lighting_keywords'])
                print(f"✓ 识别到'{lighting_config['description']}'，自动添加光影关键词: {', '.join(lighting_config['lighting_keywords'])}")

            # 添加导演风格的特定关键词
            director_keywords = {
                'tsui_hark': ['wuxia', 'martial arts', 'flowing', 'dynamic'],
                'zhang_yimou': ['traditional', 'red', 'gold', 'period drama'],
                'wong_kar_wai': ['nostalgic', 'atmospheric', 'saturated colors']
            }
            if director_style in director_keywords:
                style_keywords.extend(director_keywords[director_style])
                print(f"✓ 识别到导演风格'{director_style}'，添加特征关键词: {', '.join(director_keywords[director_style])}")

        if style_keywords:
            style_elements = self.search_style_elements(style_keywords)
            elements.extend(style_elements)

        return elements

    def calculate_relevance(self, element: Dict, required_keywords: List[str]) -> float:
        """
        计算元素与需求的相关性得分（0-1）

        参数:
            element: 元素字典
            required_keywords: 用户需求的关键词列表

        返回:
            相关性得分 (0.0 - 1.0)
        """
        if not required_keywords:
            return 0.5  # 无关键词，默认中等相关性

        template = element.get('template', '').lower()
        keywords = element.get('keywords', [])

        # 构建元素的所有文本
        element_text = template
        if keywords:
            element_text += ' ' + ' '.join(keywords).lower()

        # 计算匹配的关键词数量
        matched = 0
        for kw in required_keywords:
            if kw.lower() in element_text:
                matched += 1

        # 相关性 = 匹配数 / 总关键词数
        relevance = matched / len(required_keywords)

        return relevance

    def search_style_elements(self, keywords: List[str]) -> List[Dict]:
        """搜索风格元素，排除人物属性类别，按相关性×质量排序"""
        excluded_categories = self.knowledge['subject_attribute_categories']

        keyword_conditions = " OR ".join(["ai_prompt_template LIKE ?" for _ in keywords])
        query = f"""
            SELECT element_id, name, chinese_name, ai_prompt_template,
                   keywords, reusability_score, category_id
            FROM elements
            WHERE ({keyword_conditions})
              AND ai_prompt_template != ''
            ORDER BY reusability_score DESC
            LIMIT 30
        """

        params = [f"%{kw}%" for kw in keywords]
        self.cursor.execute(query, params)

        elements = []
        for row in self.cursor.fetchall():
            # 过滤掉人物属性类别
            if row[6] in excluded_categories:
                continue

            keywords_data = None
            if row[4]:
                try:
                    keywords_data = json.loads(row[4])
                except:
                    pass

            elem = {
                'element_id': row[0],
                'name': row[1],
                'chinese_name': row[2],
                'template': row[3],
                'keywords': keywords_data,
                'reusability': row[5],
                'category': row[6]
            }

            # 计算相关性得分
            relevance = self.calculate_relevance(elem, keywords)

            # 综合得分 = 相关性 × 质量分
            elem['relevance'] = relevance
            elem['final_score'] = relevance * row[5]  # reusability_score

            elements.append(elem)

        # 按综合得分排序
        elements.sort(key=lambda x: x['final_score'], reverse=True)

        # 返回前10个最相关的
        return elements[:10]

    def check_consistency(self, elements: List[Dict]) -> List[Dict]:
        """
        检查元素之间的一致性

        返回问题列表，每个问题包含：
        - type: 问题类型
        - severity: 严重程度 (low/medium/high)
        - description: 问题描述
        - suggestion: 修正建议
        """
        issues = []

        # 提取关键元素
        ethnicity_elem = self.find_element_by_category(elements, 'ethnicity')
        eye_elem = self.find_element_by_category(elements, 'eye_types')
        hair_elem = self.find_element_by_category(elements, 'hair_colors')

        # 检查1：人种 vs 眼睛颜色（检测不合理的颜色如green/blue for 东亚人）
        if ethnicity_elem and eye_elem:
            ethnicity_name = self.extract_ethnicity_name(ethnicity_elem['name'])
            eye_template = eye_elem['template'].lower()

            # 检测不合理的颜色
            incompatible_colors = []
            if ethnicity_name == 'East_Asian':
                # 东亚人不应该有这些眼睛颜色
                if 'green' in eye_template or 'blue' in eye_template or 'violet' in eye_template:
                    incompatible_colors = ['green', 'blue', 'violet']
            elif ethnicity_name == 'African':
                if 'blue' in eye_template or 'green' in eye_template:
                    incompatible_colors = ['blue', 'green']

            if incompatible_colors:
                typical_eyes = self.knowledge['ethnicity_typical_eyes'].get(ethnicity_name, ['brown'])
                issues.append({
                    'type': 'ethnicity_eye_mismatch',
                    'severity': 'medium',
                    'current_ethnicity': ethnicity_elem['chinese_name'],
                    'current_eye': eye_elem['template'],
                    'incompatible_colors': incompatible_colors,
                    'typical_eyes': typical_eyes,
                    'description': f"{ethnicity_elem['chinese_name']}通常不会有包含'{', '.join(incompatible_colors)}'的眼睛",
                    'suggestion': f"建议选择包含这些颜色的眼型: {', '.join(typical_eyes)}"
                })

        # 检查2：人种 vs 发色
        if ethnicity_elem and hair_elem:
            ethnicity_name = self.extract_ethnicity_name(ethnicity_elem['name'])
            typical_hair = self.knowledge['ethnicity_typical_hair'].get(ethnicity_name, [])

            hair_template = hair_elem['template'].lower()
            is_typical = any(color in hair_template for color in typical_hair)

            if not is_typical:
                issues.append({
                    'type': 'ethnicity_hair_mismatch',
                    'severity': 'low',
                    'current_ethnicity': ethnicity_elem['chinese_name'],
                    'current_hair': hair_elem['template'],
                    'typical_hair': typical_hair,
                    'description': f"{ethnicity_elem['chinese_name']}通常不会有'{hair_elem['template']}'",
                    'suggestion': f"建议改为: {', '.join(typical_hair)}"
                })

        # 检查3：重复类别（但lighting_techniques允许多个）
        category_counts = {}
        for elem in elements:
            cat = elem['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # 允许多个元素的类别
        multi_element_categories = {'lighting_techniques', 'photography_techniques'}

        for cat, count in category_counts.items():
            # lighting_techniques等类别允许多个元素组合
            if count > 1 and cat not in multi_element_categories:
                issues.append({
                    'type': 'duplicate_category',
                    'severity': 'high',
                    'category': cat,
                    'count': count,
                    'description': f"类别'{cat}'出现了{count}次（应该只有1次）",
                    'suggestion': "保留最相关的一个元素"
                })

        return issues

    def check_completeness(self, intent: Dict, prompt: str) -> List[Dict]:
        """
        检查生成的提示词是否满足所有用户要求

        参数:
            intent: 原始意图字典
            prompt: 生成的提示词字符串

        返回:
            缺失需求列表，每个包含：
            - requirement: 需求类型
            - expected: 期望的关键词
            - description: 缺失描述
        """
        missing = []
        prompt_lower = prompt.lower()

        # 检查1：服装要求
        clothing = intent.get('clothing')
        if clothing and clothing != 'modern':
            clothing_keywords = {
                'traditional_chinese': ['traditional', 'costume', 'hanfu', 'chinese dress', 'period dress'],
                'kimono': ['kimono', 'traditional japanese'],
                'business': ['business', 'suit', 'professional'],
                'casual': ['casual'],
                'formal': ['formal', 'evening gown', 'dress']
            }
            expected_kws = clothing_keywords.get(clothing, [])
            if expected_kws and not any(kw in prompt_lower for kw in expected_kws):
                missing.append({
                    'requirement': 'clothing',
                    'expected': expected_kws,
                    'description': f"用户要求'{clothing}'服装，但提示词中未找到相关描述",
                    'suggestion': f"应包含: {', '.join(expected_kws[:3])}"
                })

        # 检查2：发型要求
        hairstyle = intent.get('hairstyle')
        if hairstyle and hairstyle != 'modern':
            hairstyle_keywords = {
                'ancient_chinese': ['traditional hairstyle', 'classical hair', 'hair ornament', 'hairpin', 'bun'],
                'traditional_japanese': ['traditional japanese hair', 'kanzashi']
            }
            expected_kws = hairstyle_keywords.get(hairstyle, [])
            if expected_kws and not any(kw in prompt_lower for kw in expected_kws):
                missing.append({
                    'requirement': 'hairstyle',
                    'expected': expected_kws,
                    'description': f"用户要求'{hairstyle}'发型，但提示词中未找到相关描述",
                    'suggestion': f"应包含: {', '.join(expected_kws[:3])}"
                })

        # 检查3：时代背景
        era = intent.get('era')
        if era and era != 'modern':
            era_keywords = {
                'ancient': ['traditional', 'period', 'classical', 'ancient'],
                'republic_of_china': ['republic era', '1920s', '1930s', 'vintage']
            }
            expected_kws = era_keywords.get(era, [])
            if expected_kws and not any(kw in prompt_lower for kw in expected_kws):
                missing.append({
                    'requirement': 'era',
                    'expected': expected_kws,
                    'description': f"用户要求'{era}'时代背景，但提示词中未找到相关描述",
                    'suggestion': f"应包含: {', '.join(expected_kws[:3])}"
                })

        # 检查4：导演风格特征
        atmosphere = intent.get('atmosphere', {})
        director_style = atmosphere.get('director_style')
        if director_style:
            director_keywords = {
                'tsui_hark': ['wuxia', 'martial arts', 'flowing', 'dynamic'],
                'zhang_yimou': ['traditional', 'red', 'gold', 'dramatic'],
                'wong_kar_wai': ['nostalgic', 'atmospheric', 'saturated']
            }
            expected_kws = director_keywords.get(director_style, [])
            if expected_kws and not any(kw in prompt_lower for kw in expected_kws):
                missing.append({
                    'requirement': 'director_style',
                    'expected': expected_kws,
                    'description': f"用户要求'{director_style}'导演风格，但提示词中未找到特征关键词",
                    'suggestion': f"应包含: {', '.join(expected_kws[:3])}"
                })

        # 检查5：光影要求（必选）
        # 支持两种格式：字符串（旧格式）和dict（框架格式）
        lighting = intent.get('lighting', 'natural')
        if isinstance(lighting, dict):
            lighting = lighting.get('lighting_type', 'natural')

        lighting_keywords = {
            'natural': ['natural', 'window light', 'daylight', 'soft light'],
            'cinematic': ['cinematic', 'dramatic', 'rim light'],
            'zhang_yimou': ['dramatic', 'shadow', 'rim', 'chiaroscuro'],
            'film_noir': ['shadow', 'contrast', 'chiaroscuro', 'low key'],
            'neon': ['neon', 'colorful', 'glow'],
            'soft': ['soft', 'gentle', 'diffused'],
            'dramatic': ['dramatic', 'shadow', 'contrast']
        }
        expected_kws = lighting_keywords.get(lighting, [])
        if expected_kws and not any(kw in prompt_lower for kw in expected_kws):
            missing.append({
                'requirement': 'lighting',
                'expected': expected_kws,
                'description': f"用户要求'{lighting}'光影，但提示词中未找到相关描述",
                'suggestion': f"应包含: {', '.join(expected_kws[:3])}"
            })

        return missing

    def resolve_conflicts(self, elements: List[Dict], issues: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """
        解决检测到的冲突

        返回：(修正后的元素列表, 修正说明列表)
        """
        fixed_elements = elements.copy()
        fixes_applied = []

        for issue in issues:
            if issue['type'] == 'ethnicity_eye_mismatch':
                # 替换为符合人种的眼睛（选择almond/brown等合适的）
                ethnicity_elem = self.find_element_by_category(fixed_elements, 'ethnicity')
                ethnicity_name = self.extract_ethnicity_name(ethnicity_elem['name']) if ethnicity_elem else 'East_Asian'

                # 为不同人种选择合适的眼型
                if ethnicity_name == 'East_Asian':
                    new_eye_elem = self.get_element_by_category('portrait', 'eye_types', 'almond brown')
                    if not new_eye_elem:
                        new_eye_elem = self.get_element_by_category('portrait', 'eye_types', 'almond')
                else:
                    new_eye_elem = self.get_element_by_category('portrait', 'eye_types')

                if new_eye_elem:
                    # 移除旧的eye元素
                    fixed_elements = [e for e in fixed_elements if e['category'] != 'eye_types']
                    # 添加新的
                    fixed_elements.append(new_eye_elem)

                    fixes_applied.append(
                        f"✓ 修正眼睛: '{issue['current_eye']}' → '{new_eye_elem['template']}' "
                        f"(符合{issue['current_ethnicity']}特征)"
                    )

            elif issue['type'] == 'ethnicity_hair_mismatch':
                # 替换发色
                suggested_color = issue['typical_hair'][0]
                new_hair_elem = self.get_element_by_category('portrait', 'hair_colors', suggested_color)

                if new_hair_elem:
                    fixed_elements = [e for e in fixed_elements if e['category'] != 'hair_colors']
                    fixed_elements.append(new_hair_elem)

                    fixes_applied.append(
                        f"✓ 修正发色: '{issue['current_hair']}' → '{new_hair_elem['template']}' "
                        f"(符合{issue['current_ethnicity']}特征)"
                    )

            elif issue['type'] == 'duplicate_category':
                # 保留第一个，删除其他
                cat = issue['category']
                kept = False
                new_list = []
                for elem in fixed_elements:
                    if elem['category'] == cat:
                        if not kept:
                            new_list.append(elem)
                            kept = True
                    else:
                        new_list.append(elem)

                fixed_elements = new_list
                fixes_applied.append(f"✓ 移除重复的'{cat}'类别元素")

        return fixed_elements, fixes_applied

    def find_element_by_category(self, elements: List[Dict], category: str) -> Optional[Dict]:
        """从元素列表中查找指定类别的元素"""
        for elem in elements:
            if elem['category'] == category:
                return elem
        return None

    def extract_ethnicity_name(self, name: str) -> str:
        """从元素名称提取人种标准名称"""
        mapping = {
            'east_asian': 'East_Asian',
            'southeast_asian': 'Southeast_Asian',
            'south_asian': 'South_Asian',
            'european': 'European',
            'african': 'African',
            'middle_eastern': 'Middle_Eastern',
            'latin_american': 'Latin_American',
        }
        return mapping.get(name.lower(), name)

    def compose_prompt(self, elements: List[Dict], mode: str = 'auto',
                      keywords_limit: int = 3) -> str:
        """
        组合元素生成最终提示词（带去重和过滤）

        mode: 'simple', 'auto', 'detailed'
        """
        all_keywords = []
        seen_concepts = set()  # 用于去重

        # 同义词组（用于去重）
        synonym_groups = {
            'woman': ['woman', 'female', 'lady', 'girl'],
            'man': ['man', 'male', 'gentleman', 'boy'],
            'young': ['young', 'youthful', 'young adult'],
            'fair': ['fair', 'pale', 'light'],
            'East Asian': ['East Asian', 'Chinese', 'Japanese', 'Korean'],
            'eyes': ['eyes', 'eye', 'large expressive eyes', 'almond eyes'],
            'hair': ['hair', 'hairs', 'black hair'],
            'skin': ['skin', 'fair skin', 'pale skin', 'realistic skin texture'],
            'face': ['face', 'oval face'],
            'ponytail': ['ponytail with bangs', 'straight bangs ponytail', 'ponytail and fringe', 'ponytail'],
            'bokeh': ['creamy bokeh', 'cinematic bokeh', 'smooth bokeh', 'bokeh'],
            'dramatic': ['dramatic shadows', 'dramatic lighting', 'dramatic'],
            'rim light': ['rim light', 'edge lighting', 'backlight', 'rim lighting'],
            'gaze': ['innocent gaze', 'gentle smile', 'soft introspective', 'gaze'],
            'pose': ['relaxed', 'casual stance', 'natural pose', 'pose'],
        }

        # 无关/错误的关键词黑名单（明显不属于人像）
        blacklist = {
            'bottle', 'highlighting', 'condensa', 'elements', 'surroundings',
            'practical', 'string', 'lanterns', 'vintage lamps', 'accent lights'
        }

        # 反向映射：关键词 → 代表词
        concept_map = {}
        for representative, synonyms in synonym_groups.items():
            for syn in synonyms:
                concept_map[syn.lower()] = representative

        for elem in elements:
            template = elem.get('template', '')
            keywords = elem.get('keywords')

            # 选择文本
            if mode == 'simple':
                text = template
            elif mode == 'detailed' and keywords and len(keywords) > 0:
                text_list = keywords[:keywords_limit]
            elif mode == 'auto' and keywords and len(keywords) > 2:
                text_list = keywords[:keywords_limit]
            else:
                text = template
                text_list = None

            # 如果有keywords列表，逐个处理
            if text_list:
                for kw in text_list:
                    # 过滤无效关键词
                    if not kw or len(kw.strip()) == 0:
                        continue

                    kw_stripped = kw.strip()
                    kw_lower = kw_stripped.lower()

                    # 黑名单过滤
                    if any(blackword in kw_lower for blackword in blacklist):
                        continue

                    words = kw_stripped.split()

                    # 过滤单个词碎片（<4字符或明显无关）
                    if len(words) == 1:
                        # 单词过滤：短于4字符，或在黑名单
                        if len(kw_stripped) < 4 or kw_lower in blacklist:
                            continue

                    # 去重检查 - 检查完整短语
                    concept = concept_map.get(kw_lower, None)

                    # 如果没有精确匹配，检查是否完全匹配已知概念
                    # 注意：只对完整短语进行同义词匹配，不做子串匹配
                    if not concept:
                        # 先尝试精确匹配整个短语
                        for rep, syns in synonym_groups.items():
                            if kw_lower in [s.lower() for s in syns]:
                                concept = rep
                                break

                    # 如果还是没找到概念，用完整短语作为唯一标识
                    if not concept:
                        concept = kw_lower

                    if concept not in seen_concepts:
                        all_keywords.append(kw_stripped)
                        seen_concepts.add(concept)
            else:
                # 使用template
                if text and text.strip():
                    text_stripped = text.strip()
                    text_lower = text_stripped.lower()

                    # 黑名单过滤
                    if any(blackword in text_lower for blackword in blacklist):
                        continue

                    # 去重检查
                    concept = concept_map.get(text_lower, None)

                    # 检查是否完全匹配已知概念（不做子串匹配）
                    if not concept:
                        for rep, syns in synonym_groups.items():
                            if text_lower in [s.lower() for s in syns]:
                                concept = rep
                                break

                    if not concept:
                        concept = text_lower

                    if concept not in seen_concepts:
                        all_keywords.append(text_stripped)
                        seen_concepts.add(concept)

        return ', '.join(all_keywords)

    def close(self):
        """关闭数据库连接"""
        self.conn.close()


def test_intelligent_generator():
    """测试智能生成器"""
    gen = IntelligentGenerator()

    print("="*80)
    print("测试智能提示词生成器")
    print("="*80)

    # 测试intent
    intent = {
        'subject': {
            'gender': 'female',
            'ethnicity': 'East_Asian',
            'age_range': 'young_adult'
        },
        'visual_style': {
            'art_style': 'anime'
        },
        'atmosphere': {
            'theme': 'cyberpunk'
        }
    }

    print("\n1. 基于intent选择元素...")
    elements = gen.select_elements_by_intent(intent)
    print(f"   选择了 {len(elements)} 个元素")

    print("\n2. 检查一致性...")
    issues = gen.check_consistency(elements)

    if issues:
        print(f"   发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"   - [{issue['severity']}] {issue['description']}")
            print(f"     {issue['suggestion']}")

        print("\n3. 修正冲突...")
        fixed_elements, fixes = gen.resolve_conflicts(elements, issues)
        for fix in fixes:
            print(f"   {fix}")
    else:
        print("   ✓ 没有发现问题")
        fixed_elements = elements

    print("\n4. 生成最终提示词...")
    prompt = gen.compose_prompt(fixed_elements, mode='auto')
    print(f"\n{prompt}")

    print("\n5. 检查完整性...")
    missing = gen.check_completeness(intent, prompt)
    if missing:
        print(f"   ⚠️ 发现 {len(missing)} 个缺失的需求:")
        for item in missing:
            print(f"   - {item['description']}")
            print(f"     {item['suggestion']}")
    else:
        print("   ✓ 提示词满足所有用户要求")

    gen.close()


def query_candidates_by_intent(intent: dict, db_path: str = 'extracted_results/elements.db') -> dict:
    """
    【执行层】根据Intent查询所有候选元素

    输入：Intent字典（由SKILL构造）
    输出：候选字典 {field: [elements]}
    """
    from framework_loader import FrameworkDrivenGenerator

    gen = FrameworkDrivenGenerator(db_path)
    candidates = gen.query_all_candidates_by_framework(intent)

    return candidates


def assemble_prompt_from_elements(elements: list, subject_desc: str = '') -> str:
    """
    【执行层】从元素列表拼接提示词

    输入：
    - elements: 元素列表（由SKILL选择）
    - subject_desc: 主体描述（可选，如"A young woman"）

    输出：完整提示词字符串
    """
    parts = []

    if subject_desc:
        parts.append(subject_desc)

    for element in elements:
        template = element.get('template', '')
        if template:
            parts.append(template)

    return ', '.join(parts)


def save_generated_prompt(prompt_text: str, user_intent: str,
                         elements_used: list, style_tag: str = None,
                         quality_score: float = 9.0,
                         db_path: str = 'extracted_results/elements.db') -> int:
    """
    【执行层】保存生成的Prompt到数据库

    这是prompt-analyzer工作的数据来源！

    参数：
    - prompt_text: 完整的提示词文本
    - user_intent: 用户的原始需求描述
    - elements_used: 使用的元素列表（每个元素应包含element_id, category, field_name）
    - style_tag: 风格标签（如ancient_chinese, modern_sci_fi等）
    - quality_score: 质量评分（由SKILL评估，默认9.0）
    - db_path: 数据库路径

    返回：
    - prompt_id: 保存后的Prompt ID
    """
    import sqlite3
    from datetime import datetime

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. 保存到generated_prompts表
        cursor.execute('''
            INSERT INTO generated_prompts
            (prompt_text, user_intent, quality_score, style_tag, generation_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (prompt_text, user_intent, quality_score, style_tag, datetime.now()))

        prompt_id = cursor.lastrowid

        # 2. 保存元素关联到prompt_elements表
        for element in elements_used:
            element_id = element.get('element_id')
            category = element.get('category')
            field_name = element.get('field_name', '')

            if element_id:  # 只保存有效的element_id
                cursor.execute('''
                    INSERT INTO prompt_elements
                    (prompt_id, element_id, category, field_name)
                    VALUES (?, ?, ?, ?)
                ''', (prompt_id, element_id, category, field_name))

        # 3. 更新元素使用统计
        for element in elements_used:
            element_id = element.get('element_id')
            if element_id:
                # 检查是否已存在统计记录
                cursor.execute('''
                    SELECT usage_count, avg_quality
                    FROM element_usage_stats
                    WHERE element_id = ?
                ''', (element_id,))

                existing = cursor.fetchone()

                if existing:
                    # 更新统计
                    old_count = existing[0]
                    old_avg = existing[1]
                    new_count = old_count + 1
                    new_avg = (old_avg * old_count + quality_score) / new_count

                    cursor.execute('''
                        UPDATE element_usage_stats
                        SET usage_count = ?, avg_quality = ?, last_used = ?
                        WHERE element_id = ?
                    ''', (new_count, new_avg, datetime.now(), element_id))
                else:
                    # 创建新统计记录
                    cursor.execute('''
                        INSERT INTO element_usage_stats
                        (element_id, usage_count, avg_quality, last_used)
                        VALUES (?, 1, ?, ?)
                    ''', (element_id, quality_score, datetime.now()))

        conn.commit()
        print(f"✅ Prompt已保存到数据库，ID: #{prompt_id}")
        return prompt_id

    except Exception as e:
        conn.rollback()
        print(f"❌ 保存Prompt失败: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    # 测试：旧的Intent-based流程
    test_intelligent_generator()
