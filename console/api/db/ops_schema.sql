-- SOC Purple Lab — analyst console (operational schema)
-- OLTP side: analyst-facing alerts, agent tickets, decision audit trail.
-- Kept OUT of the gold star schema on purpose: gold stays read-only for analytics.
-- Apply on the serving PostgreSQL:  psql -h localhost -U soc -d soc_gold -f ops_schema.sql

CREATE SCHEMA IF NOT EXISTS ops;

-- ---------------------------------------------------------------------------
-- Alerts surfaced to the analyst (fed by the triage pipeline).
-- `id` reuses the Wazuh/pipeline alert id so it joins back to gold.fact_triage.
-- `status` is the canonical disposition the analyst drives.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ops.alerts (
    id          BIGINT       PRIMARY KEY,
    ts          TIMESTAMPTZ  NOT NULL,
    agent       TEXT         NOT NULL,
    rule_id     INTEGER      NOT NULL,
    rule_level  SMALLINT     NOT NULL,
    severity    TEXT         NOT NULL,              -- derived from rule_level (injection-proof)
    technique   TEXT,                               -- MITRE id, e.g. 'T1057'
    src_ip      INET,
    description TEXT         NOT NULL,
    raw         JSONB,                              -- full enriched Sysmon event
    status      TEXT         NOT NULL DEFAULT 'new',-- new | validated | false_positive | escalated
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT alerts_severity_chk CHECK (severity IN ('faible','moyen','eleve')),
    CONSTRAINT alerts_status_chk   CHECK (status   IN ('new','validated','false_positive','escalated'))
);

-- ---------------------------------------------------------------------------
-- Agent-written triage ticket, 1:1 with an alert.
-- `recommended_action` lets us later compute analyst-vs-agent agreement.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ops.tickets (
    id                 BIGSERIAL   PRIMARY KEY,
    alert_id           BIGINT      NOT NULL UNIQUE REFERENCES ops.alerts(id) ON DELETE CASCADE,
    confiance_siem     TEXT        NOT NULL,        -- facts from the SIEM (reliable)
    analyse_llm        TEXT        NOT NULL,        -- advisory judgment from the local LLM
    severity           TEXT        NOT NULL,        -- derived severity, mirrored from the alert
    recommended_action TEXT,                        -- validate | false_positive | escalate (nullable)
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT tickets_reco_chk CHECK (
        recommended_action IS NULL OR
        recommended_action IN ('validate','false_positive','escalate')
    )
);

-- ---------------------------------------------------------------------------
-- Analyst decision history (who / when / old -> new). Append-only audit trail.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ops.decisions (
    id         BIGSERIAL   PRIMARY KEY,
    alert_id   BIGINT      NOT NULL REFERENCES ops.alerts(id) ON DELETE CASCADE,
    analyst    TEXT        NOT NULL,
    action     TEXT        NOT NULL,                -- validate | false_positive | escalate
    old_status TEXT,
    new_status TEXT        NOT NULL,
    comment    TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT decisions_action_chk CHECK (action IN ('validate','false_positive','escalate'))
);

CREATE INDEX IF NOT EXISTS idx_alerts_ts        ON ops.alerts (ts DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_disp      ON ops.alerts (status, severity);
CREATE INDEX IF NOT EXISTS idx_decisions_alert  ON ops.decisions (alert_id, created_at DESC);
