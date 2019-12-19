#!/bin/bash
mkdir -p /dev/net
mknod /dev/net/tun c 10 200

# Rewrite source of outgoing packets (from ns or replicator)
iptables -t nat -A POSTROUTING -o tun0 -j MASQUERADE

envsubst < /etc/openvpn/client.conf.var > /etc/openvpn/client.conf
openvpn --config /etc/openvpn/client.conf
