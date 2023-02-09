FROM golang:1.18-bullseye

RUN git clone https://github.com/AdguardTeam/dnsproxy.git
WORKDIR dnsproxy
RUN git checkout v0.43.1
RUN go build -mod=vendor

CMD ./dnsproxy -l 0.0.0.0 \
    --quic-port=853 \
    --tls-crt=/etc/dnsproxy/certs/dox.cer \
    --tls-key=/etc/dnsproxy/certs/dox.key \
    -u ns:53 \
    -p 0 \
