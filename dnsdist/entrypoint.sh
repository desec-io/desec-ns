#!/usr/bin/env bash

iptables -t nat -A PREROUTING -p udp --dport 853 -j DNAT --to-destination 10.16.0.3:853
iptables -t nat -A POSTROUTING -j MASQUERADE
ip6tables -t nat -A PREROUTING -p udp --dport 853 -j DNAT --to-destination "${DESEC_NS_IPV6_PREFIX}:3"
ip6tables -t nat -A POSTROUTING -j MASQUERADE

exec dnsdist --supervised
