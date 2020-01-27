#!/bin/sh

# Route required for asking questions via VPN
/sbin/ip route add 172.16.7.0/24 via 10.16.3.2

exec python -u run.py
