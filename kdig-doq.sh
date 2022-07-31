#!/usr/bin/env sh

docker run -t --network "$(docker network ls | grep -oE 'desec-?ns_front')" cznic/knot:master \
  kdig +quic @dnsproxy "$@"
