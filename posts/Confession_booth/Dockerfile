FROM golang:1.25-alpine AS builder

WORKDIR /app

RUN apk add --no-cache gcc musl-dev

COPY go.mod go.sum ./
RUN go mod download

COPY . ./

RUN CGO_ENABLED=0 go build -o /app/ctf-server .

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y postgresql postgresql-contrib sudo ca-certificates openssl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/ctf-server .

COPY entrypoint.sh .
COPY flag.txt /flag.txt

COPY templates/ ./templates/
COPY static/ ./static/

RUN chmod +x entrypoint.sh

EXPOSE 8080

CMD ["./entrypoint.sh"]