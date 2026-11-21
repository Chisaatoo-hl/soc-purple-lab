#!/usr/bin/env python3
"""Orchestrateur rouge - v1 (decision seule ; execution branchee ensuite).
L'IA choisit la PROCHAINE technique MITRE UNIQUEMENT dans un catalogue whiteliste.
Emulation, pas armement : une technique hors catalogue n'est jamais executee.
"""
import os, json
import requests, urllib3
urllib3.disable_warnings()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL  = os.getenv("RED_MODEL", "llama3.2:3b")
BUDGET = int(os.getenv("RED_BUDGET", "4"))

# Catalogue whiteliste (techniques Atomic sans risque, lab isole)
CATALOGUE = {
  "T1033":     "System Owner/User Discovery (whoami)",
  "T1057":     "Process Discovery",
  "T1082":     "System Information Discovery",
  "T1016":     "System Network Configuration Discovery (ipconfig)",
  "T1087.001": "Local Account Discovery (net user)",
  "T1059.001": "PowerShell execution (commande benigne)",
  "T1136.001": "Create Local Account (compte de test, reversible)",
}
OBJECTIF = ("Enchainer de la reconnaissance puis de l'execution sur un controleur "
            "de domaine, pour tester la detection du SOC.")

SYSTEM = (
  "Tu es un operateur red team en LAB ISOLE. Tu choisis la PROCHAINE technique "
  "a jouer UNIQUEMENT parmi le catalogue fourni, par son identifiant exact. "
  "Varie les tactiques (discovery -> execution -> persistence) et ne repete pas "
  "une technique deja jouee. Reponds UNIQUEMENT en JSON : "
  "{\"technique_id\":str,\"raison\":str}."
)

def decide(history):
    prompt = (f"Objectif : {OBJECTIF}\n\n"
              f"Catalogue autorise :\n{json.dumps(CATALOGUE, ensure_ascii=False, indent=1)}\n\n"
              f"Deja jouees : {history or 'aucune'}\n\n"
              f"Choisis la prochaine technique (un identifiant du catalogue).")
    r = requests.post(f"{OLLAMA_URL}/api/generate", timeout=180, json={
        "model": MODEL, "system": SYSTEM, "prompt": prompt,
        "stream": False, "format": "json", "options": {"temperature": 0.3}})
    r.raise_for_status()
    return json.loads(r.json()["response"])

def main():
    history = []
    print(f"Objectif : {OBJECTIF}\nBudget : {BUDGET} techniques\n")
    for step in range(BUDGET):
        d = decide(history)
        tid = d.get("technique_id")
        if tid not in CATALOGUE:                 # whitelist = garde-fou
            print(f"[{step+1}] REJET : '{tid}' hors catalogue."); continue
        if tid in history:
            print(f"[{step+1}] {tid} deja jouee, on passe."); continue
        history.append(tid)
        print(f"[{step+1}] -> {tid}  ({CATALOGUE[tid]})")
        print(f"      raison : {d.get('raison','')[:90]}")
    print(f"\nPlan retenu : {history}")

if __name__ == "__main__":
    main()
