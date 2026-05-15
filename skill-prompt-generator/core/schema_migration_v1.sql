-- Schema Migration v1: Add Variable Support
-- 添加元素变量化支持

-- 1. 创建 element_variables 表
CREATE TABLE IF NOT EXISTS element_variables (
    variable_id TEXT PRIMARY KEY,
    element_id TEXT NOT NULL,
    parameter_name TEXT NOT NULL,  -- 参数名（如：color, intensity, style）
    parameter_type TEXT NOT NULL CHECK(parameter_type IN ('enum', 'range', 'boolean')),
    possible_values TEXT,  -- JSON数组（enum类型的可选值，或range类型的[min, max]）
    default_value TEXT,
    description TEXT,  -- 参数描述
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (element_id) REFERENCES elements(element_id) ON DELETE CASCADE
);

-- 2. 创建索引
CREATE INDEX IF NOT EXISTS idx_element_variables_element ON element_variables(element_id);
CREATE INDEX IF NOT EXISTS idx_element_variables_param ON element_variables(parameter_name);

-- 3. 创建 design_variables 表（从YAML导入的设计变量）
CREATE TABLE IF NOT EXISTS design_variables (
    variable_id TEXT PRIMARY KEY,
    style_name TEXT NOT NULL,        -- 温馨可爱、现代简约
    variable_type TEXT NOT NULL,     -- colors、borders、decorations
    variable_name TEXT NOT NULL,     -- 珊瑚粉色系、圆角边框
    variable_data TEXT NOT NULL,     -- JSON数据
    priority INTEGER DEFAULT 5,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 创建索引
CREATE INDEX IF NOT EXISTS idx_design_variables_style ON design_variables(style_name);
CREATE INDEX IF NOT EXISTS idx_design_variables_type ON design_variables(variable_type);

-- 5. 插入示例数据（element_variables）
INSERT OR IGNORE INTO element_variables VALUES
  ('var_001', 'common_lighting_001', 'intensity', 'enum',
   '["soft", "medium", "dramatic", "harsh"]', 'medium',
   'Light intensity level', CURRENT_TIMESTAMP),

  ('var_002', 'common_lighting_001', 'color_temp', 'range',
   '[2700, 6500]', '5000',
   'Color temperature in Kelvin', CURRENT_TIMESTAMP),

  ('var_003', 'portrait_makeup_003', 'style', 'enum',
   '["natural", "glamorous", "editorial", "avant-garde"]', 'natural',
   'Makeup style variation', CURRENT_TIMESTAMP),

  ('var_004', 'art_special_effects_001', 'opacity', 'range',
   '[0.0, 1.0]', '0.7',
   'Effect opacity level', CURRENT_TIMESTAMP),

  ('var_005', 'video_motion_effects_001', 'speed', 'enum',
   '["slow", "normal", "fast", "very_fast"]', 'normal',
   'Motion speed variation', CURRENT_TIMESTAMP);

-- 6. 插入示例数据（design_variables - 从prompt-crafter导入示例）
INSERT OR IGNORE INTO design_variables VALUES
  ('design_001', '温馨可爱', 'colors', '珊瑚粉色系',
   '{"base_hue": 355, "variants": [{"hex": "#FF9AA2", "name": "蜜桃粉"}]}',
   1, '温暖的珊瑚粉色系', CURRENT_TIMESTAMP),

  ('design_002', '温馨可爱', 'borders', '大圆角',
   '{"radius": "24px", "shadow": "soft"}',
   1, '柔和的大圆角边框', CURRENT_TIMESTAMP),

  ('design_003', '现代简约', 'colors', '深蓝色系',
   '{"base_hue": 215, "variants": [{"hex": "#1F2937", "name": "深炭蓝"}]}',
   1, '现代感的深蓝色系', CURRENT_TIMESTAMP),

  ('design_004', '现代简约', 'borders', '直角边框',
   '{"radius": "0px", "shadow": "none"}',
   1, '简洁的直角边框', CURRENT_TIMESTAMP);
