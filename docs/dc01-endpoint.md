# DC01 - telemetrie & agent (cote endpoint)

## Agent Wazuh (4.14.10)
msiexec /i wazuh-agent-4.14.10-1.msi /q WAZUH_MANAGER='10.10.10.40' WAZUH_AGENT_NAME='DC01'
# manager = lab-services (labnet) ; puis Start-Service WazuhSvc
# NB : la propriete est WAZUH_MANAGER (pas WAAZUH) ; sinon corriger <address> dans ossec.conf

## Sysmon
- Sysmon64 + config SwiftOnSecurity (sysmonconfig-export.xml)
- install : Sysmon64.exe -accepteula -i sysmonconfig.xml

## Collecte Sysmon par l'agent
Bloc ajoute a "C:\Program Files (x86)\ossec-agent\ossec.conf" :
<ossec_config>
  <localfile>
    <location>Microsoft-Windows-Sysmon/Operational</location>
    <log_format>eventchannel</log_format>
  </localfile>
</ossec_config>

## Validation (Atomic Red Team)
Install-AtomicRedTeam -getAtomics ; Invoke-AtomicTest T1033
-> alerte Discovery / rule.mitre.id:T1033 visible dans Wazuh
