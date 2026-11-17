import pytest

from src.utils.database_urls import parse_test_database_url


def test_parse_test_database_url_returns_connection_config():
    config = parse_test_database_url(
        "postgresql://test_user:test%40password@localhost:5433/unython_test"
    )

    assert config["dbname"] == "unython_test"
    assert config["host"] == "localhost"
    assert config["port"] == 5433
    assert config["user"] == "test_user"
    assert config["password"] == "test@password"


@pytest.mark.parametrize(
    "database_url",
    [
        None,
        "postgresql://localhost/unython",
        "postgresql://localhost/unython_dev",
        "sqlite:///unython_test",
        "postgresql://localhost/",
    ],
)
def test_parse_test_database_url_rejects_unsafe_targets(database_url):
    with pytest.raises(ValueError):
        parse_test_database_url(database_url)
