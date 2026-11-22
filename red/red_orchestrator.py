#!/usr/bin/env python3
"""Orchestrateur rouge - v2 (decision + execution).
L'IA PLANIFIE une suite de techniques (whitelist), puis l'orchestrateur les
EXECUTE sur DC01 par SSH (Atomic Red Team). Emulation, pas armement.
"""
import os, json, subprocess, time
import requests, urllib3
urllib3.disable_warnings()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL  = os.getenv("RED_MODEL", "llama3.2:3b")
BUDGET = int(os.getenv("RED_BUDGET", "4"))
EXECUTE = os.getenv("RED_DRYRUN") != "1"   # execute par defaut ; RED_DRYRUN=1 pour planifier seulement

SSH = ["ssh", "-i", os.path.expanduser("~/.ssh/dc01_key"), "-p", "2223",
       "-o", "StrictHostKeyChecking=no", "Administrator@localhost"]
ATOMIC = ("Import-Module C:\\AtomicRedTeam\\invoke-atomicredteam\\Invoke-AtomicRedTeam.psd1; "
          "Invoke-AtomicTest {tid}")

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
    prompt = (f"Objectif : {OBJECTIF}\n\nCatalogue autorise :\n"
              f"{json.dumps(CATALOGUE, ensure_ascii=False, indent=1)}\n\n"
              f"Deja jouees : {history or 'aucune'}\n\n"
              f"Choisis la prochaine technique (un identifiant du catalogue).")
    r = requests.post(f"{OLLAMA_URL}/api/generate", timeout=180, json={
        "model": MODEL, "system": SYSTEM, "prompt": prompt, "stream": False,
        "format": "json", "keep_alive": 0, "options": {"temperature": 0.3}})
    r.raise_for_status()
    return json.loads(r.json()["response"])

def execute(tid):
    cmd = f'powershell -c "{ATOMIC.format(tid=tid)}"'
    try:
        r = subprocess.run(SSH + [cmd], capture_output=True, text=True, timeout=240)
        return r.returncode, (r.stdout or r.stderr or "")[-300:]
    except subprocess.TimeoutExpired:
        return -1, "timeout"

def main():
    history = []
    print(f"Objectif : {OBJECTIF}\nBudget : {BUDGET} techniques\n")
    # 1. Planification (IA)
    for _ in range(BUDGET):
        d = decide(history)
        tid = d.get("technique_id")
        if tid not in CATALOGUE or tid in history:
            continue
        history.append(tid)
        print(f"[plan {len(history)}] {tid}  ({CATALOGUE[tid]})")
        print(f"            raison : {d.get('raison','')[:80]}")
    # 2. Execution (whitelist deja garantie)
    if not EXECUTE:
        print(f"\n[DRY-RUN] Plan : {history}"); return
    print("\n--- Execution de la manche sur DC01 ---")
    for tid in history:
        rc, out = execute(tid)
        print(f"[exec] {tid} -> {'OK' if rc == 0 else f'echec (rc={rc})'}")
        time.sleep(2)
    print(f"\nManche terminee : {history}")

if __name__ == "__main__":
    main()
