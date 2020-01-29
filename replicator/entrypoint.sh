#!/bin/sh

# Route required for asking questions via VPN
/sbin/ip route add 172.16.7.0/24 via 10.16.3.2

# Hardcode internal IP address for www service to make sure HTTPS goes through VPN
echo 172.16.7.4 ${DESECSTACK_VPN_SERVER} >> /etc/hosts

exec python -u run.py
