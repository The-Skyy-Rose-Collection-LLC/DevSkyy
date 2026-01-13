#!/usr/bin/env python3
"""
Monitor HuggingFace AutoTrain LoRA Training Progress.

Polls AutoTrain job status and displays real-time progress.

Usage:
    python3 scripts/monitor_autotrain.py
"""

import time
from datetime import datetime

try:
    from huggingface_hub import fetch_job_logs, inspect_job, list_jobs
except ImportError:
    print("Installing huggingface_hub...")
    import subprocess
    import sys

    subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
    from huggingface_hub import fetch_job_logs, inspect_job, list_jobs


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def monitor_training(poll_interval: int = 30):
    """Monitor AutoTrain job progress."""
    print("=" * 70)
    print("🚀 SkyyRose LoRA AutoTrain Monitor")
    print("=" * 70)
    print()

    # List all jobs and find most recent
    print("Fetching training jobs...")
    jobs = list(list_jobs())

    if not jobs:
        print("❌ No training jobs found")
        print("\n💡 Start training at: https://huggingface.co/new-space")
        return 1

    # Get most recent job
    job = jobs[0]
    print(f"📋 Monitoring Job: {job.id}")
    print(f"   Status: {job.status.stage}")
    print()

    start_time = time.time()
    last_stage = None

    try:
        while True:
            # Inspect job status
            job_info = inspect_job(job_id=job.id)
            current_stage = job_info.status.stage
            elapsed = time.time() - start_time

            # Status update
            timestamp = datetime.now().strftime("%H:%M:%S")

            if current_stage != last_stage:
                print(f"\n[{timestamp}] Status changed: {current_stage}")
                last_stage = current_stage

            # Progress indicator
            if current_stage == "RUNNING":
                print(
                    f"[{timestamp}] ⏳ Training in progress... (Elapsed: {format_duration(elapsed)})",
                    end="\r",
                )

            elif current_stage == "COMPLETED":
                print(f"\n\n✅ Training Complete! (Total: {format_duration(elapsed)})")
                print("=" * 70)
                print("\n📦 Trained Model Location:")
                print(f"   Job ID: {job.id}")
                print("\n📋 Next Steps:")
                print("   1. Download model from HuggingFace")
                print("   2. Test with Stable Diffusion inference")
                print("   3. Integrate into product generation pipeline")
                return 0

            elif current_stage == "ERROR":
                print(f"\n\n❌ Training Failed after {format_duration(elapsed)}")
                print("=" * 70)
                print(f"Error: {job_info.status.message}")

                # Fetch logs for debugging
                print("\n📜 Error Logs:")
                print("-" * 70)
                try:
                    for log in fetch_job_logs(job_id=job.id):
                        print(log)
                except Exception as e:
                    print(f"Could not fetch logs: {e}")

                return 1

            elif current_stage == "PENDING":
                print(
                    f"[{timestamp}] ⏸️  Waiting to start... (Elapsed: {format_duration(elapsed)})",
                    end="\r",
                )

            # Poll every interval
            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print(f"\n\n⏹️  Monitoring stopped (Elapsed: {format_duration(elapsed)})")
        print(f"Job {job.id} is still {current_stage}")
        print("\nResume monitoring anytime by running this script again")
        return 0


if __name__ == "__main__":
    import sys

    sys.exit(monitor_training())
