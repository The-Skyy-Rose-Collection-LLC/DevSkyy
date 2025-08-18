
import os
import requests
from typing import Dict, Any, List
import json

def scan_site(url: str = "https://theskyy-rose-collection.com") -> Dict[str, Any]:
    """Scan website for issues and gather data."""
    try:
        response = requests.get(url, timeout=10)
        
        scan_results = {
            "url": url,
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds(),
            "content_length": len(response.content),
            "headers": dict(response.headers),
            "issues_found": [],
            "recommendations": []
        }
        
        # Basic checks
        if response.status_code != 200:
            scan_results["issues_found"].append(f"HTTP {response.status_code} error")
        
        if response.elapsed.total_seconds() > 3:
            scan_results["issues_found"].append("Slow response time")
            scan_results["recommendations"].append("Optimize server performance")
            
        # Content checks
        content = response.text.lower()
        if "error" in content:
            scan_results["issues_found"].append("Error messages found in content")
            
        return scan_results
        
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "status": "scan_failed"
        }

def scan_code_files(directory: str = ".") -> List[Dict[str, Any]]:
    """Scan local code files for issues."""
    issues = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.py', '.js', '.css', '.html')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    file_issues = {
                        "file": file_path,
                        "size": len(content),
                        "lines": len(content.splitlines()),
                        "issues": []
                    }
                    
                    # Basic code quality checks
                    if len(content) > 50000:
                        file_issues["issues"].append("Large file size")
                    
                    if content.count('\n\n\n') > 5:
                        file_issues["issues"].append("Too many empty lines")
                    
                    issues.append(file_issues)
                    
                except Exception as e:
                    issues.append({
                        "file": file_path,
                        "error": str(e)
                    })
    
    return issues
