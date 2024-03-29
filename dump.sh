#!/bin/bash
docker-compose -f docker-compose.yml -f docker-compose.dump.yml up replicator  # exits replicator when done
docker-compose -f docker-compose.yml -f docker-compose.dump.yml down  # exits other containers as well
docker-compose -f docker-compose.yml -f docker-compose.dump.yml pull lmdb-backup
docker-compose -f docker-compose.yml -f docker-compose.dump.yml run lmdb-backup ./dump
docker-compose -f docker-compose.yml -f docker-compose.dump.yml down
