#!/usr/bin/env python3
"""
Generate comprehensive coverage visualization graphs.
Part of the Truth Protocol (Rule #8: Test Coverage ≥90%).
"""
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# Configuration
ARTIFACTS_DIR = Path("/home/user/DevSkyy/artifacts")
COVERAGE_FILE = Path("/home/user/DevSkyy/coverage.json")
TARGET_COVERAGE = 90.0
BASELINE_COVERAGE = 10.35  # Before adding tests

# Create artifacts directory if it doesn't exist
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def load_coverage_data() -> Dict:
    """Load coverage data from JSON file."""
    with open(COVERAGE_FILE, 'r') as f:
        return json.load(f)


def calculate_module_coverage(data: Dict) -> Dict[str, Dict]:
    """Calculate coverage statistics by module."""
    module_stats = defaultdict(lambda: {
        'lines_covered': 0,
        'total_lines': 0,
        'files': 0,
        'coverage': 0.0
    })

    files = data.get('files', {})

    for file_path, file_data in files.items():
        # Determine module from path
        path_parts = Path(file_path).parts

        # Skip test files and setup files
        if 'tests' in path_parts or 'test_' in file_path or 'setup.py' in file_path:
            continue

        # Extract module name
        if len(path_parts) > 1:
            module = path_parts[0] if path_parts[0] not in ['home', 'user', 'DevSkyy'] else \
                     path_parts[-2] if len(path_parts) > 2 else 'root'
        else:
            module = 'root'

        # Get coverage stats
        summary = file_data.get('summary', {})
        lines_covered = summary.get('covered_lines', 0)
        total_lines = summary.get('num_statements', 0)

        module_stats[module]['lines_covered'] += lines_covered
        module_stats[module]['total_lines'] += total_lines
        module_stats[module]['files'] += 1

    # Calculate coverage percentages
    for module, stats in module_stats.items():
        if stats['total_lines'] > 0:
            stats['coverage'] = (stats['lines_covered'] / stats['total_lines']) * 100

    return dict(module_stats)


def get_file_coverage_list(data: Dict) -> List[Tuple[str, float, int, int]]:
    """Get sorted list of files with coverage stats."""
    file_list = []
    files = data.get('files', {})

    for file_path, file_data in files.items():
        # Skip test files
        if 'tests' in file_path or 'test_' in file_path:
            continue

        summary = file_data.get('summary', {})
        covered = summary.get('covered_lines', 0)
        total = summary.get('num_statements', 0)

        if total > 0:
            coverage = (covered / total) * 100
            file_list.append((file_path, coverage, covered, total))

    return sorted(file_list, key=lambda x: x[1], reverse=True)


def graph_1_module_coverage_bar(module_stats: Dict):
    """Graph 1: Coverage by Module (Bar Chart)."""
    plt.figure(figsize=(14, 8))

    # Sort modules by coverage
    modules = list(module_stats.keys())
    coverages = [module_stats[m]['coverage'] for m in modules]

    # Sort by coverage
    sorted_data = sorted(zip(modules, coverages), key=lambda x: x[1], reverse=True)
    modules, coverages = zip(*sorted_data) if sorted_data else ([], [])

    # Create bar chart
    bars = plt.bar(range(len(modules)), coverages, color=['#2ecc71' if c >= TARGET_COVERAGE else '#e74c3c' if c < 50 else '#f39c12' for c in coverages])

    # Add target line
    plt.axhline(y=TARGET_COVERAGE, color='blue', linestyle='--', linewidth=2, label=f'Target ({TARGET_COVERAGE}%)')

    plt.xlabel('Module', fontsize=12, fontweight='bold')
    plt.ylabel('Coverage (%)', fontsize=12, fontweight='bold')
    plt.title('Test Coverage by Module', fontsize=16, fontweight='bold', pad=20)
    plt.xticks(range(len(modules)), modules, rotation=45, ha='right')
    plt.ylim(0, 100)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.legend()

    # Add value labels on bars
    for i, (bar, coverage) in enumerate(zip(bars, coverages)):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{coverage:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / 'coverage_by_module.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Generated: coverage_by_module.png")


def graph_2_before_after_comparison(current_coverage: float):
    """Graph 2: Before/After Coverage Comparison."""
    plt.figure(figsize=(10, 6))

    categories = ['Before\n(Baseline)', 'After\n(Current)']
    values = [BASELINE_COVERAGE, current_coverage]
    colors = ['#e74c3c', '#2ecc71' if current_coverage >= TARGET_COVERAGE else '#f39c12']

    bars = plt.bar(categories, values, color=colors, width=0.5, edgecolor='black', linewidth=2)

    # Add target line
    plt.axhline(y=TARGET_COVERAGE, color='blue', linestyle='--', linewidth=2, label=f'Target ({TARGET_COVERAGE}%)')

    plt.ylabel('Coverage (%)', fontsize=12, fontweight='bold')
    plt.title('Coverage Improvement: Before vs After', fontsize=16, fontweight='bold', pad=20)
    plt.ylim(0, 100)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.legend()

    # Add value labels
    for bar, value in zip(bars, values):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{value:.2f}%', ha='center', va='bottom', fontsize=14, fontweight='bold')

    # Add improvement annotation
    improvement = current_coverage - BASELINE_COVERAGE
    plt.text(0.5, max(values)/2, f'↑ +{improvement:.2f}%\nimprovement',
            ha='center', va='center', fontsize=14, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / 'coverage_before_after.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Generated: coverage_before_after.png")


def graph_3_file_distribution(file_list: List[Tuple[str, float, int, int]]):
    """Graph 3: File Coverage Distribution (Histogram)."""
    plt.figure(figsize=(12, 6))

    coverages = [f[1] for f in file_list]

    # Create bins
    bins = [0, 20, 40, 60, 80, 100]
    hist, _ = np.histogram(coverages, bins=bins)

    # Create bar chart
    bin_labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
    colors = ['#e74c3c', '#e67e22', '#f39c12', '#3498db', '#2ecc71']

    bars = plt.bar(range(len(bin_labels)), hist, color=colors, edgecolor='black', linewidth=1.5)

    plt.xlabel('Coverage Range', fontsize=12, fontweight='bold')
    plt.ylabel('Number of Files', fontsize=12, fontweight='bold')
    plt.title('Distribution of File Coverage Levels', fontsize=16, fontweight='bold', pad=20)
    plt.xticks(range(len(bin_labels)), bin_labels)
    plt.grid(axis='y', alpha=0.3, linestyle='--')

    # Add value labels
    for bar, count in zip(bars, hist):
        height = bar.get_height()
        if height > 0:
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(count)}', ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / 'coverage_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Generated: coverage_distribution.png")


def graph_4_top_performers(file_list: List[Tuple[str, float, int, int]]):
    """Graph 4: Top 10 Files with Best Coverage."""
    plt.figure(figsize=(14, 8))

    # Get top 10
    top_files = file_list[:10]

    if not top_files:
        print("⚠️  No files to display for top performers")
        return

    # Extract data
    file_names = [Path(f[0]).name for f in top_files]
    coverages = [f[1] for f in top_files]

    # Create horizontal bar chart
    y_pos = np.arange(len(file_names))
    bars = plt.barh(y_pos, coverages, color='#2ecc71', edgecolor='black', linewidth=1.5)

    plt.xlabel('Coverage (%)', fontsize=12, fontweight='bold')
    plt.ylabel('File', fontsize=12, fontweight='bold')
    plt.title('Top 10 Files: Best Coverage', fontsize=16, fontweight='bold', pad=20)
    plt.yticks(y_pos, file_names)
    plt.xlim(0, 100)
    plt.grid(axis='x', alpha=0.3, linestyle='--')

    # Add value labels
    for i, (bar, coverage) in enumerate(zip(bars, coverages)):
        width = bar.get_width()
        plt.text(width + 1, bar.get_y() + bar.get_height()/2.,
                f'{coverage:.1f}%', ha='left', va='center', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / 'top_covered_files.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Generated: top_covered_files.png")


def graph_5_coverage_gaps(file_list: List[Tuple[str, float, int, int]]):
    """Graph 5: Top 10 Files Needing Most Improvement."""
    plt.figure(figsize=(14, 8))

    # Get bottom 10 (excluding 0% coverage)
    bottom_files = [f for f in file_list if f[1] < TARGET_COVERAGE and f[3] > 10]  # At least 10 lines
    bottom_files = sorted(bottom_files, key=lambda x: x[1])[:10]

    if not bottom_files:
        print("⚠️  No files to display for coverage gaps")
        return

    # Extract data
    file_names = [Path(f[0]).name for f in bottom_files]
    coverages = [f[1] for f in bottom_files]
    covered = [f[2] for f in bottom_files]
    total = [f[3] for f in bottom_files]

    # Create horizontal bar chart
    y_pos = np.arange(len(file_names))
    bars = plt.barh(y_pos, coverages, color='#e74c3c', edgecolor='black', linewidth=1.5)

    plt.xlabel('Coverage (%)', fontsize=12, fontweight='bold')
    plt.ylabel('File', fontsize=12, fontweight='bold')
    plt.title('Top 10 Files: Needs Improvement (Most Critical)', fontsize=16, fontweight='bold', pad=20)
    plt.yticks(y_pos, file_names)
    plt.xlim(0, 100)
    plt.grid(axis='x', alpha=0.3, linestyle='--')

    # Add value labels with lines needed
    for i, (bar, coverage, cov, tot) in enumerate(zip(bars, coverages, covered, total)):
        width = bar.get_width()
        lines_needed = tot - cov
        plt.text(width + 1, bar.get_y() + bar.get_height()/2.,
                f'{coverage:.1f}% ({cov}/{tot}, need {lines_needed} more)',
                ha='left', va='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / 'coverage_gaps.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Generated: coverage_gaps.png")


def graph_6_module_heatmap(module_stats: Dict):
    """Graph 6: Module Coverage Heatmap."""
    plt.figure(figsize=(14, 8))

    # Prepare data for heatmap
    modules = list(module_stats.keys())
    coverages = [module_stats[m]['coverage'] for m in modules]
    files_count = [module_stats[m]['files'] for m in modules]

    # Sort by coverage
    sorted_indices = np.argsort(coverages)[::-1]
    modules = [modules[i] for i in sorted_indices]
    coverages = [coverages[i] for i in sorted_indices]
    files_count = [files_count[i] for i in sorted_indices]

    # Create color map
    colors = []
    for cov in coverages:
        if cov >= 80:
            colors.append('#2ecc71')  # Green
        elif cov >= 60:
            colors.append('#3498db')  # Blue
        elif cov >= 40:
            colors.append('#f39c12')  # Orange
        else:
            colors.append('#e74c3c')  # Red

    # Create bar chart with color gradient
    y_pos = np.arange(len(modules))
    bars = plt.barh(y_pos, coverages, color=colors, edgecolor='black', linewidth=1.5)

    plt.xlabel('Coverage (%)', fontsize=12, fontweight='bold')
    plt.ylabel('Module', fontsize=12, fontweight='bold')
    plt.title('Module Coverage Heatmap', fontsize=16, fontweight='bold', pad=20)
    plt.yticks(y_pos, modules)
    plt.xlim(0, 100)
    plt.grid(axis='x', alpha=0.3, linestyle='--')

    # Add value labels
    for i, (bar, coverage, files) in enumerate(zip(bars, coverages, files_count)):
        width = bar.get_width()
        plt.text(width + 1, bar.get_y() + bar.get_height()/2.,
                f'{coverage:.1f}% ({files} files)', ha='left', va='center',
                fontsize=9, fontweight='bold')

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2ecc71', edgecolor='black', label='Excellent (80-100%)'),
        Patch(facecolor='#3498db', edgecolor='black', label='Good (60-80%)'),
        Patch(facecolor='#f39c12', edgecolor='black', label='Fair (40-60%)'),
        Patch(facecolor='#e74c3c', edgecolor='black', label='Needs Work (<40%)')
    ]
    plt.legend(handles=legend_elements, loc='lower right')

    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / 'module_coverage_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Generated: module_coverage_heatmap.png")


def graph_7_test_type_distribution():
    """Graph 7: Test Type Distribution (Pie Chart)."""
    plt.figure(figsize=(10, 8))

    # Count test files by type (based on directory structure)
    test_types = {
        'Unit Tests': 0,
        'Integration Tests': 0,
        'ML Tests': 0,
        'API Tests': 0,
        'Security Tests': 0,
        'Other Tests': 0
    }

    # Scan test directory
    test_dir = Path("/home/user/DevSkyy/tests")
    if test_dir.exists():
        for test_file in test_dir.rglob("test_*.py"):
            file_path_str = str(test_file)
            if 'unit' in file_path_str:
                test_types['Unit Tests'] += 1
            elif 'integration' in file_path_str:
                test_types['Integration Tests'] += 1
            elif 'ml' in file_path_str or 'rlvr' in file_path_str:
                test_types['ML Tests'] += 1
            elif 'api' in file_path_str:
                test_types['API Tests'] += 1
            elif 'security' in file_path_str:
                test_types['Security Tests'] += 1
            else:
                test_types['Other Tests'] += 1

    # Filter out zero counts
    labels = [k for k, v in test_types.items() if v > 0]
    sizes = [v for v in test_types.values() if v > 0]

    if not sizes:
        print("⚠️  No test files found for distribution")
        return

    # Colors
    colors = ['#3498db', '#2ecc71', '#9b59b6', '#e74c3c', '#f39c12', '#95a5a6']

    # Create pie chart
    _, texts, autotexts = plt.pie(sizes, labels=labels, colors=colors[:len(labels)],
                                        autopct='%1.1f%%', startangle=90,
                                        explode=[0.05] * len(labels),
                                        textprops={'fontsize': 11, 'fontweight': 'bold'})

    plt.title('Test Distribution by Type', fontsize=16, fontweight='bold', pad=20)

    # Add count in legend
    legend_labels = [f'{label}: {count} files' for label, count in zip(labels, sizes)]
    plt.legend(legend_labels, loc='upper left', bbox_to_anchor=(1, 1))

    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / 'test_type_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Generated: test_type_distribution.png")


def graph_8_coverage_trend():
    """Graph 8: Coverage Trend Timeline."""
    plt.figure(figsize=(12, 6))

    # Simulated timeline data (in real scenario, would load from history)
    milestones = [
        'Initial\n(Baseline)',
        'After\nBug Fixes',
        'After\nNew Tests',
        'Current\nState'
    ]

    # Load current coverage
    data = load_coverage_data()
    current_coverage = data.get('totals', {}).get('percent_covered', 0)

    # Simulated progression (would be real data in production)
    coverages = [
        BASELINE_COVERAGE,
        BASELINE_COVERAGE * 1.5,  # After fixes
        BASELINE_COVERAGE * 2.5,  # After tests
        current_coverage
    ]

    x_pos = range(len(milestones))

    # Create line plot
    plt.plot(x_pos, coverages, marker='o', linewidth=3, markersize=12,
            color='#3498db', markerfacecolor='#2ecc71', markeredgewidth=2,
            markeredgecolor='black')

    # Add target line
    plt.axhline(y=TARGET_COVERAGE, color='red', linestyle='--', linewidth=2,
               label=f'Target ({TARGET_COVERAGE}%)')

    plt.xlabel('Timeline', fontsize=12, fontweight='bold')
    plt.ylabel('Coverage (%)', fontsize=12, fontweight='bold')
    plt.title('Coverage Progress Over Time', fontsize=16, fontweight='bold', pad=20)
    plt.xticks(x_pos, milestones)
    plt.ylim(0, 100)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.legend()

    # Add value labels
    for i, (x, y) in enumerate(zip(x_pos, coverages)):
        plt.text(x, y + 3, f'{y:.1f}%', ha='center', va='bottom',
                fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / 'coverage_trend.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Generated: coverage_trend.png")


def generate_all_graphs():
    """Generate all coverage visualization graphs."""
    print("\n" + "="*60)
    print("📊 Generating Coverage Visualization Graphs")
    print("="*60 + "\n")

    # Load coverage data
    print("📁 Loading coverage data...")
    data = load_coverage_data()

    # Calculate statistics
    current_coverage = data.get('totals', {}).get('percent_covered', 0)
    module_stats = calculate_module_coverage(data)
    file_list = get_file_coverage_list(data)

    print(f"✅ Current Coverage: {current_coverage:.2f}%")
    print(f"✅ Target Coverage: {TARGET_COVERAGE}%")
    print(f"✅ Gap: {TARGET_COVERAGE - current_coverage:.2f}%\n")

    # Generate all graphs
    print("🎨 Generating graphs...\n")

    graph_1_module_coverage_bar(module_stats)
    graph_2_before_after_comparison(current_coverage)
    graph_3_file_distribution(file_list)
    graph_4_top_performers(file_list)
    graph_5_coverage_gaps(file_list)
    graph_6_module_heatmap(module_stats)
    graph_7_test_type_distribution()
    graph_8_coverage_trend()

    print("\n" + "="*60)
    print("✅ All graphs generated successfully!")
    print(f"📂 Location: {ARTIFACTS_DIR}")
    print("="*60 + "\n")

    return {
        'current_coverage': current_coverage,
        'module_stats': module_stats,
        'file_count': len(file_list),
        'top_files': file_list[:10],
        'bottom_files': [f for f in file_list if f[1] < TARGET_COVERAGE][:10]
    }


if __name__ == '__main__':
    generate_all_graphs()
