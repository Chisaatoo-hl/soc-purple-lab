#!/usr/bin/env bash
set -euo pipefail

VM=DC01
ISO="${1:?Usage: ./infra/create-dc01.sh /chemin/vers/windows-server-2022.iso}"
VMDIR="$HOME/VirtualBox VMs/$VM"
OSTYPE=$(VBoxManage list ostypes | grep -q Windows2022_64 && echo Windows2022_64 || echo Windows2019_64)

VBoxManage createvm --name "$VM" --ostype "$OSTYPE" --register
VBoxManage modifyvm "$VM" --memory 2560 --cpus 2 --vram 128
VBoxManage createmedium disk --filename "$VMDIR/$VM.vdi" --size 25600 --format VDI
VBoxManage storagectl "$VM" --name SATA --add sata --controller IntelAhci --portcount 2
VBoxManage storageattach "$VM" --storagectl SATA --port 0 --device 0 --type hdd --medium "$VMDIR/$VM.vdi"
VBoxManage storageattach "$VM" --storagectl SATA --port 1 --device 0 --type dvddrive --medium "$ISO"
VBoxManage modifyvm "$VM" --nic1 intnet --intnet1 labnet
VBoxManage modifyvm "$VM" --nic2 nat
VBoxManage modifyvm "$VM" --boot1 dvd --boot2 disk --boot3 none --boot4 none
echo "DC01 créée. Démarre-la : VBoxManage startvm $VM --type gui"
