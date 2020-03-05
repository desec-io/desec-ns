FROM gcc:9 as builder

WORKDIR /usr/src/app
COPY ./build-lmdb.sh .
RUN ./build-lmdb.sh


FROM ubuntu:latest
COPY --from=builder /tmp/stage/usr/local/bin/* /usr/local/bin/

WORKDIR /usr/src/app
COPY ./dump ./load ./

RUN mkdir /backup /var/lib/powerdns
