def get_status() -> str:
    """Return the project health status."""
    return "healthy"


def format_status(name: str) -> str:
    return f"{name}: {get_status()}"
