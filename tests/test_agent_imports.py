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
    from agent.modules import CustomerServiceAgent
    
    if CustomerServiceAgent is None:
        pytest.skip("CustomerServiceAgent not available due to missing dependencies")
    
    assert CustomerServiceAgent.__name__ == "CustomerServiceAgent"


def test_design_automation_agent_import():
    """Test DesignAutomationAgent can be imported."""
    from agent.modules import DesignAutomationAgent
    
    if DesignAutomationAgent is None:
        pytest.skip("DesignAutomationAgent not available due to missing dependencies")
    
    assert DesignAutomationAgent.__name__ == "DesignAutomationAgent"


def test_email_sms_automation_agent_import():
    """Test EmailSMSAutomationAgent can be imported."""
    from agent.modules import EmailSMSAutomationAgent
    
    if EmailSMSAutomationAgent is None:
        pytest.skip("EmailSMSAutomationAgent not available due to missing dependencies")
    
    assert EmailSMSAutomationAgent.__name__ == "EmailSMSAutomationAgent"


def test_financial_agent_import():
    """Test FinancialAgent can be imported."""
    from agent.modules import FinancialAgent
    
    if FinancialAgent is None:
        pytest.skip("FinancialAgent not available due to missing dependencies")
    
    assert FinancialAgent.__name__ == "FinancialAgent"


def test_social_media_automation_agent_import():
    """Test SocialMediaAutomationAgent can be imported."""
    from agent.modules import SocialMediaAutomationAgent
    
    if SocialMediaAutomationAgent is None:
        pytest.skip("SocialMediaAutomationAgent not available due to missing dependencies")
    
    assert SocialMediaAutomationAgent.__name__ == "SocialMediaAutomationAgent"


def test_performance_agent_import():
    """Test PerformanceAgent can be imported."""
    from agent.modules import PerformanceAgent
    
    if PerformanceAgent is None:
        pytest.skip("PerformanceAgent not available due to missing dependencies")
    
    assert PerformanceAgent.__name__ == "PerformanceAgent"


def test_security_agent_import():
    """Test SecurityAgent can be imported."""
    from agent.modules import SecurityAgent
    
    if SecurityAgent is None:
        pytest.skip("SecurityAgent not available due to missing dependencies")
    
    assert SecurityAgent.__name__ == "SecurityAgent"


def test_inventory_agent_import():
    """Test InventoryAgent can be imported."""
    from agent.modules import InventoryAgent
    
    if InventoryAgent is None:
        pytest.skip("InventoryAgent not available due to missing dependencies")
    
    assert InventoryAgent.__name__ == "InventoryAgent"


def test_web_development_agent_import():
    """Test WebDevelopmentAgent can be imported."""
    from agent.modules import WebDevelopmentAgent
    
    if WebDevelopmentAgent is None:
        pytest.skip("WebDevelopmentAgent not available due to missing dependencies")
    
    assert WebDevelopmentAgent.__name__ == "WebDevelopmentAgent"


def test_wordpress_agent_import():
    """Test WordPressAgent can be imported."""
    from agent.modules import WordPressAgent
    
    if WordPressAgent is None:
        pytest.skip("WordPressAgent not available due to missing dependencies")
    
    assert WordPressAgent.__name__ == "WordPressAgent"


def test_site_communication_agent_import():
    """Test SiteCommunicationAgent can be imported."""
    from agent.modules import SiteCommunicationAgent
    
    if SiteCommunicationAgent is None:
        pytest.skip("SiteCommunicationAgent not available due to missing dependencies")
    
    assert SiteCommunicationAgent.__name__ == "SiteCommunicationAgent"


def test_brand_intelligence_agent_import():
    """Test BrandIntelligenceAgent can be imported."""
    from agent.modules import BrandIntelligenceAgent
    
    if BrandIntelligenceAgent is None:
        pytest.skip("BrandIntelligenceAgent not available due to missing dependencies")
    
    assert BrandIntelligenceAgent.__name__ == "BrandIntelligenceAgent"


def test_seo_marketing_agent_import():
    """Test SEOMarketingAgent can be imported."""
    from agent.modules import SEOMarketingAgent
    
    if SEOMarketingAgent is None:
        pytest.skip("SEOMarketingAgent not available due to missing dependencies")
    
    assert SEOMarketingAgent.__name__ == "SEOMarketingAgent"


def test_ecommerce_agent_import():
    """Test EcommerceAgent can be imported."""
    from agent.modules import EcommerceAgent
    
    if EcommerceAgent is None:
        pytest.skip("EcommerceAgent not available due to missing dependencies")
    
    assert EcommerceAgent.__name__ == "EcommerceAgent"


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
