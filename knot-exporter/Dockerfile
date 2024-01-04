ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}cznic/knot
# TODO fix version

RUN apt-get update \
    && apt-get install -y python3-pip python3-venv \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

RUN mkdir /usr/src/app
WORKDIR /usr/src/app

RUN python3 -m venv venv && ./venv/bin/pip install --no-cache-dir knot-exporter

EXPOSE 9433/TCP
USER knot

CMD ["/usr/src/app/venv/bin/knot-exporter", "--no-zone-stats", "--no-zone-status", "--no-zone-timers", "--no-zone-serial"]
