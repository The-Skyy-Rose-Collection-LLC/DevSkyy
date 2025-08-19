import requests


def scan_site(url: str = "https://example.com") -> str:
    """Fetch the HTML content of a website.

    Parameters
    ----------
    url: str
        The URL to retrieve.

    Returns
    -------
    str
        The response text from the given URL.
    """
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text
