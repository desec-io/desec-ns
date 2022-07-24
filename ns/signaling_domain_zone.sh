#!/usr/bin/env bash

SIGNALING_DOMAIN="_signal.$DESEC_NS_NAME"

# Create Signaling Domain zone and sign with provided key
pdnsutil create-zone "$SIGNALING_DOMAIN" || exit  # quit if zone exists
pdnsutil replace-rrset "$SIGNALING_DOMAIN" "@" SOA \
    "${DESEC_NS_SIGNALING_DOMAIN_SOA_MNAME}. ${DESEC_NS_SIGNALING_DOMAIN_SOA_RNAME}. 0 86400 3600 2419200 3600"
pdnsutil import-zone-key "$SIGNALING_DOMAIN" <(base64 -d <<< "$DESEC_NS_SIGNALING_DOMAIN_ZONE_PRIVATE_KEY_B64")
pdnsutil unset-presigned "$SIGNALING_DOMAIN"
pdnsutil unset-nsec3 "$SIGNALING_DOMAIN"
pdnsutil rectify-zone "$SIGNALING_DOMAIN"

# Insert LUA records
function lua {
  echo "$1 \";require('signaling') return signal('$SIGNALING_DOMAIN', pdns.$1)\""
}
pdnsutil replace-rrset "$SIGNALING_DOMAIN" "*" LUA 1 "$(lua CDS)" "$(lua CDNSKEY)"
