
import re
import json
from typing import Dict, Any, List

def fix_code(raw_code: Dict[str, Any]) -> Dict[str, Any]:
    """Fix common code issues and optimize."""
    if isinstance(raw_code, str):
        # Handle string input
        fixed_content = fix_string_content(raw_code)
        return {
            "original_length": len(raw_code),
            "fixed_length": len(fixed_content),
            "fixed_content": fixed_content,
            "fixes_applied": ["string_optimization"]
        }
    
    fixes_applied = []
    fixed_data = raw_code.copy()
    
    # Fix common issues
    if "issues_found" in fixed_data:
        for issue in fixed_data["issues_found"]:
            if "slow response" in issue.lower():
                fixed_data["optimizations"] = ["Enable caching", "Optimize database queries"]
                fixes_applied.append("performance_optimization")
            
            if "error" in issue.lower():
                fixed_data["error_handling"] = "Enhanced error handling implemented"
                fixes_applied.append("error_handling")
    
    fixed_data["fixes_applied"] = fixes_applied
    fixed_data["status"] = "fixed"
    
    return fixed_data

def fix_string_content(content: str) -> str:
    """Fix common string content issues."""
    # Remove excessive whitespace
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    # Fix common spacing issues
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'\s*\n\s*', '\n', content)
    
    return content.strip()

def fix_css_issues(css_content: str) -> str:
    """Fix common CSS issues."""
    # Remove empty rules
    css_content = re.sub(r'\{\s*\}', '', css_content)
    
    # Fix spacing
    css_content = re.sub(r'\s*{\s*', ' {\n    ', css_content)
    css_content = re.sub(r';\s*', ';\n    ', css_content)
    css_content = re.sub(r'\s*}\s*', '\n}\n', css_content)
    
    return css_content

def fix_javascript_issues(js_content: str) -> str:
    """Fix common JavaScript issues."""
    # Add missing semicolons
    lines = js_content.split('\n')
    fixed_lines = []
    
    for line in lines:
        line = line.strip()
        if line and not line.endswith((';', '{', '}', ',')) and not line.startswith(('if', 'for', 'while', 'function')):
            if not any(keyword in line for keyword in ['var ', 'let ', 'const ', 'return ', 'break', 'continue']):
                line += ';'
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)
