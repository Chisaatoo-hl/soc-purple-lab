"""Write triaged alerts + agent tickets into the operational `ops` schema,
so the analyst console sees real data from each triage run.

Additive: call this alongside your existing ticket-file write — it does not
replace anything. Idempotent: a given (agent, rule_id, ts) maps to a stable
alert id, so re-running triage over the same window updates instead of
duplicating.

Requires psycopg v3 in the triage environment:  pip install 'psycopg[binary]'
"""
from __future__ import annotations

import hashlib
import os
from typing import Optional

import psycopg
from psycopg.types.json import Jsonb

DATABASE_URL = os.getenv("OPS_DATABASE_URL", "postgresql://soc:soc@localhost:5432/soc_gold")

# Agent recommendation baseline, derived from the SIEM-derived severity (NOT the
# LLM, to stay injection-proof). This is what the console compares against the
# analyst's decision to compute the agreement rate. Make the LLM emit its own
# recommendation later and pass it explicitly to override.
RECO_BY_SEVERITY = {
    "eleve": "escalate",
    "moyen": "validate",
    "faible": "false_positive",
}


def stable_id(agent: str, rule_id, ts: str) -> int:
    """Deterministic id from a natural key.

    Masked to 52 bits so the value is < 2**53 and therefore exactly
    representable as a JavaScript number — otherwise the front-end would round
    the id and detail lookups would 404.
    """
    h = hashlib.blake2b(f"{agent}|{rule_id}|{ts}".encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") & ((1 << 52) - 1)


def upsert_triage(
    *,
    ts: str,
    agent: str,
    rule_id: int,
    rule_level: int,
    severity: str,
    description: str,
    confiance_siem: str,
    analyse_llm: str,
    technique: Optional[str] = None,
    src_ip: Optional[str] = None,
    raw: Optional[dict] = None,
    recommended_action: Optional[str] = None,
    conninfo: str = DATABASE_URL,
) -> int:
    """Insert/update one alert and its ticket. Returns the alert id.

    On conflict the alert's `status` is preserved (an analyst may already have
    acted on it); only the descriptive fields and the ticket are refreshed.
    """
    alert_id = stable_id(agent, rule_id, ts)
    reco = recommended_action or RECO_BY_SEVERITY.get(severity)
    raw_param = Jsonb(raw) if raw is not None else None

    with psycopg.connect(conninfo) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ops.alerts
                (id, ts, agent, rule_id, rule_level, severity, technique, src_ip,
                 description, raw, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'new')
            ON CONFLICT (id) DO UPDATE SET
                ts          = EXCLUDED.ts,
                rule_level  = EXCLUDED.rule_level,
                severity    = EXCLUDED.severity,
                technique   = EXCLUDED.technique,
                src_ip      = EXCLUDED.src_ip,
                description = EXCLUDED.description,
                raw         = EXCLUDED.raw
            """,
            (alert_id, ts, agent, rule_id, rule_level, severity, technique,
             src_ip, description, raw_param),
        )
        cur.execute(
            """
            INSERT INTO ops.tickets
                (alert_id, confiance_siem, analyse_llm, severity, recommended_action)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (alert_id) DO UPDATE SET
                confiance_siem     = EXCLUDED.confiance_siem,
                analyse_llm        = EXCLUDED.analyse_llm,
                severity           = EXCLUDED.severity,
                recommended_action = EXCLUDED.recommended_action
            """,
            (alert_id, confiance_siem, analyse_llm, severity, reco),
        )
    return alert_id
