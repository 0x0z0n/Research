Rogue_Synthesis


Rogue Synthesis
AI Misuse
Cymbal Investments' Threat Hunting team has received an intelligence bulletin regarding AI threats. Armed with Google Threat Intelligence (GTI) reporting and Google SecOps SIEM, your mission is to hunt down the initial compromise and identify the adversary's ultimate target in our CI/CD pipeline.


What developer username initiated a request to the model used by our AI threat? (expected format: user.name)
What package was downloaded immediately prior to the API query? (expected format: File_Name.extension)
Following the outbound API request, what compiled executable was dropped into the local directory used by the malware for staging? (expected format: file_name.extension)
After elevating privileges via process hollowing on the developer’s workstation, what existing file in the user’s local cloud SDK configuration directory was read by the injected process to harvest tokens? (expected format: file_name.extension)
Shortly after the local tokens were harvested on the workstation, the stolen data was exfiltrated via an outbound HTTP POST request to an external URI path masquerading as a telemetry endpoint. To what external domain was the data sent? (expected format: domain-name.com)
Using the harvested service account to pivot laterally from the developer’s workstation to a secondary server, what PowerShell script was overwritten by the attacker via PowerShell to establish persistence? (expected format: file_name.extension)

1.


metadata.event_type = "NETWORK_HTTP" AND target.hostname = /huggingface|generativelanguage|openai|anthropic/ nocase

metadata.product_log_id = "9841285257713960002"
metadata.event_timestamp.seconds = 1792092695
metadata.event_timestamp.nanos = 0
metadata.event_type = "NETWORK_HTTP"
metadata.vendor_name = "Zscaler"
metadata.product_name = "NSS"
metadata.ingested_timestamp.seconds = 1792098652
metadata.ingested_timestamp.nanos = 938225000
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.id = b"AAAAAGD+UuRw0xSXljiknwi3wpsAAAAABQAAAAgAAAA="
metadata.log_type = "ZSCALER_WEBPROXY"
metadata.base_labels.log_types = "ZSCALER_WEBPROXY"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "31.0"
additional.fields["fileclass"] = "None"
additional.fields["appclass"] = "AI Tools"
additional.fields["urlclass"] = "Business Use"
principal.user.userid = "alex.chen"
principal.user.department = "Cloud Engineering & DevOps"
principal.ip = "10.240.12.80"
principal.application = "Google Gemini API"
principal.location.name = "Denver HQ"
principal.namespace = "Cymbal"
principal.asset.ip = "10.240.12.80"
target.hostname = "generativelanguage.googleapis.com"
target.ip = "142.250.190.95"
target.url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=AIzaSyD8x9L2M1N4P7Q0R3S6T9U2V5W8X1Y4Z7"
target.location.country_or_region = "United States"
target.location.region_latitude = 38.794594
target.location.region_longitude = -106.534836
target.location.region_coordinates.latitude = 38.794595199999996
target.location.region_coordinates.longitude = -106.5348379
target.namespace = "Cymbal"
target.asset.hostname = "generativelanguage.googleapis.com"
target.asset.ip = "142.250.190.95"
target.ip_geo_artifact.ip = "142.250.190.95"
target.ip_geo_artifact.location.country_or_region = "United States"
target.ip_geo_artifact.location.region_latitude = 38.794594
target.ip_geo_artifact.location.region_longitude = -106.534836
target.ip_geo_artifact.location.region_coordinates.latitude = 38.794595199999996
target.ip_geo_artifact.location.region_coordinates.longitude = -106.5348379
target.ip_geo_artifact.network.dns_domain = "1e100.net"
target.ip_geo_artifact.network.carrier_name = "google"
target.ip_geo_artifact.network.organization_name = "google llc"
security_result.category_details = "Artificial Intelligence"
security_result.category_details = "Information Technology"
security_result.action = "ALLOW"
security_result.action_details = "Allowed"
security_result.associations.name = "None"
network.sent_bytes = 4200
network.received_bytes = 14200
network.application_protocol = "HTTPS"
network.http.method = "POST"
network.http.user_agent = "node-fetch/3.3.2 (Windows NT 10.0; Win64; x64)"
network.http.response_code = 200
network.http.parsed_user_agent.family = "USER_DEFINED"
network.http.parsed_user_agent.platform = "Windows"
network.http.parsed_user_agent.device = "x64"
network.http.parsed_user_agent.device_version = "3.3.2"
network.http.parsed_user_agent.os = "Windows NT 10.0"
network.http.parsed_user_agent.os_variant = "Win64"
network.http.parsed_user_agent.annotation.key = "OS_NAME"
network.http.parsed_user_agent.annotation.value = "Windows NT"
network.http.parsed_user_agent.annotation.key = "OS_VERSION"
network.http.parsed_user_agent.annotation.value = "10.0"
network.http.parsed_user_agent.annotation.key = "misc"
network.http.parsed_user_agent.annotation.value = "x64"
network.http.parsed_user_agent.os_type = "OS_TYPE_WINDOWS"
network.http.parsed_user_agent.os_variant_type = "OS_VARIANT_TYPE_UNKNOWN"


alex.chen

2.

principal.user.userid = "alex.chen"

	
2026-10-15T19:58:05.000
PROCESS_LAUNCH
gcloud.cmd launched by Code.exe
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Users\alex.chen\AppData\Local\Programs\Microsoft VS Code\Code.exe
2026-10-15T19:54:20.000
NETWORK_HTTP
alex.chen to Cymbal > stackoverflow.com
alex.chen
stackoverflow.com
—
2026-10-15T19:51:10.000
PROCESS_LAUNCH
git.exe launched by Code.exe
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Users\alex.chen\AppData\Local\Programs\Microsoft VS Code\Code.exe
2026-10-15T19:50:00.000
NETWORK_HTTP
alex.chen to Cymbal > github.cymbal.corp
alex.chen
github.cymbal.corp
—
2026-10-15T19:46:05.000
USER_LOGIN
alex.chen - Cymbal > 10.240.12.80
alex.chen
—
—
2026-10-15T19:33:00.000
PROCESS_LAUNCH
python.exe launched by cmd.exe
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Windows\System32\cmd.exe
2026-10-15T19:29:00.000
PROCESS_LAUNCH
git.exe launched by cmd.exe
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Windows\System3

target.hostname = "marketplace.visualstudio.com.cdn-cache.net"



metadata.product_log_id = "9841285257713960001"
metadata.event_timestamp.seconds = 1792092365
metadata.event_timestamp.nanos = 0
metadata.event_type = "NETWORK_HTTP"
metadata.vendor_name = "Zscaler"
metadata.product_name = "NSS"
metadata.ingested_timestamp.seconds = 1792098652
metadata.ingested_timestamp.nanos = 938225000
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.id = b"AAAAAGD+UuRw0xSXljiknwi3wpsAAAAABQAAAAcAAAA="
metadata.log_type = "ZSCALER_WEBPROXY"
metadata.base_labels.log_types = "ZSCALER_WEBPROXY"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "31.0"
additional.fields["appclass"] = "Development"
additional.fields["fileclass"] = "None"
additional.fields["urlclass"] = "Business Use"
principal.user.userid = "alex.chen"
principal.user.department = "Cloud Engineering & DevOps"
principal.ip = "10.240.12.80"
principal.application = "Visual Studio Code"
principal.location.name = "Denver HQ"
principal.namespace = "Cymbal"
principal.asset.ip = "10.240.12.80"
target.hostname = "marketplace.visualstudio.com.cdn-cache.net"
target.ip = "13.107.246.10"
target.url = "https://marketplace.visualstudio.com.cdn-cache.net/extensions/DevTools/SyntaxOptimizer/2.1.4/SyntaxOptimizer-2.1.4.vsix"
target.location.country_or_region = "United States"
target.location.region_latitude = 38.794594
target.location.region_longitude = -106.534836
target.location.region_coordinates.latitude = 38.794595199999996
target.location.region_coordinates.longitude = -106.5348379
target.namespace = "Cymbal"
target.asset.hostname = "marketplace.visualstudio.com.cdn-cache.net"
target.asset.ip = "13.107.246.10"
target.ip_geo_artifact.ip = "13.107.246.10"
target.ip_geo_artifact.location.country_or_region = "United States"
target.ip_geo_artifact.location.region_latitude = 38.794594
target.ip_geo_artifact.location.region_longitude = -106.534836
target.ip_geo_artifact.location.region_coordinates.latitude = 38.794595199999996
target.ip_geo_artifact.location.region_coordinates.longitude = -106.5348379
target.ip_geo_artifact.network.asn = "8075"
target.ip_geo_artifact.network.carrier_name = "microsoft corporation"
target.ip_geo_artifact.network.organization_name = "microsoft corporation"
security_result.category_details = "Computers and Technology"
security_result.category_details = "Information Technology"
security_result.action = "ALLOW"
security_result.action_details = "Allowed"
security_result.associations.name = "None"
network.sent_bytes = 4200
network.received_bytes = 14200
network.application_protocol = "HTTPS"
network.http.method = "GET"
network.http.referral_url = "https://marketplace.visualstudio.com/items?itemName=DevTools.SyntaxOptimizer"
network.http.user_agent = "VSCode/1.89.1 (Windows_NT x64)"
network.http.response_code = 200
network.http.parsed_user_agent.family = "USER_DEFINED"
network.http.parsed_user_agent.platform = "Windows"
network.http.parsed_user_agent.device = "VSCode"
network.http.parsed_user_agent.device_version = "1.89.1"
network.http.parsed_user_agent.os = "Windows_NT x64"
network.http.parsed_user_agent.annotation.key = "OS_NAME"
network.http.parsed_user_agent.annotation.value = "Windows_NT x64"
network.http.parsed_user_agent.os_type = "OS_TYPE_UNKNOWN"
network.http.parsed_user_agent.os_variant_type = "OS_VARIANT_TYPE_UNKNOWN"



3.principal.hostname = "CYM-DEV-WS-019.cymbal.corp"


	
2026-10-15T21:14:10.000
PROCESS_LAUNCH
docker.exe launched by Code.exe
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Users\alex.chen\AppData\Local\Programs\Microsoft VS Code\Code.exe
2026-10-15T20:54:00.000
PROCESS_LAUNCH
cmd.exe launched by svchost.exe
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Windows\System32\svchost.exe
2026-10-15T20:41:00.000
PROCESS_MODULE_LOAD
sys_worker.exe
S-1-5-21-3849102931-1029384910-1003
CYM-DEV-WS-019.cymbal.corp
C:\Users\alex.chen\AppData\Local\Temp\sys_worker.exe
2026-10-15T20:37:50.000
PROCESS_LAUNCH
npm.cmd launched by Code.exe
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Users\alex.chen\AppData\Local\Programs\Microsoft VS Code\Code.exe
2026-10-15T20:33:05.000
PROCESS_LAUNCH
gcc.exe launched by node.exe
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Program Files\nodejs\node.exe
2026-10-15T20:32:20.000
FILE_CREATION
cache_worker.c
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Program Files\nodejs\node.exe
2026-10-15T20:32:00.000
FILE_CREATION
thinking_robot_log.txt
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Program Files\nodejs\node.exe
2026-10-15T20:27:50.000
PROCESS_LAUNCH
node.exe launched by Code.exe
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Users\alex.chen\AppData\Local\Programs\Microsoft VS Code\Code.exe
2026-10-15T20:21:00.000
PROCESS_LAUNCH
gcc.exe launched by Code.exe
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Users\alex.chen\AppData\Local\Programs\Microsoft VS Code\Code.exe
2026-10-15T19:58:05.000
PROCESS_LAUNCH
gcloud.cmd launched by Code.exe
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Users\alex.chen\AppData\Local\Programs\Microsoft VS Code\Code.exe
2026-10-15T19:51:10.000
PROCESS_LAUNCH
git.exe launched by Code.exe
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Users\alex.chen\AppData\Local\Programs\Microsoft VS Code\Code.exe
2026-10-15T19:33:00.000
PROCESS_LAUNCH
python.exe launched by cmd.exe
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Windows\System32\cmd.exe
2026-10-15T19:29:00.000
PROCESS_LAUNCH
git.exe launched by cmd.exe
alex.chen
CYM-DEV-WS-019.cymbal.corp
C:\Windows\System32\cmd.exe


metadata.product_log_id = "104828"
metadata.event_timestamp.seconds = 1792093260
metadata.event_timestamp.nanos = 0
metadata.event_type = "PROCESS_MODULE_LOAD"
metadata.vendor_name = "Microsoft"
metadata.product_name = "Microsoft-Windows-Sysmon"
metadata.product_event_type = "8"
metadata.ingested_timestamp.seconds = 1792098652
metadata.ingested_timestamp.nanos = 628595000
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.id = b"AAAAAIaKWnA6wsn/zb3sLjpC71EAAAAABgAAAAgAAAA="
metadata.log_type = "WINDOWS_SYSMON"
metadata.base_labels.log_types = "WINDOWS_SYSMON"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.log_types = "WINDOWS_SYSMON"
metadata.enrichment_labels.namespaces = "Cymbal"
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "15.0"
additional.fields["Keywords"] = "0x8000000000000000"
principal.hostname = "CYM-DEV-WS-019.cymbal.corp"
principal.user.windows_sid = "S-1-5-21-3849102931-1029384910-1003"
principal.process.pid = "7140"
principal.process.file.full_path = "C:\\Users\\alex.chen\\AppData\\Local\\Temp\\sys_worker.exe"
principal.process.command_line = "gcc.exe -O2 C:\\Users\\alex.chen\\AppData\\Local\\Temp\\cache_worker.c -o C:\\Users\\alex.chen\\AppData\\Local\\Temp\\sys_worker.exe"
principal.process.product_specific_process_id = "SYSMON:{D1E2F3A4-B5C6-7890-0000-555566667777}"
principal.process.parent_process.pid = "6720"
principal.process.parent_process.file.full_path = "C:\\Program Files\\nodejs\\node.exe"
principal.process.parent_process.command_line = "node.exe \"C:\\Users\\alex.chen\\.vscode\\extensions\\devtools.syntaxoptimizer-2.1.4\\out\\optimizer-daemon.js\""
principal.process.parent_process.product_specific_process_id = "SYSMON:{D1E2F3A4-B5C6-7890-0000-444455556666}"
principal.namespace = "Cymbal"
principal.asset.hostname = "CYM-DEV-WS-019.cymbal.corp"
target.process.pid = "624"
target.process.file.full_path = "C:\\Windows\\System32\\svchost.exe"
target.process.product_specific_process_id = "SYSMON:{D1E2F3A4-B5C6-7890-0000-000000000001}"
target.namespace = "Cymbal"
observer.asset_id = "5770385F:C22A:43E0:BF4C:06F5698FFBD9"
observer.process.pid = "2048"
observer.namespace = "Cymbal"
security_result.rule_name = "technique_id=T1055.012,technique_name=Process Hollowing"
security_result.severity = "INFORMATIONAL"
security_result.rule_name = "EventID: 8"
extracted.fields["Event.EventData.Data[11].#text"] = "NT AUTHORITY\\SYSTEM"
extracted.fields["Event.EventData.Data[1].#text"] = "2026-10-15 19:41:00.000"
extracted.fields["Event.EventData.Data[5].@Name"] = "TargetProcessGuid"
extracted.fields["Event.System.Task"] = "8"
extracted.fields["Event.@xmlns"] = "http://schemas.microsoft.com/win/2004/08/events/event"
extracted.fields["Event.EventData.Data[8].@Name"] = "NewThreadId"
extracted.fields["Event.EventData.Data[5].#text"] = "{D1E2F3A4-B5C6-7890-0000-000000000001}"
extracted.fields["Event.EventData.Data[11].@Name"] = "TargetUser"
extracted.fields["Event.EventData.Data[4].#text"] = "C:\\Users\\alex.chen\\AppData\\Local\\Temp\\sys_worker.exe"
extracted.fields["Event.EventData.Data[9].#text"] = "0x00007FF7B4920000"
extracted.fields["Event.System.Provider.@Name"] = "Microsoft-Windows-Sysmon"
extracted.fields["Event.EventData.Data[0].#text"] = "technique_id=T1055.012,technique_name=Process Hollowing"
extracted.fields["Event.EventData.Data[0].@Name"] = "RuleName"
extracted.fields["Event.System.Keywords"] = "0x8000000000000000"
extracted.fields["Event.EventData.Data[6].@Name"] = "TargetProcessId"
extracted.fields["Event.EventData.Data[10].#text"] = "CYMBAL\\alex.chen"
extracted.fields["Event.EventData.Data[3].@Name"] = "SourceProcessId"
extracted.fields["Event.System.Security.@UserID"] = "S-1-5-21-3849102931-1029384910-1003"
extracted.fields["Event.System.EventID"] = "8"
extracted.fields["Event.EventData.Data[9].@Name"] = "StartAddress"
extracted.fields["Event.EventData.Data[2].@Name"] = "SourceProcessGuid"
extracted.fields["Event.System.Version"] = "2"
extracted.fields["Event.EventData.Data[4].@Name"] = "SourceImage"
extracted.fields["Event.System.Channel"] = "Microsoft-Windows-Sysmon/Operational"
extracted.fields["Event.System.EventRecordID"] = "104828"
extracted.fields["Event.EventData.Data[6].#text"] = "624"
extracted.fields["Event.System.Level"] = "4"
extracted.fields["Event.System.Computer"] = "CYM-DEV-WS-019.cymbal.corp"
extracted.fields["Event.EventData.Data[1].@Name"] = "UtcTime"
extracted.fields["Event.EventData.Data[8].#text"] = "4810"
extracted.fields["Event.System.Provider.@Guid"] = "{5770385F-C22A-43E0-BF4C-06F5698FFBD9}"
extracted.fields["Event.System.Opcode"] = "0"
extracted.fields["Event.EventData.Data[2].#text"] = "{D1E2F3A4-B5C6-7890-0000-555566667777}"
extracted.fields["Event.EventData.Data[7].@Name"] = "TargetImage"
extracted.fields["Event.EventData.Data[7].#text"] = "C:\\Windows\\System32\\svchost.exe"
extracted.fields["Event.System.Execution.@ProcessID"] = "2048"
extracted.fields["Event.System.Execution.@ThreadID"] = "3120"
extracted.fields["Event.System.TimeCreated.@SystemTime"] = "2026-10-15T19:41:00.000Z"
extracted.fields["Event.EventData.Data[10].@Name"] = "SourceUser"
extracted.fields["Event.EventData.Data[3].#text"] = "7140"


sys_worker.exe



4.

principal.hostname = "CYM-DEV-WS-019.cymbal.corp" AND principal.process.file.full_path = /svchost/ nocase

metadata.product_log_id = "104830"
metadata.event_timestamp.seconds = 1792094040
metadata.event_timestamp.nanos = 0
metadata.event_type = "PROCESS_LAUNCH"
metadata.vendor_name = "Microsoft"
metadata.product_name = "Microsoft-Windows-Sysmon"
metadata.product_event_type = "1"
metadata.ingested_timestamp.seconds = 1792098652
metadata.ingested_timestamp.nanos = 628595000
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.id = b"AAAAAIaKWnA6wsn/zb3sLjpC71EAAAAABgAAAAoAAAA="
metadata.log_type = "WINDOWS_SYSMON"
metadata.base_labels.log_types = "WINDOWS_SYSMON"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.parser_version = "15.0"
additional.fields["Keywords"] = "0x8000000000000000"
additional.fields["UserID"] = "S-1-5-21-3849102931-1029384910-192837465-1003"
additional.fields["current_directory"] = "C:\\Users\\alex.chen\\"
principal.hostname = "CYM-DEV-WS-019.cymbal.corp"
principal.user.userid = "alex.chen"
principal.process.pid = "624"
principal.process.file.full_path = "C:\\Windows\\System32\\svchost.exe"
principal.process.command_line = "C:\\Windows\\system32\\svchost.exe -k netsvcs -p"
principal.process.product_specific_process_id = "SYSMON:{D1E2F3A4-B5C6-7890-0000-000000000001}"
principal.administrative_domain = "CYMBAL"
principal.namespace = "Cymbal"
principal.asset.hostname = "CYM-DEV-WS-019.cymbal.corp"
target.process.pid = "7890"
target.process.file.full_path = "C:\\Windows\\System32\\cmd.exe"
target.process.command_line = "cmd.exe /c \"type C:\\Users\\alex.chen\\.gcloud\\credentials.db\""
target.process.product_specific_process_id = "SYSMON:{D1E2F3A4-B5C6-7890-0000-777788889999}"
target.namespace = "Cymbal"
observer.asset_id = "5770385F:C22A:43E0:BF4C:06F5698FFBD9"
observer.process.pid = "2048"
observer.namespace = "Cymbal"
security_result.rule_name = "technique_id=T1003.008,technique_name=/etc/passwd and /etc/shadow or Cloud Tokens"
security_result.severity = "INFORMATIONAL"
security_result.rule_name = "EventID: 1"
extracted.fields["Event.System.Computer"] = "CYM-DEV-WS-019.cymbal.corp"
extracted.fields["Event.EventData.Data[14].@Name"] = "ParentUser"
extracted.fields["Event.EventData.Data[11].@Name"] = "ParentProcessId"
extracted.fields["Event.EventData.Data[2].#text"] = "{D1E2F3A4-B5C6-7890-0000-777788889999}"
extracted.fields["Event.EventData.Data[5].#text"] = "cmd.exe /c \"type C:\\Users\\alex.chen\\.gcloud\\credentials.db\""
extracted.fields["Event.System.Keywords"] = "0x8000000000000000"
extracted.fields["Event.EventData.Data[8].@Name"] = "LogonGuid"
extracted.fields["Event.EventData.Data[9].#text"] = "0x3C4D1"
extracted.fields["Event.EventData.Data[12].#text"] = "C:\\Windows\\System32\\svchost.exe"
extracted.fields["Event.System.Channel"] = "Microsoft-Windows-Sysmon/Operational"
extracted.fields["Event.EventData.Data[10].#text"] = "{D1E2F3A4-B5C6-7890-0000-000000000001}"
extracted.fields["Event.EventData.Data[7].#text"] = "CYMBAL\\alex.chen"
extracted.fields["Event.System.Task"] = "1"
extracted.fields["Event.EventData.Data[10].@Name"] = "ParentProcessGuid"
extracted.fields["Event.EventData.Data[7].@Name"] = "User"
extracted.fields["Event.EventData.Data[6].@Name"] = "CurrentDirectory"
extracted.fields["Event.EventData.Data[14].#text"] = "NT AUTHORITY\\SYSTEM"
extracted.fields["Event.EventData.Data[3].#text"] = "7890"
extracted.fields["Event.EventData.Data[4].@Name"] = "Image"
extracted.fields["Event.EventData.Data[13].@Name"] = "ParentCommandLine"
extracted.fields["Event.EventData.Data[3].@Name"] = "ProcessId"
extracted.fields["Event.EventData.Data[12].@Name"] = "ParentImage"
extracted.fields["Event.EventData.Data[1].#text"] = "2026-10-15 19:54:00.000"
extracted.fields["Event.System.TimeCreated.@SystemTime"] = "2026-10-15T19:54:00.000Z"
extracted.fields["Event.System.Provider.@Name"] = "Microsoft-Windows-Sysmon"
extracted.fields["Event.EventData.Data[8].#text"] = "{D1E2F3A4-0000-0000-0000-112233445566}"
extracted.fields["Event.EventData.Data[0].#text"] = "technique_id=T1003.008,technique_name=/etc/passwd and /etc/shadow or Cloud Tokens"
extracted.fields["Event.EventData.Data[4].#text"] = "C:\\Windows\\System32\\cmd.exe"
extracted.fields["Event.EventData.Data[6].#text"] = "C:\\Users\\alex.chen\\"
extracted.fields["Event.System.Execution.@ProcessID"] = "2048"
extracted.fields["Event.EventData.Data[5].@Name"] = "CommandLine"
extracted.fields["Event.EventData.Data[13].#text"] = "C:\\Windows\\system32\\svchost.exe -k netsvcs -p"
extracted.fields["Event.EventData.Data[0].@Name"] = "RuleName"
extracted.fields["Event.System.EventID"] = "1"
extracted.fields["Event.System.EventRecordID"] = "104830"
extracted.fields["Event.System.Version"] = "5"
extracted.fields["Event.System.Security.@UserID"] = "S-1-5-21-3849102931-1029384910-192837465-1003"
extracted.fields["Event.EventData.Data[1].@Name"] = "UtcTime"
extracted.fields["Event.EventData.Data[9].@Name"] = "LogonId"
extracted.fields["Event.System.Level"] = "4"
extracted.fields["Event.System.Provider.@Guid"] = "{5770385F-C22A-43E0-BF4C-06F5698FFBD9}"
extracted.fields["Event.@xmlns"] = "http://schemas.microsoft.com/win/2004/08/events/event"
extracted.fields["Event.System.Execution.@ThreadID"] = "3120"
extracted.fields["Event.EventData.Data[11].#text"] = "624"
extracted.fields["Event.System.Opcode"] = "0"
extracted.fields["Event.EventData.Data[2].@Name"] = "ProcessGuid"


credentials.db


5.

metadata.base_labels.namespaces = "Cymbal" AND metadata.log_type = "WINDOWS_SYSMON" AND target.process.command_line = /\.ps1/ nocase

metadata.product_log_id = "45890"
metadata.event_timestamp.seconds = 1792096265
metadata.event_timestamp.nanos = 0
metadata.event_type = "PROCESS_LAUNCH"
metadata.vendor_name = "Microsoft"
metadata.product_name = "Microsoft-Windows-Sysmon"
metadata.product_event_type = "1"
metadata.ingested_timestamp.seconds = 1792098652
metadata.ingested_timestamp.nanos = 628595000
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.id = b"AAAAAIaKWnA6wsn/zb3sLjpC71EAAAAABgAAAA0AAAA="
metadata.log_type = "WINDOWS_SYSMON"
metadata.base_labels.log_types = "WINDOWS_SYSMON"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.parser_version = "15.0"
additional.fields["Keywords"] = "0x8000000000000000"
additional.fields["UserID"] = "S-1-5-21-3849102931-1029384910-192837465-1002"
additional.fields["current_directory"] = "C:\\BuildRunner\\scripts\\"
principal.hostname = "CYM-CI-RUNNER-01.cymbal.corp"
principal.user.userid = "sarah.jenkins"
principal.process.pid = "810"
principal.process.file.full_path = "C:\\Windows\\System32\\svchost.exe"
principal.process.command_line = "C:\\Windows\\system32\\svchost.exe -k DcomLaunch"
principal.process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-000000000001}"
principal.administrative_domain = "CYMBAL"
principal.namespace = "Cymbal"
principal.asset.hostname = "CYM-CI-RUNNER-01.cymbal.corp"
target.process.pid = "2980"
target.process.file.full_path = "C:\\Windows\\System32\\cmd.exe"
target.process.command_line = "cmd.exe /c \"copy C:\\BuildRunner\\scripts\\build_production.ps1 C:\\BuildRunner\\backups\\build_production.ps1.bak\""
target.process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-888899990000}"
target.namespace = "Cymbal"
observer.asset_id = "5770385F:C22A:43E0:BF4C:06F5698FFBD9"
observer.process.pid = "1024"
observer.namespace = "Cymbal"
security_result.rule_name = "technique_id=T1059.003,technique_name=Command and Scripting Interpreter"
security_result.severity = "INFORMATIONAL"
security_result.rule_name = "EventID: 1"
extracted.fields["Event.EventData.Data[14].#text"] = "NT AUTHORITY\\SYSTEM"
extracted.fields["Event.EventData.Data[9].@Name"] = "LogonId"
extracted.fields["Event.System.Security.@UserID"] = "S-1-5-21-3849102931-1029384910-192837465-1002"
extracted.fields["Event.EventData.Data[5].#text"] = "cmd.exe /c \"copy C:\\BuildRunner\\scripts\\build_production.ps1 C:\\BuildRunner\\backups\\build_production.ps1.bak\""
extracted.fields["Event.EventData.Data[11].#text"] = "810"
extracted.fields["Event.EventData.Data[10].#text"] = "{E1F2A3B4-C5D6-7890-0000-000000000001}"
extracted.fields["Event.System.Opcode"] = "0"
extracted.fields["Event.EventData.Data[2].#text"] = "{E1F2A3B4-C5D6-7890-0000-888899990000}"
extracted.fields["Event.System.Provider.@Name"] = "Microsoft-Windows-Sysmon"
extracted.fields["Event.EventData.Data[3].#text"] = "2980"
extracted.fields["Event.EventData.Data[6].#text"] = "C:\\BuildRunner\\scripts\\"
extracted.fields["Event.EventData.Data[4].#text"] = "C:\\Windows\\System32\\cmd.exe"
extracted.fields["Event.System.EventRecordID"] = "45890"
extracted.fields["Event.EventData.Data[12].@Name"] = "ParentImage"
extracted.fields["Event.EventData.Data[3].@Name"] = "ProcessId"
extracted.fields["Event.EventData.Data[0].#text"] = "technique_id=T1059.003,technique_name=Command and Scripting Interpreter"
extracted.fields["Event.@xmlns"] = "http://schemas.microsoft.com/win/2004/08/events/event"
extracted.fields["Event.EventData.Data[13].@Name"] = "ParentCommandLine"
extracted.fields["Event.EventData.Data[0].@Name"] = "RuleName"
extracted.fields["Event.EventData.Data[13].#text"] = "C:\\Windows\\system32\\svchost.exe -k DcomLaunch"
extracted.fields["Event.EventData.Data[8].@Name"] = "LogonGuid"
extracted.fields["Event.EventData.Data[12].#text"] = "C:\\Windows\\System32\\svchost.exe"
extracted.fields["Event.EventData.Data[1].#text"] = "2026-10-15 20:31:05.000"
extracted.fields["Event.EventData.Data[6].@Name"] = "CurrentDirectory"
extracted.fields["Event.System.Keywords"] = "0x8000000000000000"
extracted.fields["Event.EventData.Data[1].@Name"] = "UtcTime"
extracted.fields["Event.System.Provider.@Guid"] = "{5770385F-C22A-43E0-BF4C-06F5698FFBD9}"
extracted.fields["Event.EventData.Data[10].@Name"] = "ParentProcessGuid"
extracted.fields["Event.System.EventID"] = "1"
extracted.fields["Event.EventData.Data[7].@Name"] = "User"
extracted.fields["Event.EventData.Data[11].@Name"] = "ParentProcessId"
extracted.fields["Event.EventData.Data[5].@Name"] = "CommandLine"
extracted.fields["Event.EventData.Data[9].#text"] = "0x2B5C1"
extracted.fields["Event.System.Channel"] = "Microsoft-Windows-Sysmon/Operational"
extracted.fields["Event.System.Version"] = "5"
extracted.fields["Event.EventData.Data[7].#text"] = "CYMBAL\\sarah.jenkins"
extracted.fields["Event.EventData.Data[14].@Name"] = "ParentUser"
extracted.fields["Event.System.Execution.@ProcessID"] = "1024"
extracted.fields["Event.EventData.Data[8].#text"] = "{B2C3D4E5-0000-0000-0000-112233445566}"
extracted.fields["Event.System.Computer"] = "CYM-CI-RUNNER-01.cymbal.corp"
extracted.fields["Event.System.Level"] = "4"
extracted.fields["Event.System.Execution.@ThreadID"] = "1840"
extracted.fields["Event.System.TimeCreated.@SystemTime"] = "2026-10-15T20:31:05.000Z"
extracted.fields["Event.EventData.Data[4].@Name"] = "Image"
extracted.fields["Event.System.Task"] = "1"
extracted.fields["Event.EventData.Data[2].@Name"] = "ProcessGuid"

principal.hostname = "CYM-CI-RUNNER-01.cymbal.corp"




metadata.product_log_id = "45915"
metadata.event_timestamp.seconds = 1792098650
metadata.event_timestamp.nanos = 0
metadata.event_type = "FILE_CREATION"
metadata.vendor_name = "Microsoft"
metadata.product_name = "Microsoft-Windows-Sysmon"
metadata.product_event_type = "11"
metadata.ingested_timestamp.seconds = 1792098652
metadata.ingested_timestamp.nanos = 628595000
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.id = b"AAAAAIaKWnA6wsn/zb3sLjpC71EAAAAABgAAABEAAAA="
metadata.log_type = "WINDOWS_SYSMON"
metadata.base_labels.log_types = "WINDOWS_SYSMON"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.log_types = "WINDOWS_SYSMON"
metadata.enrichment_labels.namespaces = "Cymbal"
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "15.0"
additional.fields["UserID"] = "S-1-5-21-3849102931-1029384910-1099"
additional.fields["Keywords"] = "0x8000000000000000"
principal.hostname = "CYM-CI-RUNNER-01.cymbal.corp"
principal.user.userid = "svc_cicd_deploy"
principal.process.pid = "3410"
principal.process.file.full_path = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
principal.process.command_line = "C:\\Windows\\system32\\wsmprovhost.exe -Embedding"
principal.process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-999900001111}"
principal.process.parent_process.pid = "810"
principal.process.parent_process.file.full_path = "C:\\Windows\\System32\\svchost.exe"
principal.process.parent_process.command_line = "C:\\Windows\\system32\\svchost.exe -k DcomLaunch"
principal.process.parent_process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-000000000001}"
principal.administrative_domain = "CYMBAL"
principal.namespace = "Cymbal"
principal.asset.hostname = "CYM-CI-RUNNER-01.cymbal.corp"
target.file.full_path = "C:\\BuildRunner\\scripts\\build_production.ps1"
target.resource.name = "2026-10-15 21:10:50.000"
target.resource.resource_subtype = "CreationUtcTime"
target.namespace = "Cymbal"
observer.asset_id = "5770385F:C22A:43E0:BF4C:06F5698FFBD9"
observer.process.pid = "1024"
observer.namespace = "Cymbal"
security_result.rule_name = "technique_id=T1505.003,technique_name=Build Hook Injection"
security_result.severity = "INFORMATIONAL"
security_result.rule_name = "EventID: 11"
extracted.fields["Event.EventData.Data[1].@Name"] = "UtcTime"
extracted.fields["Event.EventData.Data[4].@Name"] = "Image"
extracted.fields["Event.EventData.Data[0].#text"] = "technique_id=T1505.003,technique_name=Build Hook Injection"
extracted.fields["Event.System.Opcode"] = "0"
extracted.fields["Event.System.Task"] = "11"
extracted.fields["Event.EventData.Data[6].#text"] = "2026-10-15 21:10:50.000"
extracted.fields["Event.System.Computer"] = "CYM-CI-RUNNER-01.cymbal.corp"
extracted.fields["Event.System.Channel"] = "Microsoft-Windows-Sysmon/Operational"
extracted.fields["Event.System.EventID"] = "11"
extracted.fields["Event.EventData.Data[3].#text"] = "3410"
extracted.fields["Event.System.EventRecordID"] = "45915"
extracted.fields["Event.System.Execution.@ThreadID"] = "1840"
extracted.fields["Event.System.Execution.@ProcessID"] = "1024"
extracted.fields["Event.System.TimeCreated.@SystemTime"] = "2026-10-15T21:10:50.000Z"
extracted.fields["Event.EventData.Data[5].@Name"] = "TargetFilename"
extracted.fields["Event.EventData.Data[7].@Name"] = "User"
extracted.fields["Event.EventData.Data[5].#text"] = "C:\\BuildRunner\\scripts\\build_production.ps1"
extracted.fields["Event.@xmlns"] = "http://schemas.microsoft.com/win/2004/08/events/event"
extracted.fields["Event.System.Security.@UserID"] = "S-1-5-21-3849102931-1029384910-1099"
extracted.fields["Event.EventData.Data[2].#text"] = "{E1F2A3B4-C5D6-7890-0000-999900001111}"
extracted.fields["Event.EventData.Data[1].#text"] = "2026-10-15 21:10:50.000"
extracted.fields["Event.EventData.Data[4].#text"] = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
extracted.fields["Event.EventData.Data[7].#text"] = "CYMBAL\\svc_cicd_deploy"
extracted.fields["Event.EventData.Data[6].@Name"] = "CreationUtcTime"
extracted.fields["Event.System.Level"] = "4"
extracted.fields["Event.EventData.Data[3].@Name"] = "ProcessId"
extracted.fields["Event.System.Keywords"] = "0x8000000000000000"
extracted.fields["Event.EventData.Data[0].@Name"] = "RuleName"
extracted.fields["Event.System.Provider.@Name"] = "Microsoft-Windows-Sysmon"
extracted.fields["Event.EventData.Data[2].@Name"] = "ProcessGuid"
extracted.fields["Event.System.Provider.@Guid"] = "{5770385F-C22A-43E0-BF4C-06F5698FFBD9}"
extracted.fields["Event.System.Version"] = "2"