-- RLVR (Reinforcement Learning with Verifiable Rewards) Database Schema
-- Version: 1.0.0
-- Created: 2025-11-20

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- AGENTS TABLE (Base table - should already exist)
-- ============================================================================
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,  -- e.g., 'code-reviewer', 'deployment-assistant'
    model_provider VARCHAR(50),  -- 'anthropic', 'openai', 'local'
    model_name VARCHAR(100),     -- 'claude-3-sonnet-20240229'
    base_prompt TEXT,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);
CREATE INDEX IF NOT EXISTS idx_agents_active ON agents(is_active);

-- ============================================================================
-- AGENT EXECUTIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    agent_version INTEGER NOT NULL,

    -- Input/Output
    input_prompt TEXT NOT NULL,
    output_completion TEXT,

    -- Execution Metrics
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),

    -- Status
    status VARCHAR(50) NOT NULL,  -- 'success', 'error', 'timeout'
    error_message TEXT,

    -- Context
    user_id UUID,
    session_id UUID,
    request_id UUID,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_executions_agent ON agent_executions(agent_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON agent_executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_created ON agent_executions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_executions_user ON agent_executions(user_id);

-- ============================================================================
-- REWARD SCORES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS reward_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES agent_executions(id) ON DELETE CASCADE,

    -- Reward Components (all in range 0.0000 to 1.0000)
    reward_score DECIMAL(5, 4) NOT NULL CHECK (reward_score >= 0 AND reward_score <= 1),
    user_feedback_score DECIMAL(5, 4) CHECK (user_feedback_score >= 0 AND user_feedback_score <= 1),
    objective_score DECIMAL(5, 4) CHECK (objective_score >= 0 AND objective_score <= 1),
    business_score DECIMAL(5, 4) CHECK (business_score >= 0 AND business_score <= 1),
    automated_score DECIMAL(5, 4) CHECK (automated_score >= 0 AND automated_score <= 1),

    -- Verification Details
    verification_method VARCHAR(100) NOT NULL,  -- 'user_feedback', 'test_execution', etc.
    verification_confidence DECIMAL(5, 4) CHECK (verification_confidence >= 0 AND verification_confidence <= 1),

    -- User Feedback
    user_feedback TEXT,
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),

    -- Business Impact
    revenue_impact_usd DECIMAL(10, 2),
    conversion_impact DECIMAL(5, 4),

    -- Metadata
    verified_at TIMESTAMP DEFAULT NOW(),
    verified_by_user_id UUID
);

CREATE INDEX IF NOT EXISTS idx_rewards_execution ON reward_scores(execution_id);
CREATE INDEX IF NOT EXISTS idx_rewards_score ON reward_scores(reward_score DESC);
CREATE INDEX IF NOT EXISTS idx_rewards_verified ON reward_scores(verified_at DESC);
CREATE INDEX IF NOT EXISTS idx_rewards_method ON reward_scores(verification_method);

-- ============================================================================
-- TRAINING EXAMPLES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS training_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    execution_id UUID REFERENCES agent_executions(id) ON DELETE SET NULL,

    -- Training Data
    prompt TEXT NOT NULL,
    completion TEXT NOT NULL,
    reward_score DECIMAL(5, 4) NOT NULL,

    -- Classification
    example_type VARCHAR(50) CHECK (example_type IN ('positive', 'negative', 'neutral')),
    is_synthetic BOOLEAN DEFAULT FALSE,

    -- Quality Control
    is_validated BOOLEAN DEFAULT FALSE,
    validation_notes TEXT,

    -- Training Status
    used_in_training BOOLEAN DEFAULT FALSE,
    training_run_id UUID,

    created_at TIMESTAMP DEFAULT NOW(),

    -- Ensure unique execution_id per training example
    CONSTRAINT unique_execution_training UNIQUE (execution_id)
);

CREATE INDEX IF NOT EXISTS idx_training_agent ON training_examples(agent_id);
CREATE INDEX IF NOT EXISTS idx_training_reward ON training_examples(reward_score DESC);
CREATE INDEX IF NOT EXISTS idx_training_type ON training_examples(example_type);
CREATE INDEX IF NOT EXISTS idx_training_used ON training_examples(used_in_training);
CREATE INDEX IF NOT EXISTS idx_training_validated ON training_examples(is_validated);

-- ============================================================================
-- FINE-TUNING RUNS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS fine_tuning_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,

    -- Training Configuration
    base_model VARCHAR(100) NOT NULL,
    training_examples_count INTEGER NOT NULL,
    epochs INTEGER,
    learning_rate DECIMAL(10, 8),

    -- Provider-Specific
    provider VARCHAR(50) NOT NULL CHECK (provider IN ('openai', 'anthropic', 'local')),
    provider_job_id VARCHAR(255),   -- External fine-tuning job ID

    -- Status
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),

    -- Results
    trained_model_id VARCHAR(255),
    validation_loss DECIMAL(10, 6),
    validation_accuracy DECIMAL(5, 4),

    -- Metrics
    cost_usd DECIMAL(10, 2),
    training_time_seconds INTEGER,

    -- Deployment
    deployed_at TIMESTAMP,
    deployed_version INTEGER,

    -- Timestamps
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_finetuning_agent ON fine_tuning_runs(agent_id);
CREATE INDEX IF NOT EXISTS idx_finetuning_status ON fine_tuning_runs(status);
CREATE INDEX IF NOT EXISTS idx_finetuning_created ON fine_tuning_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_finetuning_provider ON fine_tuning_runs(provider);

-- ============================================================================
-- COMPOSITE VIEWS FOR ANALYTICS
-- ============================================================================

-- View: Agent Performance Over Time
CREATE OR REPLACE VIEW agent_performance_stats AS
SELECT
    a.id as agent_id,
    a.name as agent_name,
    a.type as agent_type,
    DATE(e.created_at) as date,
    COUNT(DISTINCT e.id) as total_executions,
    AVG(r.reward_score) as avg_reward_score,
    STDDEV(r.reward_score) as reward_std_dev,
    SUM(CASE WHEN r.reward_score >= 0.7 THEN 1 ELSE 0 END) as high_reward_count,
    SUM(CASE WHEN r.reward_score <= 0.3 THEN 1 ELSE 0 END) as low_reward_count,
    AVG(e.execution_time_ms) as avg_execution_time_ms,
    SUM(e.cost_usd) as total_cost_usd
FROM agents a
LEFT JOIN agent_executions e ON a.id = e.agent_id
LEFT JOIN reward_scores r ON e.id = r.execution_id
WHERE e.status = 'success'
GROUP BY a.id, a.name, a.type, DATE(e.created_at);

-- View: Training Data Readiness
CREATE OR REPLACE VIEW training_data_readiness AS
SELECT
    a.id as agent_id,
    a.name as agent_name,
    a.type as agent_type,
    COUNT(CASE WHEN t.example_type = 'positive' THEN 1 END) as positive_examples,
    COUNT(CASE WHEN t.example_type = 'negative' THEN 1 END) as negative_examples,
    COUNT(CASE WHEN t.example_type = 'neutral' THEN 1 END) as neutral_examples,
    COUNT(*) as total_examples,
    AVG(t.reward_score) as avg_reward_score,
    MAX(t.created_at) as last_example_created,
    COUNT(*) >= 100 as ready_for_training
FROM agents a
LEFT JOIN training_examples t ON a.id = t.agent_id
WHERE t.is_validated = TRUE
GROUP BY a.id, a.name, a.type;

-- View: Fine-Tuning History
CREATE OR REPLACE VIEW fine_tuning_history AS
SELECT
    f.id as run_id,
    f.agent_id,
    a.name as agent_name,
    f.provider,
    f.base_model,
    f.status,
    f.progress_percentage,
    f.training_examples_count,
    f.trained_model_id,
    f.cost_usd,
    f.started_at,
    f.completed_at,
    EXTRACT(EPOCH FROM (f.completed_at - f.started_at)) as duration_seconds,
    f.deployed_at,
    f.deployed_version
FROM fine_tuning_runs f
INNER JOIN agents a ON f.agent_id = a.id
ORDER BY f.created_at DESC;

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function: Update agent version after fine-tuning
CREATE OR REPLACE FUNCTION update_agent_version()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        UPDATE agents
        SET version = version + 1,
            updated_at = NOW()
        WHERE id = NEW.agent_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-increment agent version on successful fine-tuning
CREATE TRIGGER trigger_update_agent_version
AFTER UPDATE ON fine_tuning_runs
FOR EACH ROW
WHEN (NEW.status = 'completed')
EXECUTE FUNCTION update_agent_version();

-- Function: Mark training examples as used
CREATE OR REPLACE FUNCTION mark_training_examples_used()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'running' THEN
        UPDATE training_examples
        SET used_in_training = TRUE,
            training_run_id = NEW.id
        WHERE agent_id = NEW.agent_id
            AND used_in_training = FALSE
            AND is_validated = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Mark training examples as used when training starts
CREATE TRIGGER trigger_mark_training_examples
AFTER INSERT OR UPDATE ON fine_tuning_runs
FOR EACH ROW
WHEN (NEW.status = 'running')
EXECUTE FUNCTION mark_training_examples_used();

-- ============================================================================
-- INITIAL DATA (Optional - Example Agent)
-- ============================================================================

-- Insert example agent if not exists
INSERT INTO agents (name, type, model_provider, model_name, base_prompt, version, is_active)
VALUES (
    'Code Review Assistant',
    'code-reviewer',
    'anthropic',
    'claude-3-sonnet-20240229',
    'You are an expert code reviewer. Review code for quality, security, and best practices.',
    1,
    TRUE
)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- GRANTS (adjust based on your user setup)
-- ============================================================================

-- Grant permissions (assuming user 'devskyy')
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO devskyy;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO devskyy;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO devskyy;

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE agent_executions IS 'Records all agent executions with inputs, outputs, and metrics';
COMMENT ON TABLE reward_scores IS 'Verified reward scores for agent executions from multiple sources';
COMMENT ON TABLE training_examples IS 'Curated training examples for fine-tuning agents';
COMMENT ON TABLE fine_tuning_runs IS 'Fine-tuning job tracking and results';

COMMENT ON COLUMN reward_scores.verification_confidence IS 'Confidence level (0-1) in the reward score';
COMMENT ON COLUMN training_examples.is_synthetic IS 'Whether example was synthetically generated vs real execution';
COMMENT ON COLUMN fine_tuning_runs.provider_job_id IS 'External job ID from OpenAI, Anthropic, etc.';
