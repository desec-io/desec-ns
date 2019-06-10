#!/bin/bash

echo Preparing database configuration ...
envsubst < /etc/mysql/conf.d/51-server.cnf.var > /etc/mysql/conf.d/51-server.cnf

chgrp mysql /etc/ssl/private/*.pem

exec /docker-entrypoint.sh "$@"
