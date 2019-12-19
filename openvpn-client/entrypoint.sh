#!/bin/bash
mkdir -p /dev/net
mknod /dev/net/tun c 10 200


# Accept DNS packages for forwarding to ns
# See https://wiki.debian.org/de/Portweiterleitung for this and below iptables rules
iptables -A FORWARD -j ACCEPT -p udp --dport 53 -d 172.16.3.3 -m state --state NEW
iptables -A FORWARD -j ACCEPT -p tcp --dport 53 -d 172.16.3.3 -m state --state NEW

# Rewrite destination of incoming DNS packets
iptables -t nat -A PREROUTING -i tun0 -p udp --dport 53 -j DNAT --to-destination 172.16.3.3:53
iptables -t nat -A PREROUTING -i tun0 -p tcp --dport 53 -j DNAT --to-destination 172.16.3.3:53

# Rewrite source of outgoing packets (from ns or replicator)
iptables -t nat -A POSTROUTING -o tun0 -j MASQUERADE

envsubst < /etc/openvpn/client.conf.var > /etc/openvpn/client.conf
openvpn --config /etc/openvpn/client.conf
