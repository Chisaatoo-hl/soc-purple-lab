#!/usr/bin/env bash
set -euo pipefail
VM=lab-services
ISO="${1:?Usage: ./infra/create-lab-services.sh /chemin/vers/debian-netinst.iso}"
VMDIR="$HOME/VirtualBox VMs/$VM"

VBoxManage createvm --name "$VM" --ostype Debian_64 --register
VBoxManage modifyvm "$VM" --memory 7168 --cpus 4 --vram 16
VBoxManage createmedium disk --filename "$VMDIR/$VM.vdi" --size 40960 --format VDI
VBoxManage storagectl "$VM" --name SATA --add sata --controller IntelAhci --portcount 2
VBoxManage storageattach "$VM" --storagectl SATA --port 0 --device 0 --type hdd --medium "$VMDIR/$VM.vdi"
VBoxManage storageattach "$VM" --storagectl SATA --port 1 --device 0 --type dvddrive --medium "$ISO"
VBoxManage modifyvm "$VM" --nic1 intnet --intnet1 labnet
VBoxManage modifyvm "$VM" --nic2 nat
VBoxManage modifyvm "$VM" --boot1 dvd --boot2 disk --boot3 none --boot4 none
echo "lab-services creee. Demarre-la : VBoxManage startvm $VM --type gui"
