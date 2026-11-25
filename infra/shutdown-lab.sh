#!/usr/bin/env bash
# Shutdown the lab cleanly: stop the host BI stack, then save-state both VMs.
# Counterpart to resume-lab.sh. Idempotent — safe to re-run.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Adjust these if your VMs are named differently (VBoxManage list vms).
DC01_VM="${DC01_VM:-DC01}"
SVC_VM="${SVC_VM:-lab-services}"

echo "==> Stopping host BI stack (postgres, metabase, api, web)…"
docker compose -f "$REPO/bi/docker-compose.yml" stop || true

savestate() {
  local vm="$1"
  if VBoxManage list runningvms | grep -q "\"$vm\""; then
    echo "==> Saving state: $vm"
    VBoxManage controlvm "$vm" savestate
  else
    echo "==> $vm not running, skipping"
  fi
}

# Services VM first (Wazuh), then the domain controller.
savestate "$SVC_VM"
savestate "$DC01_VM"

echo "==> Lab stopped. Resume with ./infra/resume-lab.sh"
