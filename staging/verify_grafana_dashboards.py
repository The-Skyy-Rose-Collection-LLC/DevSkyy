#!/usr/bin/env python3
"""
DevSkyy Grafana Dashboard Verification
Purpose: Verify Grafana dashboards are operational and populated with data
Usage: python verify_grafana_dashboards.py
"""

import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Optional

import requests


@dataclass
class PanelStatus:
    """Dashboard panel status"""

    id: int
    title: str
    type: str
    has_data: bool
    query_count: int
    status: str  # ok, warning, error


@dataclass
class DashboardStatus:
    """Dashboard verification status"""

    uid: str
    title: str
    version: int
    panel_count: int
    panels_with_data: int
    panels_without_data: int
    panels: list[PanelStatus]
    overall_status: str
    url: str


@dataclass
class GrafanaVerificationReport:
    """Complete Grafana verification report"""

    timestamp: str
    grafana_url: str
    grafana_version: str
    datasource_status: dict[str, str]
    dashboards: list[DashboardStatus]
    overall_status: str
    issues: list[str]
    recommendations: list[str]


class GrafanaClient:
    """Client for interacting with Grafana API"""

    def __init__(self, base_url: str, username: str = "admin", password: str = "admin"):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api"
        self.auth = (username, password)
        self.headers = {"Content-Type": "application/json"}

    def check_health(self) -> bool:
        """Check if Grafana is healthy"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_version(self) -> str:
        """Get Grafana version"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                return response.json().get("version", "unknown")
        except requests.exceptions.RequestException:
            pass
        return "unknown"

    def get_datasources(self) -> list[dict[str, Any]]:
        """Get all datasources"""
        try:
            response = requests.get(
                f"{self.api_url}/datasources", auth=self.auth, headers=self.headers, timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching datasources: {e}")
        return []

    def test_datasource(self, datasource_id: int) -> bool:
        """Test datasource connectivity"""
        try:
            response = requests.get(
                f"{self.api_url}/datasources/{datasource_id}/health",
                auth=self.auth,
                headers=self.headers,
                timeout=10,
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def search_dashboards(self, query: str = "") -> list[dict[str, Any]]:
        """Search for dashboards"""
        try:
            response = requests.get(
                f"{self.api_url}/search",
                params={"type": "dash-db", "query": query},
                auth=self.auth,
                headers=self.headers,
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error searching dashboards: {e}")
        return []

    def get_dashboard_by_uid(self, uid: str) -> Optional[dict[str, Any]]:
        """Get dashboard by UID"""
        try:
            response = requests.get(
                f"{self.api_url}/dashboards/uid/{uid}",
                auth=self.auth,
                headers=self.headers,
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching dashboard {uid}: {e}")
        return None

    def query_panel(self, datasource_uid: str, query: str, start: int, end: int) -> dict[str, Any]:
        """Query panel data from datasource"""
        try:
            # Construct query for Prometheus datasource
            payload = {
                "queries": [
                    {
                        "datasource": {"uid": datasource_uid},
                        "expr": query,
                        "refId": "A",
                        "instant": False,
                        "range": True,
                    }
                ],
                "from": str(start * 1000),
                "to": str(end * 1000),
            }

            response = requests.post(
                f"{self.api_url}/ds/query",
                json=payload,
                auth=self.auth,
                headers=self.headers,
                timeout=15,
            )

            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying panel: {e}")
        return {"results": {}}


class GrafanaDashboardVerifier:
    """Main class for verifying Grafana dashboards"""

    def __init__(
        self,
        grafana_url: str = "http://localhost:3000",
        username: str = "admin",
        password: str = "admin",
    ):
        self.client = GrafanaClient(grafana_url, username, password)
        self.report_dir = "monitoring_logs"
        os.makedirs(self.report_dir, exist_ok=True)

    def verify_datasources(self) -> dict[str, str]:
        """Verify all datasources are working"""
        print("\nVerifying datasources...")

        datasources = self.client.get_datasources()
        status_map = {}

        for ds in datasources:
            ds_name = ds.get("name", "unknown")
            ds_id = ds.get("id")

            print(f"  Testing datasource: {ds_name}...")

            if self.client.test_datasource(ds_id):
                status_map[ds_name] = "healthy"
                print(f"    ✓ {ds_name} is healthy")
            else:
                status_map[ds_name] = "unhealthy"
                print(f"    ✗ {ds_name} is unhealthy")

        return status_map

    def extract_queries_from_target(self, target: dict[str, Any]) -> list[str]:
        """Extract Prometheus queries from panel target"""
        queries = []

        # Handle different query formats
        if "expr" in target:
            queries.append(target["expr"])
        elif "target" in target:
            queries.append(target["target"])

        return queries

    def check_panel_data(self, panel: dict[str, Any], datasource_uid: str) -> bool:
        """Check if panel has data"""
        targets = panel.get("targets", [])

        if not targets:
            return False

        # Get current time range (last 5 minutes)
        end = int(time.time())
        start = end - 300

        for target in targets:
            queries = self.extract_queries_from_target(target)

            for query in queries:
                if not query or query.strip() == "":
                    continue

                # Query the datasource
                result = self.client.query_panel(datasource_uid, query, start, end)

                # Check if we got data
                if result.get("results"):
                    for key, value in result["results"].items():
                        frames = value.get("frames", [])
                        if frames:
                            # Check if any frame has data
                            for frame in frames:
                                if frame.get("data", {}).get("values", []):
                                    return True

        return False

    def verify_dashboard(self, dashboard_info: dict[str, Any]) -> DashboardStatus:
        """Verify a single dashboard"""
        uid = dashboard_info.get("uid", "")
        title = dashboard_info.get("title", "Unknown")

        print(f"\nVerifying dashboard: {title} ({uid})")

        # Get full dashboard details
        dashboard_data = self.client.get_dashboard_by_uid(uid)

        if not dashboard_data:
            print("  ✗ Could not fetch dashboard data")
            return DashboardStatus(
                uid=uid,
                title=title,
                version=0,
                panel_count=0,
                panels_with_data=0,
                panels_without_data=0,
                panels=[],
                overall_status="error",
                url=f"{self.client.base_url}/d/{uid}",
            )

        dashboard = dashboard_data.get("dashboard", {})
        panels = dashboard.get("panels", [])

        # Find datasource UID (typically Prometheus)
        datasource_uid = None
        datasources = self.client.get_datasources()
        for ds in datasources:
            if ds.get("type") == "prometheus":
                datasource_uid = ds.get("uid")
                break

        panel_statuses = []
        panels_with_data = 0
        panels_without_data = 0

        for panel in panels:
            # Skip row panels
            if panel.get("type") == "row":
                continue

            panel_id = panel.get("id", 0)
            panel_title = panel.get("title", f"Panel {panel_id}")
            panel_type = panel.get("type", "unknown")

            print(f"  Checking panel: {panel_title} ({panel_type})...")

            # Check if panel has data
            has_data = False
            if datasource_uid:
                has_data = self.check_panel_data(panel, datasource_uid)

            if has_data:
                panels_with_data += 1
                status = "ok"
                print("    ✓ Panel has data")
            else:
                panels_without_data += 1
                status = "warning"
                print("    ⚠ Panel has no data")

            targets = panel.get("targets", [])
            query_count = len([t for t in targets if t.get("expr") or t.get("target")])

            panel_statuses.append(
                PanelStatus(
                    id=panel_id,
                    title=panel_title,
                    type=panel_type,
                    has_data=has_data,
                    query_count=query_count,
                    status=status,
                )
            )

        # Determine overall dashboard status
        total_panels = len(panel_statuses)
        if total_panels == 0:
            overall_status = "error"
        elif panels_without_data == 0:
            overall_status = "ok"
        elif panels_with_data > 0:
            overall_status = "warning"
        else:
            overall_status = "error"

        return DashboardStatus(
            uid=uid,
            title=title,
            version=dashboard.get("version", 0),
            panel_count=total_panels,
            panels_with_data=panels_with_data,
            panels_without_data=panels_without_data,
            panels=panel_statuses,
            overall_status=overall_status,
            url=f"{self.client.base_url}/d/{uid}",
        )

    def generate_report(self) -> GrafanaVerificationReport:
        """Generate comprehensive Grafana verification report"""
        print("\n" + "=" * 60)
        print("DevSkyy Grafana Dashboard Verification")
        print("=" * 60)

        # Check Grafana health
        print("\nChecking Grafana connectivity...")
        if not self.client.check_health():
            print("ERROR: Cannot connect to Grafana")
            sys.exit(1)
        print("Connected to Grafana successfully")

        # Get Grafana version
        version = self.client.get_version()
        print(f"Grafana version: {version}")

        # Verify datasources
        datasource_status = self.verify_datasources()

        # Search for security-related dashboards
        dashboards = self.client.search_dashboards(query="")

        if not dashboards:
            print("\nWARNING: No dashboards found")

        dashboard_statuses = []
        for dashboard in dashboards:
            status = self.verify_dashboard(dashboard)
            dashboard_statuses.append(status)

        # Collect issues and recommendations
        issues = []
        recommendations = []

        # Check datasource issues
        for ds_name, ds_status in datasource_status.items():
            if ds_status != "healthy":
                issues.append(f"Datasource '{ds_name}' is {ds_status}")
                recommendations.append(f"Investigate and fix datasource: {ds_name}")

        # Check dashboard issues
        for dashboard in dashboard_statuses:
            if dashboard.overall_status == "error":
                issues.append(f"Dashboard '{dashboard.title}' has errors")
                recommendations.append(f"Review dashboard configuration: {dashboard.title}")
            elif dashboard.panels_without_data > 0:
                issues.append(
                    f"Dashboard '{dashboard.title}' has {dashboard.panels_without_data} panels without data"
                )
                if dashboard.panels_without_data == dashboard.panel_count:
                    recommendations.append(
                        f"Check Prometheus queries and data collection for: {dashboard.title}"
                    )

        # Determine overall status
        if any(ds != "healthy" for ds in datasource_status.values()):
            overall_status = "CRITICAL"
        elif any(d.overall_status == "error" for d in dashboard_statuses):
            overall_status = "ERROR"
        elif any(d.overall_status == "warning" for d in dashboard_statuses):
            overall_status = "WARNING"
        else:
            overall_status = "OK"

        if not issues:
            recommendations.append("All dashboards are operational and displaying data.")

        return GrafanaVerificationReport(
            timestamp=datetime.utcnow().isoformat(),
            grafana_url=self.client.base_url,
            grafana_version=version,
            datasource_status=datasource_status,
            dashboards=dashboard_statuses,
            overall_status=overall_status,
            issues=issues,
            recommendations=recommendations,
        )

    def save_report(self, report: GrafanaVerificationReport):
        """Save report to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON report
        json_file = os.path.join(self.report_dir, f"grafana_verification_report_{timestamp}.json")

        # Convert dataclass to dict
        report_dict = asdict(report)

        with open(json_file, "w") as f:
            json.dump(report_dict, f, indent=2)

        print(f"\nJSON report saved to: {json_file}")

        # Save human-readable report
        text_file = os.path.join(self.report_dir, f"grafana_verification_report_{timestamp}.txt")

        with open(text_file, "w") as f:
            self.write_text_report(f, report)

        print(f"Text report saved to: {text_file}")

    def write_text_report(self, file, report: GrafanaVerificationReport):
        """Write human-readable text report"""
        file.write("=" * 60 + "\n")
        file.write("DevSkyy Grafana Dashboard Verification Report\n")
        file.write("=" * 60 + "\n\n")

        file.write(f"Timestamp: {report.timestamp}\n")
        file.write(f"Grafana URL: {report.grafana_url}\n")
        file.write(f"Grafana Version: {report.grafana_version}\n")
        file.write(f"Overall Status: {report.overall_status}\n\n")

        file.write("-" * 60 + "\n")
        file.write("Datasource Status\n")
        file.write("-" * 60 + "\n\n")

        for ds_name, ds_status in report.datasource_status.items():
            status_symbol = "✓" if ds_status == "healthy" else "✗"
            file.write(f"{status_symbol} {ds_name}: {ds_status}\n")

        file.write("\n")
        file.write("-" * 60 + "\n")
        file.write("Dashboard Status\n")
        file.write("-" * 60 + "\n\n")

        for dashboard in report.dashboards:
            status_symbol = {"ok": "✓", "warning": "⚠", "error": "✗"}.get(
                dashboard.overall_status, "?"
            )

            file.write(f"{status_symbol} {dashboard.title}\n")
            file.write(f"  UID: {dashboard.uid}\n")
            file.write(f"  URL: {dashboard.url}\n")
            file.write(f"  Total Panels: {dashboard.panel_count}\n")
            file.write(f"  Panels with Data: {dashboard.panels_with_data}\n")
            file.write(f"  Panels without Data: {dashboard.panels_without_data}\n")
            file.write(f"  Status: {dashboard.overall_status.upper()}\n\n")

        if report.issues:
            file.write("-" * 60 + "\n")
            file.write("Issues Found\n")
            file.write("-" * 60 + "\n\n")

            for i, issue in enumerate(report.issues, 1):
                file.write(f"{i}. {issue}\n")

            file.write("\n")

        file.write("-" * 60 + "\n")
        file.write("Recommendations\n")
        file.write("-" * 60 + "\n\n")

        for i, recommendation in enumerate(report.recommendations, 1):
            file.write(f"{i}. {recommendation}\n")

        file.write("\n" + "=" * 60 + "\n")

    def print_summary(self, report: GrafanaVerificationReport):
        """Print summary to console"""
        print("\n" + "=" * 60)
        print("Grafana Verification Summary")
        print("=" * 60 + "\n")

        status_color = {
            "OK": "\033[0;32m",
            "WARNING": "\033[1;33m",
            "ERROR": "\033[0;31m",
            "CRITICAL": "\033[0;31m",
        }
        color = status_color.get(report.overall_status, "")
        reset = "\033[0m"

        print(f"Overall Status: {color}{report.overall_status}{reset}\n")

        print("Datasources:")
        for ds_name, ds_status in report.datasource_status.items():
            print(f"  {ds_name}: {ds_status}")

        print(f"\nDashboards: {len(report.dashboards)} found")

        operational = sum(1 for d in report.dashboards if d.overall_status == "ok")
        print(f"  Operational: {operational}")
        print(f"  With Issues: {len(report.dashboards) - operational}")

        if report.recommendations:
            print("\nTop Recommendation:")
            print(f"  {report.recommendations[0]}")

        print("\n" + "=" * 60 + "\n")


def main():
    """Main execution function"""
    # Get configuration from environment or use defaults
    grafana_url = os.getenv("GRAFANA_URL", "http://localhost:3000")
    username = os.getenv("GRAFANA_USERNAME", "admin")
    password = os.getenv("GRAFANA_PASSWORD", "admin")

    # Create verifier and generate report
    verifier = GrafanaDashboardVerifier(grafana_url, username, password)

    try:
        report = verifier.generate_report()
        verifier.save_report(report)
        verifier.print_summary(report)

        # Exit with appropriate code
        if report.overall_status in ["CRITICAL", "ERROR"]:
            sys.exit(2)
        elif report.overall_status == "WARNING":
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
