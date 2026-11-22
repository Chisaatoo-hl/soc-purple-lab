#!/usr/bin/env python3
"""Score d'une manche : couverture tente vs detecte + delai (console + Postgres)."""
import json, pathlib, datetime
import requests, urllib3, duckdb
urllib3.disable_warnings()

WAZUH_URL = "https://localhost:9200"
AUTH = ("admin", "SecretPassword")
PG = "host=localhost port=5432 dbname=soc_gold user=soc password=soc"
base = lambda tid: tid.split(".")[0]

manche = json.loads(pathlib.Path("red/last_manche.json").read_text())
debut = manche["debut"]

q = {"size": 2000, "sort": [{"@timestamp": "asc"}],
     "query": {"bool": {"must": [
        {"range": {"@timestamp": {"gte": debut}}},
        {"exists": {"field": "rule.mitre.id"}}]}}}
r = requests.get(f"{WAZUH_URL}/wazuh-alerts-*/_search", auth=AUTH, json=q, verify=False, timeout=30)
r.raise_for_status()
hits = [h["_source"] for h in r.json()["hits"]["hits"]]

premiere = {}
for h in hits:
    ts = h.get("timestamp")
    for mid in ((h.get("rule", {}).get("mitre") or {}).get("id") or []):
        b = base(mid)
        if b not in premiere or ts < premiere[b]:
            premiere[b] = ts

rows = []
print(f"Manche du {debut}\n{'Technique':12} {'Detecte':9} {'Delai'}\n" + "-"*34)
detectes = 0
for t in manche["techniques"]:
    det = premiere.get(base(t["id"]))
    delai = None
    if det:
        detectes += 1
        delai = max((datetime.datetime.fromisoformat(det.replace('Z','+00:00'))
                     - datetime.datetime.fromisoformat(t["lance_a"])).total_seconds(), 0.0)
        print(f"{t['id']:12} {'OUI':9} {delai:.0f} s")
    else:
        print(f"{t['id']:12} {'NON':9} -")
    rows.append((debut, t["id"], det is not None, delai))
n = len(manche["techniques"])
print("-"*34 + f"\nCouverture : {detectes}/{n} detectees ({100*detectes//n if n else 0} %)")

# Persistance (historique des manches, idempotent par manche)
con = duckdb.connect()
con.execute("INSTALL postgres; LOAD postgres;")
con.execute(f"ATTACH '{PG}' AS pg (TYPE postgres)")
con.execute("""CREATE TABLE IF NOT EXISTS pg.fact_couverture(
    manche_debut VARCHAR, technique_id VARCHAR, detecte BOOLEAN, delai_s DOUBLE)""")
con.execute("DELETE FROM pg.fact_couverture WHERE manche_debut = ?", [debut])
con.executemany("INSERT INTO pg.fact_couverture VALUES (?,?,?,?)", rows)
con.close()
print("-> couverture poussee dans Postgres (fact_couverture)")
