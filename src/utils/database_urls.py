from typing import Optional
from urllib.parse import unquote, urlsplit


def parse_test_database_url(database_url: Optional[str]) -> dict:
    """Parse a test-only PostgreSQL URL and reject non-test database names."""
    if not database_url:
        raise ValueError(
            "TEST_DATABASE_URL is required for integration tests and must target a dedicated *_test database."
        )

    try:
        parsed = urlsplit(database_url)
        database_name = unquote(parsed.path.lstrip("/"))
        port = parsed.port or 5432
    except ValueError as exc:
        raise ValueError("TEST_DATABASE_URL is not a valid PostgreSQL URL.") from exc

    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("TEST_DATABASE_URL must use the postgres or postgresql scheme.")
    if (
        not parsed.hostname
        or not database_name
        or "/" in database_name
        or parsed.path.count("/") != 1
        or parsed.fragment
    ):
        raise ValueError("TEST_DATABASE_URL must include a PostgreSQL host and database name.")
    if not database_name.casefold().endswith("_test"):
        raise ValueError("TEST_DATABASE_URL must target a dedicated database whose name ends with '_test'.")

    return {
        "type": "postgres",
        "host": parsed.hostname,
        "port": port,
        "dbname": database_name,
        "user": unquote(parsed.username) if parsed.username else None,
        "password": unquote(parsed.password) if parsed.password else "",
        "dsn": database_url,
    }
