#!/bin/bash
docker-compose -f docker-compose.yml -f docker-compose.dump.yml pull lmdb-backup
docker-compose -f docker-compose.yml -f docker-compose.dump.yml run lmdb-backup ./load "$1"
