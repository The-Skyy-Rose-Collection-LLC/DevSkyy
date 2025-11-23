#!/usr/bin/env python3
"""
Comprehensive Branch Analysis Script for DevSkyy Repository
Analyzes all branches using git ls-remote and provides detailed insights
"""

import subprocess
import json
import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

def run_git_command(cmd: str) -> Tuple[str, int]:
    """Run a git command and return output and return code"""
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

def get_remote_branches() -> List[Dict[str, str]]:
    """Get all remote branches with their commit hashes"""
    cmd = "git ls-remote --heads origin"
    output, returncode = run_git_command(cmd)
    
    branches = []
    if returncode == 0:
        for line in output.split('\n'):
            if line:
                parts = line.split('\t')
                if len(parts) == 2:
                    commit_hash = parts[0]
                    branch_ref = parts[1]
                    branch_name = branch_ref.replace('refs/heads/', '')
                    branches.append({
                        'name': branch_name,
                        'hash': commit_hash,
                        'short_hash': commit_hash[:7]
                    })
    
    return branches

def get_main_commit() -> str:
    """Get the current commit hash of main branch"""
    cmd = "git rev-parse origin/main 2>/dev/null || git rev-parse main 2>/dev/null"
    output, _ = run_git_command(cmd)
    return output.strip()

def categorize_branches(branches: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize branches by prefix"""
    categories = defaultdict(list)
    
    for branch in branches:
        name = branch['name']
        if '/' in name:
            prefix = name.split('/')[0]
            categories[prefix].append(branch)
        else:
            categories['other'].append(branch)
    
    return categories

def analyze_branch_pattern(branch_name: str) -> Dict[str, str]:
    """Analyze branch naming pattern and extract metadata"""
    patterns = {
        'copilot/fix': 'Bug fix branch (Copilot)',
        'copilot/': 'Feature/task branch (Copilot)',
        'claude/': 'AI assistant branch (Claude)',
        'cursor/': 'Feature branch (Cursor)',
        'codex/': 'Code generation branch (Codex)',
        'coderabbitai/': 'Code review branch (CodeRabbit)',
        'dependabot/': 'Dependency update (Dependabot)',
        'feature/': 'Feature branch',
        'conflict_': 'Conflict resolution branch',
        'alert-autofix': 'Auto-fix branch',
    }
    
    analysis = {
        'type': 'unknown',
        'purpose': 'Unknown purpose',
        'priority': 'low'
    }
    
    for pattern, description in patterns.items():
        if branch_name.startswith(pattern):
            analysis['purpose'] = description
            analysis['type'] = pattern.rstrip('/-_')
            
            # Determine priority
            if 'fix' in branch_name.lower() or 'bug' in branch_name.lower():
                analysis['priority'] = 'high'
            elif 'dependabot' in branch_name:
                analysis['priority'] = 'medium'
            elif 'conflict' in branch_name:
                analysis['priority'] = 'high'
            
            break
    
    return analysis

def create_visual_diagram(categories: Dict[str, List[Dict]]) -> str:
    """Create an ASCII diagram of branch structure"""
    diagram = []
    diagram.append("\n" + "=" * 100)
    diagram.append("BRANCH STRUCTURE DIAGRAM")
    diagram.append("=" * 100)
    diagram.append("")
    diagram.append("main ─┬─ Active Development Branches")
    diagram.append("      │")
    
    total_branches = sum(len(branches) for branches in categories.values())
    current = 0
    
    for category, branches in sorted(categories.items()):
        count = len(branches)
        current += count
        is_last = (current == total_branches)
        
        connector = "└─" if is_last else "├─"
        sub_connector = "  " if is_last else "│ "
        
        diagram.append(f"      {connector} {category.upper()} ({count} branches)")
        
        # Show first few branches in each category
        for i, branch in enumerate(sorted(branches, key=lambda x: x['name'])[:5]):
            is_last_branch = (i == min(4, count - 1))
            branch_connector = "└─" if is_last_branch else "├─"
            diagram.append(f"      {sub_connector}   {branch_connector} {branch['name'][:60]}")
        
        if count > 5:
            diagram.append(f"      {sub_connector}   └─ ... and {count - 5} more")
    
    diagram.append("")
    return "\n".join(diagram)

def generate_cleanup_recommendations(categories: Dict[str, List[Dict]]) -> List[str]:
    """Generate recommendations for branch cleanup"""
    recommendations = []
    
    # Check for old conflict branches
    conflict_branches = categories.get('other', [])
    conflict_branches = [b for b in conflict_branches if 'conflict' in b['name']]
    if conflict_branches:
        recommendations.append(
            f"🔴 CRITICAL: Found {len(conflict_branches)} conflict resolution branches. "
            "These should be merged or deleted: " + 
            ", ".join([b['name'] for b in conflict_branches[:3]])
        )
    
    # Check for dependabot branches
    dependabot_branches = categories.get('dependabot', [])
    if len(dependabot_branches) > 10:
        recommendations.append(
            f"⚠️  WARNING: {len(dependabot_branches)} Dependabot branches found. "
            "Consider reviewing and merging dependency updates in batches."
        )
    
    # Check for fix branches
    copilot_fixes = [b for b in categories.get('copilot', []) if 'fix' in b['name']]
    if len(copilot_fixes) > 20:
        recommendations.append(
            f"ℹ️  INFO: {len(copilot_fixes)} Copilot fix branches. "
            "Consider consolidating merged fixes."
        )
    
    # Check for duplicate work
    all_branches = []
    for branches in categories.values():
        all_branches.extend([b['name'] for b in branches])
    
    # Look for similar branch names
    similar_patterns = defaultdict(list)
    for branch in all_branches:
        # Extract base pattern (remove unique IDs)
        base = re.sub(r'[a-f0-9]{8,}', 'XXX', branch)
        base = re.sub(r'-\d+$', '', base)
        similar_patterns[base].append(branch)
    
    duplicates = {k: v for k, v in similar_patterns.items() if len(v) > 3}
    if duplicates:
        recommendations.append(
            f"ℹ️  INFO: Found {len(duplicates)} patterns with multiple branches. "
            "This might indicate duplicate work or stale branches."
        )
    
    return recommendations

def create_action_plan(categories: Dict[str, List[Dict]]) -> List[str]:
    """Create a prioritized action plan"""
    plan = []
    
    plan.append("=" * 100)
    plan.append("RECOMMENDED ACTION PLAN")
    plan.append("=" * 100)
    plan.append("")
    
    # Phase 1: Critical cleanup
    plan.append("📋 PHASE 1: Critical Cleanup (High Priority)")
    plan.append("-" * 100)
    
    conflict_branches = [b for b in categories.get('other', []) if 'conflict' in b['name']]
    if conflict_branches:
        plan.append(f"1. Review and delete {len(conflict_branches)} conflict resolution branches:")
        for branch in conflict_branches[:5]:
            plan.append(f"   - {branch['name']}")
        if len(conflict_branches) > 5:
            plan.append(f"   - ... and {len(conflict_branches) - 5} more")
    
    # Phase 2: Dependency updates
    plan.append("")
    plan.append("📋 PHASE 2: Dependency Management (Medium Priority)")
    plan.append("-" * 100)
    
    dependabot = categories.get('dependabot', [])
    if dependabot:
        plan.append(f"2. Review and merge {len(dependabot)} Dependabot PRs:")
        
        # Group by package ecosystem
        by_ecosystem = defaultdict(list)
        for branch in dependabot:
            parts = branch['name'].split('/')
            if len(parts) > 2:
                ecosystem = parts[1]
                by_ecosystem[ecosystem].append(branch)
        
        for ecosystem, branches in sorted(by_ecosystem.items()):
            plan.append(f"   - {ecosystem}: {len(branches)} updates")
    
    # Phase 3: Feature branch consolidation
    plan.append("")
    plan.append("📋 PHASE 3: Feature Branch Review (Low Priority)")
    plan.append("-" * 100)
    
    for category in ['copilot', 'claude', 'cursor', 'codex']:
        branches = categories.get(category, [])
        if branches:
            plan.append(f"3. Review {len(branches)} {category} branches for completion status")
    
    # Phase 4: Maintenance
    plan.append("")
    plan.append("📋 PHASE 4: Ongoing Maintenance")
    plan.append("-" * 100)
    plan.append("4. Establish branch naming conventions")
    plan.append("5. Set up automated branch cleanup policies")
    plan.append("6. Create branch protection rules for main/develop")
    plan.append("7. Document branching strategy in CONTRIBUTING.md")
    
    return plan

def main():
    """Main execution function"""
    print("=" * 100)
    print("DevSkyy Repository - Comprehensive Branch Analysis")
    print("=" * 100)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 100)
    print()
    
    # Get all remote branches
    print("📡 Fetching branch information from remote repository...")
    branches = get_remote_branches()
    main_commit = get_main_commit()
    
    print(f"✅ Found {len(branches)} total branches")
    print(f"📌 Main branch commit: {main_commit[:12] if main_commit else 'N/A'}")
    print()
    
    # Categorize branches
    categories = categorize_branches(branches)
    
    # Display visual diagram
    print(create_visual_diagram(categories))
    
    # Statistics
    print("\n" + "=" * 100)
    print("BRANCH STATISTICS")
    print("=" * 100)
    print(f"Total Branches: {len(branches)}")
    print(f"Categories: {len(categories)}")
    print()
    
    # Category breakdown
    for category, branch_list in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        percentage = (len(branch_list) / len(branches)) * 100
        bar_length = int(percentage / 2)
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"{category:20s} {bar} {len(branch_list):3d} ({percentage:5.1f}%)")
    
    # Detailed category analysis
    print("\n" + "=" * 100)
    print("DETAILED CATEGORY ANALYSIS")
    print("=" * 100)
    
    for category, branch_list in sorted(categories.items()):
        print(f"\n🏷️  {category.upper()} ({len(branch_list)} branches)")
        print("-" * 100)
        
        # Show sample branches
        for i, branch in enumerate(sorted(branch_list, key=lambda x: x['name'])[:10]):
            analysis = analyze_branch_pattern(branch['name'])
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(analysis['priority'], "⚪")
            print(f"  {priority_icon} {branch['name'][:70]:70s} [{branch['short_hash']}]")
        
        if len(branch_list) > 10:
            print(f"  ... and {len(branch_list) - 10} more branches")
    
    # Recommendations
    print("\n" + "=" * 100)
    print("CLEANUP RECOMMENDATIONS")
    print("=" * 100)
    recommendations = generate_cleanup_recommendations(categories)
    
    if recommendations:
        for rec in recommendations:
            print(f"\n{rec}")
    else:
        print("\n✅ No immediate cleanup recommendations")
    
    # Action plan
    print()
    action_plan = create_action_plan(categories)
    for line in action_plan:
        print(line)
    
    # Save detailed JSON report
    report = {
        'generated_at': datetime.now().isoformat(),
        'total_branches': len(branches),
        'main_commit': main_commit,
        'categories': {
            category: {
                'count': len(branch_list),
                'branches': [
                    {
                        'name': b['name'],
                        'hash': b['hash'],
                        'short_hash': b['short_hash'],
                        'analysis': analyze_branch_pattern(b['name'])
                    }
                    for b in branch_list
                ]
            }
            for category, branch_list in categories.items()
        },
        'recommendations': recommendations,
        'statistics': {
            'by_category': {cat: len(branches) for cat, branches in categories.items()}
        }
    }
    
    output_file = '/home/runner/work/DevSkyy/DevSkyy/branch_analysis_detailed.json'
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print()
    print("=" * 100)
    print(f"📄 Detailed JSON report saved to: {output_file}")
    print("=" * 100)

if __name__ == '__main__':
    main()
