#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${OUT_DIR:-/home/stickai/stickbot-voice/certs/m7d-https}"
LAN_IP="${LAN_IP:-192.168.1.107}"
DNS_NAME="${DNS_NAME:-localhost}"
DAYS="${DAYS:-30}"

case "$OUT_DIR" in /mnt/c/*|/mnt/c) echo "MNT_C_PATH_BLOCKED:$OUT_DIR" >&2; exit 31;; esac
case "$LAN_IP" in ''|*[!0-9.]* ) echo "INVALID_LAN_IP:$LAN_IP" >&2; exit 32;; esac
command -v openssl >/dev/null 2>&1 || { echo "OPENSSL_MISSING" >&2; exit 33; }

mkdir -p "$OUT_DIR"
chmod 700 "$OUT_DIR"

CA_KEY="$OUT_DIR/stickbot-tars-m7d-local-ca.key.pem"
CA_CERT="$OUT_DIR/stickbot-tars-m7d-local-ca.cert.pem"
SERVER_KEY="$OUT_DIR/stickbot-tars-m7d-server.key.pem"
SERVER_CSR="$OUT_DIR/stickbot-tars-m7d-server.csr.pem"
SERVER_CERT="$OUT_DIR/stickbot-tars-m7d-server.cert.pem"
EXT="$OUT_DIR/stickbot-tars-m7d-server.ext"
MANIFEST="$OUT_DIR/manifest.json"

if [ ! -s "$CA_KEY" ] || [ ! -s "$CA_CERT" ]; then
  openssl req -x509 -newkey rsa:3072 -sha256 -days "$DAYS" -nodes \
    -keyout "$CA_KEY" \
    -out "$CA_CERT" \
    -subj "/CN=Stickbot TARS M7D Local Dev CA" \
    -addext "basicConstraints=critical,CA:TRUE,pathlen:0" \
    -addext "keyUsage=critical,keyCertSign,cRLSign" \
    >/dev/null 2>&1
fi

cat > "$EXT" <<EOF
subjectAltName = IP:$LAN_IP,IP:127.0.0.1,DNS:$DNS_NAME,DNS:localhost
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
EOF

openssl req -newkey rsa:3072 -nodes \
  -keyout "$SERVER_KEY" \
  -out "$SERVER_CSR" \
  -subj "/CN=$LAN_IP" \
  >/dev/null 2>&1

openssl x509 -req -in "$SERVER_CSR" \
  -CA "$CA_CERT" \
  -CAkey "$CA_KEY" \
  -CAcreateserial \
  -out "$SERVER_CERT" \
  -days "$DAYS" \
  -sha256 \
  -extfile "$EXT" \
  >/dev/null 2>&1

chmod 600 "$CA_KEY" "$SERVER_KEY"
chmod 644 "$CA_CERT" "$SERVER_CERT"

python3 - <<PY
import json, pathlib, subprocess
out = pathlib.Path('$OUT_DIR')
files = {
  'caCert': pathlib.Path('$CA_CERT'),
  'serverCert': pathlib.Path('$SERVER_CERT'),
  'serverKey': pathlib.Path('$SERVER_KEY'),
}
def sha(p):
    return subprocess.check_output(['sha256sum', str(p)], text=True).split()[0]
manifest = {
  'classification': 'STICKBOT_TARS_M7D_LOCAL_HTTPS_CERT_READY_NEEDS_CLIENT_TRUST',
  'lanIp': '$LAN_IP',
  'dnsName': '$DNS_NAME',
  'days': int('$DAYS'),
  'outDir': str(out),
  'caCert': str(files['caCert']),
  'serverCert': str(files['serverCert']),
  'serverKey': str(files['serverKey']),
  'sha256': {name: sha(path) for name, path in files.items()},
  'trustRequired': 'Install/trust caCert on the client device/browser before expecting microphone permission on https LAN IP.'
}
pathlib.Path('$MANIFEST').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
PY

printf 'STICKBOT_TARS_M7D_LOCAL_HTTPS_CERT_READY_NEEDS_CLIENT_TRUST\n'
