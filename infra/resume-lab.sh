#!/usr/bin/env bash
# Reveille le lab : demarre les VM, re-injecte les redirections, aligne les horloges.
set -uo pipefail
VBoxManage startvm lab-services --type headless 2>/dev/null || true
VBoxManage startvm DC01 --type headless 2>/dev/null || true
echo "Demarrage... (25s)"; sleep 25

# Redirections de ports (idempotent : ignore si deja presentes)
VBoxManage controlvm lab-services natpf2 "ssh,tcp,,2222,,22"       2>/dev/null || true
VBoxManage controlvm lab-services natpf2 "wazuh,tcp,,8443,,443"    2>/dev/null || true
VBoxManage controlvm lab-services natpf2 "indexer,tcp,,9200,,9200" 2>/dev/null || true
VBoxManage controlvm DC01         natpf2 "winssh,tcp,,2223,,22"    2>/dev/null || true

NOW=$(date '+%Y-%m-%d %H:%M:%S')
ssh -i ~/.ssh/dc01_key -o StrictHostKeyChecking=no -p 2222 maxime@localhost "sudo date -s '$NOW'" >/dev/null && echo "lab-services a l'heure"
ssh -i ~/.ssh/dc01_key -o StrictHostKeyChecking=no -p 2223 Administrator@localhost "powershell -c \"Set-Date '$NOW'; Restart-Service WazuhSvc\"" >/dev/null && echo "DC01 a l'heure + agent reconnecte"
echo "Lab pret ($NOW)."
