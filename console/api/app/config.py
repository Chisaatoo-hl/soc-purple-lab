import os

# Serving PostgreSQL (same instance as the gold star schema; ops schema lives beside it).
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://soc:soc@localhost:5432/soc_gold",
)

# Vite dev server by default; override in prod.
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
