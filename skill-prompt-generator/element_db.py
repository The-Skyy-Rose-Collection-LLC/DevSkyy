#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Elements Library - Database Layer
通用元素库 - 数据库层

使用SQLite数据库存储所有领域的可复用元素
支持导出/导入JSON用于版本控制
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re


class ElementDB:
    """通用元素库数据库管理类"""

    def __init__(self, db_path: str = "extracted_results/elements.db"):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # 返回字典形式的行

        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        cursor = self.conn.cursor()

        # 1. 领域表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS domains (
            domain_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            total_elements INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 2. 类别表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id TEXT PRIMARY KEY,
            domain_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            total_elements INTEGER DEFAULT 0,
            FOREIGN KEY (domain_id) REFERENCES domains(domain_id)
        )
        """)

        # 3. 元素表（核心）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS elements (
            element_id TEXT PRIMARY KEY,
            domain_id TEXT NOT NULL,
            category_id TEXT NOT NULL,

            -- 基本信息
            name TEXT NOT NULL,
            chinese_name TEXT,

            -- Prompt模板
            ai_prompt_template TEXT NOT NULL,
            keywords TEXT,  -- JSON array

            -- 评分和元数据
            reusability_score REAL CHECK(reusability_score >= 0 AND reusability_score <= 10),
            confidence_score REAL,

            -- 溯源
            source_prompts TEXT,  -- JSON array: [1, 5, 10]
            learned_from TEXT,    -- 'manual' or 'auto_learner'

            -- 扩展字段
            metadata TEXT,        -- JSON: 其他自定义字段

            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (domain_id) REFERENCES domains(domain_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
        """)

        # 4. 标签表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_name TEXT UNIQUE NOT NULL,
            tag_type TEXT,
            usage_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 5. 元素-标签关联表（多对多）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS element_tags (
            element_id TEXT NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (element_id, tag_id),
            FOREIGN KEY (element_id) REFERENCES elements(element_id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
        )
        """)

        # 6. 来源Prompt表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS source_prompts (
            prompt_id INTEGER PRIMARY KEY,
            original_prompt TEXT NOT NULL,
            prompt_length INTEGER,
            theme TEXT,
            domain_classification TEXT,  -- JSON: ['portrait', 'product']
            learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            quality_score REAL,
            complexity TEXT,
            learning_status TEXT DEFAULT 'pending',
            extracted_elements_count INTEGER DEFAULT 0
        )
        """)

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_elements_domain ON elements(domain_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_elements_category ON elements(category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_elements_reusability ON elements(reusability_score DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(tag_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_element_tags_tag ON element_tags(tag_id)")

        self.conn.commit()

        # 初始化7个领域
        self._init_domains()

    def _init_domains(self):
        """初始化7个领域"""
        domains = [
            ("portrait", "人像摄影", "Portrait photography elements"),
            ("interior", "室内设计", "Interior design elements"),
            ("product", "产品摄影", "Product photography elements"),
            ("design", "平面设计", "Graphic design elements"),
            ("art", "艺术风格", "Art style elements"),
            ("video", "视频生成", "Video generation elements"),
            ("common", "通用摄影", "Common photography techniques")
        ]

        cursor = self.conn.cursor()
        for domain_id, name, desc in domains:
            cursor.execute("""
                INSERT OR IGNORE INTO domains (domain_id, name, description)
                VALUES (?, ?, ?)
            """, (domain_id, name, desc))

        self.conn.commit()

    # ========== 核心操作方法 ==========

    def add_element(self,
                   element_id: str,
                   domain_id: str,
                   category_id: str,
                   name: str,
                   ai_prompt_template: str,
                   chinese_name: Optional[str] = None,
                   keywords: Optional[List[str]] = None,
                   tags: Optional[List[str]] = None,
                   reusability_score: Optional[float] = None,
                   source_prompts: Optional[List[int]] = None,
                   learned_from: str = "manual",
                   metadata: Optional[Dict] = None) -> bool:
        """
        添加元素到库中

        Args:
            element_id: 元素ID，如 'portrait_facial_001'
            domain_id: 领域ID，如 'portrait'
            category_id: 类别ID，如 'facial_features'
            name: 元素名称，如 'large_expressive_almond'
            ai_prompt_template: AI提示词模板
            chinese_name: 中文名称
            keywords: 关键词列表
            tags: 标签列表
            reusability_score: 复用性评分 (0-10)
            source_prompts: 来源Prompt ID列表
            learned_from: 学习方式 ('manual' or 'auto_learner')
            metadata: 其他元数据

        Returns:
            bool: 是否添加成功
        """
        cursor = self.conn.cursor()

        try:
            # 确保category存在
            cursor.execute("""
                INSERT OR IGNORE INTO categories (category_id, domain_id, name)
                VALUES (?, ?, ?)
            """, (category_id, domain_id, category_id.replace('_', ' ').title()))

            # 插入元素
            cursor.execute("""
                INSERT INTO elements (
                    element_id, domain_id, category_id, name, chinese_name,
                    ai_prompt_template, keywords, reusability_score,
                    source_prompts, learned_from, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                element_id,
                domain_id,
                category_id,
                name,
                chinese_name,
                ai_prompt_template,
                json.dumps(keywords or [], ensure_ascii=False),
                reusability_score,
                json.dumps(source_prompts or [], ensure_ascii=False),
                learned_from,
                json.dumps(metadata or {}, ensure_ascii=False)
            ))

            # 添加标签
            if tags:
                for tag_name in tags:
                    self._add_tag_to_element(element_id, tag_name)

            # 更新统计
            self._update_counts(domain_id, category_id)

            self.conn.commit()
            return True

        except sqlite3.IntegrityError as e:
            print(f"❌ 添加元素失败: {e}")
            self.conn.rollback()
            return False

    def save_source_prompt(self,
                          prompt_id: int,
                          original_prompt: str,
                          theme: Optional[str] = None,
                          domain_classification: Optional[str] = None,
                          quality_score: Optional[float] = None,
                          complexity: Optional[str] = None,
                          extracted_elements_count: int = 0) -> bool:
        """
        保存学习的源Prompt记录到source_prompts表

        Args:
            prompt_id: Prompt ID
            original_prompt: 原始提示词文本
            theme: 主题
            domain_classification: 领域分类（JSON格式）
            quality_score: 质量评分
            complexity: 复杂度（'simple', 'medium', 'complex'）
            extracted_elements_count: 提取的元素数量

        Returns:
            bool: 是否保存成功
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO source_prompts (
                    prompt_id, original_prompt, prompt_length, theme,
                    domain_classification, quality_score, complexity,
                    learning_status, extracted_elements_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'completed', ?)
            """, (
                prompt_id,
                original_prompt,
                len(original_prompt),
                theme,
                domain_classification,
                quality_score,
                complexity,
                extracted_elements_count
            ))

            self.conn.commit()
            return True

        except sqlite3.IntegrityError as e:
            # Prompt ID已存在，更新记录
            try:
                cursor.execute("""
                    UPDATE source_prompts
                    SET extracted_elements_count = extracted_elements_count + ?,
                        learning_status = 'completed'
                    WHERE prompt_id = ?
                """, (extracted_elements_count, prompt_id))
                self.conn.commit()
                return True
            except Exception as update_error:
                print(f"❌ 更新学习记录失败: {update_error}")
                self.conn.rollback()
                return False

    def _add_tag_to_element(self, element_id: str, tag_name: str):
        """为元素添加标签"""
        cursor = self.conn.cursor()

        # 确保标签存在
        cursor.execute("""
            INSERT OR IGNORE INTO tags (tag_name)
            VALUES (?)
        """, (tag_name,))

        # 获取tag_id
        cursor.execute("SELECT tag_id FROM tags WHERE tag_name = ?", (tag_name,))
        tag_id = cursor.fetchone()[0]

        # 关联元素和标签
        cursor.execute("""
            INSERT OR IGNORE INTO element_tags (element_id, tag_id)
            VALUES (?, ?)
        """, (element_id, tag_id))

        # 更新标签使用计数
        cursor.execute("""
            UPDATE tags SET usage_count = usage_count + 1
            WHERE tag_id = ?
        """, (tag_id,))

    def _update_counts(self, domain_id: str, category_id: str):
        """更新领域和类别的元素计数"""
        cursor = self.conn.cursor()

        # 更新category计数
        cursor.execute("""
            UPDATE categories
            SET total_elements = (
                SELECT COUNT(*) FROM elements WHERE category_id = ?
            )
            WHERE category_id = ?
        """, (category_id, category_id))

        # 更新domain计数
        cursor.execute("""
            UPDATE domains
            SET total_elements = (
                SELECT COUNT(*) FROM elements WHERE domain_id = ?
            )
            WHERE domain_id = ?
        """, (domain_id, domain_id))

    # ========== 查询方法 ==========

    def search_by_tags(self, tags: List[str], require_all: bool = False) -> List[Dict]:
        """
        按标签搜索元素

        Args:
            tags: 标签列表
            require_all: 是否要求包含所有标签（AND逻辑），否则为OR逻辑

        Returns:
            元素列表
        """
        cursor = self.conn.cursor()

        if require_all:
            # AND逻辑：必须包含所有标签
            query = """
                SELECT DISTINCT e.* FROM elements e
                WHERE element_id IN (
                    SELECT element_id FROM element_tags et
                    JOIN tags t ON et.tag_id = t.tag_id
                    WHERE t.tag_name IN ({})
                    GROUP BY element_id
                    HAVING COUNT(DISTINCT t.tag_name) = ?
                )
            """.format(','.join(['?' for _ in tags]))
            cursor.execute(query, tags + [len(tags)])
        else:
            # OR逻辑：包含任意标签
            query = """
                SELECT DISTINCT e.* FROM elements e
                JOIN element_tags et ON e.element_id = et.element_id
                JOIN tags t ON et.tag_id = t.tag_id
                WHERE t.tag_name IN ({})
            """.format(','.join(['?' for _ in tags]))
            cursor.execute(query, tags)

        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def search_by_domain(self,
                        domain_id: str,
                        category_id: Optional[str] = None,
                        min_reusability: Optional[float] = None,
                        limit: Optional[int] = None) -> List[Dict]:
        """
        按领域搜索元素

        Args:
            domain_id: 领域ID
            category_id: 可选的类别ID
            min_reusability: 最小复用性评分
            limit: 限制返回数量

        Returns:
            元素列表
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM elements WHERE domain_id = ?"
        params = [domain_id]

        if category_id:
            query += " AND category_id = ?"
            params.append(category_id)

        if min_reusability is not None:
            query += " AND reusability_score >= ?"
            params.append(min_reusability)

        query += " ORDER BY reusability_score DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_element(self, element_id: str) -> Optional[Dict]:
        """获取单个元素"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM elements WHERE element_id = ?", (element_id,))
        row = cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def get_element_tags(self, element_id: str) -> List[str]:
        """获取元素的所有标签"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT t.tag_name FROM tags t
            JOIN element_tags et ON t.tag_id = et.tag_id
            WHERE et.element_id = ?
        """, (element_id,))
        return [row[0] for row in cursor.fetchall()]

    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """将数据库行转换为字典"""
        if not row:
            return {}

        result = dict(row)

        # 解析JSON字段
        if result.get('keywords'):
            result['keywords'] = json.loads(result['keywords'])
        if result.get('source_prompts'):
            result['source_prompts'] = json.loads(result['source_prompts'])
        if result.get('metadata'):
            result['metadata'] = json.loads(result['metadata'])

        # 添加标签
        result['tags'] = self.get_element_tags(result['element_id'])

        return result

    # ========== 统计方法 ==========

    def get_stats(self) -> Dict:
        """获取库的统计信息"""
        cursor = self.conn.cursor()

        stats = {}

        # 总体统计
        cursor.execute("SELECT COUNT(*) FROM elements")
        stats['total_elements'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tags")
        stats['total_tags'] = cursor.fetchone()[0]

        # 各领域统计
        cursor.execute("""
            SELECT d.domain_id, d.name, d.total_elements
            FROM domains d
            ORDER BY d.total_elements DESC
        """)
        stats['domains'] = [
            {'domain_id': row[0], 'name': row[1], 'total_elements': row[2]}
            for row in cursor.fetchall()
        ]

        # 热门标签
        cursor.execute("""
            SELECT tag_name, usage_count
            FROM tags
            ORDER BY usage_count DESC
            LIMIT 20
        """)
        stats['top_tags'] = [
            {'tag': row[0], 'count': row[1]}
            for row in cursor.fetchall()
        ]

        return stats

    # ========== 导出/导入 JSON ==========

    def export_to_json(self, output_path: str) -> bool:
        """
        导出数据库为JSON格式（用于版本控制）

        Args:
            output_path: 输出JSON文件路径

        Returns:
            是否导出成功
        """
        cursor = self.conn.cursor()

        try:
            library = {
                "library_metadata": {
                    "name": "Universal Elements Library",
                    "version": "1.0",
                    "architecture": "unified",
                    "exported_at": datetime.now().isoformat(),
                    "total_elements": 0,
                    "total_domains": 0
                },
                "domains": {},
                "tag_index": {},
                "source_prompts": []
            }

            # 导出各领域
            cursor.execute("SELECT * FROM domains WHERE total_elements > 0")
            domains_data = cursor.fetchall()

            library["library_metadata"]["total_domains"] = len(domains_data)

            for domain_row in domains_data:
                domain_id = domain_row['domain_id']

                library["domains"][domain_id] = {
                    "domain_metadata": {
                        "name": domain_row['name'],
                        "total_elements": domain_row['total_elements']
                    },
                    "categories": {}
                }

                # 获取该领域的所有类别
                cursor.execute("""
                    SELECT DISTINCT category_id FROM elements
                    WHERE domain_id = ?
                """, (domain_id,))

                for cat_row in cursor.fetchall():
                    category_id = cat_row['category_id']

                    # 获取该类别的所有元素
                    cursor.execute("""
                        SELECT * FROM elements
                        WHERE domain_id = ? AND category_id = ?
                    """, (domain_id, category_id))

                    category_elements = {}
                    for elem_row in cursor.fetchall():
                        element = self._row_to_dict(elem_row)
                        category_elements[element['name']] = element
                        library["library_metadata"]["total_elements"] += 1

                    if category_elements:
                        library["domains"][domain_id]["categories"][category_id] = category_elements

            # 导出标签索引
            cursor.execute("SELECT tag_name, tag_id FROM tags")
            for tag_row in cursor.fetchall():
                tag_name = tag_row['tag_name']
                tag_id = tag_row['tag_id']

                cursor.execute("""
                    SELECT element_id FROM element_tags WHERE tag_id = ?
                """, (tag_id,))

                library["tag_index"][tag_name] = [row[0] for row in cursor.fetchall()]

            # 导出来源Prompts
            cursor.execute("SELECT * FROM source_prompts")
            for prompt_row in cursor.fetchall():
                library["source_prompts"].append(dict(prompt_row))

            # 写入文件
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(library, f, indent=2, ensure_ascii=False)

            print(f"✅ 导出完成: {output_path}")
            print(f"   - {library['library_metadata']['total_elements']} 个元素")
            print(f"   - {library['library_metadata']['total_domains']} 个领域")
            print(f"   - {len(library['tag_index'])} 个标签")

            return True

        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return False

    def import_from_json(self, json_path: str, clear_existing: bool = False) -> bool:
        """
        从JSON导入到数据库

        Args:
            json_path: JSON文件路径
            clear_existing: 是否清空现有数据

        Returns:
            是否导入成功
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                library = json.load(f)

            if clear_existing:
                self._clear_all_data()

            imported_count = 0

            # 导入各领域的元素
            for domain_id, domain_data in library.get("domains", {}).items():
                for category_id, category_elements in domain_data.get("categories", {}).items():
                    for element_name, element in category_elements.items():
                        if self.add_element(
                            element_id=element.get('element_id', f"{domain_id}_{category_id}_{imported_count:03d}"),
                            domain_id=domain_id,
                            category_id=category_id,
                            name=element.get('name', element_name),
                            chinese_name=element.get('chinese_name'),
                            ai_prompt_template=element.get('ai_prompt_template', ''),
                            keywords=element.get('keywords', []),
                            tags=element.get('tags', []),
                            reusability_score=element.get('reusability_score'),
                            source_prompts=element.get('source_prompts', []),
                            learned_from=element.get('learned_from', 'imported'),
                            metadata=element.get('metadata')
                        ):
                            imported_count += 1

            print(f"✅ 导入完成: {imported_count} 个元素")
            return True

        except Exception as e:
            print(f"❌ 导入失败: {e}")
            return False

    def _clear_all_data(self):
        """清空所有数据（保留表结构）"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM element_tags")
        cursor.execute("DELETE FROM elements")
        cursor.execute("DELETE FROM tags")
        cursor.execute("DELETE FROM categories")
        cursor.execute("DELETE FROM source_prompts")
        cursor.execute("UPDATE domains SET total_elements = 0")
        self.conn.commit()

    def close(self):
        """关闭数据库连接"""
        self.conn.close()


# ========== 使用示例 ==========
if __name__ == "__main__":
    # 创建数据库
    db = ElementDB('extracted_results/elements.db')

    print("=" * 60)
    print("Universal Elements Library - Database Test")
    print("=" * 60)

    # 测试添加元素
    print("\n1. 添加测试元素...")
    db.add_element(
        element_id='product_type_001',
        domain_id='product',
        category_id='product_types',
        name='collector_edition_book',
        chinese_name='收藏版书籍',
        ai_prompt_template='premium collector\'s edition book, luxury binding, Italian calfskin cover',
        keywords=['collector\'s edition', 'premium book', 'luxury binding'],
        tags=['product', 'book', 'luxury', 'collectible'],
        reusability_score=7.5,
        source_prompts=[1]
    )

    db.add_element(
        element_id='design_layout_001',
        domain_id='design',
        category_id='layout_systems',
        name='bento_grid',
        chinese_name='Bento网格布局',
        ai_prompt_template='modern Bento grid layout, modular card-based design, asymmetric arrangement',
        keywords=['bento grid', 'modular', 'card-based'],
        tags=['layout', 'grid', 'modern', 'ui'],
        reusability_score=8.5,
        source_prompts=[2]
    )

    print("✅ 元素已添加")

    # 测试搜索
    print("\n2. 按标签搜索 ['luxury']...")
    results = db.search_by_tags(['luxury'])
    for elem in results:
        print(f"   - {elem['element_id']}: {elem['chinese_name']}")

    print("\n3. 按领域搜索 [product]...")
    results = db.search_by_domain('product')
    for elem in results:
        print(f"   - {elem['element_id']}: {elem['name']} (复用性: {elem['reusability_score']})")

    # 统计
    print("\n4. 库统计信息:")
    stats = db.get_stats()
    print(f"   总元素数: {stats['total_elements']}")
    print(f"   总标签数: {stats['total_tags']}")
    print(f"\n   各领域:")
    for domain in stats['domains']:
        if domain['total_elements'] > 0:
            print(f"   - {domain['name']}: {domain['total_elements']} 个元素")

    # 导出
    print("\n5. 导出为JSON...")
    db.export_to_json('extracted_results/universal_elements_export.json')

    db.close()
    print("\n✅ 数据库测试完成")
