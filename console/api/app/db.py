from collections.abc import Iterator

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import DATABASE_URL

# min_size=0 -> no eager connection, so the app (and unit tests) can import and
# boot without a live database. Connections are created lazily on first use.
pool = ConnectionPool(
    DATABASE_URL,
    min_size=0,
    max_size=5,
    open=False,
    kwargs={"row_factory": dict_row},
)


def get_conn() -> Iterator:
    """FastAPI dependency: a pooled connection, committed/rolled back on exit."""
    with pool.connection() as conn:
        yield conn
