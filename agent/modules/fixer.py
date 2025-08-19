import re
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def fix_code(raw_code: str, language: str = "html") -> Dict[str, Any]:
    """Main function to fix code based on language type."""
    try:
        if language.lower() == "html":
            return fix_html_issues(raw_code)
        elif language.lower() == "css":
            return fix_css_issues(raw_code)
        elif language.lower() in ["javascript", "js"]:
            return fix_javascript_issues(raw_code)
        elif language.lower() == "python":
            return fix_python_issues(raw_code)
        else:
            return fix_html_issues(raw_code)  # Default to HTML
    except Exception as e:
        logger.error(f"Error fixing code: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
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
    """Fix common CSS issues with modern standards."""
    fixes_applied = []
    fixed_css = css_content

    # Remove unnecessary whitespace and format properly
    fixed_css = re.sub(r'\s*{\s*', ' {\n    ', fixed_css)
    fixed_css = re.sub(r';\s*', ';\n    ', fixed_css)
    fixed_css = re.sub(r'\s*}\s*', '\n}\n\n', fixed_css)
    fixes_applied.append("Formatted CSS structure")

    # Fix missing vendor prefixes for common properties
    vendor_prefixes = {
        'transform': ['-webkit-transform', '-moz-transform', '-ms-transform'],
        'transition': ['-webkit-transition', '-moz-transition', '-ms-transition'],
        'border-radius': ['-webkit-border-radius', '-moz-border-radius']
    }

    for prop, prefixes in vendor_prefixes.items():
        if prop in fixed_css:
            for prefix in prefixes:
                if prefix not in fixed_css:
                    fixed_css = re.sub(f'({prop}:[^;]+;)', f'{prefix}: \\1\n    \\1', fixed_css)
            fixes_applied.append(f"Added vendor prefixes for {prop}")

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

    return {
        "status": "success",
        "original_code": js_content,
        "fixed_code": fixed_js,
        "fixes_applied": fixes_applied,
        "timestamp": datetime.now().isoformat()
    }

import re
from datetime import datetime
from typing import Dict, Any, List

def fix_python_issues(python_content: str) -> Dict[str, Any]:
    """Fix common Python issues with PEP 8 standards."""
    fixes_applied = []
    fixed_python = python_content

    # Fix import organization
    lines = fixed_python.split('\n')
    imports = []
    from_imports = []
    other_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('import '):
            imports.append(line)
        elif stripped.startswith('from '):
            from_imports.append(line)
        else:
            other_lines.append(line)

    if imports or from_imports:
        # Sort imports
        imports.sort()
        from_imports.sort()

        # Rebuild file with proper import order
        new_lines = imports + from_imports + [''] + other_lines
        fixed_python = '\n'.join(new_lines)
        fixes_applied.append("Organized imports according to PEP 8")

    # Fix spacing around operators
    fixed_python = re.sub(r'(\w+)=(\w+)', r'\1 = \2', fixed_python)
    fixed_python = re.sub(r'(\w+)\+(\w+)', r'\1 + \2', fixed_python)
    fixed_python = re.sub(r'(\w+)-(\w+)', r'\1 - \2', fixed_python)

    if '=' in python_content and ' = ' not in python_content:
        fixes_applied.append("Added proper spacing around operators")

    return {
        "status": "success",
        "original_code": python_content,
        "fixed_code": fixed_python,
        "fixes_applied": fixes_applied,
        "timestamp": datetime.now().isoformat()
    }

def fix_web_issues(content: str, content_type: str = "html") -> Dict[str, Any]:
    """General web content fixer."""
    if content_type.lower() == "html":
        return fix_html_issues(content)
    elif content_type.lower() == "css":
        return fix_css_issues(content)
    elif content_type.lower() in ["js", "javascript"]:
        return fix_javascript_issues(content)
    else:
        return fix_html_issues(content)

def analyze_and_fix(content: str, language: str = "auto") -> Dict[str, Any]:
    """Analyze content and apply appropriate fixes."""
    if language == "auto":
        # Auto-detect language
        if content.strip().startswith('<!DOCTYPE') or '<html' in content:
            language = "html"
        elif content.strip().startswith('@') or 'css' in content.lower():
            language = "css"
        elif 'function' in content or 'const' in content or 'let' in content:
            language = "javascript"
        elif 'def ' in content or 'import ' in content:
            language = "python"
        else:
            language = "html"

    return fix_code(content, language)