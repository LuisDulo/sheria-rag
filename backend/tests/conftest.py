import os

import pytest

from app.db import apply_schema, connect


@pytest.fixture(scope="session")
def database_url(tmp_path_factory):
    """Use TEST_DATABASE_URL when set (CI), otherwise an embedded PostgreSQL with pgvector."""
    if url := os.environ.get("TEST_DATABASE_URL"):
        yield url
        return
    pgserver = pytest.importorskip("pgserver")
    server = pgserver.get_server(tmp_path_factory.mktemp("pgdata"))
    yield server.get_uri()
    server.cleanup()


@pytest.fixture
def conn(database_url):
    connection = connect(database_url)
    apply_schema(connection)
    connection.execute("TRUNCATE documents CASCADE")
    connection.commit()
    yield connection
    connection.close()
