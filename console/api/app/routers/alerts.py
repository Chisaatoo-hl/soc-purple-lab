from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..db import get_conn
from ..logic import status_for_action
from ..models import Alert, AlertDetail, AlertList, DecisionCreate

router = APIRouter(prefix="/alerts", tags=["alerts"])

# src_ip cast to text so Pydantic gets a plain string, not an ipaddress object.
ALERT_COLS = (
    "id, ts, agent, rule_id, rule_level, severity, technique, "
    "src_ip::text AS src_ip, description, status, created_at"
)


@router.get("", response_model=AlertList)
def list_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    from_: Optional[datetime] = Query(None, alias="from"),
    to: Optional[datetime] = None,
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=200),
    conn=Depends(get_conn),
):
    where: list[str] = []
    params: list = []
    if severity:
        where.append("severity = %s")
        params.append(severity)
    if status:
        where.append("status = %s")
        params.append(status)
    if from_:
        where.append("ts >= %s")
        params.append(from_)
    if to:
        where.append("ts <= %s")
        params.append(to)
    if q:
        where.append("(description ILIKE %s OR agent ILIKE %s OR technique ILIKE %s)")
        like = f"%{q}%"
        params += [like, like, like]

    clause = ("WHERE " + " AND ".join(where)) if where else ""
    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) AS n FROM ops.alerts {clause}", params)
        total = cur.fetchone()["n"]
        cur.execute(
            f"SELECT {ALERT_COLS} FROM ops.alerts {clause} "
            "ORDER BY ts DESC LIMIT %s OFFSET %s",
            params + [size, (page - 1) * size],
        )
        items = cur.fetchall()
    return {"items": items, "total": total, "page": page, "size": size}


@router.get("/{alert_id}", response_model=AlertDetail)
def get_alert(alert_id: int, conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute(f"SELECT {ALERT_COLS} FROM ops.alerts WHERE id = %s", [alert_id])
        alert = cur.fetchone()
        if not alert:
            raise HTTPException(status_code=404, detail="alert not found")
        cur.execute(
            "SELECT id, alert_id, confiance_siem, analyse_llm, severity, "
            "recommended_action, created_at FROM ops.tickets WHERE alert_id = %s",
            [alert_id],
        )
        ticket = cur.fetchone()
        cur.execute(
            "SELECT id, alert_id, analyst, action, old_status, new_status, "
            "comment, created_at FROM ops.decisions WHERE alert_id = %s "
            "ORDER BY created_at DESC",
            [alert_id],
        )
        decisions = cur.fetchall()
    return {"alert": alert, "ticket": ticket, "decisions": decisions}


@router.post("/{alert_id}/decision", response_model=Alert)
def decide(alert_id: int, body: DecisionCreate, conn=Depends(get_conn)):
    new_status = status_for_action(body.action)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT status FROM ops.alerts WHERE id = %s FOR UPDATE", [alert_id]
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="alert not found")
        old_status = row["status"]
        cur.execute(
            "UPDATE ops.alerts SET status = %s WHERE id = %s", [new_status, alert_id]
        )
        cur.execute(
            "INSERT INTO ops.decisions "
            "(alert_id, analyst, action, old_status, new_status, comment) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            [alert_id, body.analyst, body.action, old_status, new_status, body.comment],
        )
        cur.execute(f"SELECT {ALERT_COLS} FROM ops.alerts WHERE id = %s", [alert_id])
        alert = cur.fetchone()
    # pool connection context commits on clean exit of the request.
    return alert
