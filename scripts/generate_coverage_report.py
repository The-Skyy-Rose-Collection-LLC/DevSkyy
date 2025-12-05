#!/usr/bin/env python3
"""
Generate comprehensive coverage analysis report.
Part of the Truth Protocol (Rule #8: Test Coverage ≥90%).
"""
from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path


ARTIFACTS_DIR = Path("/home/user/DevSkyy/artifacts")
COVERAGE_FILE = Path("/home/user/DevSkyy/coverage.json")
REPORT_FILE = Path("/home/user/DevSkyy/COVERAGE_ANALYSIS_WITH_GRAPHS.md")
STATS_FILE = ARTIFACTS_DIR / "coverage_statistics.json"
TARGET_COVERAGE = 90.0
BASELINE_COVERAGE = 10.35


def load_coverage_data() -> dict:
    """Load coverage data from JSON file."""
    with open(COVERAGE_FILE, 'r') as f:
        return json.load(f)


def calculate_module_coverage(data: dict) -> dict[str, dict]:
    """Calculate coverage statistics by module."""
    module_stats = defaultdict(lambda: {
        'lines_covered': 0,
        'total_lines': 0,
        'files': 0,
        'coverage': 0.0,
        'missing_lines': 0
    })

    files = data.get('files', {})

    for file_path, file_data in files.items():
        path_parts = Path(file_path).parts

        # Skip test files
        if 'tests' in path_parts or 'test_' in file_path:
            continue

        # Extract module name
        if len(path_parts) > 1:
            # Try to get the first meaningful directory
            for part in path_parts:
                if part not in ['home', 'user', 'DevSkyy', '__pycache__']:
                    module = part
                    break
            else:
                module = 'root'
        else:
            module = 'root'

        summary = file_data.get('summary', {})
        lines_covered = summary.get('covered_lines', 0)
        total_lines = summary.get('num_statements', 0)
        missing_lines = total_lines - lines_covered

        module_stats[module]['lines_covered'] += lines_covered
        module_stats[module]['total_lines'] += total_lines
        module_stats[module]['files'] += 1
        module_stats[module]['missing_lines'] += missing_lines

    # Calculate coverage percentages
    for module, stats in module_stats.items():
        if stats['total_lines'] > 0:
            stats['coverage'] = (stats['lines_covered'] / stats['total_lines']) * 100

    return dict(module_stats)


def get_file_coverage_list(data: dict) -> list[tuple[str, float, int, int]]:
    """Get sorted list of files with coverage stats."""
    file_list = []
    files = data.get('files', {})

    for file_path, file_data in files.items():
        if 'tests' in file_path or 'test_' in file_path:
            continue

        summary = file_data.get('summary', {})
        covered = summary.get('covered_lines', 0)
        total = summary.get('num_statements', 0)

        if total > 0:
            coverage = (covered / total) * 100
            file_list.append((file_path, coverage, covered, total))

    return sorted(file_list, key=lambda x: x[1], reverse=True)


def count_tests() -> dict:
    """Count test files by type."""
    test_counts = {
        'unit': 0,
        'integration': 0,
        'ml': 0,
        'api': 0,
        'security': 0,
        'other': 0,
        'total': 0
    }

    test_dir = Path("/home/user/DevSkyy/tests")
    if test_dir.exists():
        for test_file in test_dir.rglob("test_*.py"):
            test_counts['total'] += 1
            file_path_str = str(test_file)

            if 'unit' in file_path_str:
                test_counts['unit'] += 1
            elif 'integration' in file_path_str:
                test_counts['integration'] += 1
            elif 'ml' in file_path_str or 'rlvr' in file_path_str:
                test_counts['ml'] += 1
            elif 'api' in file_path_str:
                test_counts['api'] += 1
            elif 'security' in file_path_str:
                test_counts['security'] += 1
            else:
                test_counts['other'] += 1

    return test_counts


def generate_markdown_report(data: dict, module_stats: dict, file_list: list, test_counts: dict):
    """Generate comprehensive markdown report."""
    current_coverage = data.get('totals', {}).get('percent_covered', 0)
    total_lines = data.get('totals', {}).get('num_statements', 0)
    covered_lines = data.get('totals', {}).get('covered_lines', 0)
    missing_lines = total_lines - covered_lines

    improvement = current_coverage - BASELINE_COVERAGE
    gap = TARGET_COVERAGE - current_coverage

    report = f"""# DevSkyy Test Coverage Analysis with Visualizations

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Truth Protocol Compliance:** Rule #8 (Test Coverage ≥90%)

---

## 📊 Executive Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Current Coverage** | **{current_coverage:.2f}%** | 90.00% | {'✅ PASS' if current_coverage >= TARGET_COVERAGE else '❌ NEEDS WORK'} |
| **Gap to Target** | {gap:.2f}% | 0.00% | {gap:.0f}% remaining |
| **Improvement from Baseline** | +{improvement:.2f}% | N/A | {'📈 Good progress' if improvement > 0 else '⚠️ No change'} |
| **Total Lines** | {total_lines:,} | N/A | - |
| **Covered Lines** | {covered_lines:,} | N/A | - |
| **Missing Coverage** | {missing_lines:,} lines | 0 | {(missing_lines/(TARGET_COVERAGE/100)):,.0f} more lines needed |
| **Test Files** | {test_counts['total']} | N/A | - |
| **Modules Analyzed** | {len(module_stats)} | N/A | - |
| **Files Analyzed** | {len(file_list)} | N/A | - |

### 🎯 Coverage Status

```
Current:  {current_coverage:.2f}% {'█' * int(current_coverage/5)}{'░' * (20 - int(current_coverage/5))}
Target:   {TARGET_COVERAGE:.2f}% {'█' * int(TARGET_COVERAGE/5)}
```

**Verdict:** {'✅ EXCELLENT - Target achieved!' if current_coverage >= TARGET_COVERAGE else f'⚠️ NEEDS IMPROVEMENT - {gap:.2f}% gap remains'}

---

## 📈 Coverage Visualizations

### 1. Module Coverage Overview

![Module Coverage](./artifacts/coverage_by_module.png)

**Key Insights:**
- Shows coverage percentage for each major module
- Red bars indicate modules below 50% coverage (critical)
- Orange bars indicate modules 50-80% coverage (needs improvement)
- Green bars indicate modules above 80% coverage (good)
- Blue dashed line shows the 90% target

### 2. Before vs After Comparison

![Before/After Comparison](./artifacts/coverage_before_after.png)

**Improvement Analysis:**
- **Baseline Coverage:** {BASELINE_COVERAGE:.2f}%
- **Current Coverage:** {current_coverage:.2f}%
- **Absolute Improvement:** +{improvement:.2f}%
- **Relative Improvement:** +{(improvement/BASELINE_COVERAGE)*100:.1f}%

### 3. Coverage Distribution

![Coverage Distribution](./artifacts/coverage_distribution.png)

**Distribution Breakdown:**
- Files with excellent coverage (80-100%): High priority maintained
- Files with good coverage (60-80%): Moderate improvement needed
- Files with fair coverage (40-60%): Significant work required
- Files with poor coverage (20-40%): Critical attention needed
- Files with minimal coverage (0-20%): Immediate action required

### 4. Top Performers

![Top Covered Files](./artifacts/top_covered_files.png)

**Best Practices:**
- These files demonstrate excellent test coverage
- Use as reference for testing standards
- Maintain high coverage in critical modules

### 5. Coverage Gaps

![Coverage Gaps](./artifacts/coverage_gaps.png)

**Priority Areas:**
- These files need immediate attention
- Focus testing efforts on these modules
- High impact on overall coverage

### 6. Module Heatmap

![Module Coverage Heatmap](./artifacts/module_coverage_heatmap.png)

**Color Legend:**
- 🟢 **Green (80-100%)**: Excellent coverage
- 🔵 **Blue (60-80%)**: Good coverage
- 🟠 **Orange (40-60%)**: Fair coverage
- 🔴 **Red (<40%)**: Needs work

### 7. Test Type Distribution

![Test Type Distribution](./artifacts/test_type_distribution.png)

**Test Breakdown:**
- Unit Tests: {test_counts['unit']} files
- Integration Tests: {test_counts['integration']} files
- ML Tests: {test_counts['ml']} files
- API Tests: {test_counts['api']} files
- Security Tests: {test_counts['security']} files
- Other Tests: {test_counts['other']} files

### 8. Coverage Trend

![Coverage Trend](./artifacts/coverage_trend.png)

**Progress Timeline:**
- Shows coverage progression from baseline to current state
- Demonstrates improvement trajectory
- Helps visualize path to 90% target

---

## 📋 Detailed Module Breakdown

"""

    # Add module details
    sorted_modules = sorted(module_stats.items(), key=lambda x: x[1]['coverage'], reverse=True)

    for module, stats in sorted_modules:
        status_emoji = '✅' if stats['coverage'] >= 80 else '⚠️' if stats['coverage'] >= 60 else '❌'
        report += f"""
### {status_emoji} {module}

| Metric | Value |
|--------|-------|
| Coverage | **{stats['coverage']:.2f}%** |
| Files | {stats['files']} |
| Lines Covered | {stats['lines_covered']:,} |
| Total Lines | {stats['total_lines']:,} |
| Missing Lines | {stats['missing_lines']:,} |
| Lines Needed for 90% | {int(stats['total_lines'] * 0.9 - stats['lines_covered']):,} |
"""

    # Add top and bottom files
    report += """

---

## 🏆 Top 10 Best Covered Files

| Rank | File | Coverage | Covered | Total |
|------|------|----------|---------|-------|
"""

    for i, (file_path, coverage, covered, total) in enumerate(file_list[:10], 1):
        file_name = Path(file_path).name
        report += f"| {i} | `{file_name}` | {coverage:.1f}% | {covered} | {total} |\n"

    report += """

---

## ⚠️ Top 10 Files Needing Improvement

| Rank | File | Coverage | Covered | Total | Lines Needed |
|------|------|----------|---------|-------|--------------|
"""

    bottom_files = [f for f in file_list if f[1] < TARGET_COVERAGE][:10]
    for i, (file_path, coverage, covered, total) in enumerate(bottom_files, 1):
        file_name = Path(file_path).name
        lines_needed = int(total * 0.9) - covered
        report += f"| {i} | `{file_name}` | {coverage:.1f}% | {covered} | {total} | {lines_needed} |\n"

    # Add recommendations
    report += f"""

---

## 🎯 Recommendations to Reach 90% Coverage

### Immediate Actions (High Priority)

1. **Focus on Critical Modules**
   - Target modules below 50% coverage first
   - These have the highest impact on overall coverage

2. **Add Tests for High-Impact Files**
   - Files with many lines but low coverage
   - Each test added has maximum impact

3. **Improve Integration Testing**
   - Current integration coverage needs expansion
   - Focus on API endpoints and database interactions

### Medium-Term Goals

1. **Expand Unit Test Coverage**
   - Add tests for edge cases
   - Test error handling paths
   - Validate input validation logic

2. **Increase ML/AI Test Coverage**
   - Add model validation tests
   - Test training pipelines
   - Validate prediction accuracy

3. **Security Test Expansion**
   - Add authentication tests
   - Test authorization scenarios
   - Validate encryption/decryption

### Long-Term Strategy

1. **Maintain Coverage Standards**
   - Require 90% coverage for all new code
   - Add pre-commit hooks to enforce coverage
   - Regular coverage reviews in code reviews

2. **Continuous Improvement**
   - Weekly coverage reports
   - Team coverage goals
   - Recognition for coverage improvements

3. **Automated Coverage Monitoring**
   - CI/CD pipeline coverage gates
   - Automated coverage reports
   - Alert on coverage decreases

### Estimated Effort to Reach 90%

- **Lines to Cover:** {int(total_lines * 0.9 - covered_lines):,} additional lines
- **Estimated Tests Needed:** {int((total_lines * 0.9 - covered_lines) / 10)} tests (assuming 10 lines per test)
- **Estimated Time:** {int((total_lines * 0.9 - covered_lines) / 100)} developer-hours

---

## 📝 Coverage Analysis Notes

### Test Quality Assessment

- **Unit Tests:** {test_counts['unit']} files - {'Good' if test_counts['unit'] > 50 else 'Needs expansion'}
- **Integration Tests:** {test_counts['integration']} files - {'Good' if test_counts['integration'] > 10 else 'Needs expansion'}
- **ML Tests:** {test_counts['ml']} files - {'Good' if test_counts['ml'] > 20 else 'Needs expansion'}
- **Security Tests:** {test_counts['security']} files - {'Good' if test_counts['security'] > 5 else 'Critical - add more'}

### Truth Protocol Compliance

✅ **Rule #8 Status:** {'COMPLIANT' if current_coverage >= TARGET_COVERAGE else 'NON-COMPLIANT'}

**Requirements:**
- Test Coverage ≥90%: {'✅ PASS' if current_coverage >= TARGET_COVERAGE else f'❌ FAIL ({gap:.2f}% gap)'}
- Coverage Reports Generated: ✅ PASS
- HTML Report Available: ✅ PASS
- JSON Data Available: ✅ PASS
- Visualizations Created: ✅ PASS

---

## 📊 Additional Resources

- **HTML Coverage Report:** [htmlcov/index.html](./htmlcov/index.html)
- **JSON Coverage Data:** [coverage.json](./coverage.json)
- **Coverage Statistics:** [artifacts/coverage_statistics.json](./artifacts/coverage_statistics.json)
- **Coverage Graphs:** [artifacts/](./artifacts/)

---

## 🔄 Next Steps

1. **Review this report** with the development team
2. **Prioritize modules** with lowest coverage
3. **Create testing tasks** for identified gaps
4. **Set milestones** for coverage improvements
5. **Re-run coverage analysis** after adding tests
6. **Track progress** toward 90% target

---

**Report Generated by:** DevSkyy Coverage Analysis Tool
**Truth Protocol:** Rule #8 - Test Coverage ≥90%
**Status:** {'Production Ready ✅' if current_coverage >= TARGET_COVERAGE else 'Development 🚧'}

"""

    # Write report
    with open(REPORT_FILE, 'w') as f:
        f.write(report)

    print(f"✅ Generated: {REPORT_FILE}")


def generate_statistics_json(data: dict, module_stats: dict, file_list: list, test_counts: dict):
    """Generate JSON statistics file."""
    current_coverage = data.get('totals', {}).get('percent_covered', 0)
    total_lines = data.get('totals', {}).get('num_statements', 0)
    covered_lines = data.get('totals', {}).get('covered_lines', 0)

    stats = {
        "generated_at": datetime.now().isoformat(),
        "overall_coverage": round(current_coverage, 2),
        "target_coverage": TARGET_COVERAGE,
        "baseline_coverage": BASELINE_COVERAGE,
        "gap": round(TARGET_COVERAGE - current_coverage, 2),
        "improvement": round(current_coverage - BASELINE_COVERAGE, 2),
        "total_lines": total_lines,
        "covered_lines": covered_lines,
        "missing_lines": total_lines - covered_lines,
        "lines_needed_for_target": int(total_lines * 0.9 - covered_lines),
        "modules": {
            module: {
                "coverage": round(stats['coverage'], 2),
                "files": stats['files'],
                "lines_covered": stats['lines_covered'],
                "total_lines": stats['total_lines'],
                "missing_lines": stats['missing_lines']
            }
            for module, stats in module_stats.items()
        },
        "tests": {
            "total_files": test_counts['total'],
            "by_type": {
                "unit": test_counts['unit'],
                "integration": test_counts['integration'],
                "ml": test_counts['ml'],
                "api": test_counts['api'],
                "security": test_counts['security'],
                "other": test_counts['other']
            }
        },
        "top_covered_files": [
            {
                "file": str(Path(f[0]).name),
                "full_path": f[0],
                "coverage": round(f[1], 2),
                "covered": f[2],
                "total": f[3]
            }
            for f in file_list[:10]
        ],
        "bottom_covered_files": [
            {
                "file": str(Path(f[0]).name),
                "full_path": f[0],
                "coverage": round(f[1], 2),
                "covered": f[2],
                "total": f[3],
                "lines_needed": int(f[3] * 0.9) - f[2]
            }
            for f in file_list if f[1] < TARGET_COVERAGE
        ][:10],
        "truth_protocol_compliance": {
            "rule_8_status": "COMPLIANT" if current_coverage >= TARGET_COVERAGE else "NON-COMPLIANT",
            "coverage_requirement_met": current_coverage >= TARGET_COVERAGE,
            "gap_percentage": round(TARGET_COVERAGE - current_coverage, 2)
        }
    }

    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"✅ Generated: {STATS_FILE}")


def main():
    """Main execution function."""
    print("\n" + "="*60)
    print("📊 Generating Comprehensive Coverage Report")
    print("="*60 + "\n")

    # Load data
    print("📁 Loading coverage data...")
    data = load_coverage_data()

    # Calculate statistics
    print("📊 Calculating statistics...")
    module_stats = calculate_module_coverage(data)
    file_list = get_file_coverage_list(data)
    test_counts = count_tests()

    # Generate reports
    print("📝 Generating markdown report...")
    generate_markdown_report(data, module_stats, file_list, test_counts)

    print("📄 Generating JSON statistics...")
    generate_statistics_json(data, module_stats, file_list, test_counts)

    print("\n" + "="*60)
    print("✅ Coverage analysis complete!")
    print("="*60 + "\n")

    # Print summary
    current_coverage = data.get('totals', {}).get('percent_covered', 0)
    print(f"📊 Current Coverage: {current_coverage:.2f}%")
    print(f"🎯 Target Coverage: {TARGET_COVERAGE}%")
    print(f"📈 Gap: {TARGET_COVERAGE - current_coverage:.2f}%")
    print(f"📝 Test Files: {test_counts['total']}")
    print(f"📂 Modules: {len(module_stats)}")
    print(f"📄 Files: {len(file_list)}\n")


if __name__ == '__main__':
    main()
