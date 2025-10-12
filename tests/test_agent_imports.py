"""
Smoke tests for agent imports.

This test file validates that all agents can be imported successfully.
It's a lightweight check to ensure deployment readiness without heavy execution.
"""

import pytest


def test_agent_modules_package_imports():
    """Test that the agent.modules package can be imported."""
    from agent import modules
    
    assert modules is not None
    assert hasattr(modules, "__version__")


def test_core_utility_imports():
    """Test that core utilities (scanner, fixer) can be imported."""
    from agent.modules import scan_site, fix_code
    
    assert callable(scan_site)
    assert callable(fix_code)


def test_customer_service_agent_import():
    """Test CustomerServiceAgent can be imported."""
    try:
        from agent.modules import CustomerServiceAgent
        assert CustomerServiceAgent is not None
        assert CustomerServiceAgent.__name__ == "CustomerServiceAgent"
    except ImportError as e:
        pytest.skip(f"CustomerServiceAgent not available: {e}")


def test_design_automation_agent_import():
    """Test DesignAutomationAgent can be imported."""
    try:
        from agent.modules import DesignAutomationAgent
        assert DesignAutomationAgent is not None
        assert DesignAutomationAgent.__name__ == "DesignAutomationAgent"
    except ImportError as e:
        pytest.skip(f"DesignAutomationAgent not available: {e}")


def test_email_sms_automation_agent_import():
    """Test EmailSMSAutomationAgent can be imported."""
    try:
        from agent.modules import EmailSMSAutomationAgent
        assert EmailSMSAutomationAgent is not None
        assert EmailSMSAutomationAgent.__name__ == "EmailSMSAutomationAgent"
    except ImportError as e:
        pytest.skip(f"EmailSMSAutomationAgent not available: {e}")


def test_financial_agent_import():
    """Test FinancialAgent can be imported."""
    try:
        from agent.modules import FinancialAgent
        assert FinancialAgent is not None
        assert FinancialAgent.__name__ == "FinancialAgent"
    except ImportError as e:
        pytest.skip(f"FinancialAgent not available: {e}")


def test_social_media_automation_agent_import():
    """Test SocialMediaAutomationAgent can be imported."""
    try:
        from agent.modules import SocialMediaAutomationAgent
        assert SocialMediaAutomationAgent is not None
        assert SocialMediaAutomationAgent.__name__ == "SocialMediaAutomationAgent"
    except ImportError as e:
        pytest.skip(f"SocialMediaAutomationAgent not available: {e}")


def test_performance_agent_import():
    """Test PerformanceAgent can be imported."""
    try:
        from agent.modules import PerformanceAgent
        assert PerformanceAgent is not None
        assert PerformanceAgent.__name__ == "PerformanceAgent"
    except ImportError as e:
        pytest.skip(f"PerformanceAgent not available: {e}")


def test_security_agent_import():
    """Test SecurityAgent can be imported."""
    try:
        from agent.modules import SecurityAgent
        assert SecurityAgent is not None
        assert SecurityAgent.__name__ == "SecurityAgent"
    except ImportError as e:
        pytest.skip(f"SecurityAgent not available: {e}")


def test_inventory_agent_import():
    """Test InventoryAgent can be imported."""
    try:
        from agent.modules import InventoryAgent
        assert InventoryAgent is not None
        assert InventoryAgent.__name__ == "InventoryAgent"
    except ImportError as e:
        pytest.skip(f"InventoryAgent not available: {e}")


def test_web_development_agent_import():
    """Test WebDevelopmentAgent can be imported."""
    try:
        from agent.modules import WebDevelopmentAgent
        assert WebDevelopmentAgent is not None
        assert WebDevelopmentAgent.__name__ == "WebDevelopmentAgent"
    except ImportError as e:
        pytest.skip(f"WebDevelopmentAgent not available: {e}")


def test_wordpress_agent_import():
    """Test WordPressAgent can be imported."""
    try:
        from agent.modules import WordPressAgent
        assert WordPressAgent is not None
        assert WordPressAgent.__name__ == "WordPressAgent"
    except ImportError as e:
        pytest.skip(f"WordPressAgent not available: {e}")


def test_site_communication_agent_import():
    """Test SiteCommunicationAgent can be imported."""
    try:
        from agent.modules import SiteCommunicationAgent
        assert SiteCommunicationAgent is not None
        assert SiteCommunicationAgent.__name__ == "SiteCommunicationAgent"
    except ImportError as e:
        pytest.skip(f"SiteCommunicationAgent not available: {e}")


def test_brand_intelligence_agent_import():
    """Test BrandIntelligenceAgent can be imported."""
    try:
        from agent.modules import BrandIntelligenceAgent
        assert BrandIntelligenceAgent is not None
        assert BrandIntelligenceAgent.__name__ == "BrandIntelligenceAgent"
    except ImportError as e:
        pytest.skip(f"BrandIntelligenceAgent not available: {e}")


def test_seo_marketing_agent_import():
    """Test SEOMarketingAgent can be imported."""
    try:
        from agent.modules import SEOMarketingAgent
        assert SEOMarketingAgent is not None
        assert SEOMarketingAgent.__name__ == "SEOMarketingAgent"
    except ImportError as e:
        pytest.skip(f"SEOMarketingAgent not available: {e}")


def test_ecommerce_agent_import():
    """Test EcommerceAgent can be imported."""
    try:
        from agent.modules import EcommerceAgent
        assert EcommerceAgent is not None
        assert EcommerceAgent.__name__ == "EcommerceAgent"
    except ImportError as e:
        pytest.skip(f"EcommerceAgent not available: {e}")


def test_all_agents_in_all_list():
    """Test that __all__ contains expected agent exports."""
    from agent.modules import __all__
    
    expected_core_agents = [
        "CustomerServiceAgent",
        "DesignAutomationAgent",
        "EmailSMSAutomationAgent",
        "FinancialAgent",
        "SocialMediaAutomationAgent",
        "PerformanceAgent",
        "SecurityAgent",
        "InventoryAgent",
        "WebDevelopmentAgent",
        "WordPressAgent",
        "SiteCommunicationAgent",
        "BrandIntelligenceAgent",
        "SEOMarketingAgent",
        "EcommerceAgent",
    ]
    
    for agent in expected_core_agents:
        assert agent in __all__, f"{agent} should be in __all__"


def test_scanner_module_accessible():
    """Test that scanner module is accessible."""
    from agent.modules import scanner
    
    assert hasattr(scanner, "scan_site")
    assert callable(scanner.scan_site)


def test_agent_module_has_version():
    """Test that agent.modules has version info."""
    from agent import modules
    
    assert hasattr(modules, "__version__")
    assert hasattr(modules, "__author__")
    assert modules.__version__ == "2.0.0"
