import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


try:
    import httpx  # Optional for async usage
except Exception:
    httpx = None  # type: ignore

logger = logging.getLogger(__name__)


def _build_session(total_retries: int = 3, backoff_factor: float = 0.5, timeout: float = 5.0) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE", "PATCH"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    # Attach default timeout via wrapper
    session.request = _with_timeout(session.request, timeout)  # type: ignore
    return session


def _with_timeout(request_fn, default_timeout: float):
    def _wrapped(method: str, url: str, **kwargs):
        if "timeout" not in kwargs or kwargs["timeout"] is None:
            kwargs["timeout"] = default_timeout
        return request_fn(method, url, **kwargs)

    return _wrapped


_session = _build_session()


def get(url: str, **kwargs) -> requests.Response:
    return _session.get(url, **kwargs)


def post(url: str, **kwargs) -> requests.Response:
    return _session.post(url, **kwargs)


async def async_get(url: str, **kwargs) -> Any:
    if httpx is None:
        raise RuntimeError("httpx is not available for async HTTP requests")
    timeout = kwargs.pop("timeout", 5.0)
    retries = kwargs.pop("retries", 3)
    backoff = kwargs.pop("backoff", 0.5)

    for attempt in range(1, retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, **kwargs)
                return resp
        except Exception as e:
            if attempt == retries:
                raise
            sleep_time = backoff * (2 ** (attempt - 1))
            logger.warning(f"async_get failed (attempt {attempt}/{retries}) for {url}: {e}. Retrying in {sleep_time}s")
            await _async_sleep(sleep_time)


async def _async_sleep(seconds: float) -> None:
    if httpx is not None:
        # Simple async sleep without importing asyncio at module import for lightness
        import asyncio

        await asyncio.sleep(seconds)
