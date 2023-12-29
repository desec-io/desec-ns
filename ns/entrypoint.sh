#!/usr/bin/env bash

# Route required for asking questions into the stack-side network via VPN
# Ths is assuming that the stack-side network prefix is 172.16
/sbin/ip route add 172.16.7.0/24 via 10.16.3.2

# Route to contact VPN client
/sbin/ip route add 10.8.0.0/24 via 10.16.3.2

echo mgroup from eth2 group 239.1.2.3 > /etc/smcroute.conf
/usr/sbin/smcroute -d

# Render configuration
envsubst < /etc/knot/knot.conf.var > /etc/knot/knot.conf

# TODO Create signaling domain zone if we have a private key
#[ -n "$DESEC_NS_SIGNALING_DOMAIN_ZONE_PRIVATE_KEY_B64" ] && \
#    su pdns -s /bin/bash -c /usr/bin/local/signaling_domain_zone.sh

# TODO Consider XDP, https://www.knot-dns.cz/docs/3.3/html/operation.html#pre-requisites

# Apply config to confdb
knotc conf-import -f /etc/knot/knot.conf +nopurge

# Start knot for production
exec knotd
