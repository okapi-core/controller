services:
  caddy:
    image: caddy:2
    depends_on:
      - frontend-proxy
    environment:
      OTEL_HOSTNAME: ${OTEL_HOSTNAME}
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - /opt/okapi-demo/caddy-otel/data:/data
      - /opt/okapi-demo/caddy-otel/config:/config
