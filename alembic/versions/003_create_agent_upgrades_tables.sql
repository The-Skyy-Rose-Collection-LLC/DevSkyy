-- Agent Upgrades Tracking Schema
-- Version: 1.0.0
-- Created: 2025-11-20

-- ============================================================================
-- AGENT UPGRADES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_upgrades (
    upgrade_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type VARCHAR(100) NOT NULL,
    upgrade_name VARCHAR(255) NOT NULL,
    upgrade_description TEXT,

    -- Deployment tracking
    deployed_by UUID,  -- User who deployed
    deployed_at TIMESTAMP DEFAULT NOW(),
    promoted_at TIMESTAMP,
    rolled_back_at TIMESTAMP,

    -- Status tracking
    status VARCHAR(50) NOT NULL CHECK (status IN ('ab_testing', 'deployed', 'production', 'rolled_back')),

    -- Verification requirements
    verification_methods TEXT,  -- Comma-separated list
    expected_improvement DECIMAL(5, 4),  -- Expected improvement (e.g., 0.25 = 25%)

    -- Results
    final_score DECIMAL(5, 4),

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_upgrades_agent_type ON agent_upgrades(agent_type);
CREATE INDEX IF NOT EXISTS idx_upgrades_status ON agent_upgrades(status);
CREATE INDEX IF NOT EXISTS idx_upgrades_deployed ON agent_upgrades(deployed_at DESC);

-- ============================================================================
-- A/B TESTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS ab_tests (
    ab_test_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upgrade_id UUID NOT NULL REFERENCES agent_upgrades(upgrade_id) ON DELETE CASCADE,
    agent_type VARCHAR(100) NOT NULL,

    -- Test variants
    variant_a VARCHAR(100) NOT NULL,  -- e.g., 'baseline'
    variant_b VARCHAR(100) NOT NULL,  -- e.g., 'upgraded'

    -- Test parameters
    traffic_split DECIMAL(3, 2) DEFAULT 0.50,  -- 50/50 split
    min_sample_size INTEGER DEFAULT 100,

    -- Status
    status VARCHAR(50) NOT NULL CHECK (status IN ('running', 'completed', 'cancelled')),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    -- Results
    variant_a_score DECIMAL(5, 4),
    variant_b_score DECIMAL(5, 4),
    variant_a_count INTEGER DEFAULT 0,
    variant_b_count INTEGER DEFAULT 0,
    winner VARCHAR(100),  -- 'variant_a', 'variant_b', or 'no_difference'
    confidence_level DECIMAL(5, 4),  -- Statistical confidence (0-1)

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_abtests_upgrade ON ab_tests(upgrade_id);
CREATE INDEX IF NOT EXISTS idx_abtests_status ON ab_tests(status);
CREATE INDEX IF NOT EXISTS idx_abtests_started ON ab_tests(started_at DESC);

-- ============================================================================
-- UPGRADE VERIFICATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS upgrade_verifications (
    verification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upgrade_id UUID NOT NULL REFERENCES agent_upgrades(upgrade_id) ON DELETE CASCADE,
    execution_id UUID REFERENCES agent_executions(id) ON DELETE SET NULL,

    -- Verification details
    verification_method VARCHAR(100) NOT NULL,
    verification_score DECIMAL(5, 4) NOT NULL,
    verification_data JSONB,

    -- Metadata
    verified_by UUID,
    verified_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verifications_upgrade ON upgrade_verifications(upgrade_id);
CREATE INDEX IF NOT EXISTS idx_verifications_execution ON upgrade_verifications(execution_id);
CREATE INDEX IF NOT EXISTS idx_verifications_method ON upgrade_verifications(verification_method);

-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- View: Upgrade Performance Summary
CREATE OR REPLACE VIEW upgrade_performance_summary AS
SELECT
    u.upgrade_id,
    u.agent_type,
    u.upgrade_name,
    u.status,
    u.deployed_at,
    u.expected_improvement,
    u.final_score,
    COUNT(v.verification_id) as total_verifications,
    AVG(v.verification_score) as avg_verification_score,
    ARRAY_AGG(DISTINCT v.verification_method) as verification_methods_used,
    CASE
        WHEN u.final_score IS NOT NULL AND u.final_score >= (0.7 + u.expected_improvement) THEN 'success'
        WHEN u.final_score IS NOT NULL AND u.final_score < (0.7 + u.expected_improvement) THEN 'underperformed'
        ELSE 'in_progress'
    END as performance_status
FROM agent_upgrades u
LEFT JOIN upgrade_verifications v ON u.upgrade_id = v.upgrade_id
GROUP BY u.upgrade_id, u.agent_type, u.upgrade_name, u.status, u.deployed_at, u.expected_improvement, u.final_score;

-- View: A/B Test Results Summary
CREATE OR REPLACE VIEW ab_test_results AS
SELECT
    t.ab_test_id,
    t.upgrade_id,
    u.agent_type,
    u.upgrade_name,
    t.variant_a,
    t.variant_b,
    t.variant_a_score,
    t.variant_b_score,
    t.variant_a_count,
    t.variant_b_count,
    t.winner,
    t.confidence_level,
    t.status,
    t.started_at,
    t.completed_at,
    EXTRACT(EPOCH FROM (t.completed_at - t.started_at)) / 3600 as duration_hours,
    CASE
        WHEN t.variant_b_score > t.variant_a_score
        THEN ((t.variant_b_score - t.variant_a_score) / t.variant_a_score) * 100
        ELSE 0
    END as improvement_percentage
FROM ab_tests t
INNER JOIN agent_upgrades u ON t.upgrade_id = u.upgrade_id;

-- View: Agent Upgrade History
CREATE OR REPLACE VIEW agent_upgrade_history AS
SELECT
    a.id as agent_id,
    a.name as agent_name,
    a.type as agent_type,
    u.upgrade_id,
    u.upgrade_name,
    u.status,
    u.deployed_at,
    u.final_score,
    u.expected_improvement,
    u.promoted_at,
    u.rolled_back_at,
    CASE
        WHEN u.status = 'production' THEN 'active'
        WHEN u.status = 'rolled_back' THEN 'reverted'
        ELSE 'testing'
    END as upgrade_status
FROM agents a
INNER JOIN agent_upgrades u ON a.type = u.agent_type
ORDER BY u.deployed_at DESC;

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function: Complete A/B test when sample size reached
CREATE OR REPLACE FUNCTION check_ab_test_completion()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.variant_a_count >= NEW.min_sample_size
       AND NEW.variant_b_count >= NEW.min_sample_size
       AND NEW.status = 'running' THEN

        -- Determine winner (simple comparison, can be enhanced with statistical tests)
        IF ABS(NEW.variant_b_score - NEW.variant_a_score) < 0.02 THEN
            NEW.winner = 'no_difference';
            NEW.confidence_level = 0.5;
        ELSIF NEW.variant_b_score > NEW.variant_a_score THEN
            NEW.winner = 'variant_b';
            NEW.confidence_level = 0.95;  -- Simplified, should use proper statistical test
        ELSE
            NEW.winner = 'variant_a';
            NEW.confidence_level = 0.95;
        END IF;

        NEW.status = 'completed';
        NEW.completed_at = NOW();
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-complete A/B tests
CREATE TRIGGER trigger_check_ab_test_completion
BEFORE UPDATE ON ab_tests
FOR EACH ROW
EXECUTE FUNCTION check_ab_test_completion();

-- Function: Record verification in upgrade_verifications
CREATE OR REPLACE FUNCTION record_upgrade_verification()
RETURNS TRIGGER AS $$
DECLARE
    v_upgrade_id UUID;
BEGIN
    -- Check if this execution is related to an upgrade
    SELECT upgrade_id INTO v_upgrade_id
    FROM agent_upgrades
    WHERE agent_type = (
        SELECT type FROM agents WHERE id = NEW.agent_id
    )
    AND status IN ('ab_testing', 'deployed')
    LIMIT 1;

    IF v_upgrade_id IS NOT NULL THEN
        -- Create verification record
        INSERT INTO upgrade_verifications (
            upgrade_id,
            execution_id,
            verification_method,
            verification_score,
            verified_at
        ) VALUES (
            v_upgrade_id,
            NEW.execution_id,
            NEW.verification_method,
            NEW.reward_score,
            NEW.verified_at
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-record verifications
CREATE TRIGGER trigger_record_upgrade_verification
AFTER INSERT ON reward_scores
FOR EACH ROW
EXECUTE FUNCTION record_upgrade_verification();

-- ============================================================================
-- INITIAL DATA (Example Upgrade)
-- ============================================================================

-- Insert example upgrade deployment
INSERT INTO agent_upgrades (
    upgrade_id,
    agent_type,
    upgrade_name,
    upgrade_description,
    deployed_by,
    status,
    verification_methods,
    expected_improvement
) VALUES (
    gen_random_uuid(),
    'scanner',
    'Real-Time Code Quality Scoring',
    'ML-powered real-time code quality analysis with prioritized recommendations',
    NULL,  -- System deployment
    'deployed',
    'code_analysis,test_execution,user_feedback',
    0.25
) ON CONFLICT DO NOTHING;

-- ============================================================================
-- GRANTS (adjust based on your user setup)
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO devskyy;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO devskyy;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO devskyy;

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE agent_upgrades IS 'Tracks agent upgrade deployments and their verification status';
COMMENT ON TABLE ab_tests IS 'A/B testing framework for gradual upgrade rollout';
COMMENT ON TABLE upgrade_verifications IS 'Individual verification results for upgrade deployments';

COMMENT ON COLUMN agent_upgrades.expected_improvement IS 'Expected performance improvement (0.25 = 25% improvement)';
COMMENT ON COLUMN ab_tests.traffic_split IS 'Traffic allocation to variant B (0.5 = 50% of traffic)';
COMMENT ON COLUMN ab_tests.confidence_level IS 'Statistical confidence in winner determination (0-1)';
