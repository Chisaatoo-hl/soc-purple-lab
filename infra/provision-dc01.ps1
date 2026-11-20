#Requires -RunAsAdministrator
<#
  provision-dc01.ps1 - Runbook de provisioning de DC01 (Windows Server 2022 Core)
  A executer DANS la VM, section par section : deux reboots (rename, promotion AD).
  Les mots de passe sont demandes a l'execution - aucun secret stocke ici.
#>

# --- Section 1 : reseau (carte labnet = celle sans passerelle par defaut) ---
$labnet = Get-NetIPConfiguration | Where-Object { -not $_.IPv4DefaultGateway } | Select-Object -First 1
$idx = $labnet.InterfaceIndex
New-NetIPAddress -InterfaceIndex $idx -IPAddress 10.10.10.10 -PrefixLength 24
Set-DnsClientServerAddress -InterfaceIndex $idx -ServerAddresses 127.0.0.1

# --- Section 2 : renommage (REDEMARRE la VM) ---
Rename-Computer -NewName DC01 -Restart

# --- Section 3 : apres reboot, promotion en controleur de foret (REDEMARRE) ---
Install-WindowsFeature AD-Domain-Services -IncludeManagementTools
Install-ADDSForest -DomainName "lab.local" -DomainNetbiosName "LAB" -InstallDns `
  -SafeModeAdministratorPassword (Read-Host -AsSecureString "Mot de passe DSRM") -Force

# --- Section 4 : apres reboot, OU + utilisateur de test ---
New-ADOrganizationalUnit -Name "LabUsers" -Path "DC=lab,DC=local"
New-ADUser -Name "jdupont" -SamAccountName "jdupont" -UserPrincipalName "jdupont@lab.local" `
  -Path "OU=LabUsers,DC=lab,DC=local" `
  -AccountPassword (Read-Host -AsSecureString "Mot de passe jdupont") `
  -Enabled $true -PasswordNeverExpires $true
