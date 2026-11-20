# Wazuh (SIEM) - lab-services

Version : 4.14.10 (single-node), depot officiel wazuh/wazuh-docker.

## Installation (lab-services, Debian + Docker)
1. Prerequis : echo 'vm.max_map_count=262144' | sudo tee /etc/sysctl.d/99-wazuh.conf && sudo sysctl -p /etc/sysctl.d/99-wazuh.conf
2. Depot : git clone https://github.com/wazuh/wazuh-docker.git && cd wazuh-docker && git checkout v4.14.10 && cd single-node
3. Certs : docker compose -f generate-indexer-certs.yml run --rm generator
4. Up : docker compose up -d

## Acces
- Dashboard : https://10.10.10.40 (labnet) ou port-forward VBox 8443->443
- Login defaut : admin / SecretPassword  -> A CHANGER (Phase 6)
