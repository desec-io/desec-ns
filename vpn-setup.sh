#!/usr/bin/env bash

TARGET="$(pwd)"
cd "$(mktemp -d)" || exit
git clone -b v3.1.0 https://github.com/OpenVPN/easy-rsa.git
cat > easy-rsa/easyrsa3/vars << EOF
set_var EASYRSA_DN "cn_only"
set_var EASYRSA_KEY_SIZE 2048
set_var EASYRSA_BATCH    "yes"
EOF

(
  cd easy-rsa/easyrsa3 || exit
  ./easyrsa init-pki
  mv vars pki/
  ./easyrsa --batch --req-cn="ca@desec.example.com" build-ca nopass
  ./easyrsa --batch --req-cn="server@desec.example.com" build-server-full server nopass
  ./easyrsa --batch --req-cn="client@desec.example.com" build-client-full client nopass
  openvpn --genkey --secret pki/private/ta.key
  cd pki || exit
  mkdir "$TARGET/openvpn-server/secrets/" "$TARGET/openvpn-client/secrets/"
  # Distribute CA and TA
  cp ca.crt private/ca.key private/ta.key "$TARGET/openvpn-server/secrets/"
  cp ca.crt private/ca.key private/ta.key "$TARGET/openvpn-client/secrets/"
  # Distribute Server
  cp private/server.key issued/server.crt "$TARGET/openvpn-server/secrets/"
  # Distribute Client
  cp private/client.key issued/client.crt "$TARGET/openvpn-client/secrets/"
)

pwd
ls -lh easy-rsa/easyrsa3/pki/issued
