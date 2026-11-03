OAuth Heist


NOw


SCENARIO NAME
OAuth Heist
Threat Hunting
Welcome to the Cymbal Investments Security Operations Center. A high-priority threat bulletin from Google Threat Intelligence covering SHINYHUNTERS has landed in your Emerging Threats. Leveraging the full power of Google SecOps, from SIEM search and Curated Detections to Google Threat Intelligence (GTI) adversary reporting, your mission is to investigate the initial identity compromise and uncover the full scope of the incident.

What is the phishing domain where employee credentials were submitted via an HTTP POST request? (expected format: domainname.com)
To prevent the compromised employee from noticing the persistence mechanism, the adversary abused a newly authorized third-party OAuth application to permanently purge security notifications from the victim’s inbox. What is the exact subject line of the first permanently deleted email, which alerted on multi-factor authentication changes? (expected format: Hello! This is a fake email subject line)
Continuing to monitor the compromised employee’s cloud activity from the attacker’s proxy infrastructure, what sensitive internal document did the adversary locate and download? (expected format: File_Name.extension)
Armed with credentials discovered in the stolen document, what privileged service account did the attacker authenticate to from the compromised employee’s workstation to access the internal database server? (expected format: username)
Once authenticated to that internal server, what is the file name of the raw database dump exported by the attacker prior to compressing it into an archive? (expected format: file_name.extension)
What is the full exfiltration URL (including destination IP and port) used by the attacker to transfer the compressed archive? (expected format: http://8.8.8.8:0000/path/file_name.extensions)


1

sso-cymbal-portal.com

2026-10-17T06:01:03.000
NETWORK_HTTP
warren-morris to Demoverse > signin.accounts-gooqle.com
warren-morris
warren-morris-pc
—
2026-10-17T05:52:03.000
NETWORK_HTTP
emil-palmer to Demoverse > signin.office365x24.com
emil-palmer
emil-palmer-pc
—
2026-10-17T05:50:03.000
NETWORK_HTTP
ashton-davidson to Demoverse > signin.office365x24.com
ashton-davidson
ashton-davidson-pc
—
2026-10-16T18:59:02.000
NETWORK_HTTP
warren-morris to Demoverse > signin.accounts-gooqle.com
warren-morris
warren-morris-pc
—
2026-10-16T18:50:02.000
NETWORK_HTTP
emil-palmer to Demoverse > signin.office365x24.com
emil-palmer
emil-palmer-pc
—
2026-10-16T18:48:02.000
NETWORK_HTTP
ashton-davidson to Demoverse > signin.office365x24.com
ashton-davidson
ashton-davidson-pc
—
2026-10-16T06:01:45.000
NETWORK_HTTP
warren-morris to Demoverse > signin.accounts-gooqle.com
warren-morris
signin.accounts-gooqle.com
—
2026-10-16T05:52:45.000
NETWORK_HTTP
emil-palmer to Demoverse > signin.office365x24.com
emil-palmer
signin.office365x24.com
—
2026-10-16T05:50:45.000
NETWORK_HTTP
ashton-davidson to Demoverse > signin.office365x24.com
ashton-davidson
signin.office365x24.com
—
2026-10-15T19:41:55.000
NETWORK_HTTP
elena.rostova to Cymbal > sso-cymbal-portal.com
elena.rostova
sso-cymbal-portal.com
—
2026-10-15T18:58:56.000
NETWORK_HTTP
warren-morris to Demoverse > signin.accounts-gooqle.com
warren-morris
signin.accounts-gooqle.com
—
2026-10-15T18:49:56.000
NETWORK_HTTP
emil-palmer to Demoverse > signin.office365x24.com
emil-palmer
signin.office365x24.com
—
2026-10-15T18:47:56.000
NETWORK_HTTP
ashton-davidson to Demoverse > signin.office365x24.com
ashton-davidson
signin.office365x24.com
—



2. 

2026-10-15T20:18:20.000
NETWORK_HTTP
elena.rostova to Cymbal > slack.com
elena.rostova
slack.com
—
2026-10-15T20:15:05.000
PROCESS_LAUNCH
Ssms.exe launched by explorer.exe
elena.rostova
CYM-DATA-WS-007.cymbal.corp
C:\Windows\explorer.exe
2026-10-15T19:49:10.000
USER_UNCATEGORIZED
user.mfa.factor.activate
ALERT
elena.rostova - Cymbal > 157.131.172.74
elena.rostova
—
—
2026-10-15T19:47:50.000
USER_LOGIN
elena.rostova - Cymbal > 157.131.172.74
elena.rostova
—
—
2026-10-15T19:41:55.000
NETWORK_HTTP
elena.rostova to Cymbal > sso-cymbal-portal.com
elena.rostova
sso-cymbal-portal.com
—
2026-10-15T19:41:00.000
NETWORK_HTTP
elena.rostova to Cymbal > sso-cymbal-portal.com
elena.rostova
sso-cymbal-portal.com
—
2026-10-15T19:31:10.000
NETWORK_HTTP
elena.rostova to Cymbal > intranet.cymbal.corp
elena.rostova
intranet.cymbal.corp
—
2026-10-15T19:28:00.000
USER_LOGIN
elena.rostova - Cymbal > 10.240.12.65
elena.rostova
—
—
\


principal.user.email_addresses = "elena.rostova@cymbal-investments.com"


metadata.event_timestamp.seconds = 1792090150
metadata.event_timestamp.nanos = 0
metadata.event_type = "USER_UNCATEGORIZED"
metadata.vendor_name = "Okta"
metadata.product_name = "Okta"
metadata.product_version = "0"
metadata.product_event_type = "user.mfa.factor.activate"
metadata.ingested_timestamp.seconds = 1792098652
metadata.ingested_timestamp.nanos = 349083000
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.id = b"AAAAAHlHsm95FJa/Z95pCLBroecAAAAADgAAAAQAAAA="
metadata.log_type = "OKTA"
metadata.base_labels.log_types = "OKTA"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "22.0"
additional.fields["device"] = "Macintosh (Sonoma 14.4)"
principal.user.userid = "elena.rostova"
principal.user.user_display_name = "Elena Rostova"
principal.user.email_addresses = "elena.rostova@cymbal-investments.com"
principal.user.product_object_id = "00u5918237461"
principal.user.attribute.roles.name = "User"
principal.ip = "157.131.172.74"
principal.location.city = "Chicago"
principal.location.state = "Illinois"
principal.location.country_or_region = "United States"
principal.resource.attribute.labels.key = "actor_displayName"
principal.resource.attribute.labels.value = "Elena Rostova"
principal.namespace = "Cymbal"
principal.asset.ip = "157.131.172.74"
principal.ip_geo_artifact.ip = "157.131.172.74"
principal.ip_geo_artifact.location.state = "California"
principal.ip_geo_artifact.location.country_or_region = "United States"
principal.ip_geo_artifact.location.region_latitude = 36.77826
principal.ip_geo_artifact.location.region_longitude = -119.41793
principal.ip_geo_artifact.location.region_coordinates.latitude = 36.778261
principal.ip_geo_artifact.location.region_coordinates.longitude = -119.41793240000001
principal.ip_geo_artifact.network.asn = "46375"
principal.ip_geo_artifact.network.dns_domain = "sonic.net"
principal.ip_geo_artifact.network.carrier_name = "sonic telecom llc"
principal.ip_geo_artifact.network.organization_name = "sonic.net  llc"
target.asset_id = "device_finger_print:fp_8a92f019b7"
target.user.user_display_name = "Elena Rostova"
target.namespace = "Cymbal"
target.asset.asset_id = "device_finger_print:fp_8a92f019b7"
security_result.summary = "User enrolled rogue device factor from anonymized proxy"
security_result.action = "ALLOW"
security_result.severity = "MEDIUM"
security_result.action_details = "SUCCESS"
security_result.detection_fields.key = "type"
security_result.detection_fields.value = "User"
security_result.detection_fields.key = "asNumber"
security_result.detection_fields.value = "13335"
security_result.detection_fields.key = "target_display_name_UDDevice_0"
security_result.detection_fields.value = "Macintosh (Sonoma 14.4)"
security_result.detection_fields.key = "tunnels"
security_result.detection_fields.value = "{\"anonymous\":true}"
network.http.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
network.http.parsed_user_agent.family = "APPLEWEBKIT"
network.http.parsed_user_agent.sub_family = "AppleWebKit"
network.http.parsed_user_agent.platform = "Macintosh"
network.http.parsed_user_agent.os = "Intel Mac OS X 10_15_7"
network.http.parsed_user_agent.browser = "Chrome"
network.http.parsed_user_agent.browser_version = "143.0.0.0"
network.http.parsed_user_agent.browser_engine_version = "537.36"
network.http.parsed_user_agent.annotation.key = "Chrome"
network.http.parsed_user_agent.annotation.value = "Chrome/143.0.0.0"
network.http.parsed_user_agent.annotation.key = "SafariType"
network.http.parsed_user_agent.annotation.value = "Safari/537.36"
network.http.parsed_user_agent.annotation.key = "OS_NAME"
network.http.parsed_user_agent.annotation.value = "Intel Mac OS X"
network.http.parsed_user_agent.annotation.key = "OS_VERSION"
network.http.parsed_user_agent.annotation.value = "10_15_7"
network.http.parsed_user_agent.os_type = "OS_TYPE_MAC_OS"
network.http.parsed_user_agent.os_variant_type = "OS_VARIANT_TYPE_UNKNOWN"
network.http.parsed_user_agent.browser_type = "BROWSER_TYPE_CHROME"
network.http.parsed_user_agent.browser_variant_type = "BROWSER_VARIANT_TYPE_UNKNOWN"
network.organization_name = "Cloudflare Inc."
network.is_proxy = true
network.proxy_info.anonymous = true
extensions.auth.type = "SSO"
extracted.fields["actor.id"] = "00u5918237461"
extracted.fields["securityContext.ipDetails.asOrg"] = "Cloudflare Inc."
extracted.fields["severity"] = "WARN"
extracted.fields["published"] = "2026-10-15T18:49:10.000Z"
extracted.fields["eventType"] = "user.mfa.factor.activate"
extracted.fields["securityContext.asNumber"] = "13335"
extracted.fields["outcome.result"] = "SUCCESS"
extracted.fields["debugContext.debugData.tunnels"] = "{\"anonymous\":true}"
extracted.fields["client.geographicalContext.state"] = "Illinois"
extracted.fields["client.geographicalContext.city"] = "Chicago"
extracted.fields["actor.type"] = "User"
extracted.fields["debugContext.debugData.deviceFingerprint"] = "fp_8a92f019b7"
extracted.fields["client.ipAddress"] = "157.131.172.74"
extracted.fields["actor.displayName"] = "Elena Rostova"
extracted.fields["securityContext.ipDetails.ipServiceCategories[0].operator"] = "NordVPN"
extracted.fields["securityContext.asOrg"] = "Cloudflare Inc."
extracted.fields["client.userAgent.rawUserAgent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
extracted.fields["client.device"] = "Macintosh (Sonoma 14.4)"
extracted.fields["version"] = "0"
extracted.fields["securityContext.isProxy"] = "true"
extracted.fields["client.geographicalContext.country"] = "United States"
extracted.fields["displayMessage"] = "User enrolled rogue device factor from anonymized proxy"
extracted.fields["actor.alternateId"] = "elena.rostova@cymbal-investments.com"
extracted.fields["debugContext.debugData.target_display_name_UDDevice_0"] = "Macintosh (Sonoma 14.4)"

2026-10-15T22:10:53.499
EMAIL_TRANSACTION
Security alert: New macOS device registered to your account
elena.rostova@cymbal-investments.com
—
—
2026-10-15T22:10:53.499
EMAIL_TRANSACTION
Okta: A new MFA factor was added
elena.rostova@cymbal-investments.com
—
—
2026-10-15T20:31:30.000
STATUS_UPDATE
item_download
Cymbal > 23.234.119.110
elena.rostova@cymbal-investments.com
—
—
2026-10-15T20:27:50.000
USER_UNCATEGORIZED
search
elena.rostova@cymbal-investments.com - Cymbal > 23.234.119.110
elena.rostova@cymbal-investments.com
—
—
2026-10-15T20:01:00.000
USER_RESOURCE_ACCESS
ALERT
elena.rostova@cymbal-investments.com - ToogleBox Recall
elena.rostova@cymbal-investments.com
—
—
2026-10-15T19:55:05.000
STATUS_UPDATE
saml_sso_login
Cymbal > 23.234.119.110
elena.rostova@cymbal-investments.com
—
—
2026-10-15T19:49:10.000
USER_UNCATEGORIZED
user.mfa.factor.activate
ALERT
elena.rostova - Cymbal > 157.131.172.74
elena.rostova
—
—
2026-10-15T19:47:50.000
USER_LOGIN
elena.rostova - Cymbal > 157.131.172.74
elena.rostova
—
—
2026-10-15T19:28:00.000
USER_LOGIN
elena.rostova - Cymbal > 10.240.12.65
elena.rostova
—
—
Rows per page
100
1
to
9
of
9
1


	
2026-10-15T20:31:30.000
STATUS_UPDATE
item_download
Cymbal > 23.234.119.110
elena.rostova@cymbal-investments.com
—
—
2026-10-15T20:27:50.000
USER_UNCATEGORIZED
search
elena.rostova@cymbal-investments.com - Cymbal > 23.234.119.110
elena.rostova@cymbal-investments.com
—
—
2026-10-15T20:01:00.000
USER_RESOURCE_ACCESS
ALERT
elena.rostova@cymbal-investments.com - ToogleBox Recall
elena.rostova@cymbal-investments.com
—
—
2026-10-15T19:55:05.000
STATUS_UPDATE
saml_sso_login
Cymbal > 23.234.119.110
elena.rostova@cymbal-investments.com
—
—
2026-10-15T19:49:10.000
USER_UNCATEGORIZED
user.mfa.factor.activate
ALERT
elena.rostova - Cymbal > 157.131.172.74
elena.rostova
—
—
2026-10-15T19:47:50.000
USER_LOGIN
elena.rostova - Cymbal > 157.131.172.74
elena.rostova
—
—
2026-10-15T19:28:00.000
USER_LOGIN
elena.rostova - Cymbal > 10.240.12.65
elena.rostova
—
—


------------------------------------------------


metadata.product_log_id = "98124018296"
metadata.event_timestamp.seconds = 1792098653
metadata.event_timestamp.nanos = 499920000
metadata.event_type = "EMAIL_TRANSACTION"
metadata.vendor_name = "Google Workspace"
metadata.product_name = "gmail"
metadata.ingested_timestamp.seconds = 1792098653
metadata.ingested_timestamp.nanos = 499920000
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.id = b"AAAAANGf9DQEQ/kB/OyBH743MugAAAAADwAAAAQAAAA="
metadata.log_type = "WORKSPACE_ACTIVITY"
metadata.base_labels.log_types = "WORKSPACE_ACTIVITY"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "27.0"
additional.fields["kind"] = "admin#reports#activity"
principal.user.email_addresses = "elena.rostova@cymbal-investments.com"
principal.user.product_object_id = "10829103849102"
principal.user.attribute.labels.key = "actor_caller_type"
principal.user.attribute.labels.value = "USER"
principal.ip = "23.234.119.110"
principal.location.state = "Texas"
principal.location.country_or_region = "United States"
principal.location.region_latitude = 31.9686
principal.location.region_longitude = -99.90181
principal.location.region_coordinates.latitude = 31.968598800000002
principal.location.region_coordinates.longitude = -99.9018131
principal.namespace = "Cymbal"
principal.asset.ip = "23.234.119.110"
principal.ip_geo_artifact.ip = "23.234.119.110"
principal.ip_geo_artifact.location.state = "Texas"
principal.ip_geo_artifact.location.country_or_region = "United States"
principal.ip_geo_artifact.location.region_latitude = 31.9686
principal.ip_geo_artifact.location.region_longitude = -99.90181
principal.ip_geo_artifact.location.region_coordinates.latitude = 31.968598800000002
principal.ip_geo_artifact.location.region_coordinates.longitude = -99.9018131
principal.ip_geo_artifact.network.asn = "11878"
principal.ip_geo_artifact.network.dns_domain = "tzulo.com"
principal.ip_geo_artifact.network.carrier_name = "tzulo  inc."
principal.ip_geo_artifact.network.organization_name = "tzulo  inc."
about.resource.product_object_id = "C01234567"
about.namespace = "Cymbal"
security_result.action_details = "71 - A user took an action in the inbox after receiving the message. Post-delivery actions include opening a message, clicking a link in a message, and downloading an attachment. BigQuery export doesn't provide details about the action."
security_result.about.email = "elena.rostova@cymbal-investments.com"
security_result.about.namespace = "Cymbal"
security_result.action = "ALLOW"
security_result.action_details = "true"
network.email.to = "elena.rostova@cymbal-investments.com"
network.email.mail_id = "<security-alert-981241@cymbal-investments.com>"
network.email.subject = "Security alert: New macOS device registered to your account"

metadata.product_log_id = "98124018295"
metadata.event_timestamp.seconds = 1792098653
metadata.event_timestamp.nanos = 499920000
metadata.event_type = "EMAIL_TRANSACTION"
metadata.vendor_name = "Google Workspace"
metadata.product_name = "gmail"
metadata.ingested_timestamp.seconds = 1792098653
metadata.ingested_timestamp.nanos = 499920000
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.id = b"AAAAANGf9DQEQ/kB/OyBH743MugAAAAADwAAAAMAAAA="
metadata.log_type = "WORKSPACE_ACTIVITY"
metadata.base_labels.log_types = "WORKSPACE_ACTIVITY"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "27.0"
additional.fields["kind"] = "admin#reports#activity"
principal.user.email_addresses = "elena.rostova@cymbal-investments.com"
principal.user.product_object_id = "10829103849102"
principal.user.attribute.labels.key = "actor_caller_type"
principal.user.attribute.labels.value = "USER"
principal.ip = "23.234.119.110"
principal.location.state = "Texas"
principal.location.country_or_region = "United States"
principal.location.region_latitude = 31.9686
principal.location.region_longitude = -99.90181
principal.location.region_coordinates.latitude = 31.968598800000002
principal.location.region_coordinates.longitude = -99.9018131
principal.namespace = "Cymbal"
principal.asset.ip = "23.234.119.110"
principal.ip_geo_artifact.ip = "23.234.119.110"
principal.ip_geo_artifact.location.state = "Texas"
principal.ip_geo_artifact.location.country_or_region = "United States"
principal.ip_geo_artifact.location.region_latitude = 31.9686
principal.ip_geo_artifact.location.region_longitude = -99.90181
principal.ip_geo_artifact.location.region_coordinates.latitude = 31.968598800000002
principal.ip_geo_artifact.location.region_coordinates.longitude = -99.9018131
principal.ip_geo_artifact.network.asn = "11878"
principal.ip_geo_artifact.network.dns_domain = "tzulo.com"
principal.ip_geo_artifact.network.carrier_name = "tzulo  inc."
principal.ip_geo_artifact.network.organization_name = "tzulo  inc."
about.resource.product_object_id = "C01234567"
about.namespace = "Cymbal"
security_result.action_details = "71 - A user took an action in the inbox after receiving the message. Post-delivery actions include opening a message, clicking a link in a message, and downloading an attachment. BigQuery export doesn't provide details about the action."
security_result.about.email = "elena.rostova@cymbal-investments.com"
security_result.about.namespace = "Cymbal"
security_result.action = "ALLOW"
security_result.action_details = "true"
network.email.to = "elena.rostova@cymbal-investments.com"
network.email.mail_id = "<mfa-alert-981240@okta.cymbal-investments.com>"
network.email.subject = "Okta: A new MFA factor was added"

metadata.product_log_id = "98124018301"
metadata.event_timestamp.seconds = 1792092470
metadata.event_timestamp.nanos = 0
metadata.event_type = "USER_UNCATEGORIZED"
metadata.vendor_name = "Google Workspace"
metadata.product_name = "drive"
metadata.product_event_type = "search"
metadata.ingested_timestamp.seconds = 1792098653
metadata.ingested_timestamp.nanos = 499920000
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.id = b"AAAAANGf9DQEQ/kB/OyBH743MugAAAAADgAAAAUAAAA="
metadata.log_type = "WORKSPACE_ACTIVITY"
metadata.base_labels.log_types = "WORKSPACE_ACTIVITY"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "27.0"
additional.fields["kind"] = "admin#reports#activity"
principal.user.email_addresses = "elena.rostova@cymbal-investments.com"
principal.user.product_object_id = "10829103849102"
principal.user.attribute.labels.key = "actor_caller_type"
principal.user.attribute.labels.value = "USER"
principal.ip = "23.234.119.110"
principal.location.state = "Texas"
principal.location.country_or_region = "United States"
principal.location.region_latitude = 31.9686
principal.location.region_longitude = -99.90181
principal.location.region_coordinates.latitude = 31.968598800000002
principal.location.region_coordinates.longitude = -99.9018131
principal.namespace = "Cymbal"
principal.asset.ip = "23.234.119.110"
principal.ip_geo_artifact.ip = "23.234.119.110"
principal.ip_geo_artifact.location.state = "Texas"
principal.ip_geo_artifact.location.country_or_region = "United States"
principal.ip_geo_artifact.location.region_latitude = 31.9686
principal.ip_geo_artifact.location.region_longitude = -99.90181
principal.ip_geo_artifact.location.region_coordinates.latitude = 31.968598800000002
principal.ip_geo_artifact.location.region_coordinates.longitude = -99.9018131
principal.ip_geo_artifact.network.asn = "11878"
principal.ip_geo_artifact.network.dns_domain = "tzulo.com"
principal.ip_geo_artifact.network.carrier_name = "tzulo  inc."
principal.ip_geo_artifact.network.organization_name = "tzulo  inc."
target.application = "Google Drive"
target.namespace = "Cymbal"
about.resource.product_object_id = "C01234567"
about.namespace = "Cymbal"
security_result.about.email = "elena.rostova@cymbal-investments.com"
security_result.about.namespace = "Cymbal"
security_result.category_details = "view"
network.email.to = "elena.rostova@cymbal-investments.com"


metadata.product_log_id = "98124018301"
metadata.event_timestamp.seconds = 1792092470
metadata.event_timestamp.nanos = 0
metadata.event_type = "USER_UNCATEGORIZED"
metadata.vendor_name = "Google Workspace"
metadata.product_name = "drive"
metadata.product_event_type = "search"
metadata.ingested_timestamp.seconds = 1792098653
metadata.ingested_timestamp.nanos = 499920000
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.id = b"AAAAANGf9DQEQ/kB/OyBH743MugAAAAADgAAAAUAAAA="
metadata.log_type = "WORKSPACE_ACTIVITY"
metadata.base_labels.log_types = "WORKSPACE_ACTIVITY"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "27.0"
additional.fields["kind"] = "admin#reports#activity"
principal.user.email_addresses = "elena.rostova@cymbal-investments.com"
principal.user.product_object_id = "10829103849102"
principal.user.attribute.labels.key = "actor_caller_type"
principal.user.attribute.labels.value = "USER"
principal.ip = "23.234.119.110"
principal.location.state = "Texas"
principal.location.country_or_region = "United States"
principal.location.region_latitude = 31.9686
principal.location.region_longitude = -99.90181
principal.location.region_coordinates.latitude = 31.968598800000002
principal.location.region_coordinates.longitude = -99.9018131
principal.namespace = "Cymbal"
principal.asset.ip = "23.234.119.110"
principal.ip_geo_artifact.ip = "23.234.119.110"
principal.ip_geo_artifact.location.state = "Texas"
principal.ip_geo_artifact.location.country_or_region = "United States"
principal.ip_geo_artifact.location.region_latitude = 31.9686
principal.ip_geo_artifact.location.region_longitude = -99.90181
principal.ip_geo_artifact.location.region_coordinates.latitude = 31.968598800000002
principal.ip_geo_artifact.location.region_coordinates.longitude = -99.9018131
principal.ip_geo_artifact.network.asn = "11878"
principal.ip_geo_artifact.network.dns_domain = "tzulo.com"
principal.ip_geo_artifact.network.carrier_name = "tzulo  inc."
principal.ip_geo_artifact.network.organization_name = "tzulo  inc."
target.application = "Google Drive"
target.namespace = "Cymbal"
about.resource.product_object_id = "C01234567"
about.namespace = "Cymbal"
security_result.about.email = "elena.rostova@cymbal-investments.com"
security_result.about.namespace = "Cymbal"
security_result.category_details = "view"
network.email.to = "elena.rostova@cymbal-investments.com"

metadata.product_log_id = "98124018293"
metadata.event_timestamp.seconds = 1792090860
metadata.event_timestamp.nanos = 0
metadata.event_type = "USER_RESOURCE_ACCESS"
metadata.vendor_name = "Google Workspace"
metadata.product_name = "token"
metadata.product_event_type = "authorize"
metadata.ingested_timestamp.seconds = 1792098653
metadata.ingested_timestamp.nanos = 499920000
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.id = b"AAAAANGf9DQEQ/kB/OyBH743MugAAAAADgAAAAIAAAA="
metadata.log_type = "WORKSPACE_ACTIVITY"
metadata.base_labels.log_types = "WORKSPACE_ACTIVITY"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "27.0"
additional.fields["kind"] = "admin#reports#activity"
principal.user.email_addresses = "elena.rostova@cymbal-investments.com"
principal.user.product_object_id = "10829103849102"
principal.user.attribute.labels.key = "actor_caller_type"
principal.user.attribute.labels.value = "USER"
principal.ip = "23.234.119.110"
principal.location.state = "Texas"
principal.location.country_or_region = "United States"
principal.location.region_latitude = 31.9686
principal.location.region_longitude = -99.90181
principal.location.region_coordinates.latitude = 31.968598800000002
principal.location.region_coordinates.longitude = -99.9018131
principal.namespace = "Cymbal"
principal.asset.ip = "23.234.119.110"
principal.ip_geo_artifact.ip = "23.234.119.110"
principal.ip_geo_artifact.location.state = "Texas"
principal.ip_geo_artifact.location.country_or_region = "United States"
principal.ip_geo_artifact.location.region_latitude = 31.9686
principal.ip_geo_artifact.location.region_longitude = -99.90181
principal.ip_geo_artifact.location.region_coordinates.latitude = 31.968598800000002
principal.ip_geo_artifact.location.region_coordinates.longitude = -99.9018131
principal.ip_geo_artifact.network.asn = "11878"
principal.ip_geo_artifact.network.dns_domain = "tzulo.com"
principal.ip_geo_artifact.network.carrier_name = "tzulo  inc."
principal.ip_geo_artifact.network.organization_name = "tzulo  inc."
target.application = "ToogleBox Recall"
target.resource.name = "ToogleBox Recall"
target.resource.attribute.labels.key = "scope"
target.resource.attribute.labels.value = "https://mail.google.com/ , https://www.googleapis.com/auth/gmail.modify"
target.resource.product_object_id = "918237461928-tooglebox-recall.apps.googleusercontent.com"
target.namespace = "Cymbal"
about.resource.product_object_id = "C01234567"
about.namespace = "Cymbal"
security_result.about.email = "elena.rostova@cymbal-investments.com"
security_result.about.namespace = "Cymbal"
security_result.category_details = "token"
network.email.to = "elena.rostova@cymbal-investments.com"


metadata.product_log_id = "98124018290"
metadata.event_timestamp.seconds = 1792090505
metadata.event_timestamp.nanos = 0
metadata.event_type = "STATUS_UPDATE"
metadata.vendor_name = "Google Workspace"
metadata.product_name = "login"
metadata.product_event_type = "saml_sso_login"
metadata.ingested_timestamp.seconds = 1792098653
metadata.ingested_timestamp.nanos = 499920000
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.id = b"AAAAANGf9DQEQ/kB/OyBH743MugAAAAABgAAAAEAAAA="
metadata.log_type = "WORKSPACE_ACTIVITY"
metadata.base_labels.log_types = "WORKSPACE_ACTIVITY"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "27.0"
additional.fields["kind"] = "admin#reports#activity"
principal.user.email_addresses = "elena.rostova@cymbal-investments.com"
principal.user.product_object_id = "10829103849102"
principal.user.attribute.labels.key = "actor_caller_type"
principal.user.attribute.labels.value = "USER"
principal.ip = "23.234.119.110"
principal.location.state = "Texas"
principal.location.country_or_region = "United States"
principal.location.region_latitude = 31.9686
principal.location.region_longitude = -99.90181
principal.location.region_coordinates.latitude = 31.968598800000002
principal.location.region_coordinates.longitude = -99.9018131
principal.namespace = "Cymbal"
principal.asset.ip = "23.234.119.110"
principal.ip_geo_artifact.ip = "23.234.119.110"
principal.ip_geo_artifact.location.state = "Texas"
principal.ip_geo_artifact.location.country_or_region = "United States"
principal.ip_geo_artifact.location.region_latitude = 31.9686
principal.ip_geo_artifact.location.region_longitude = -99.90181
principal.ip_geo_artifact.location.region_coordinates.latitude = 31.968598800000002
principal.ip_geo_artifact.location.region_coordinates.longitude = -99.9018131
principal.ip_geo_artifact.network.asn = "11878"
principal.ip_geo_artifact.network.dns_domain = "tzulo.com"
principal.ip_geo_artifact.network.carrier_name = "tzulo  inc."
principal.ip_geo_artifact.network.organization_name = "tzulo  inc."
target.application = "Login"
target.namespace = "Cymbal"
about.resource.product_object_id = "C01234567"
about.namespace = "Cymbal"
security_result.about.email = "elena.rostova@cymbal-investments.com"
security_result.about.namespace = "Cymbal"
security_result.category_details = "login"
security_result.action = "ALLOW"
security_result.detection_fields.key = "login_type"
security_result.detection_fields.value = "saml"
network.email.to = "elena.rostova@cymbal-investments.com"
extensions.auth.type = "SSO"

metadata.event_timestamp.seconds = 1792090150
metadata.event_timestamp.nanos = 0
metadata.event_type = "USER_UNCATEGORIZED"
metadata.vendor_name = "Okta"
metadata.product_name = "Okta"
metadata.product_version = "0"
metadata.product_event_type = "user.mfa.factor.activate"
metadata.ingested_timestamp.seconds = 1792098652
metadata.ingested_timestamp.nanos = 349083000
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.id = b"AAAAAHlHsm95FJa/Z95pCLBroecAAAAADgAAAAQAAAA="
metadata.log_type = "OKTA"
metadata.base_labels.log_types = "OKTA"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "22.0"
additional.fields["device"] = "Macintosh (Sonoma 14.4)"
principal.user.userid = "elena.rostova"
principal.user.user_display_name = "Elena Rostova"
principal.user.email_addresses = "elena.rostova@cymbal-investments.com"
principal.user.product_object_id = "00u5918237461"
principal.user.attribute.roles.name = "User"
principal.ip = "157.131.172.74"
principal.location.city = "Chicago"
principal.location.state = "Illinois"
principal.location.country_or_region = "United States"
principal.resource.attribute.labels.key = "actor_displayName"
principal.resource.attribute.labels.value = "Elena Rostova"
principal.namespace = "Cymbal"
principal.asset.ip = "157.131.172.74"
principal.ip_geo_artifact.ip = "157.131.172.74"
principal.ip_geo_artifact.location.state = "California"
principal.ip_geo_artifact.location.country_or_region = "United States"
principal.ip_geo_artifact.location.region_latitude = 36.77826
principal.ip_geo_artifact.location.region_longitude = -119.41793
principal.ip_geo_artifact.location.region_coordinates.latitude = 36.778261
principal.ip_geo_artifact.location.region_coordinates.longitude = -119.41793240000001
principal.ip_geo_artifact.network.asn = "46375"
principal.ip_geo_artifact.network.dns_domain = "sonic.net"
principal.ip_geo_artifact.network.carrier_name = "sonic telecom llc"
principal.ip_geo_artifact.network.organization_name = "sonic.net  llc"
target.asset_id = "device_finger_print:fp_8a92f019b7"
target.user.user_display_name = "Elena Rostova"
target.namespace = "Cymbal"
target.asset.asset_id = "device_finger_print:fp_8a92f019b7"
security_result.summary = "User enrolled rogue device factor from anonymized proxy"
security_result.action = "ALLOW"
security_result.severity = "MEDIUM"
security_result.action_details = "SUCCESS"
security_result.detection_fields.key = "type"
security_result.detection_fields.value = "User"
security_result.detection_fields.key = "asNumber"
security_result.detection_fields.value = "13335"
security_result.detection_fields.key = "target_display_name_UDDevice_0"
security_result.detection_fields.value = "Macintosh (Sonoma 14.4)"
security_result.detection_fields.key = "tunnels"
security_result.detection_fields.value = "{\"anonymous\":true}"
network.http.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
network.http.parsed_user_agent.family = "APPLEWEBKIT"
network.http.parsed_user_agent.sub_family = "AppleWebKit"
network.http.parsed_user_agent.platform = "Macintosh"
network.http.parsed_user_agent.os = "Intel Mac OS X 10_15_7"
network.http.parsed_user_agent.browser = "Chrome"
network.http.parsed_user_agent.browser_version = "143.0.0.0"
network.http.parsed_user_agent.browser_engine_version = "537.36"
network.http.parsed_user_agent.annotation.key = "Chrome"
network.http.parsed_user_agent.annotation.value = "Chrome/143.0.0.0"
network.http.parsed_user_agent.annotation.key = "SafariType"
network.http.parsed_user_agent.annotation.value = "Safari/537.36"
network.http.parsed_user_agent.annotation.key = "OS_NAME"
network.http.parsed_user_agent.annotation.value = "Intel Mac OS X"
network.http.parsed_user_agent.annotation.key = "OS_VERSION"
network.http.parsed_user_agent.annotation.value = "10_15_7"
network.http.parsed_user_agent.os_type = "OS_TYPE_MAC_OS"
network.http.parsed_user_agent.os_variant_type = "OS_VARIANT_TYPE_UNKNOWN"
network.http.parsed_user_agent.browser_type = "BROWSER_TYPE_CHROME"
network.http.parsed_user_agent.browser_variant_type = "BROWSER_VARIANT_TYPE_UNKNOWN"
network.organization_name = "Cloudflare Inc."
network.is_proxy = true
network.proxy_info.anonymous = true
extensions.auth.type = "SSO"
extracted.fields["securityContext.isProxy"] = "true"
extracted.fields["version"] = "0"
extracted.fields["securityContext.asOrg"] = "Cloudflare Inc."
extracted.fields["client.ipAddress"] = "157.131.172.74"
extracted.fields["outcome.result"] = "SUCCESS"
extracted.fields["debugContext.debugData.tunnels"] = "{\"anonymous\":true}"
extracted.fields["actor.id"] = "00u5918237461"
extracted.fields["eventType"] = "user.mfa.factor.activate"
extracted.fields["client.geographicalContext.country"] = "United States"
extracted.fields["debugContext.debugData.deviceFingerprint"] = "fp_8a92f019b7"
extracted.fields["client.device"] = "Macintosh (Sonoma 14.4)"
extracted.fields["displayMessage"] = "User enrolled rogue device factor from anonymized proxy"
extracted.fields["securityContext.ipDetails.ipServiceCategories[0].operator"] = "NordVPN"
extracted.fields["client.geographicalContext.state"] = "Illinois"
extracted.fields["actor.displayName"] = "Elena Rostova"
extracted.fields["debugContext.debugData.target_display_name_UDDevice_0"] = "Macintosh (Sonoma 14.4)"
extracted.fields["client.userAgent.rawUserAgent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
extracted.fields["client.geographicalContext.city"] = "Chicago"
extracted.fields["securityContext.ipDetails.asOrg"] = "Cloudflare Inc."
extracted.fields["severity"] = "WARN"
extracted.fields["actor.alternateId"] = "elena.rostova@cymbal-investments.com"
extracted.fields["securityContext.asNumber"] = "13335"
extracted.fields["published"] = "2026-10-15T18:49:10.000Z"
extracted.fields["actor.type"] = "User"

metadata.event_timestamp.seconds = 1792090070
metadata.event_timestamp.nanos = 0
metadata.event_type = "USER_LOGIN"
metadata.vendor_name = "Okta"
metadata.product_name = "Okta"
metadata.product_version = "0"
metadata.product_event_type = "user.authentication.sso"
metadata.ingested_timestamp.seconds = 1792098652
metadata.ingested_timestamp.nanos = 349083000
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.id = b"AAAAAHlHsm95FJa/Z95pCLBroecAAAAADgAAAAMAAAA="
metadata.log_type = "OKTA"
metadata.base_labels.log_types = "OKTA"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "22.0"
additional.fields["device"] = "Unknown"
principal.user.userid = "elena.rostova"
principal.user.user_display_name = "Elena Rostova"
principal.user.email_addresses = "elena.rostova@cymbal-investments.com"
principal.user.product_object_id = "00u5918237461"
principal.user.attribute.roles.name = "User"
principal.ip = "157.131.172.74"
principal.location.city = "Chicago"
principal.location.state = "Illinois"
principal.location.country_or_region = "United States"
principal.resource.attribute.labels.key = "actor_displayName"
principal.resource.attribute.labels.value = "Elena Rostova"
principal.namespace = "Cymbal"
principal.asset.ip = "157.131.172.74"
principal.ip_geo_artifact.ip = "157.131.172.74"
principal.ip_geo_artifact.location.state = "California"
principal.ip_geo_artifact.location.country_or_region = "United States"
principal.ip_geo_artifact.location.region_latitude = 36.77826
principal.ip_geo_artifact.location.region_longitude = -119.41793
principal.ip_geo_artifact.location.region_coordinates.latitude = 36.778261
principal.ip_geo_artifact.location.region_coordinates.longitude = -119.41793240000001
principal.ip_geo_artifact.network.asn = "46375"
principal.ip_geo_artifact.network.dns_domain = "sonic.net"
principal.ip_geo_artifact.network.carrier_name = "sonic telecom llc"
principal.ip_geo_artifact.network.organization_name = "sonic.net  llc"
target.user.userid = "elena.rostova"
target.user.user_display_name = "Elena Rostova"
target.namespace = "Cymbal"
security_result.summary = "User single sign on to Okta from suspicious proxy IP"
security_result.action = "ALLOW"
security_result.severity = "MEDIUM"
security_result.action_details = "SUCCESS"
security_result.detection_fields.key = "type"
security_result.detection_fields.value = "User"
security_result.detection_fields.key = "asNumber"
security_result.detection_fields.value = "13335"
security_result.detection_fields.key = "tunnels"
security_result.detection_fields.value = "{\"anonymous\":true}"
network.http.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
network.http.parsed_user_agent.family = "APPLEWEBKIT"
network.http.parsed_user_agent.sub_family = "AppleWebKit"
network.http.parsed_user_agent.platform = "Macintosh"
network.http.parsed_user_agent.os = "Intel Mac OS X 10_15_7"
network.http.parsed_user_agent.browser = "Chrome"
network.http.parsed_user_agent.browser_version = "143.0.0.0"
network.http.parsed_user_agent.browser_engine_version = "537.36"
network.http.parsed_user_agent.annotation.key = "Chrome"
network.http.parsed_user_agent.annotation.value = "Chrome/143.0.0.0"
network.http.parsed_user_agent.annotation.key = "SafariType"
network.http.parsed_user_agent.annotation.value = "Safari/537.36"
network.http.parsed_user_agent.annotation.key = "OS_NAME"
network.http.parsed_user_agent.annotation.value = "Intel Mac OS X"
network.http.parsed_user_agent.annotation.key = "OS_VERSION"
network.http.parsed_user_agent.annotation.value = "10_15_7"
network.http.parsed_user_agent.os_type = "OS_TYPE_MAC_OS"
network.http.parsed_user_agent.os_variant_type = "OS_VARIANT_TYPE_UNKNOWN"
network.http.parsed_user_agent.browser_type = "BROWSER_TYPE_CHROME"
network.http.parsed_user_agent.browser_variant_type = "BROWSER_VARIANT_TYPE_UNKNOWN"
network.organization_name = "Cloudflare Inc."
network.is_proxy = true
network.proxy_info.anonymous = true
extensions.auth.type = "SSO"
extracted.fields["client.device"] = "Unknown"
extracted.fields["version"] = "0"
extracted.fields["displayMessage"] = "User single sign on to Okta from suspicious proxy IP"
extracted.fields["outcome.result"] = "SUCCESS"
extracted.fields["actor.type"] = "User"
extracted.fields["securityContext.ipDetails.ipServiceCategories[0].operator"] = "NordVPN"
extracted.fields["client.geographicalContext.city"] = "Chicago"
extracted.fields["severity"] = "WARN"
extracted.fields["actor.alternateId"] = "elena.rostova@cymbal-investments.com"
extracted.fields["eventType"] = "user.authentication.sso"
extracted.fields["client.geographicalContext.country"] = "United States"
extracted.fields["client.geographicalContext.state"] = "Illinois"
extracted.fields["actor.id"] = "00u5918237461"
extracted.fields["debugContext.debugData.tunnels"] = "{\"anonymous\":true}"
extracted.fields["securityContext.isProxy"] = "true"
extracted.fields["actor.displayName"] = "Elena Rostova"
extracted.fields["client.ipAddress"] = "157.131.172.74"
extracted.fields["securityContext.asNumber"] = "13335"
extracted.fields["client.userAgent.rawUserAgent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
extracted.fields["published"] = "2026-10-15T18:47:50.000Z"
extracted.fields["securityContext.asOrg"] = "Cloudflare Inc."
extracted.fields["securityContext.ipDetails.asOrg"] = "Cloudflare Inc."

metadata.event_timestamp.seconds = 1792088880
metadata.event_timestamp.nanos = 0
metadata.event_type = "USER_LOGIN"
metadata.vendor_name = "Okta"
metadata.product_name = "Okta"
metadata.product_version = "0"
metadata.product_event_type = "user.authentication.sso"
metadata.ingested_timestamp.seconds = 1792098652
metadata.ingested_timestamp.nanos = 349083000
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.id = b"AAAAAHlHsm95FJa/Z95pCLBroecAAAAADgAAAAEAAAA="
metadata.log_type = "OKTA"
metadata.base_labels.log_types = "OKTA"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.parser_version = "22.0"
additional.fields["device"] = "CYM-DATA-WS-007"
principal.user.userid = "elena.rostova"
principal.user.user_display_name = "Elena Rostova"
principal.user.email_addresses = "elena.rostova@cymbal-investments.com"
principal.user.product_object_id = "00u5918237461"
principal.user.attribute.roles.name = "User"
principal.ip = "10.240.12.65"
principal.location.city = "Denver"
principal.location.state = "Colorado"
principal.location.country_or_region = "United States"
principal.resource.attribute.labels.key = "actor_displayName"
principal.resource.attribute.labels.value = "Elena Rostova"
principal.namespace = "Cymbal"
principal.asset.ip = "10.240.12.65"
target.user.userid = "elena.rostova"
target.user.user_display_name = "Elena Rostova"
target.namespace = "Cymbal"
security_result.summary = "User single sign on to Okta"
security_result.action = "ALLOW"
security_result.severity = "LOW"
security_result.action_details = "SUCCESS"
security_result.detection_fields.key = "type"
security_result.detection_fields.value = "User"
security_result.detection_fields.key = "asNumber"
security_result.detection_fields.value = "15169"
network.http.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
network.http.parsed_user_agent.family = "APPLEWEBKIT"
network.http.parsed_user_agent.sub_family = "AppleWebKit"
network.http.parsed_user_agent.platform = "Windows"
network.http.parsed_user_agent.device = "x64"
network.http.parsed_user_agent.os = "Windows NT 10.0"
network.http.parsed_user_agent.os_variant = "Win64"
network.http.parsed_user_agent.browser = "Chrome"
network.http.parsed_user_agent.browser_version = "124.0.0.0"
network.http.parsed_user_agent.browser_engine_version = "537.36"
network.http.parsed_user_agent.annotation.key = "Chrome"
network.http.parsed_user_agent.annotation.value = "Chrome/124.0.0.0"
network.http.parsed_user_agent.annotation.key = "SafariType"
network.http.parsed_user_agent.annotation.value = "Safari/537.36"
network.http.parsed_user_agent.annotation.key = "OS_NAME"
network.http.parsed_user_agent.annotation.value = "Windows NT"
network.http.parsed_user_agent.annotation.key = "OS_VERSION"
network.http.parsed_user_agent.annotation.value = "10.0"
network.http.parsed_user_agent.annotation.key = "misc"
network.http.parsed_user_agent.annotation.value = "x64"
network.http.parsed_user_agent.os_type = "OS_TYPE_WINDOWS"
network.http.parsed_user_agent.os_variant_type = "OS_VARIANT_TYPE_UNKNOWN"
network.http.parsed_user_agent.browser_type = "BROWSER_TYPE_CHROME"
network.http.parsed_user_agent.browser_variant_type = "BROWSER_VARIANT_TYPE_UNKNOWN"
network.organization_name = "Cymbal Investments"
extensions.auth.type = "SSO"
extracted.fields["client.userAgent.rawUserAgent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
extracted.fields["client.geographicalContext.country"] = "United States"
extracted.fields["actor.displayName"] = "Elena Rostova"
extracted.fields["actor.type"] = "User"
extracted.fields["client.geographicalContext.state"] = "Colorado"
extracted.fields["actor.alternateId"] = "elena.rostova@cymbal-investments.com"
extracted.fields["severity"] = "INFO"
extracted.fields["eventType"] = "user.authentication.sso"
extracted.fields["client.device"] = "CYM-DATA-WS-007"
extracted.fields["client.geographicalContext.city"] = "Denver"
extracted.fields["displayMessage"] = "User single sign on to Okta"
extracted.fields["securityContext.asNumber"] = "15169"
extracted.fields["published"] = "2026-10-15T18:28:00.000Z"
extracted.fields["outcome.result"] = "SUCCESS"
extracted.fields["client.ipAddress"] = "10.240.12.65"
extracted.fields["version"] = "0"
extracted.fields["actor.id"] = "00u5918237461"
extracted.fields["securityContext.asOrg"] = "Cymbal Investments"



Okta: A new MFA factor was added



2. 



3. 

metadata.product_name = "drive" AND metadata.product_event_type = "item_download" AND principal.ip = "23.234.119.110"


metadata.product_log_id = "98124018305"
metadata.event_timestamp.seconds = 1792092690
metadata.event_timestamp.nanos = 0
metadata.event_type = "STATUS_UPDATE"
metadata.vendor_name = "Google Workspace"
metadata.product_name = "drive"
metadata.product_event_type = "item_download"
metadata.ingested_timestamp.seconds = 1792098653
metadata.ingested_timestamp.nanos = 499920000
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.id = b"AAAAANGf9DQEQ/kB/OyBH743MugAAAAABgAAAAYAAAA="
metadata.log_type = "WORKSPACE_ACTIVITY"
metadata.base_labels.log_types = "WORKSPACE_ACTIVITY"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "27.0"
additional.fields["kind"] = "admin#reports#activity"
principal.user.email_addresses = "elena.rostova@cymbal-investments.com"
principal.user.product_object_id = "10829103849102"
principal.user.attribute.labels.key = "actor_caller_type"
principal.user.attribute.labels.value = "USER"
principal.ip = "23.234.119.110"
principal.location.state = "Texas"
principal.location.country_or_region = "United States"
principal.location.region_latitude = 31.9686
principal.location.region_longitude = -99.90181
principal.location.region_coordinates.latitude = 31.968598800000002
principal.location.region_coordinates.longitude = -99.9018131
principal.namespace = "Cymbal"
principal.asset.ip = "23.234.119.110"
principal.ip_geo_artifact.ip = "23.234.119.110"
principal.ip_geo_artifact.location.state = "Texas"
principal.ip_geo_artifact.location.country_or_region = "United States"
principal.ip_geo_artifact.location.region_latitude = 31.9686
principal.ip_geo_artifact.location.region_longitude = -99.90181
principal.ip_geo_artifact.location.region_coordinates.latitude = 31.968598800000002
principal.ip_geo_artifact.location.region_coordinates.longitude = -99.9018131
principal.ip_geo_artifact.network.asn = "11878"
principal.ip_geo_artifact.network.dns_domain = "tzulo.com"
principal.ip_geo_artifact.network.carrier_name = "tzulo  inc."
principal.ip_geo_artifact.network.organization_name = "tzulo  inc."
target.application = "Google Drive"
target.resource.name = "Cymbal_Q3_Database_Architecture_and_Service_Accounts.pdf"
target.resource.attribute.labels.key = "doc_type"
target.resource.attribute.labels.value = "pdf"
target.resource.attribute.labels.key = "owner"
target.resource.attribute.labels.value = "elena.rostova@cymbal-investments.com"
target.resource.product_object_id = "1x9ZkQ7vM3P9s8kL"
target.namespace = "Cymbal"
about.user.email_addresses = "elena.rostova@cymbal-investments.com"
about.resource.product_object_id = "C01234567"
about.namespace = "Cymbal"
security_result.about.email = "elena.rostova@cymbal-investments.com"
security_result.about.namespace = "Cymbal"
security_result.category_details = "download"
network.email.to = "elena.rostova@cymbal-investments.com"

Cymbal_Q3_Database_Architecture_and_Service_Accounts.pdf


4. 

principal.hostname = "CYM-DATA-WS-007" AND metadata.event_type = "USER_LOGIN" AND principal.user.userid != "elena.rostova"

metadata.product_log_id = "910481"
metadata.event_timestamp.seconds = 1792094105
metadata.event_timestamp.nanos = 0
metadata.event_type = "USER_LOGIN"
metadata.vendor_name = "Microsoft"
metadata.product_name = "Microsoft-Windows-Security-Auditing"
metadata.product_event_type = "4624"
metadata.ingested_timestamp.seconds = 1792098653
metadata.ingested_timestamp.nanos = 248323000
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.product_deployment_id = "{54849625-5478-4994-A5BA-3E3B0328C30D}"
metadata.id = b"AAAAADsIPPC6XGqarrZDZsjsbTIAAAAADgAAAAAAAAA="
metadata.log_type = "WINEVTLOG"
metadata.base_labels.log_types = "WINEVTLOG"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.parser_version = "42.0"
additional.fields["Category"] = "Logon"
additional.fields["LogonGuid"] = "{E1F2A3B4-0000-0000-0000-112233445566}"
additional.fields["LmPackageName"] = "-"
additional.fields["Keywords"] = "-9214364837600035000"
additional.fields["Opcode"] = "Info"
additional.fields["TransmittedServices"] = "-"
additional.fields["KeyLength"] = "0"
additional.fields["Workstation Name"] = "CYM-DATA-WS-007"
additional.fields["Channel"] = "Security"
principal.hostname = "CYM-DATA-WS-007"
principal.user.userid = "svc_dbadmin"
principal.process.pid = "640"
principal.ip = "10.240.12.65"
principal.port = 52180
principal.administrative_domain = "CYMBAL"
principal.namespace = "Cymbal"
principal.labels.key = "Workstation Name"
principal.labels.value = "CYM-DATA-WS-007"
principal.asset.hostname = "CYM-DATA-WS-007"
principal.asset.ip = "10.240.12.65"
target.user.userid = "svc_dbadmin"
target.process.file.full_path = "NtLmSsp"
target.administrative_domain = "CYMBAL"
target.namespace = "Cymbal"
target.labels.key = "TransmittedServices"
target.labels.value = "-"
target.labels.key = "LmPackageName"
target.labels.value = "-"
target.labels.key = "KeyLength"
target.labels.value = "0"
intermediary.hostname = "CYM-DB-01.cymbal.corp"
intermediary.namespace = "Cymbal"
about.namespace = "Cymbal"
about.labels.key = "Category"
about.labels.value = "Logon"
about.labels.key = "Channel"
about.labels.value = "Security"
about.labels.key = "Opcode"
about.labels.value = "Info"
security_result.about.resource.name = "NTLM"
security_result.about.namespace = "Cymbal"
security_result.rule_name = "EventID: 4624"
security_result.action = "ALLOW"
security_result.severity = "INFORMATIONAL"
extensions.auth.mechanism = "NETWORK"
extensions.auth.auth_details = "3"

svc_dbadmin

5.

principal.hostname = "CYM-DB-01.cymbal.corp" AND principal.user.userid = "svc_dbadmin" AND (target.process.command_line = /bcp|sqlcmd|mysqldump|pg_dump|BACKUP|SELECT.*INTO OUTFILE/ nocase)

metadata.product_log_id = "64104"
metadata.event_timestamp.seconds = 1792094270
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
metadata.id = b"AAAAAIaKWnA6wsn/zb3sLjpC71EAAAAABgAAABYAAAA="
metadata.log_type = "WINDOWS_SYSMON"
metadata.base_labels.log_types = "WINDOWS_SYSMON"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.log_types = "WINDOWS_SYSMON"
metadata.enrichment_labels.namespaces = "Cymbal"
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "15.0"
additional.fields["UserID"] = "S-1-5-21-3849102931-1029384910-192837465-1089"
additional.fields["current_directory"] = "C:\\ProgramData\\MSSQL\\Backup\\"
additional.fields["Keywords"] = "0x8000000000000000"
principal.hostname = "CYM-DB-01.cymbal.corp"
principal.user.userid = "svc_dbadmin"
principal.process.pid = "3820"
principal.process.file.full_path = "C:\\Windows\\System32\\wsmprovhost.exe"
principal.process.command_line = "C:\\Windows\\system32\\wsmprovhost.exe -Embedding"
principal.process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-111122223333}"
principal.process.parent_process.pid = "810"
principal.process.parent_process.file.full_path = "C:\\Windows\\System32\\wsmprovhost.exe"
principal.process.parent_process.command_line = "C:\\Windows\\system32\\wsmprovhost.exe -Embedding"
principal.process.parent_process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-000000000001}"
principal.administrative_domain = "CYMBAL"
principal.namespace = "Cymbal"
principal.asset.hostname = "CYM-DB-01.cymbal.corp"
target.process.pid = "4910"
target.process.file.full_path = "C:\\Program Files\\Microsoft SQL Server\\Client SDK\\ODBC\\170\\Tools\\Binn\\sqlcmd.exe"
target.process.command_line = "\"C:\\Program Files\\Microsoft SQL Server\\Client SDK\\ODBC\\170\\Tools\\Binn\\sqlcmd.exe\" -S localhost -E -Q \"BACKUP DATABASE [CymbalWealthMaster] TO DISK=\\'C:\\ProgramData\\MSSQL\\Backup\\cymbal_cust_q3.bak\\' WITH FORMAT, COMPRESSION=OFF\""
target.process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-111122224444}"
target.namespace = "Cymbal"
observer.asset_id = "5770385F:C22A:43E0:BF4C:06F5698FFBD9"
observer.process.pid = "1024"
observer.namespace = "Cymbal"
security_result.rule_name = "technique_id=T1565.001,technique_name=Stored Data Manipulation"
security_result.severity = "INFORMATIONAL"
security_result.rule_name = "EventID: 1"
extracted.fields["Event.EventData.Data[8].#text"] = "{E1F2A3B4-0000-0000-0000-112233445566}"
extracted.fields["Event.EventData.Data[13].@Name"] = "ParentCommandLine"
extracted.fields["Event.System.EventID"] = "1"
extracted.fields["Event.EventData.Data[2].#text"] = "{E1F2A3B4-C5D6-7890-0000-111122224444}"
extracted.fields["Event.EventData.Data[4].@Name"] = "Image"
extracted.fields["Event.EventData.Data[13].#text"] = "C:\\Windows\\system32\\wsmprovhost.exe -Embedding"
extracted.fields["Event.System.Level"] = "4"
extracted.fields["Event.EventData.Data[3].#text"] = "4910"
extracted.fields["Event.EventData.Data[1].#text"] = "2026-10-15 19:57:50.000"
extracted.fields["Event.EventData.Data[4].#text"] = "C:\\Program Files\\Microsoft SQL Server\\Client SDK\\ODBC\\170\\Tools\\Binn\\sqlcmd.exe"
extracted.fields["Event.EventData.Data[5].#text"] = "\"C:\\Program Files\\Microsoft SQL Server\\Client SDK\\ODBC\\170\\Tools\\Binn\\sqlcmd.exe\" -S localhost -E -Q \"BACKUP DATABASE [CymbalWealthMaster] TO DISK=\\'C:\\ProgramData\\MSSQL\\Backup\\cymbal_cust_q3.bak\\' WITH FORMAT, COMPRESSION=OFF\""
extracted.fields["Event.EventData.Data[6].@Name"] = "CurrentDirectory"
extracted.fields["Event.System.Task"] = "1"
extracted.fields["Event.System.Opcode"] = "0"
extracted.fields["Event.EventData.Data[11].#text"] = "3820"
extracted.fields["Event.EventData.Data[3].@Name"] = "ProcessId"
extracted.fields["Event.System.Computer"] = "CYM-DB-01.cymbal.corp"
extracted.fields["Event.System.TimeCreated.@SystemTime"] = "2026-10-15T19:57:50.000Z"
extracted.fields["Event.EventData.Data[14].#text"] = "CYMBAL\\svc_dbadmin"
extracted.fields["Event.EventData.Data[5].@Name"] = "CommandLine"
extracted.fields["Event.System.Provider.@Guid"] = "{5770385F-C22A-43E0-BF4C-06F5698FFBD9}"
extracted.fields["Event.System.Version"] = "5"
extracted.fields["Event.System.Provider.@Name"] = "Microsoft-Windows-Sysmon"
extracted.fields["Event.EventData.Data[12].@Name"] = "ParentImage"
extracted.fields["Event.@xmlns"] = "http://schemas.microsoft.com/win/2004/08/events/event"
extracted.fields["Event.System.Execution.@ProcessID"] = "1024"
extracted.fields["Event.EventData.Data[0].#text"] = "technique_id=T1565.001,technique_name=Stored Data Manipulation"
extracted.fields["Event.EventData.Data[7].#text"] = "CYMBAL\\svc_dbadmin"
extracted.fields["Event.EventData.Data[12].#text"] = "C:\\Windows\\System32\\wsmprovhost.exe"
extracted.fields["Event.System.Execution.@ThreadID"] = "1840"
extracted.fields["Event.EventData.Data[2].@Name"] = "ProcessGuid"
extracted.fields["Event.EventData.Data[1].@Name"] = "UtcTime"
extracted.fields["Event.EventData.Data[8].@Name"] = "LogonGuid"
extracted.fields["Event.EventData.Data[9].@Name"] = "LogonId"
extracted.fields["Event.EventData.Data[7].@Name"] = "User"
extracted.fields["Event.EventData.Data[10].#text"] = "{E1F2A3B4-C5D6-7890-0000-111122223333}"
extracted.fields["Event.EventData.Data[14].@Name"] = "ParentUser"
extracted.fields["Event.EventData.Data[10].@Name"] = "ParentProcessGuid"
extracted.fields["Event.EventData.Data[6].#text"] = "C:\\ProgramData\\MSSQL\\Backup\\"
extracted.fields["Event.EventData.Data[9].#text"] = "0x6E1F4"
extracted.fields["Event.System.Keywords"] = "0x8000000000000000"
extracted.fields["Event.EventData.Data[0].@Name"] = "RuleName"
extracted.fields["Event.EventData.Data[11].@Name"] = "ParentProcessId"
extracted.fields["Event.System.EventRecordID"] = "64104"
extracted.fields["Event.System.Security.@UserID"] = "S-1-5-21-3849102931-1029384910-192837465-1089"
extracted.fields["Event.System.Channel"] = "Microsoft-Windows-Sysmon/Operational"

6.

principal.hostname = "CYM-DB-01.cymbal.corp" AND principal.user.userid = "svc_dbadmin" AND metadata.event_type = "PROCESS_LAUNCH" AND target.process.command_line = /cymbal_cust_q3|7z|Compress-Archive|tar|zip|curl|Invoke-WebRequest|Invoke-RestMethod|bitsadmin|certutil/ nocase

metadata.product_log_id = "64104"
metadata.event_timestamp.seconds = 1792094270
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
metadata.id = b"AAAAAIaKWnA6wsn/zb3sLjpC71EAAAAABgAAABYAAAA="
metadata.log_type = "WINDOWS_SYSMON"
metadata.base_labels.log_types = "WINDOWS_SYSMON"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.log_types = "WINDOWS_SYSMON"
metadata.enrichment_labels.namespaces = "Cymbal"
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "15.0"
additional.fields["UserID"] = "S-1-5-21-3849102931-1029384910-192837465-1089"
additional.fields["current_directory"] = "C:\\ProgramData\\MSSQL\\Backup\\"
additional.fields["Keywords"] = "0x8000000000000000"
principal.hostname = "CYM-DB-01.cymbal.corp"
principal.user.userid = "svc_dbadmin"
principal.process.pid = "3820"
principal.process.file.full_path = "C:\\Windows\\System32\\wsmprovhost.exe"
principal.process.command_line = "C:\\Windows\\system32\\wsmprovhost.exe -Embedding"
principal.process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-111122223333}"
principal.process.parent_process.pid = "810"
principal.process.parent_process.file.full_path = "C:\\Windows\\System32\\wsmprovhost.exe"
principal.process.parent_process.command_line = "C:\\Windows\\system32\\wsmprovhost.exe -Embedding"
principal.process.parent_process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-000000000001}"
principal.administrative_domain = "CYMBAL"
principal.namespace = "Cymbal"
principal.asset.hostname = "CYM-DB-01.cymbal.corp"
target.process.pid = "4910"
target.process.file.full_path = "C:\\Program Files\\Microsoft SQL Server\\Client SDK\\ODBC\\170\\Tools\\Binn\\sqlcmd.exe"
target.process.command_line = "\"C:\\Program Files\\Microsoft SQL Server\\Client SDK\\ODBC\\170\\Tools\\Binn\\sqlcmd.exe\" -S localhost -E -Q \"BACKUP DATABASE [CymbalWealthMaster] TO DISK=\\'C:\\ProgramData\\MSSQL\\Backup\\cymbal_cust_q3.bak\\' WITH FORMAT, COMPRESSION=OFF\""
target.process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-111122224444}"
target.namespace = "Cymbal"
observer.asset_id = "5770385F:C22A:43E0:BF4C:06F5698FFBD9"
observer.process.pid = "1024"
observer.namespace = "Cymbal"
security_result.rule_name = "technique_id=T1565.001,technique_name=Stored Data Manipulation"
security_result.severity = "INFORMATIONAL"
security_result.rule_name = "EventID: 1"
extracted.fields["Event.EventData.Data[8].#text"] = "{E1F2A3B4-0000-0000-0000-112233445566}"
extracted.fields["Event.EventData.Data[13].@Name"] = "ParentCommandLine"
extracted.fields["Event.System.EventID"] = "1"
extracted.fields["Event.EventData.Data[2].#text"] = "{E1F2A3B4-C5D6-7890-0000-111122224444}"
extracted.fields["Event.EventData.Data[4].@Name"] = "Image"
extracted.fields["Event.EventData.Data[13].#text"] = "C:\\Windows\\system32\\wsmprovhost.exe -Embedding"
extracted.fields["Event.System.Level"] = "4"
extracted.fields["Event.EventData.Data[3].#text"] = "4910"
extracted.fields["Event.EventData.Data[1].#text"] = "2026-10-15 19:57:50.000"
extracted.fields["Event.EventData.Data[4].#text"] = "C:\\Program Files\\Microsoft SQL Server\\Client SDK\\ODBC\\170\\Tools\\Binn\\sqlcmd.exe"
extracted.fields["Event.EventData.Data[5].#text"] = "\"C:\\Program Files\\Microsoft SQL Server\\Client SDK\\ODBC\\170\\Tools\\Binn\\sqlcmd.exe\" -S localhost -E -Q \"BACKUP DATABASE [CymbalWealthMaster] TO DISK=\\'C:\\ProgramData\\MSSQL\\Backup\\cymbal_cust_q3.bak\\' WITH FORMAT, COMPRESSION=OFF\""
extracted.fields["Event.EventData.Data[6].@Name"] = "CurrentDirectory"
extracted.fields["Event.System.Task"] = "1"
extracted.fields["Event.System.Opcode"] = "0"
extracted.fields["Event.EventData.Data[11].#text"] = "3820"
extracted.fields["Event.EventData.Data[3].@Name"] = "ProcessId"
extracted.fields["Event.System.Computer"] = "CYM-DB-01.cymbal.corp"
extracted.fields["Event.System.TimeCreated.@SystemTime"] = "2026-10-15T19:57:50.000Z"
extracted.fields["Event.EventData.Data[14].#text"] = "CYMBAL\\svc_dbadmin"
extracted.fields["Event.EventData.Data[5].@Name"] = "CommandLine"
extracted.fields["Event.System.Provider.@Guid"] = "{5770385F-C22A-43E0-BF4C-06F5698FFBD9}"
extracted.fields["Event.System.Version"] = "5"
extracted.fields["Event.System.Provider.@Name"] = "Microsoft-Windows-Sysmon"
extracted.fields["Event.EventData.Data[12].@Name"] = "ParentImage"
extracted.fields["Event.@xmlns"] = "http://schemas.microsoft.com/win/2004/08/events/event"
extracted.fields["Event.System.Execution.@ProcessID"] = "1024"
extracted.fields["Event.EventData.Data[0].#text"] = "technique_id=T1565.001,technique_name=Stored Data Manipulation"
extracted.fields["Event.EventData.Data[7].#text"] = "CYMBAL\\svc_dbadmin"
extracted.fields["Event.EventData.Data[12].#text"] = "C:\\Windows\\System32\\wsmprovhost.exe"
extracted.fields["Event.System.Execution.@ThreadID"] = "1840"
extracted.fields["Event.EventData.Data[2].@Name"] = "ProcessGuid"
extracted.fields["Event.EventData.Data[1].@Name"] = "UtcTime"
extracted.fields["Event.EventData.Data[8].@Name"] = "LogonGuid"
extracted.fields["Event.EventData.Data[9].@Name"] = "LogonId"
extracted.fields["Event.EventData.Data[7].@Name"] = "User"
extracted.fields["Event.EventData.Data[10].#text"] = "{E1F2A3B4-C5D6-7890-0000-111122223333}"
extracted.fields["Event.EventData.Data[14].@Name"] = "ParentUser"
extracted.fields["Event.EventData.Data[10].@Name"] = "ParentProcessGuid"
extracted.fields["Event.EventData.Data[6].#text"] = "C:\\ProgramData\\MSSQL\\Backup\\"
extracted.fields["Event.EventData.Data[9].#text"] = "0x6E1F4"
extracted.fields["Event.System.Keywords"] = "0x8000000000000000"
extracted.fields["Event.EventData.Data[0].@Name"] = "RuleName"
extracted.fields["Event.EventData.Data[11].@Name"] = "ParentProcessId"
extracted.fields["Event.System.EventRecordID"] = "64104"
extracted.fields["Event.System.Security.@UserID"] = "S-1-5-21-3849102931-1029384910-192837465-1089"
extracted.fields["Event.System.Channel"] = "Microsoft-Windows-Sysmon/Operational"

metadata.product_log_id = "64104"
metadata.event_timestamp.seconds = 1792094270
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
metadata.id = b"AAAAAIaKWnA6wsn/zb3sLjpC71EAAAAABgAAABYAAAA="
metadata.log_type = "WINDOWS_SYSMON"
metadata.base_labels.log_types = "WINDOWS_SYSMON"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.log_types = "WINDOWS_SYSMON"
metadata.enrichment_labels.namespaces = "Cymbal"
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "15.0"
additional.fields["UserID"] = "S-1-5-21-3849102931-1029384910-192837465-1089"
additional.fields["current_directory"] = "C:\\ProgramData\\MSSQL\\Backup\\"
additional.fields["Keywords"] = "0x8000000000000000"
principal.hostname = "CYM-DB-01.cymbal.corp"
principal.user.userid = "svc_dbadmin"
principal.process.pid = "3820"
principal.process.file.full_path = "C:\\Windows\\System32\\wsmprovhost.exe"
principal.process.command_line = "C:\\Windows\\system32\\wsmprovhost.exe -Embedding"
principal.process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-111122223333}"
principal.process.parent_process.pid = "810"
principal.process.parent_process.file.full_path = "C:\\Windows\\System32\\wsmprovhost.exe"
principal.process.parent_process.command_line = "C:\\Windows\\system32\\wsmprovhost.exe -Embedding"
principal.process.parent_process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-000000000001}"
principal.administrative_domain = "CYMBAL"
principal.namespace = "Cymbal"
principal.asset.hostname = "CYM-DB-01.cymbal.corp"
target.process.pid = "4910"
target.process.file.full_path = "C:\\Program Files\\Microsoft SQL Server\\Client SDK\\ODBC\\170\\Tools\\Binn\\sqlcmd.exe"
target.process.command_line = "\"C:\\Program Files\\Microsoft SQL Server\\Client SDK\\ODBC\\170\\Tools\\Binn\\sqlcmd.exe\" -S localhost -E -Q \"BACKUP DATABASE [CymbalWealthMaster] TO DISK=\\'C:\\ProgramData\\MSSQL\\Backup\\cymbal_cust_q3.bak\\' WITH FORMAT, COMPRESSION=OFF\""
target.process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-111122224444}"
target.namespace = "Cymbal"
observer.asset_id = "5770385F:C22A:43E0:BF4C:06F5698FFBD9"
observer.process.pid = "1024"
observer.namespace = "Cymbal"
security_result.rule_name = "technique_id=T1565.001,technique_name=Stored Data Manipulation"
security_result.severity = "INFORMATIONAL"
security_result.rule_name = "EventID: 1"
extracted.fields["Event.EventData.Data[8].#text"] = "{E1F2A3B4-0000-0000-0000-112233445566}"
extracted.fields["Event.EventData.Data[13].@Name"] = "ParentCommandLine"
extracted.fields["Event.System.EventID"] = "1"
extracted.fields["Event.EventData.Data[2].#text"] = "{E1F2A3B4-C5D6-7890-0000-111122224444}"
extracted.fields["Event.EventData.Data[4].@Name"] = "Image"
extracted.fields["Event.EventData.Data[13].#text"] = "C:\\Windows\\system32\\wsmprovhost.exe -Embedding"
extracted.fields["Event.System.Level"] = "4"
extracted.fields["Event.EventData.Data[3].#text"] = "4910"
extracted.fields["Event.EventData.Data[1].#text"] = "2026-10-15 19:57:50.000"
extracted.fields["Event.EventData.Data[4].#text"] = "C:\\Program Files\\Microsoft SQL Server\\Client SDK\\ODBC\\170\\Tools\\Binn\\sqlcmd.exe"
extracted.fields["Event.EventData.Data[5].#text"] = "\"C:\\Program Files\\Microsoft SQL Server\\Client SDK\\ODBC\\170\\Tools\\Binn\\sqlcmd.exe\" -S localhost -E -Q \"BACKUP DATABASE [CymbalWealthMaster] TO DISK=\\'C:\\ProgramData\\MSSQL\\Backup\\cymbal_cust_q3.bak\\' WITH FORMAT, COMPRESSION=OFF\""
extracted.fields["Event.EventData.Data[6].@Name"] = "CurrentDirectory"
extracted.fields["Event.System.Task"] = "1"
extracted.fields["Event.System.Opcode"] = "0"
extracted.fields["Event.EventData.Data[11].#text"] = "3820"
extracted.fields["Event.EventData.Data[3].@Name"] = "ProcessId"
extracted.fields["Event.System.Computer"] = "CYM-DB-01.cymbal.corp"
extracted.fields["Event.System.TimeCreated.@SystemTime"] = "2026-10-15T19:57:50.000Z"
extracted.fields["Event.EventData.Data[14].#text"] = "CYMBAL\\svc_dbadmin"
extracted.fields["Event.EventData.Data[5].@Name"] = "CommandLine"
extracted.fields["Event.System.Provider.@Guid"] = "{5770385F-C22A-43E0-BF4C-06F5698FFBD9}"
extracted.fields["Event.System.Version"] = "5"
extracted.fields["Event.System.Provider.@Name"] = "Microsoft-Windows-Sysmon"
extracted.fields["Event.EventData.Data[12].@Name"] = "ParentImage"
extracted.fields["Event.@xmlns"] = "http://schemas.microsoft.com/win/2004/08/events/event"
extracted.fields["Event.System.Execution.@ProcessID"] = "1024"
extracted.fields["Event.EventData.Data[0].#text"] = "technique_id=T1565.001,technique_name=Stored Data Manipulation"
extracted.fields["Event.EventData.Data[7].#text"] = "CYMBAL\\svc_dbadmin"
extracted.fields["Event.EventData.Data[12].#text"] = "C:\\Windows\\System32\\wsmprovhost.exe"
extracted.fields["Event.System.Execution.@ThreadID"] = "1840"
extracted.fields["Event.EventData.Data[2].@Name"] = "ProcessGuid"
extracted.fields["Event.EventData.Data[1].@Name"] = "UtcTime"
extracted.fields["Event.EventData.Data[8].@Name"] = "LogonGuid"
extracted.fields["Event.EventData.Data[9].@Name"] = "LogonId"
extracted.fields["Event.EventData.Data[7].@Name"] = "User"
extracted.fields["Event.EventData.Data[10].#text"] = "{E1F2A3B4-C5D6-7890-0000-111122223333}"
extracted.fields["Event.EventData.Data[14].@Name"] = "ParentUser"
extracted.fields["Event.EventData.Data[10].@Name"] = "ParentProcessGuid"
extracted.fields["Event.EventData.Data[6].#text"] = "C:\\ProgramData\\MSSQL\\Backup\\"
extracted.fields["Event.EventData.Data[9].#text"] = "0x6E1F4"
extracted.fields["Event.System.Keywords"] = "0x8000000000000000"
extracted.fields["Event.EventData.Data[0].@Name"] = "RuleName"
extracted.fields["Event.EventData.Data[11].@Name"] = "ParentProcessId"
extracted.fields["Event.System.EventRecordID"] = "64104"
extracted.fields["Event.System.Security.@UserID"] = "S-1-5-21-3849102931-1029384910-192837465-1089"
extracted.fields["Event.System.Channel"] = "Microsoft-Windows-Sysmon/Operational"


principal.hostname = "CYM-DB-01.cymbal.corp" AND metadata.event_type = "PROCESS_LAUNCH" AND target.process.command_line = /cymbal_q3_exfil/ nocase



metadata.product_log_id = "64112"
metadata.event_timestamp.seconds = 1792095680
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
metadata.id = b"AAAAAIaKWnA6wsn/zb3sLjpC71EAAAAABgAAABgAAAA="
metadata.log_type = "WINDOWS_SYSMON"
metadata.base_labels.log_types = "WINDOWS_SYSMON"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.log_types = "WINDOWS_SYSMON"
metadata.enrichment_labels.namespaces = "Cymbal"
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "15.0"
additional.fields["UserID"] = "S-1-5-21-3849102931-1029384910-192837465-1089"
additional.fields["Keywords"] = "0x8000000000000000"
additional.fields["current_directory"] = "C:\\ProgramData\\"
principal.hostname = "CYM-DB-01.cymbal.corp"
principal.user.userid = "svc_dbadmin"
principal.process.pid = "3820"
principal.process.file.full_path = "C:\\Windows\\System32\\wsmprovhost.exe"
principal.process.command_line = "C:\\Windows\\system32\\wsmprovhost.exe -Embedding"
principal.process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-111122223333}"
principal.process.parent_process.pid = "810"
principal.process.parent_process.file.full_path = "C:\\Windows\\System32\\wsmprovhost.exe"
principal.process.parent_process.command_line = "C:\\Windows\\system32\\wsmprovhost.exe -Embedding"
principal.process.parent_process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-000000000001}"
principal.administrative_domain = "CYMBAL"
principal.namespace = "Cymbal"
principal.asset.hostname = "CYM-DB-01.cymbal.corp"
target.process.pid = "5812"
target.process.file.full_path = "C:\\ProgramData\\zstd.exe"
target.process.command_line = "C:\\ProgramData\\zstd.exe -3 -T0 -o C:\\ProgramData\\cymbal_q3_exfil.tar.zst C:\\ProgramData\\MSSQL\\Backup\\cymbal_cust_q3.bak"
target.process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-111122225555}"
target.namespace = "Cymbal"
observer.asset_id = "5770385F:C22A:43E0:BF4C:06F5698FFBD9"
observer.process.pid = "1024"
observer.namespace = "Cymbal"
security_result.rule_name = "technique_id=T1560.001,technique_name=Archive via Utility"
security_result.severity = "INFORMATIONAL"
security_result.rule_name = "EventID: 1"
extracted.fields["Event.EventData.Data[12].@Name"] = "ParentImage"
extracted.fields["Event.EventData.Data[0].#text"] = "technique_id=T1560.001,technique_name=Archive via Utility"
extracted.fields["Event.EventData.Data[12].#text"] = "C:\\Windows\\System32\\wsmprovhost.exe"
extracted.fields["Event.System.Task"] = "1"
extracted.fields["Event.System.Channel"] = "Microsoft-Windows-Sysmon/Operational"
extracted.fields["Event.System.TimeCreated.@SystemTime"] = "2026-10-15T20:21:20.000Z"
extracted.fields["Event.System.Security.@UserID"] = "S-1-5-21-3849102931-1029384910-192837465-1089"
extracted.fields["Event.EventData.Data[9].@Name"] = "LogonId"
extracted.fields["Event.EventData.Data[4].@Name"] = "Image"
extracted.fields["Event.EventData.Data[7].@Name"] = "User"
extracted.fields["Event.EventData.Data[2].@Name"] = "ProcessGuid"
extracted.fields["Event.System.Opcode"] = "0"
extracted.fields["Event.EventData.Data[6].@Name"] = "CurrentDirectory"
extracted.fields["Event.EventData.Data[8].#text"] = "{E1F2A3B4-0000-0000-0000-112233445566}"
extracted.fields["Event.EventData.Data[3].#text"] = "5812"
extracted.fields["Event.EventData.Data[1].#text"] = "2026-10-15 20:21:20.000"
extracted.fields["Event.EventData.Data[9].#text"] = "0x6E1F4"
extracted.fields["Event.EventData.Data[10].@Name"] = "ParentProcessGuid"
extracted.fields["Event.EventData.Data[4].#text"] = "C:\\ProgramData\\zstd.exe"
extracted.fields["Event.System.Provider.@Name"] = "Microsoft-Windows-Sysmon"
extracted.fields["Event.EventData.Data[2].#text"] = "{E1F2A3B4-C5D6-7890-0000-111122225555}"
extracted.fields["Event.System.EventID"] = "1"
extracted.fields["Event.System.Execution.@ProcessID"] = "1024"
extracted.fields["Event.EventData.Data[11].@Name"] = "ParentProcessId"
extracted.fields["Event.EventData.Data[5].#text"] = "C:\\ProgramData\\zstd.exe -3 -T0 -o C:\\ProgramData\\cymbal_q3_exfil.tar.zst C:\\ProgramData\\MSSQL\\Backup\\cymbal_cust_q3.bak"
extracted.fields["Event.EventData.Data[13].@Name"] = "ParentCommandLine"
extracted.fields["Event.@xmlns"] = "http://schemas.microsoft.com/win/2004/08/events/event"
extracted.fields["Event.EventData.Data[5].@Name"] = "CommandLine"
extracted.fields["Event.EventData.Data[8].@Name"] = "LogonGuid"
extracted.fields["Event.EventData.Data[11].#text"] = "3820"
extracted.fields["Event.System.Computer"] = "CYM-DB-01.cymbal.corp"
extracted.fields["Event.System.Keywords"] = "0x8000000000000000"
extracted.fields["Event.EventData.Data[14].#text"] = "CYMBAL\\svc_dbadmin"
extracted.fields["Event.System.EventRecordID"] = "64112"
extracted.fields["Event.EventData.Data[0].@Name"] = "RuleName"
extracted.fields["Event.EventData.Data[7].#text"] = "CYMBAL\\svc_dbadmin"
extracted.fields["Event.System.Version"] = "5"
extracted.fields["Event.System.Execution.@ThreadID"] = "1840"
extracted.fields["Event.System.Provider.@Guid"] = "{5770385F-C22A-43E0-BF4C-06F5698FFBD9}"
extracted.fields["Event.EventData.Data[13].#text"] = "C:\\Windows\\system32\\wsmprovhost.exe -Embedding"
extracted.fields["Event.EventData.Data[10].#text"] = "{E1F2A3B4-C5D6-7890-0000-111122223333}"
extracted.fields["Event.EventData.Data[3].@Name"] = "ProcessId"
extracted.fields["Event.EventData.Data[1].@Name"] = "UtcTime"
extracted.fields["Event.EventData.Data[6].#text"] = "C:\\ProgramData\\"
extracted.fields["Event.EventData.Data[14].@Name"] = "ParentUser"
extracted.fields["Event.System.Level"] = "4"

principal.hostname = "CYM-DB-01.cymbal.corp" AND (metadata.event_type = "NETWORK_HTTP" OR metadata.event_type = "NETWORK_CONNECTION") AND target.ip != "" AND NOT net.ip_in_range_cidr(target.ip, "10.0.0.0/8")

metadata.product_log_id = "64120"
metadata.event_timestamp.seconds = 1792097860
metadata.event_timestamp.nanos = 0
metadata.event_type = "NETWORK_CONNECTION"
metadata.vendor_name = "Microsoft"
metadata.product_name = "Microsoft-Windows-Sysmon"
metadata.product_event_type = "3"
metadata.ingested_timestamp.seconds = 1792098652
metadata.ingested_timestamp.nanos = 628595000
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.id = b"AAAAAIaKWnA6wsn/zb3sLjpC71EAAAAABgAAABoAAAA="
metadata.log_type = "WINDOWS_SYSMON"
metadata.base_labels.log_types = "WINDOWS_SYSMON"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "15.0"
additional.fields["UserID"] = "S-1-5-21-3849102931-1029384910-192837465-1089"
additional.fields["Keywords"] = "0x8000000000000000"
principal.hostname = "CYM-DB-01.cymbal.corp"
principal.user.userid = "svc_dbadmin"
principal.process.pid = "6140"
principal.process.file.full_path = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
principal.process.product_specific_process_id = "SYSMON:{E1F2A3B4-C5D6-7890-0000-111122226666}"
principal.ip = "10.240.12.100"
principal.port = 54912
principal.administrative_domain = "CYMBAL"
principal.namespace = "Cymbal"
principal.asset.hostname = "CYM-DB-01.cymbal.corp"
principal.asset.ip = "10.240.12.100"
target.hostname = "142.11.200.188"
target.ip = "142.11.200.188"
target.port = 8888
target.location.country_or_region = "United States"
target.location.region_latitude = 38.794594
target.location.region_longitude = -106.534836
target.location.region_coordinates.latitude = 38.794595199999996
target.location.region_coordinates.longitude = -106.5348379
target.namespace = "Cymbal"
target.asset.hostname = "142.11.200.188"
target.asset.ip = "142.11.200.188"
target.ip_geo_artifact.ip = "142.11.200.188"
target.ip_geo_artifact.location.country_or_region = "United States"
target.ip_geo_artifact.location.region_latitude = 38.794594
target.ip_geo_artifact.location.region_longitude = -106.534836
target.ip_geo_artifact.location.region_coordinates.latitude = 38.794595199999996
target.ip_geo_artifact.location.region_coordinates.longitude = -106.5348379
target.ip_geo_artifact.network.asn = "54290"
target.ip_geo_artifact.network.dns_domain = "hostwindsdns.com"
target.ip_geo_artifact.network.carrier_name = "hostpapa"
target.ip_geo_artifact.network.organization_name = "hostpapa"
observer.asset_id = "5770385F:C22A:43E0:BF4C:06F5698FFBD9"
observer.process.pid = "1024"
observer.namespace = "Cymbal"
security_result.rule_name = "technique_id=T1048,technique_name=Exfiltration Over Alternative Protocol"
security_result.action = "ALLOW"
security_result.severity = "INFORMATIONAL"
security_result.rule_name = "EventID: 3"
network.ip_protocol = "TCP"
network.direction = "OUTBOUND"
extracted.fields["Event.EventData.Data[9].@Name"] = "SourceHostname"
extracted.fields["Event.EventData.Data[11].#text"] = "142.11.200.188"
extracted.fields["Event.EventData.Data[0].@Name"] = "RuleName"
extracted.fields["Event.EventData.Data[3].@Name"] = "ProcessId"
extracted.fields["Event.EventData.Data[7].@Name"] = "Initiated"
extracted.fields["Event.System.Level"] = "4"
extracted.fields["Event.EventData.Data[11].@Name"] = "DestinationIp"
extracted.fields["Event.System.EventRecordID"] = "64120"
extracted.fields["Event.EventData.Data[8].@Name"] = "SourceIp"
extracted.fields["Event.EventData.Data[1].@Name"] = "UtcTime"
extracted.fields["Event.System.Opcode"] = "0"
extracted.fields["Event.EventData.Data[10].#text"] = "54912"
extracted.fields["Event.EventData.Data[13].@Name"] = "DestinationPort"
extracted.fields["Event.EventData.Data[6].#text"] = "tcp"
extracted.fields["Event.EventData.Data[1].#text"] = "2026-10-15 20:57:40.000"
extracted.fields["Event.EventData.Data[14].#text"] = "http-alt"
extracted.fields["Event.System.Keywords"] = "0x8000000000000000"
extracted.fields["Event.System.EventID"] = "3"
extracted.fields["Event.EventData.Data[12].#text"] = "142.11.200.188"
extracted.fields["Event.EventData.Data[13].#text"] = "8888"
extracted.fields["Event.System.Task"] = "3"
extracted.fields["Event.EventData.Data[2].#text"] = "{E1F2A3B4-C5D6-7890-0000-111122226666}"
extracted.fields["Event.EventData.Data[5].@Name"] = "User"
extracted.fields["Event.EventData.Data[10].@Name"] = "SourcePort"
extracted.fields["Event.EventData.Data[2].@Name"] = "ProcessGuid"
extracted.fields["Event.System.Computer"] = "CYM-DB-01.cymbal.corp"
extracted.fields["Event.EventData.Data[8].#text"] = "10.240.12.100"
extracted.fields["Event.EventData.Data[12].@Name"] = "DestinationHostname"
extracted.fields["Event.System.Execution.@ProcessID"] = "1024"
extracted.fields["Event.System.Provider.@Name"] = "Microsoft-Windows-Sysmon"
extracted.fields["Event.System.Channel"] = "Microsoft-Windows-Sysmon/Operational"
extracted.fields["Event.System.Execution.@ThreadID"] = "1840"
extracted.fields["Event.System.TimeCreated.@SystemTime"] = "2026-10-15T20:57:40.000Z"
extracted.fields["Event.@xmlns"] = "http://schemas.microsoft.com/win/2004/08/events/event"
extracted.fields["Event.EventData.Data[4].@Name"] = "Image"
extracted.fields["Event.EventData.Data[4].#text"] = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
extracted.fields["Event.EventData.Data[6].@Name"] = "Protocol"
extracted.fields["Event.EventData.Data[7].#text"] = "true"
extracted.fields["Event.System.Version"] = "5"
extracted.fields["Event.EventData.Data[0].#text"] = "technique_id=T1048,technique_name=Exfiltration Over Alternative Protocol"
extracted.fields["Event.EventData.Data[9].#text"] = "CYM-DB-01.cymbal.corp"
extracted.fields["Event.EventData.Data[14].@Name"] = "DestinationPortName"
extracted.fields["Event.EventData.Data[5].#text"] = "CYMBAL\\svc_dbadmin"
extracted.fields["Event.System.Provider.@Guid"] = "{5770385F-C22A-43E0-BF4C-06F5698FFBD9}"
extracted.fields["Event.System.Security.@UserID"] = "S-1-5-21-3849102931-1029384910-192837465-1089"
extracted.fields["Event.EventData.Data[3].#text"] = "6140"

target.ip = "142.11.200.188" AND metadata.event_type = "NETWORK_HTTP"

metadata.product_log_id = "9841285257713980003"
metadata.event_timestamp.seconds = 1792097880
metadata.event_timestamp.nanos = 0
metadata.event_type = "NETWORK_HTTP"
metadata.vendor_name = "Zscaler"
metadata.product_name = "NSS"
metadata.ingested_timestamp.seconds = 1792098652
metadata.ingested_timestamp.nanos = 938225000
metadata.ingestion_labels.key = "sourceFolder"
metadata.ingestion_labels.value = "Cymbal"
metadata.ingestion_labels.key = "replayedFrom"
metadata.ingestion_labels.value = "Demoverse"
metadata.id = b"AAAAAGD+UuRw0xSXljiknwi3wpsAAAAABQAAABQAAAA="
metadata.log_type = "ZSCALER_WEBPROXY"
metadata.base_labels.log_types = "ZSCALER_WEBPROXY"
metadata.base_labels.namespaces = "Cymbal"
metadata.base_labels.allow_scoped_access = true
metadata.enrichment_labels.allow_scoped_access = true
metadata.parser_version = "31.0"
additional.fields["fileclass"] = "None"
additional.fields["urlclass"] = "Uncategorized"
additional.fields["appclass"] = "General"
principal.user.userid = "svc_dbadmin"
principal.user.department = "IT Infrastructure & Operations"
principal.ip = "10.240.12.100"
principal.application = "General Browsing"
principal.location.name = "Denver HQ"
principal.namespace = "Cymbal"
principal.asset.ip = "10.240.12.100"
target.hostname = "142.11.200.188"
target.ip = "142.11.200.188"
target.port = 8888
target.url = "http://142.11.200.188:8888/upload/cymbal_q3_exfil.tar.zst"
target.location.country_or_region = "United States"
target.location.region_latitude = 38.794594
target.location.region_longitude = -106.534836
target.location.region_coordinates.latitude = 38.794595199999996
target.location.region_coordinates.longitude = -106.5348379
target.namespace = "Cymbal"
target.asset.hostname = "142.11.200.188"
target.asset.ip = "142.11.200.188"
target.ip_geo_artifact.ip = "142.11.200.188"
target.ip_geo_artifact.location.country_or_region = "United States"
target.ip_geo_artifact.location.region_latitude = 38.794594
target.ip_geo_artifact.location.region_longitude = -106.534836
target.ip_geo_artifact.location.region_coordinates.latitude = 38.794595199999996
target.ip_geo_artifact.location.region_coordinates.longitude = -106.5348379
target.ip_geo_artifact.network.asn = "54290"
target.ip_geo_artifact.network.dns_domain = "hostwindsdns.com"
target.ip_geo_artifact.network.carrier_name = "hostpapa"
target.ip_geo_artifact.network.organization_name = "hostpapa"
security_result.category_details = "Web Hosting"
security_result.category_details = "Information Technology"
security_result.action = "ALLOW"
security_result.action_details = "Allowed"
security_result.associations.name = "None"
network.sent_bytes = 485120000
network.received_bytes = 400
network.application_protocol = "HTTP"
network.http.method = "POST"
network.http.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
network.http.response_code = 200
network.http.parsed_user_agent.family = "USER_DEFINED"
network.http.parsed_user_agent.platform = "Windows"
network.http.parsed_user_agent.device = "x64"
network.http.parsed_user_agent.device_version = "5.0"
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


http://142.11.200.188:8888/upload/cymbal_q3_exfil.tar.zst