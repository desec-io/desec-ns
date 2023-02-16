ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}ubuntu:bionic

RUN apt-get update && apt-get install -y

RUN apt-get update \
	&& apt-get install -y build-essential git libssl-dev libldns-dev libck-dev libnghttp2-dev autoconf automake libtool pkg-config man \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/DNS-OARC/dnsperf.git \
    && cd dnsperf \
    && ./autogen.sh \
    && ./configure \
    && make \
    && make install
