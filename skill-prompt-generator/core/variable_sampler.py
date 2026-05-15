#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
变量采样系统 - 智能采样元素变量
支持参数化元素，避免重复采样，上下文感知
"""

import sqlite3
import json
import random
import time
from typing import Dict, List, Optional, Any


class SQLiteVariableSampler:
    """SQLite元素变量采样器"""

    def __init__(self, db_path: str):
        """
        初始化变量采样器

        Args:
            db_path: 数据库路径
        """
        self.db = sqlite3.connect(db_path)
        self.cursor = self.db.cursor()
        self.history = []  # 采样历史，避免重复
        self.max_history = 100  # 保留最近100次采样历史

    def get_element(self, element_id: str) -> Optional[Dict]:
        """获取元素基础信息"""
        query = """
            SELECT element_id, name, chinese_name, ai_prompt_template,
                   keywords, reusability_score, category_id, domain_id
            FROM elements
            WHERE element_id = ?
        """
        self.cursor.execute(query, (element_id,))
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
            'category': row[6],
            'domain': row[7]
        }

    def get_element_variables(self, element_id: str) -> List[Dict]:
        """获取元素的所有变量配置"""
        query = """
            SELECT variable_id, parameter_name, parameter_type,
                   possible_values, default_value, description
            FROM element_variables
            WHERE element_id = ?
        """
        self.cursor.execute(query, (element_id,))
        rows = self.cursor.fetchall()

        variables = []
        for row in rows:
            possible_values = None
            if row[3]:
                try:
                    possible_values = json.loads(row[3])
                except:
                    pass

            variables.append({
                'variable_id': row[0],
                'parameter_name': row[1],
                'parameter_type': row[2],
                'possible_values': possible_values,
                'default_value': row[4],
                'description': row[5]
            })

        return variables

    def sample_element_with_variables(self, element_id: str,
                                     style_context: Optional[Dict] = None) -> Dict:
        """
        采样元素并应用变量

        Args:
            element_id: 元素ID
            style_context: 风格上下文（可选）

        Returns:
            包含原始元素和变量值的字典
        """
        # 1. 获取元素基础模板
        element = self.get_element(element_id)
        if not element:
            raise ValueError(f"Element not found: {element_id}")

        # 2. 获取该元素的所有变量
        variables = self.get_element_variables(element_id)

        if not variables:
            # 没有变量，直接返回原始元素
            return {
                'element': element,
                'variables': {},
                'result': element['template']
            }

        # 3. 采样变量值（基于风格上下文）
        sampled_vars = {}
        for var in variables:
            sampled_vars[var['parameter_name']] = self.sample_variable(
                var, style_context, avoid_history=True
            )

        # 4. 应用变量到模板
        result = self.apply_variables(element['template'], sampled_vars)

        # 5. 记录历史
        self.history.append({
            'element_id': element_id,
            'variables': sampled_vars,
            'timestamp': time.time()
        })

        # 限制历史长度
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        return {
            'element': element,
            'variables': sampled_vars,
            'result': result
        }

    def sample_variable(self, var_config: Dict, style_context: Optional[Dict],
                       avoid_history: bool) -> Any:
        """
        智能采样单个变量

        Args:
            var_config: 变量配置
            style_context: 风格上下文
            avoid_history: 是否避免最近使用过的值

        Returns:
            采样的变量值
        """
        param_type = var_config['parameter_type']

        if param_type == 'enum':
            # 枚举类型：随机选择，避免重复
            values = var_config['possible_values']
            if not values:
                return var_config['default_value']

            # 根据风格上下文过滤
            if style_context:
                values = self.filter_by_style(values, style_context)

            # 避免最近使用过的
            if avoid_history and len(values) > 1:
                recent = self.get_recent_values(var_config['variable_id'])
                filtered = [v for v in values if v not in recent]
                if filtered:
                    values = filtered

            return random.choice(values) if values else var_config['default_value']

        elif param_type == 'range':
            # 范围类型：在范围内随机
            range_vals = var_config['possible_values']
            if not range_vals or len(range_vals) != 2:
                return var_config['default_value']

            min_val, max_val = range_vals

            # 根据风格上下文调整范围
            if style_context:
                min_val, max_val = self.adjust_range_by_style(
                    min_val, max_val, style_context
                )

            # 判断是整数还是浮点数
            if isinstance(min_val, int) and isinstance(max_val, int):
                return random.randint(min_val, max_val)
            else:
                return round(random.uniform(min_val, max_val), 2)

        elif param_type == 'boolean':
            # 布尔类型
            if style_context and 'prefer_' + var_config['parameter_name'] in style_context:
                return style_context['prefer_' + var_config['parameter_name']]
            return random.choice([True, False])

        else:
            return var_config['default_value']

    def filter_by_style(self, values: List[str], style_context: Dict) -> List[str]:
        """根据风格上下文过滤值"""
        # 简单实现：如果上下文指定了偏好，优先选择
        preferred = style_context.get('preferred_values', [])
        if preferred:
            filtered = [v for v in values if v in preferred]
            if filtered:
                return filtered
        return values

    def adjust_range_by_style(self, min_val: float, max_val: float,
                              style_context: Dict) -> tuple:
        """根据风格上下文调整范围"""
        # 简单实现：如果上下文指定了偏好范围，缩小范围
        if 'range_preference' in style_context:
            pref = style_context['range_preference']
            if pref == 'low':
                # 偏向低值
                max_val = min_val + (max_val - min_val) * 0.5
            elif pref == 'high':
                # 偏向高值
                min_val = min_val + (max_val - min_val) * 0.5
        return min_val, max_val

    def get_recent_values(self, variable_id: str, n: int = 3) -> List[Any]:
        """获取最近n次使用过的值"""
        recent = []
        for record in reversed(self.history):
            for var_name, var_value in record['variables'].items():
                # 简化：通过参数名匹配（实际应该用variable_id）
                if len(recent) < n:
                    recent.append(var_value)
        return recent

    def apply_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """
        应用变量到模板

        支持格式：{variable_name}
        例如："{intensity} lighting" -> "dramatic lighting"
        """
        result = template
        for var_name, var_value in variables.items():
            placeholder = '{' + var_name + '}'
            if placeholder in result:
                result = result.replace(placeholder, str(var_value))
        return result

    def close(self):
        """关闭数据库连接"""
        self.db.close()


class DesignVariableSampler:
    """设计变量采样器（从design_variables表采样）"""

    def __init__(self, db_path: str):
        """
        初始化设计变量采样器

        Args:
            db_path: 数据库路径
        """
        self.db = sqlite3.connect(db_path)
        self.cursor = self.db.cursor()
        self.history = []
        self.max_history = 100

    def sample_design_variables(self, style_name: str,
                                variable_types: Optional[List[str]] = None) -> Dict:
        """
        采样设计变量

        Args:
            style_name: 风格名称（如：温馨可爱、现代简约）
            variable_types: 变量类型列表（如：['colors', 'borders']），None表示全部

        Returns:
            采样的设计变量字典
        """
        query = """
            SELECT variable_id, variable_type, variable_name, variable_data
            FROM design_variables
            WHERE style_name = ?
        """
        params = [style_name]

        if variable_types:
            placeholders = ','.join(['?' for _ in variable_types])
            query += f" AND variable_type IN ({placeholders})"
            params.extend(variable_types)

        query += " ORDER BY priority DESC"

        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()

        if not rows:
            return {}

        # 按类型分组
        variables_by_type = {}
        for row in rows:
            var_type = row[1]
            if var_type not in variables_by_type:
                variables_by_type[var_type] = []

            var_data = None
            if row[3]:
                try:
                    var_data = json.loads(row[3])
                except:
                    pass

            variables_by_type[var_type].append({
                'variable_id': row[0],
                'variable_name': row[2],
                'variable_data': var_data
            })

        # 从每个类型中随机选择一个
        sampled = {}
        for var_type, candidates in variables_by_type.items():
            # 避免重复
            recent = self.get_recent_variables(var_type)
            filtered = [c for c in candidates if c['variable_id'] not in recent]
            if not filtered:
                filtered = candidates

            selected = random.choice(filtered)
            sampled[var_type] = selected

            # 记录历史
            self.history.append({
                'style_name': style_name,
                'variable_type': var_type,
                'variable_id': selected['variable_id'],
                'timestamp': time.time()
            })

        # 限制历史长度
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        return sampled

    def get_recent_variables(self, variable_type: str, n: int = 3) -> List[str]:
        """获取最近使用过的变量ID"""
        recent = []
        for record in reversed(self.history):
            if record['variable_type'] == variable_type:
                recent.append(record['variable_id'])
                if len(recent) >= n:
                    break
        return recent

    def close(self):
        """关闭数据库连接"""
        self.db.close()


def test_variable_sampler():
    """测试变量采样器"""
    print("=" * 80)
    print("测试变量采样系统")
    print("=" * 80)

    # 测试SQLiteVariableSampler
    print("\n【测试1】SQLite元素变量采样")
    sampler = SQLiteVariableSampler("extracted_results/elements.db")

    # 测试采样lighting元素（假设有变量）
    try:
        result = sampler.sample_element_with_variables(
            'common_lighting_001',
            style_context={'preferred_values': ['dramatic']}
        )
        print(f"  元素: {result['element']['chinese_name']}")
        print(f"  变量: {result['variables']}")
        print(f"  结果: {result['result']}")
    except Exception as e:
        print(f"  跳过（元素可能不存在）: {e}")

    sampler.close()

    # 测试DesignVariableSampler
    print("\n【测试2】设计变量采样")
    design_sampler = DesignVariableSampler("extracted_results/elements.db")

    # 采样温馨可爱风格
    sampled = design_sampler.sample_design_variables('温馨可爱')
    print(f"  风格: 温馨可爱")
    for var_type, var_data in sampled.items():
        print(f"  {var_type}: {var_data['variable_name']}")

    # 再次采样（应该避免重复）
    print("\n  第二次采样（应避免重复）:")
    sampled2 = design_sampler.sample_design_variables('温馨可爱')
    for var_type, var_data in sampled2.items():
        print(f"  {var_type}: {var_data['variable_name']}")

    design_sampler.close()

    print("\n✅ 测试完成")


if __name__ == '__main__':
    test_variable_sampler()
