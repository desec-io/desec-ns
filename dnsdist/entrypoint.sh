#!/usr/bin/env bash

openssl req \
    -new \
    -newkey ec:<(openssl ecparam -name prime256v1) \
    -nodes \
    -keyout /etc/dnsdist/dot.key \
    -x509 \
    -days 3650 \
    -out /etc/dnsdist/dot.cer \
    -subj "/C=DE/ST=Berlin/L=Berlin/O=deSEC/OU=autocert/CN=$DESEC_NS_NAME" \
    -addext "subjectAltName = DNS:$DESEC_NS_NAME"

chmod 600 /etc/dnsdist/dot.key

exec dnsdist --supervised
