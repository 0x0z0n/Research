

```
python3 evt_cj.py -i ~/z0n/z0n/posts/DanglingTree/Forensics -o ~/z0n/z0n/posts/DanglingTree/Forensics/csv -f csv
```

/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/htb_danglintree_evtx_csv.png

/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/htb_danglintree_tables.png


```kql
.create table DanglingTreeSec (
    TimeGenerated: datetime,
    EventID: int,
    Computer: string,
    Provider: string,
    Channel: string,
    RecordID: long,
    Level: string,
    CallTrace: string,
    CommandLine: string,
    Company: string,
    Contents: string,
    CreationUtcTime: datetime,
    CurrentDirectory: string,
    Description: string,
    DestinationHostname: string,
    DestinationIp: string,
    DestinationIsIpv6: bool,
    DestinationPort: int,
    DestinationPortName: string,
    Details: string,
    EventType: string,
    FileVersion: string,
    GrantedAccess: string,
    Hash: string,
    Hashes: string,
    ID: string,
    Image: string,
    ImageLoaded: string,
    Initiated: bool,
    IntegrityLevel: string,
    IsExecutable: bool,
    LogonGuid: string,
    LogonId: string,
    OriginalFileName: string,
    ParentCommandLine: string,
    ParentImage: string,
    ParentProcessGuid: string,
    ParentProcessId: long,
    ParentUser: string,
    PipeName: string,
    PreviousCreationUtcTime: datetime,
    ProcessGuid: string,
    ProcessId: long,
    Product: string,
    Protocol: string,
    QueryName: string,
    QueryResults: string,
    QueryStatus: string,
    RuleName: string,
    SchemaVersion: string,
    Signature: string,
    SignatureStatus: string,
    Signed: bool,
    SourceHostname: string,
    SourceImage: string,
    SourceIp: string,
    SourceIsIpv6: bool,
    SourcePort: int,
    SourcePortName: string,
    SourceProcessGUID: string,
    SourceProcessId: long,
    SourceThreadId: long,
    SourceUser: string,
    State: string,
    TargetFilename: string,
    TargetImage: string,
    TargetObject: string,
    TargetProcessGUID: string,
    TargetProcessId: long,
    TargetUser: string,
    TerminalSessionId: long,
    User: string,
    UtcTime: datetime,
    Version: string
)
```


/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/htb_danglintree_def_Mapping.png
/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/htb_danglintree_def_SMBEnum.png

/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/htb_danglintree_def_lateral_mevement_andreson.png

/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/htb_danglintree_def_lateral_mevement_andreson_base64decode.png
/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/htb_danglintree_plaintext_back_cred_ident_based_on_mail_service.png

/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/8htb_danglintree_shells.png
/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/9htb_danglintree_DPAPI_artifact_access.png
/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/11htb_danglintree_AD_CS_enumeration.png
/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/18htb_danglintree_WMI_SMB.png


--------------------



/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/htb_danglintree_defsec_Mapping.png

/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/2htb_danglintree_success_login.png
/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/2htb_danglintree_success_initial_acces.png
/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/2htb_danglintree_success_lateral_movemnet.png
/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/2htb_danglintree_success_Priv_Loggeed_in.png
/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/3htb_danglintree_passthehash.png
/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/4htb_danglintree_Password_Reset.png
/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/8htb_danglintree_TGT_Req.png
/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/14htb_danglintree_AnonymousSMB.png
/home/z0n/z0n/z0n/posts/DanglingTree/Forensics/15htb_danglintree_Privlogin.png
