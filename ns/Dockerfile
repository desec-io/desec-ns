# TODO this dockerfile can probably be entirely removed after removal of watchio
FROM cznic/knot:latest

RUN set -ex && \
    apt-get update && \
    apt-get -y install python3 python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install inotify-simple  # TODO unused

COPY entrypoint watchio /usr/local/bin/
COPY knot.conf .
RUN mkdir -p /zones /rundir/knot/

CMD ["entrypoint"]
