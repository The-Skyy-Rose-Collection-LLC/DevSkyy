import threading
from typing import Callable


def schedule_hourly_job(job: Callable[[], None] | None = None) -> None:
    """Schedule ``job`` to run once every hour in a background thread.

    Parameters
    ----------
    job: Callable[[], None], optional
        The function to execute. A simple message printer is used by default.
    """

    def default_job() -> None:
        print("⏰ Scheduled job executed")

    job = job or default_job

    def _runner() -> None:
        job()
        timer = threading.Timer(3600, _runner)
        timer.daemon = True
        timer.start()

    # Start the first run one hour from now
    timer = threading.Timer(3600, _runner)
    timer.daemon = True
    timer.start()()
