#!/usr/bin/env python3
"""Score d'une manche : couverture tente vs detecte + delai de detection.
Compare le plan joue (red/last_manche.json) aux detections Wazuh (rule.mitre.id).
"""
import json, pathlib, datetime
import requests, urllib3
urllib3.disable_warnings()

WAZUH_URL = "https://localhost:9200"
AUTH = ("admin", "SecretPassword")
base = lambda tid: tid.split(".")[0]   # T1059.001 -> T1059

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

print(f"Manche du {debut}\n")
print(f"{'Technique':12} {'Detecte':9} {'Delai'}")
print("-" * 34)
detectes = 0
for t in manche["techniques"]:
    det = premiere.get(base(t["id"]))
    if det:
        detectes += 1
        dt = (datetime.datetime.fromisoformat(det.replace('Z', '+00:00'))
              - datetime.datetime.fromisoformat(t["lance_a"])).total_seconds()
        print(f"{t['id']:12} {'OUI':9} {max(dt,0):.0f} s")
    else:
        print(f"{t['id']:12} {'NON':9} -")
n = len(manche["techniques"])
print("-" * 34)
print(f"Couverture : {detectes}/{n} detectees ({100*detectes//n if n else 0} %)")
