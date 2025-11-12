FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod ./
COPY . .
RUN go mod tidy
RUN go build -o cost-engine .

FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /app/cost-engine .

EXPOSE 8080

CMD ["./cost-engine"]

