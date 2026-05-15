# 跨Domain提示词生成系统 v2.0

> 智能提示词生成系统 - 支持人像、跨domain场景、专业设计三种模式

---

## 🚀 快速开始

### 基础使用

```python
from core.cross_domain_generator import CrossDomainGenerator

# 创建生成器
generator = CrossDomainGenerator()

# 生成提示词（自动识别类型）
result = generator.generate("龙珠悟空打出龟派气功的蜡像3D感")

print(result['prompt'])  # 完整提示词
print(result['type'])    # 类型：portrait/cross_domain/design

generator.close()
```

---

## 📊 三种生成模式

### 1. Portrait（人像）

```python
result = generator.generate("生成一个年轻女性肖像")
# 类型: portrait
# 使用: portrait domain (502个元素)
```

### 2. Cross-Domain（跨域）

```python
result = generator.generate("龙珠悟空打出龟派气功的蜡像3D感")
# 类型: cross_domain
# 使用: portrait + video + art + common (4个domain)
```

### 3. Design（设计）

```python
result = generator.generate("温馨可爱风格的儿童教育海报")
# 类型: design
# 使用: SQLite元素 + YAML变量（配色、边框、装饰）
```

---

## 📁 项目结构

```
skill-prompt-generator/
├── core/                           # 核心模块
│   ├── cross_domain_generator.py   # 统一接口 ⭐
│   ├── cross_domain_query.py       # 跨domain查询引擎
│   ├── design_bridge.py            # 设计变量桥接器
│   ├── variable_sampler.py         # SQLite变量采样器
│   ├── yaml_sampler.py             # YAML变量采样器
│   ├── framework_loader.py         # 框架加载器（原有）
│   └── schema_migration_v1.sql     # Schema升级脚本
│
├── extracted_results/
│   └── elements.db                 # 元素数据库（1,246个元素）
│
├── variables/                      # YAML变量（从prompt-crafter复制）
│   ├── colors.yaml                 # 配色方案（37种）
│   ├── borders.yaml                # 边框样式
│   └── decorations.yaml            # 装饰元素
│
├── design-logic/                   # 设计逻辑
│   ├── warm-cute/                  # 温馨可爱风格
│   └── modern-minimal/             # 现代简约风格
│
├── intelligent_generator.py        # 智能生成器（原有，向后兼容）
├── framework_loader.py             # 框架加载器（原有）
├── UPGRADE_GUIDE_v2.0.md           # 升级指南
└── README_v2.0.md                  # 本文档
```

---

## 🔧 安装和初始化

### 1. Schema升级

```bash
# 扩展数据库，添加变量表
sqlite3 extracted_results/elements.db < core/schema_migration_v1.sql
```

### 2. 依赖检查

```bash
python3 -c "import yaml; print('✅ PyYAML installed')"
```

如果未安装：
```bash
pip install pyyaml
```

---

## 🧪 测试

### 运行全部测试

```bash
# 测试变量采样器
python3 core/variable_sampler.py

# 测试跨domain查询
python3 core/cross_domain_query.py

# 测试YAML采样器
python3 core/yaml_sampler.py

# 测试设计桥接器
python3 core/design_bridge.py

# 测试统一接口
python3 core/cross_domain_generator.py
```

---

## 📈 性能提升

| 指标 | v1.0 | v2.0 | 提升 |
|-----|------|------|------|
| SQLite利用率 | 40.2% | 80%+ | **2倍** |
| 可用组合数 | ~1,000 | ~10万+ | **100倍** |
| 功能范围 | 人像 | 人像+跨域+设计 | **3倍** |

---

## 🎯 使用建议

### 推荐使用场景

| 场景 | 推荐类型 | 示例 |
|------|---------|------|
| 纯人像摄影 | portrait | "电影级亚洲女性" |
| 复杂动作场景 | cross_domain | "悟空打龟派气功" |
| 海报/卡片设计 | design | "温馨可爱儿童海报" |

### API选择

- **新项目**：使用 `CrossDomainGenerator`（统一接口）
- **现有项目**：可选升级，无需强制
- **简单需求**：继续使用 `IntelligentGenerator`（向后兼容）

---

## ✅ 向后兼容

v1.0的所有功能完全保留：

```python
# v1.0方式（仍然有效）
from intelligent_generator import IntelligentGenerator
gen = IntelligentGenerator()
elements = gen.select_elements_by_intent(intent)
prompt = gen.compose_prompt(elements)
```

---

## 📚 文档

- **升级指南**：`UPGRADE_GUIDE_v2.0.md`
- **设计文档**：`/tmp/fusion_design.md`
- **架构分析**：`/tmp/domain_architecture_analysis.md`
- **对比分析**：`/tmp/sqlite_vs_yaml_comparison.md`

---

## 🎊 核心特性

✅ **跨Domain智能查询** - 自动识别需要的domain并组合
✅ **设计系统集成** - 20万+配色组合
✅ **变量采样** - 智能避免重复
✅ **统一接口** - 一个API处理所有类型
✅ **100%向后兼容** - 老代码无需修改

---

*系统版本: v2.0*
*更新日期: 2026-01-13*
