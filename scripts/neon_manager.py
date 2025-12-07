#!/usr/bin/env python3
"""
Neon Database Management Script for DevSkyy
Manages Neon branches and databases programmatically

Author: DevSkyy Team
Version: 1.0.0
Usage: python scripts/neon_manager.py [command]
"""

import os
from pathlib import Path
import sys


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from neon_api import NeonAPI
except ImportError:
    print("❌ Error: neon-api package not installed")
    print("   Run: pip install neon-api")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ Error: python-dotenv package not installed")
    print("   Run: pip install python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()


class NeonManager:
    """Manage Neon databases and branches for DevSkyy"""

    def __init__(self):
        self.api_key = os.getenv("NEON_API_KEY")
        self.project_id = os.getenv("NEON_PROJECT_ID")

        if not self.api_key:
            raise ValueError(
                "NEON_API_KEY not set in environment. "
                "Get it from: https://console.neon.tech/app/settings/api-keys"
            )
        if not self.project_id:
            raise ValueError(
                "NEON_PROJECT_ID not set in environment. "
                "Find it in your Neon dashboard URL or project settings"
            )

        self.client = NeonAPI(api_key=self.api_key)
        print(f"✅ Connected to Neon project: {self.project_id}")

    def create_environment_branches(self):
        """Create dev, staging, and prod branches"""
        environments = ["dev", "staging", "prod"]

        print("\n📊 Creating environment branches...")

        for env in environments:
            try:
                branch = self.client.branches.create(
                    project_id=self.project_id, branch_name=env, parent_branch_id="main"
                )
                print(f"\n✅ Created {env} branch:")
                print(f"   Branch ID: {branch.id}")
                print(f"   Connection: {branch.connection_uri}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"ℹ️  {env} branch already exists")
                else:
                    print(f"❌ Failed to create {env} branch: {e}")

    def list_branches(self):
        """List all branches"""
        try:
            branches = self.client.branches.list(project_id=self.project_id)

            print(f"\n📊 Branches in project {self.project_id}:")
            print("-" * 80)

            for branch in branches:
                print(f"\n  Branch: {branch.name}")
                print(f"  ID: {branch.id}")
                print(f"  Created: {branch.created_at}")
                print(f"  Status: {branch.state}")

            print(f"\n  Total branches: {len(branches)}")

        except Exception as e:
            print(f"❌ Error listing branches: {e}")

    def get_connection_strings(self):
        """Get connection strings for all branches"""
        try:
            branches = self.client.branches.list(project_id=self.project_id)

            print("\n🔗 Connection Strings:")
            print("=" * 80)

            for branch in branches:
                print(f"\n{branch.name.upper()} BRANCH:")
                print(f"DATABASE_URL={branch.connection_uri}")

                # Also provide formatted for .env
                print(f"\n# For .env.{branch.name}:")
                print(f"DATABASE_URL={branch.connection_uri}")

            print("\n" + "=" * 80)

        except Exception as e:
            print(f"❌ Error getting connection strings: {e}")

    def create_test_database(self):
        """Create a test database for CI/CD"""
        try:
            # Get dev branch
            branches = self.client.branches.list(project_id=self.project_id)
            dev_branch = next((b for b in branches if b.name == "dev"), None)

            if not dev_branch:
                print("❌ Dev branch not found. Create it first with:")
                print("   python scripts/neon_manager.py create-branches")
                return

            # Create test database
            database = self.client.databases.create(
                project_id=self.project_id, branch_id=dev_branch.id, database_name="devskyy_test"
            )

            print(f"✅ Created test database: {database.name}")
            print(f"   Branch: {dev_branch.name}")
            print(f"   Database: {database.name}")

        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️  Test database already exists")
            else:
                print(f"❌ Failed to create test database: {e}")

    def show_project_info(self):
        """Show project information"""
        try:
            project = self.client.projects.get(project_id=self.project_id)

            print("\n📊 Project Information:")
            print("=" * 80)
            print(f"Project ID: {project.id}")
            print(f"Name: {project.name}")
            print(f"Region: {project.region_id}")
            print(f"Created: {project.created_at}")
            print(f"Status: {project.state}")
            print("=" * 80)

        except Exception as e:
            print(f"❌ Error getting project info: {e}")

    def delete_branch(self, branch_name: str):
        """Delete a branch (use with caution!)"""
        try:
            branches = self.client.branches.list(project_id=self.project_id)
            branch = next((b for b in branches if b.name == branch_name), None)

            if not branch:
                print(f"❌ Branch '{branch_name}' not found")
                return

            if branch_name == "main":
                print("❌ Cannot delete main branch!")
                return

            # Confirm deletion
            confirm = input(f"⚠️  Delete branch '{branch_name}'? This cannot be undone. (yes/no): ")
            if confirm.lower() != "yes":
                print("Cancelled.")
                return

            self.client.branches.delete(project_id=self.project_id, branch_id=branch.id)

            print(f"✅ Deleted branch: {branch_name}")

        except Exception as e:
            print(f"❌ Error deleting branch: {e}")

    def show_usage_stats(self):
        """Show project usage statistics"""
        try:
            # Get project consumption data
            print("\n📊 Usage Statistics:")
            print("=" * 80)
            print("Note: Detailed usage stats require API access")
            print("View full usage in Neon dashboard:")
            print(f"https://console.neon.tech/app/projects/{self.project_id}")
            print("=" * 80)

        except Exception as e:
            print(f"❌ Error getting usage stats: {e}")


def print_help():
    """Print usage help"""
    print("\n📖 DevSkyy Neon Manager - Usage:")
    print("=" * 80)
    print("\nCommands:")
    print("  create-branches       - Create dev/staging/prod branches")
    print("  list-branches         - List all branches")
    print("  connection-strings    - Get connection strings for all branches")
    print("  create-test-db        - Create test database")
    print("  project-info          - Show project information")
    print("  delete-branch <name>  - Delete a branch (use with caution!)")
    print("  usage-stats           - Show usage statistics")
    print("  help                  - Show this help message")
    print("\nExamples:")
    print("  python scripts/neon_manager.py create-branches")
    print("  python scripts/neon_manager.py list-branches")
    print("  python scripts/neon_manager.py connection-strings")
    print("  python scripts/neon_manager.py delete-branch old-feature")
    print("\nEnvironment Variables Required:")
    print("  NEON_API_KEY     - Your Neon API key")
    print("  NEON_PROJECT_ID  - Your Neon project ID")
    print("\nGet your API key: https://console.neon.tech/app/settings/api-keys")
    print("=" * 80)


def main():
    """Main entry point"""
    print("\n🌹 DevSkyy Neon Database Manager v1.0.0")

    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]

    if command == "help" or command == "--help" or command == "-h":
        print_help()
        return

    # Initialize manager
    try:
        manager = NeonManager()
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nAdd to your .env file:")
        print("NEON_API_KEY=your_api_key_here")
        print("NEON_PROJECT_ID=your_project_id_here")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Initialization Error: {e}")
        sys.exit(1)

    # Execute command
    try:
        if command == "create-branches":
            manager.create_environment_branches()
        elif command == "list-branches":
            manager.list_branches()
        elif command == "connection-strings":
            manager.get_connection_strings()
        elif command == "create-test-db":
            manager.create_test_database()
        elif command == "project-info":
            manager.show_project_info()
        elif command == "delete-branch":
            if len(sys.argv) < 3:
                print("❌ Usage: python scripts/neon_manager.py delete-branch <branch_name>")
                sys.exit(1)
            manager.delete_branch(sys.argv[2])
        elif command == "usage-stats":
            manager.show_usage_stats()
        else:
            print(f"❌ Unknown command: {command}")
            print_help()
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error executing command: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
