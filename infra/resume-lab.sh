#!/usr/bin/env bash
# Reveille le lab et aligne les horloges des VM sur l'hote (contourne le drift savestate).
set -uo pipefail
VBoxManage startvm lab-services --type headless 2>/dev/null || true
VBoxManage startvm DC01 --type headless 2>/dev/null || true
echo "Demarrage... (25s)"; sleep 25
NOW=$(date '+%Y-%m-%d %H:%M:%S')
ssh -i ~/.ssh/dc01_key -o StrictHostKeyChecking=no -p 2222 maxime@localhost "sudo date -s '$NOW'" >/dev/null && echo "lab-services a l'heure"
ssh -i ~/.ssh/dc01_key -o StrictHostKeyChecking=no -p 2223 Administrator@localhost "powershell -c \"Set-Date '$NOW'; Restart-Service WazuhSvc\"" >/dev/null && echo "DC01 a l'heure + agent reconnecte"
echo "Lab pret ($NOW)."
