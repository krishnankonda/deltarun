FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod ./
RUN go mod download
RUN go mod verify

COPY . .
RUN go build -o scraper .

FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /app/scraper .

CMD ["./scraper"]

