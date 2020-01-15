#!/bin/bash

# Manage credentials
envsubst < /etc/powerdns/pdns.conf.var > /etc/powerdns/pdns.conf

ls /var/lib/powerdns/pdns.sqlite3 || sqlite3 /var/lib/powerdns/pdns.sqlite3 < /etc/powerdns/schema.sqlite3.sql
chown pdns /var/lib/powerdns/pdns.sqlite3
exec pdns_server --daemon=no
