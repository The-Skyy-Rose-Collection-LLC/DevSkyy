#!/usr/bin/env python3
# update_action_shas.py

import re
import requests
import yaml
from pathlib import Path

def get_latest_sha(owner, repo, tag):
    """Get the commit SHA for a specific tag."""
    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/tags/{tag}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        sha = data['object']['sha']
        # Get the actual commit SHA if it's a tag object
        if data['object']['type'] == 'tag':
            tag_url = data['object']['url']
            tag_response = requests.get(tag_url)
            sha = tag_response.json()['object']['sha']
        return sha
    return None

def update_workflow_files():
    """Update all workflow files with latest SHAs."""
    workflows_dir = Path('.github/workflows')
    
    # Common actions to update
    actions = {
        'actions/checkout@v4': ('actions', 'checkout', 'v4'),
        'actions/setup-python@v5': ('actions', 'setup-python', 'v5'),
        'actions/github-script@v6': ('actions', 'github-script', 'v6'),
    }
    
    for workflow_file in workflows_dir.glob('*.yml'):
        content = workflow_file.read_text()
        
        for action, (owner, repo, tag) in actions.items():
            sha = get_latest_sha(owner, repo, tag)
            if sha:
                # Replace version tags with SHAs
                pattern = f'{owner}/{repo}@v\\d+'
                replacement = f'{owner}/{repo}@{sha}'
                content = re.sub(pattern, replacement, content)
                print(f"Updated {action} to {sha}")
        
        workflow_file.write_text(content)

if __name__ == "__main__":
    update_workflow_files()
