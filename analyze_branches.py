#!/usr/bin/env python3
"""
Branch Analysis Script
Analyzes all active branches and their ahead/behind status relative to main
"""

import subprocess
import json
from collections import defaultdict
from datetime import datetime

def run_git_command(cmd):
    """Run a git command and return the output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd="/home/runner/work/DevSkyy/DevSkyy"
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), -1

def get_all_branches():
    """Get all remote branches"""
    cmd = "git ls-remote --heads origin | awk '{print $2}' | sed 's|refs/heads/||'"
    output, _ = run_git_command(cmd)
    return [b for b in output.split('\n') if b]

def get_branch_info(branch):
    """Get detailed information about a branch"""
    # Get ahead/behind counts using remote refs
    cmd = f"git rev-list --left-right --count origin/main...origin/{branch} 2>/dev/null"
    output, returncode = run_git_command(cmd)
    
    if returncode == 0 and output:
        parts = output.split()
        if len(parts) == 2:
            behind, ahead = parts
        else:
            behind, ahead = "0", "0"
    else:
        behind, ahead = "N/A", "N/A"
    
    # Get last commit info
    cmd = f"git log -1 --format='%ci|%s|%an' origin/{branch} 2>/dev/null"
    output, returncode = run_git_command(cmd)
    
    if returncode == 0 and output:
        parts = output.split('|', 2)
        if len(parts) == 3:
            last_commit_date, last_commit_msg, author = parts
        else:
            last_commit_date, last_commit_msg, author = "N/A", "N/A", "N/A"
    else:
        last_commit_date, last_commit_msg, author = "N/A", "N/A", "N/A"
    
    # Get file changes
    cmd = f"git diff --name-status origin/main...origin/{branch} 2>/dev/null | wc -l"
    files_changed, _ = run_git_command(cmd)
    
    # Get detailed file changes
    cmd = f"git diff --name-status origin/main...origin/{branch} 2>/dev/null"
    file_details, _ = run_git_command(cmd)
    
    # Get commit hash
    cmd = f"git rev-parse --short origin/{branch} 2>/dev/null"
    commit_hash, _ = run_git_command(cmd)
    
    return {
        'branch': branch,
        'ahead': ahead,
        'behind': behind,
        'last_commit_date': last_commit_date,
        'last_commit_msg': last_commit_msg,
        'author': author,
        'files_changed': files_changed.strip(),
        'file_details': file_details,
        'commit_hash': commit_hash.strip()
    }

def categorize_branches(branches):
    """Categorize branches by prefix"""
    categories = defaultdict(list)
    
    for branch in branches:
        if '/' in branch:
            prefix = branch.split('/')[0]
            categories[prefix].append(branch)
        else:
            categories['other'].append(branch)
    
    return categories

def main():
    print("=" * 80)
    print("DevSkyy Branch Analysis Report")
    print("Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 80)
    print()
    
    # Get all branches
    print("Fetching branch information...")
    branches = get_all_branches()
    
    print(f"Total branches found: {len(branches)}")
    print()
    
    # Categorize branches
    categories = categorize_branches(branches)
    
    # Analyze each category
    all_branch_info = []
    
    for category, branch_list in sorted(categories.items()):
        print(f"\n{'=' * 80}")
        print(f"Category: {category.upper()} ({len(branch_list)} branches)")
        print('=' * 80)
        
        for branch in sorted(branch_list):
            print(f"\nAnalyzing: {branch}")
            info = get_branch_info(branch)
            all_branch_info.append(info)
            
            print(f"  Ahead:  {info['ahead']} commits")
            print(f"  Behind: {info['behind']} commits")
            print(f"  Files:  {info['files_changed']} files changed")
            print(f"  Hash:   {info['commit_hash']}")
            print(f"  Author: {info['author']}")
            print(f"  Last:   {info['last_commit_date'][:19] if info['last_commit_date'] != 'N/A' else 'N/A'}")
            print(f"  Msg:    {info['last_commit_msg'][:70] if info['last_commit_msg'] != 'N/A' else 'N/A'}")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total branches: {len(branches)}")
    print(f"Categories: {len(categories)}")
    
    for category, branch_list in sorted(categories.items()):
        print(f"  {category}: {len(branch_list)} branches")
    
    # Branches that need attention
    print("\n" + "=" * 80)
    print("BRANCHES NEEDING ATTENTION")
    print("=" * 80)
    
    # Branches significantly behind
    print("\nBranches > 10 commits behind main:")
    behind_branches = [b for b in all_branch_info if b['behind'].isdigit() and int(b['behind']) > 10]
    for b in sorted(behind_branches, key=lambda x: int(x['behind']), reverse=True)[:20]:
        print(f"  {b['branch']}: {b['behind']} commits behind")
    
    # Branches with many file changes
    print("\nBranches with > 10 files changed:")
    file_branches = [b for b in all_branch_info if b['files_changed'].isdigit() and int(b['files_changed']) > 10]
    for b in sorted(file_branches, key=lambda x: int(x['files_changed']), reverse=True)[:20]:
        print(f"  {b['branch']}: {b['files_changed']} files")
    
    # Save detailed report
    output_file = '/home/runner/work/DevSkyy/DevSkyy/branch_analysis_report.json'
    with open(output_file, 'w') as f:
        json.dump({
            'generated': datetime.now().isoformat(),
            'total_branches': len(branches),
            'categories': {k: len(v) for k, v in categories.items()},
            'branches': all_branch_info
        }, f, indent=2)
    
    print(f"\n\nDetailed report saved to: {output_file}")

if __name__ == '__main__':
    main()
