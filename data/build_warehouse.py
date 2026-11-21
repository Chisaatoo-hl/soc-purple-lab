#!/usr/bin/env python3
"""Entrepot analytique du SOC : medallion -> star schema (DuckDB).
Bronze = tickets/*.json | Silver = lignes aplaties | Gold = schema en etoile.
"""
import json, pathlib
import duckdb

TICKETS = pathlib.Path("tickets")
pathlib.Path("data").mkdir(exist_ok=True)
DB = "data/soc.duckdb"
CONF = {"faible": 1, "moyen": 2, "eleve": 3, "élevé": 3}

# --- BRONZE -> SILVER : lecture + aplatissement ---
faits, regles, techniques, bridge = [], {}, {}, []
for f in sorted(TICKETS.glob("*.json")):
    t = json.loads(f.read_text())
    fa, llm = t.get("faits_siem", {}), t.get("analyse_llm", {})
    tid = f.stem
    faits.append((tid, fa.get("timestamp"), (fa.get("timestamp") or "")[:10],
                  fa.get("agent"), str(fa.get("rule_id")), fa.get("niveau"),
                  t.get("occurrences") or 1, t.get("delai_prise_en_charge_s"),
                  llm.get("verdict"), t.get("confiance_siem"),
                  CONF.get((t.get("confiance_siem") or "").lower())))
    regles[str(fa.get("rule_id"))] = fa.get("description")
    ids = fa.get("mitre_id") or []
    techs = fa.get("mitre_technique") or []
    tactics = fa.get("mitre_tactique") or []
    for i, mid in enumerate(ids):
        techniques[mid] = (techs[i] if i < len(techs) else None,
                           tactics[i] if i < len(tactics) else None)
        bridge.append((tid, mid))

# --- GOLD : star schema ---
con = duckdb.connect(DB)
con.execute("""CREATE OR REPLACE TABLE fact_triage(
    ticket_id VARCHAR, ts VARCHAR, jour DATE, agent VARCHAR, rule_id VARCHAR,
    niveau INT, occurrences INT, delai_s DOUBLE, verdict VARCHAR,
    confiance VARCHAR, confiance_num INT)""")
con.executemany("INSERT INTO fact_triage VALUES (?,?,?,?,?,?,?,?,?,?,?)", faits)
con.execute("CREATE OR REPLACE TABLE dim_regle(rule_id VARCHAR, description VARCHAR)")
con.executemany("INSERT INTO dim_regle VALUES (?,?)", list(regles.items()))
con.execute("CREATE OR REPLACE TABLE dim_technique(mitre_id VARCHAR, technique VARCHAR, tactique VARCHAR)")
con.executemany("INSERT INTO dim_technique VALUES (?,?,?)",
                [(k, v[0], v[1]) for k, v in techniques.items()])
con.execute("CREATE OR REPLACE TABLE bridge_triage_technique(ticket_id VARCHAR, mitre_id VARCHAR)")
con.executemany("INSERT INTO bridge_triage_technique VALUES (?,?)", bridge)

# --- Apercu GOLD ---
print("== Tickets par verdict ==")
for r in con.execute("""SELECT verdict, COUNT(*) tickets, SUM(occurrences) evenements
    FROM fact_triage GROUP BY verdict ORDER BY evenements DESC""").fetchall(): print(" ", r)
print("== Top techniques MITRE ==")
for r in con.execute("""SELECT t.mitre_id, t.technique, COUNT(*) n
    FROM bridge_triage_technique b JOIN dim_technique t USING(mitre_id)
    GROUP BY 1,2 ORDER BY n DESC""").fetchall(): print(" ", r)
print("== Delai moyen de prise en charge (s) ==")
print(" ", con.execute("SELECT ROUND(AVG(delai_s),1) FROM fact_triage").fetchone()[0])
con.close()
print(f"\nEntrepot ecrit dans {DB}")
