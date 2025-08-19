def fix_code(code: str) -> str:
    """Perform a trivial cleanup of the provided code.

    This function currently removes trailing whitespace from each line and
    normalises line endings. In a real system this could run formatters or
    linters to automatically repair code issues.

    Parameters
    ----------
    code: str
        The raw code to clean.

    Returns
    -------
    str
        The cleaned code.
    """
    cleaned_lines = [line.rstrip() for line in code.splitlines()]
    return "\n".join(cleaned_lines)
