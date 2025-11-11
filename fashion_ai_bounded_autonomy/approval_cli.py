#!/usr/bin/env python3
"""
Approval CLI Tool
Command-line interface for operators to review and approve agent actions

Usage:
    python -m fashion_ai_bounded_autonomy.approval_cli list
    python -m fashion_ai_bounded_autonomy.approval_cli review <action_id>
    python -m fashion_ai_bounded_autonomy.approval_cli approve <action_id> --operator <name>
    python -m fashion_ai_bounded_autonomy.approval_cli reject <action_id> --operator <name> --reason <reason>
    python -m fashion_ai_bounded_autonomy.approval_cli stats [--operator <name>]
"""

import argparse
import asyncio
import json
from pathlib import Path
import sys
from typing import Optional


# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fashion_ai_bounded_autonomy.approval_system import ApprovalSystem
from fashion_ai_bounded_autonomy.i18n_loader import t


class ApprovalCLI:
    """Interactive CLI for reviewing and approving agent actions"""

    def __init__(self):
        self.approval_system = ApprovalSystem()
        self.colors = {
            "RED": "\033[91m",
            "GREEN": "\033[92m",
            "YELLOW": "\033[93m",
            "BLUE": "\033[94m",
            "MAGENTA": "\033[95m",
            "CYAN": "\033[96m",
            "BOLD": "\033[1m",
            "END": "\033[0m"
        }

    def colorize(self, text: str, color: str) -> str:
        """Add color to text"""
        return f"{self.colors.get(color, '')}{text}{self.colors['END']}"

    async def list_pending(self):
        """
        Prints a formatted, colorized list of pending approval actions to the console.
        
        If there are pending actions, each entry shows an index, action ID, agent, function, risk level, creation time, and expiry time; the function also prints a total count and a short hint for how to review an action. If no actions are pending, prints an empty-state confirmation.
        """
        print(self.colorize(f"\n📋 {t('cli.list_pending')}\n", "BOLD"))

        actions = await self.approval_system.get_pending_actions()

        if not actions:
            print(self.colorize(f"✓ {t('cli.list_empty')}", "GREEN"))
            return

        for idx, action in enumerate(actions, 1):
            risk_color = {
                "low": "GREEN",
                "medium": "YELLOW",
                "high": "MAGENTA",
                "critical": "RED"
            }.get(action["risk_level"], "CYAN")

            print(f"{self.colorize(f'[{idx}]', 'BOLD')} {self.colorize(action['action_id'], 'CYAN')}")
            print(f"    Agent: {action['agent_name']}")
            print(f"    Function: {action['function_name']}")
            print(f"    Risk: {self.colorize(action['risk_level'].upper(), risk_color)}")
            print(f"    Created: {action['created_at']}")
            print(f"    Expires: {action['timeout_at']}")
            print()

        print(self.colorize(f"\nTotal pending: {len(actions)}", "BOLD"))
        print("\nTo review: python -m fashion_ai_bounded_autonomy.approval_cli review <action_id>")

    async def review_action(self, action_id: str):
        """
        Prints a detailed, human-readable view of the specified approval action to stdout.
        
        Displays identification, risk assessment, parameters, status (including approval or rejection metadata), audit trail, and execution result for the action identified by action_id. If the action is pending, also prints suggested CLI commands to approve or reject it. If no action matches action_id, prints a not-found message.
         
        Parameters:
            action_id (str): The identifier of the action to display.
        """
        details = await self.approval_system.get_action_details(action_id)

        if not details:
            print(self.colorize(f"❌ {t('approval.not_found', action_id=action_id)}", "RED"))
            return

        print(self.colorize("\n🔍 ACTION DETAILS\n", "BOLD"))
        print("=" * 70)

        # Basic info
        print(self.colorize("IDENTIFICATION", "BOLD"))
        print(f"  Action ID: {self.colorize(details['action_id'], 'CYAN')}")
        print(f"  Agent: {details['agent_name']}")
        print(f"  Function: {details['function_name']}")

        # Risk assessment
        risk_color = {
            "low": "GREEN",
            "medium": "YELLOW",
            "high": "MAGENTA",
            "critical": "RED"
        }.get(details['risk_level'], "CYAN")
        print(f"\n{self.colorize('RISK ASSESSMENT', 'BOLD')}")
        print(f"  Risk Level: {self.colorize(details['risk_level'].upper(), risk_color)}")
        print(f"  Workflow: {details['workflow_type']}")

        # Parameters
        print(f"\n{self.colorize('PARAMETERS', 'BOLD')}")
        for key, value in details['parameters'].items():
            if isinstance(value, (dict, list)):
                print(f"  {key}:")
                print(f"    {json.dumps(value, indent=4)}")
            else:
                print(f"  {key}: {value}")

        # Status
        status_color = {
            "pending": "YELLOW",
            "approved": "GREEN",
            "rejected": "RED",
            "expired": "MAGENTA",
            "executed": "CYAN"
        }.get(details['status'], "CYAN")
        print(f"\n{self.colorize('STATUS', 'BOLD')}")
        print(f"  Current: {self.colorize(details['status'].upper(), status_color)}")
        print(f"  Created: {details['created_at']}")
        print(f"  Timeout: {details['timeout_at']}")

        if details['approved_at']:
            print(f"  Approved: {details['approved_at']} by {details['approved_by']}")
        if details['rejection_reason']:
            print(f"  Rejected: {details['rejection_reason']}")

        # History
        if details['history']:
            print(f"\n{self.colorize('AUDIT TRAIL', 'BOLD')}")
            for event in details['history']:
                timestamp = event['timestamp']
                event_type = event['event']
                operator = event.get('operator', 'system')
                print(f"  [{timestamp}] {event_type} by {operator}")

        # Execution result
        if details['execution_result']:
            print(f"\n{self.colorize('EXECUTION RESULT', 'BOLD')}")
            print(f"  {json.dumps(details['execution_result'], indent=2)}")

        print("=" * 70)

        # Actions
        if details['status'] == 'pending':
            print(f"\n{self.colorize('AVAILABLE ACTIONS:', 'BOLD')}")
            print(f"  Approve: python -m fashion_ai_bounded_autonomy.approval_cli approve {action_id} --operator <your_name>")
            print(f"  Reject:  python -m fashion_ai_bounded_autonomy.approval_cli reject {action_id} --operator <your_name> --reason \"<reason>\"")

    async def approve_action(self, action_id: str, operator: str, notes: Optional[str] = None):
        """
        Approve a pending action and display the outcome to the CLI.
        
        Approves the action identified by `action_id` on behalf of `operator`, optionally attaching `notes`. Prints a success message and the approval timestamp on success; prints an error message and returns if the approval fails.
        
        Parameters:
            action_id (str): Identifier of the action to approve.
            operator (str): Name or identifier of the operator performing the approval.
            notes (Optional[str]): Optional free-text notes to attach to the approval.
        """
        print(f"\n🔄 {t('cli.review_action', action_id=action_id)}...")

        result = await self.approval_system.approve(action_id, operator, notes)

        if result.get("error"):
            print(self.colorize(f"❌ {t('cli.error', message=result['error'])}", "RED"))
            return

        print(self.colorize(f"✅ {t('cli.approve_success')}", "GREEN"))
        print(f"Approved at: {result['approved_at']}")
        print("\n⚠️  Note: The action will be executed by the agent system automatically.")

    async def reject_action(self, action_id: str, operator: str, reason: str):
        """
        Rejects a pending approval action and records the rejection.
        
        Parameters:
            action_id (str): Identifier of the action to reject.
            operator (str): Name or identifier of the operator performing the rejection.
            reason (str): Short explanation recorded with the rejection.
        """
        print(f"\n🔄 {t('cli.review_action', action_id=action_id)}...")

        result = await self.approval_system.reject(action_id, operator, reason)

        if result.get("error"):
            print(self.colorize(f"❌ {t('cli.error', message=result['error'])}", "RED"))
            return

        print(self.colorize(f"⛔ {t('cli.reject_success')}", "RED"))
        print(f"Reason: {reason}")

    async def show_statistics(self, operator: Optional[str] = None):
        """
        Print formatted approval statistics to the terminal.
        
        When `operator` is provided, display a flat list of action counts for that operator.
        When `operator` is omitted, display per-operator blocks with their action counts.
        
        Parameters:
            operator (Optional[str]): If given, limit statistics to this operator's actions; otherwise show statistics for all operators.
        """
        print(self.colorize("\n📊 APPROVAL STATISTICS\n", "BOLD"))

        stats = await self.approval_system.get_operator_statistics(operator)

        if operator:
            print(f"Operator: {self.colorize(operator, 'CYAN')}")
            print("=" * 40)
            for action, count in stats.items():
                print(f"  {action}: {count}")
        else:
            for op, actions in stats.items():
                print(f"{self.colorize(op, 'CYAN')}:")
                for action, count in actions.items():
                    print(f"  {action}: {count}")
                print()

    async def cleanup_expired(self):
        """
        Remove expired approval actions and print a localized summary.
        
        Invokes the approval system's cleanup routine to delete actions past their timeout, prints a cleanup header, and outputs a translated confirmation message that includes the number of actions removed.
        """
        print("\n🧹 Cleaning up expired actions...")
        count = await self.approval_system.cleanup_expired()
        print(self.colorize(f"✅ {t('approval.cleanup_expired', count=count)}", "GREEN"))


async def main():
    """
    Entry point for the CLI that parses command-line arguments and dispatches to ApprovalCLI commands.
    
    Parses subcommands (list, review, approve, reject, stats, cleanup), validates required options, invokes the corresponding async ApprovalCLI method, and prints localized error information with a traceback if an unhandled exception occurs.
    """
    parser = argparse.ArgumentParser(
        description="Bounded Autonomy Approval CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    subparsers.add_parser("list", help="List pending actions")

    # Review command
    review_parser = subparsers.add_parser("review", help="Review action details")
    review_parser.add_argument("action_id", help="Action ID to review")

    # Approve command
    approve_parser = subparsers.add_parser("approve", help="Approve an action")
    approve_parser.add_argument("action_id", help="Action ID to approve")
    approve_parser.add_argument("--operator", required=True, help="Operator name")
    approve_parser.add_argument("--notes", help="Approval notes")

    # Reject command
    reject_parser = subparsers.add_parser("reject", help="Reject an action")
    reject_parser.add_argument("action_id", help="Action ID to reject")
    reject_parser.add_argument("--operator", required=True, help="Operator name")
    reject_parser.add_argument("--reason", required=True, help="Rejection reason")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.add_argument("--operator", help="Operator name (optional)")

    # Cleanup command
    subparsers.add_parser("cleanup", help="Clean up expired actions")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = ApprovalCLI()

    try:
        if args.command == "list":
            await cli.list_pending()
        elif args.command == "review":
            await cli.review_action(args.action_id)
        elif args.command == "approve":
            await cli.approve_action(args.action_id, args.operator, args.notes)
        elif args.command == "reject":
            await cli.reject_action(args.action_id, args.operator, args.reason)
        elif args.command == "stats":
            await cli.show_statistics(args.operator)
        elif args.command == "cleanup":
            await cli.cleanup_expired()
    except Exception as e:
        print(cli.colorize(f"\n❌ {t('cli.error', message=str(e))}", "RED"))
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())