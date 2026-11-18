from alembic import command
from conftest import TEST_DATABASE_URL, alembic_config
from sqlalchemy import Engine


def test_models_match_migrations(engine: Engine) -> None:
    """Model değişip göç yazılmadıysa düşer: `uv run alembic revision --autogenerate -m ...`."""
    command.check(alembic_config(TEST_DATABASE_URL))
