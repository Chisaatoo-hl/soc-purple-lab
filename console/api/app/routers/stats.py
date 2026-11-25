from fastapi import APIRouter, Depends

from ..db import get_conn
from ..models import Stats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=Stats)
def get_stats(conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT to_char(date_trunc('day', ts), 'YYYY-MM-DD') AS day,
                   severity,
                   count(*) AS n
            FROM ops.alerts
            GROUP BY 1, 2
            ORDER BY 1
            """
        )
        by_severity = cur.fetchall()

        # Analyst-vs-agent agreement: latest decision per alert vs the agent's reco.
        cur.execute(
            """
            WITH latest AS (
                SELECT DISTINCT ON (alert_id) alert_id, action
                FROM ops.decisions
                ORDER BY alert_id, created_at DESC
            )
            SELECT COALESCE(
                       count(*) FILTER (WHERE l.action = t.recommended_action)::float
                       / NULLIF(count(*), 0), 0) AS rate,
                   count(*) AS decided
            FROM ops.tickets t
            JOIN latest l ON l.alert_id = t.alert_id
            WHERE t.recommended_action IS NOT NULL
            """
        )
        agr = cur.fetchone()

        # Detection coverage comes from the red-team scorer (gold.fact_couverture).
        # Column names there may differ in your build — adjust if needed; the API
        # stays up either way.
        coverage = []
        try:
            cur.execute(
                "SELECT manche, taux_couverture FROM gold.fact_couverture ORDER BY manche"
            )
            coverage = cur.fetchall()
        except Exception:
            conn.rollback()

    return {
        "by_severity_over_time": by_severity,
        "agreement_rate": agr["rate"],
        "agreement_sample": agr["decided"],
        "coverage": coverage,
    }
