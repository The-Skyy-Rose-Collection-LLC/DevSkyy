from agent.modules.scanner import scan_site
from agent.modules.fixer import fix_code
from agent.scheduler.cron import schedule_hourly_job
from agent.git_commit import commit_fixes

if __name__ == "__main__":
    print("🔁 Launching DevSkyy Agent...")
    raw_code = scan_site()
    fixed_code = fix_code(raw_code)
    commit_fixes(fixed_code)
    schedule_hourly_job()
