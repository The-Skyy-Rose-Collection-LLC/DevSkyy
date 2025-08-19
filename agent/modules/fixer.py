
import re
import json
import ast
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

def fix_code(code_data: Any) -> Dict[str, Any]:
    """
    Production-level code fixing with comprehensive error handling.
    """
    try:
        if isinstance(code_data, str):
            # Detect code type and fix accordingly
            if code_data.strip().startswith('<!DOCTYPE') or '<html' in code_data:
                return fix_html_issues(code_data)
            elif code_data.strip().startswith('{') or 'function' in code_data:
                return fix_javascript_issues(code_data)
            elif 'body' in code_data or 'margin' in code_data:
                return fix_css_issues(code_data)
            elif '<?php' in code_data:
                return fix_php_issues(code_data)
            else:
                return fix_generic_issues(code_data)
        
        return {
            "status": "success",
            "original_code": str(code_data),
            "fixed_code": str(code_data),
            "fixes_applied": ["No fixes needed"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Code fixing failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def fix_html_issues(html_content: str) -> Dict[str, Any]:
    """Fix common HTML issues with production standards."""
    fixes_applied = []
    fixed_html = html_content
    
    # Fix missing DOCTYPE
    if not fixed_html.strip().startswith('<!DOCTYPE'):
        fixed_html = '<!DOCTYPE html>\n' + fixed_html
        fixes_applied.append("Added DOCTYPE declaration")
    
    # Fix missing meta viewport
    if 'viewport' not in fixed_html:
        viewport_tag = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        if '<head>' in fixed_html:
            fixed_html = fixed_html.replace('<head>', f'<head>\n    {viewport_tag}')
        fixes_applied.append("Added viewport meta tag")
    
    # Fix unclosed tags
    unclosed_tags = ['<br>', '<hr>', '<img', '<input', '<meta', '<link']
    for tag in unclosed_tags:
        if tag in fixed_html and not tag.replace('<', '</') in fixed_html:
            fixed_html = re.sub(rf'{tag}([^>]*?)>', rf'{tag}\1 />', fixed_html)
            fixes_applied.append(f"Fixed unclosed {tag} tags")
    
    # Fix missing alt attributes for images
    img_pattern = r'<img([^>]*?)(?:alt="[^"]*")?([^>]*?)>'
    if re.search(r'<img(?![^>]*alt=)', fixed_html):
        fixed_html = re.sub(r'<img([^>]*?)>', r'<img\1 alt="Image">', fixed_html)
        fixes_applied.append("Added missing alt attributes")
    
    # Fix missing charset
    if 'charset' not in fixed_html:
        charset_tag = '<meta charset="UTF-8">'
        if '<head>' in fixed_html:
            fixed_html = fixed_html.replace('<head>', f'<head>\n    {charset_tag}')
        fixes_applied.append("Added charset meta tag")
    
    return {
        "status": "success",
        "original_code": html_content,
        "fixed_code": fixed_html,
        "fixes_applied": fixes_applied,
        "timestamp": datetime.now().isoformat()
    }

def fix_css_issues(css_content: str) -> Dict[str, Any]:
    """Fix common CSS issues with production optimization."""
    fixes_applied = []
    fixed_css = css_content
    
    # Remove empty rules
    empty_rules = re.findall(r'[^}]*\{\s*\}', fixed_css)
    if empty_rules:
        fixed_css = re.sub(r'[^}]*\{\s*\}', '', fixed_css)
        fixes_applied.append("Removed empty CSS rules")
    
    # Fix missing semicolons
    missing_semicolon = re.findall(r'[^;}\s]\s*\n\s*[a-zA-Z-]', fixed_css)
    if missing_semicolon:
        fixed_css = re.sub(r'([^;}\s])\s*\n\s*([a-zA-Z-])', r'\1;\n    \2', fixed_css)
        fixes_applied.append("Added missing semicolons")
    
    # Optimize vendor prefixes
    vendor_prefixes = {
        'transform': ['-webkit-transform', '-moz-transform', '-ms-transform'],
        'transition': ['-webkit-transition', '-moz-transition', '-ms-transition'],
        'border-radius': ['-webkit-border-radius', '-moz-border-radius']
    }
    
    for property_name, prefixes in vendor_prefixes.items():
        if property_name in fixed_css:
            for prefix in prefixes:
                if prefix not in fixed_css:
                    pattern = rf'(\s+){property_name}:\s*([^;]+);'
                    replacement = rf'\1{prefix}: \2;\n\1{property_name}: \2;'
                    fixed_css = re.sub(pattern, replacement, fixed_css)
            fixes_applied.append(f"Added vendor prefixes for {property_name}")
    
    # Format CSS properly
    fixed_css = re.sub(r'\s*{\s*', ' {\n    ', fixed_css)
    fixed_css = re.sub(r';\s*', ';\n    ', fixed_css)
    fixed_css = re.sub(r'\s*}\s*', '\n}\n\n', fixed_css)
    fixes_applied.append("Formatted CSS structure")
    
    return {
        "status": "success",
        "original_code": css_content,
        "fixed_code": fixed_css,
        "fixes_applied": fixes_applied,
        "timestamp": datetime.now().isoformat()
    }

def fix_javascript_issues(js_content: str) -> Dict[str, Any]:
    """Fix common JavaScript issues with ES6+ standards."""
    fixes_applied = []
    fixed_js = js_content
    
    # Fix missing semicolons
    lines = fixed_js.split('\n')
    fixed_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.endswith((';', '{', '}', ',', ':', '(', ')')):
            if not any(keyword in stripped for keyword in ['if', 'for', 'while', 'function', 'class', 'else', 'catch', 'try']):
                if not stripped.startswith(('var ', 'let ', 'const ', 'return ', 'break', 'continue', '//', '/*')):
                    line += ';'
                    if stripped not in ['', '}', '{']:
                        fixes_applied.append("Added missing semicolons")
        fixed_lines.append(line)
    
    fixed_js = '\n'.join(fixed_lines)
    
    # Convert var to let/const where appropriate
    var_pattern = r'\bvar\s+(\w+)\s*='
    var_matches = re.findall(var_pattern, fixed_js)
    if var_matches:
        fixed_js = re.sub(r'\bvar\s+(\w+)\s*=([^;]+);', r'const \1 =\2;', fixed_js)
        fixes_applied.append("Converted var to const where appropriate")
    
    # Fix function declarations to arrow functions where appropriate
    function_pattern = r'function\s+(\w+)\s*\(([^)]*)\)\s*\{'
    if re.search(function_pattern, fixed_js):
        # Convert simple functions to arrow functions
        fixed_js = re.sub(r'function\s+(\w+)\s*\(([^)]*)\)\s*\{', r'const \1 = (\2) => {', fixed_js)
        fixes_applied.append("Converted functions to arrow functions")
    
    # Add strict mode if not present
    if "'use strict'" not in fixed_js and '"use strict"' not in fixed_js:
        fixed_js = "'use strict';\n\n" + fixed_js
        fixes_applied.append("Added strict mode")
    
    return {
        "status": "success",
        "original_code": js_content,
        "fixed_code": fixed_js,
        "fixes_applied": fixes_applied,
        "timestamp": datetime.now().isoformat()
    }

def fix_php_issues(php_content: str) -> Dict[str, Any]:
    """Fix common PHP issues with modern PHP standards."""
    fixes_applied = []
    fixed_php = php_content
    
    # Add opening PHP tag if missing
    if not fixed_php.strip().startswith('<?php'):
        fixed_php = '<?php\n' + fixed_php
        fixes_applied.append("Added opening PHP tag")
    
    # Fix missing semicolons
    lines = fixed_php.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.endswith((';', '{', '}', ':', '?>')):
            if stripped.startswith('$') or 'echo' in stripped or 'return' in stripped:
                lines[i] = line + ';'
                fixes_applied.append("Added missing semicolons")
    
    fixed_php = '\n'.join(lines)
    
    # Fix deprecated functions
    deprecated_replacements = {
        'mysql_connect': 'mysqli_connect',
        'mysql_query': 'mysqli_query',
        'mysql_fetch_array': 'mysqli_fetch_array'
    }
    
    for old_func, new_func in deprecated_replacements.items():
        if old_func in fixed_php:
            fixed_php = fixed_php.replace(old_func, new_func)
            fixes_applied.append(f"Replaced deprecated {old_func} with {new_func}")
    
    return {
        "status": "success",
        "original_code": php_content,
        "fixed_code": fixed_php,
        "fixes_applied": fixes_applied,
        "timestamp": datetime.now().isoformat()
    }

def fix_generic_issues(content: str) -> Dict[str, Any]:
    """Fix generic code issues."""
    fixes_applied = []
    fixed_content = content
    
    # Fix line endings
    if '\r\n' in fixed_content:
        fixed_content = fixed_content.replace('\r\n', '\n')
        fixes_applied.append("Normalized line endings")
    
    # Remove trailing whitespace
    lines = fixed_content.split('\n')
    fixed_lines = [line.rstrip() for line in lines]
    fixed_content = '\n'.join(fixed_lines)
    fixes_applied.append("Removed trailing whitespace")
    
    # Ensure file ends with newline
    if fixed_content and not fixed_content.endswith('\n'):
        fixed_content += '\n'
        fixes_applied.append("Added final newline")
    
    return {
        "status": "success",
        "original_code": content,
        "fixed_code": fixed_content,
        "fixes_applied": fixes_applied,
        "timestamp": datetime.now().isoformat()
    }

def analyze_code_complexity(code: str) -> Dict[str, Any]:
    """Analyze code complexity and provide metrics."""
    lines = code.split('\n')
    
    return {
        "total_lines": len(lines),
        "non_empty_lines": len([line for line in lines if line.strip()]),
        "comment_lines": len([line for line in lines if line.strip().startswith(('#', '//', '/*'))]),
        "complexity_score": min(100, max(0, 100 - len(lines) // 10)),
        "maintainability": "high" if len(lines) < 100 else "medium" if len(lines) < 500 else "low"
    }
