from fastapi import FastAPI
from agent.modules.scanner import scan_site
from agent.modules.fixer import fix_code
from agent.scheduler.cron import schedule_hourly_job
from agent.git_commit import commit_fixes


app = FastAPI()


def run_agent() -> dict:
    """Execute the full DevSkyy agent workflow."""
    raw_code = scan_site()
    fixed_code = fix_code(raw_code)
    commit_fixes(fixed_code)
    schedule_hourly_job()
    return {"status": "completed"}


@app.post("/run")
def run() -> dict:
    """Endpoint to trigger the DevSkyy agent workflow."""
    return run_agent()


@app.get("/")
def root() -> dict:
    """Health check endpoint."""
    return {"message": "DevSkyy Agent online"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
