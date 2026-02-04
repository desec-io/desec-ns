ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}cznic/knot:v3.5.3

RUN apt-get update && \
    apt-get install -y \
        python3-full python3-pip python3-venv \
        iproute2 \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

RUN mkdir /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt ./
RUN python3 -m venv .venv && ./.venv/bin/pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["/usr/src/app/entrypoint.sh"]
