#!/bin/bash

# Route required for asking questions into the stack-side network via VPN
# Ths is assuming that the stack-side network prefix is 172.16
/sbin/ip route add 172.16.7.0/24 via 10.16.3.2

# Route to contact VPN client
/sbin/ip route add 10.8.0.0/24 via 10.16.3.2

echo mgroup from eth2 group 239.1.2.3 > /etc/smcroute.conf
/usr/sbin/smcroute -d

# Manage credentials
envsubst < /etc/powerdns/pdns.conf.var > /etc/powerdns/pdns.conf

# Fix ownership (may be off after importing a backup)
chown -R pdns:pdns /var/lib/powerdns

exec pdns_server --daemon=no
