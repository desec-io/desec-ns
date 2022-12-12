#!/usr/bin/env bash

iptables -t nat -A PREROUTING -p udp --dport 853 -j DNAT --to-destination 10.16.5.3:853
iptables -t nat -A POSTROUTING -j MASQUERADE

exec dnsdist --supervised -v
