# syntax=docker/dockerfile:1.7

FROM node:22.23.1-bookworm-slim AS web-build
WORKDIR /src
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
RUN npm ci
COPY apps/web apps/web
RUN npm run build --workspace=@kestrel-terminal/web

FROM ghcr.io/astral-sh/uv:0.11.28 AS uv-bin

FROM --platform=$TARGETPLATFORM python:3.12-slim-bookworm AS engine-build
COPY --from=uv-bin /uv /usr/local/bin/uv
WORKDIR /app
COPY services/engine/pyproject.toml services/engine/uv.lock services/engine/
COPY services/engine/kestrel_engine services/engine/kestrel_engine
RUN uv sync --project services/engine --python 3.12 --frozen --no-dev

FROM --platform=$BUILDPLATFORM golang:1.27.2-bookworm AS gateway-build
ARG TARGETOS
ARG TARGETARCH
WORKDIR /src
COPY services/gateway/go.mod services/gateway/go.sum ./
RUN go mod download
COPY services/gateway ./
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} go build -trimpath -ldflags="-s -w" -o /out/kestrel ./cmd/kestrel

FROM --platform=$TARGETPLATFORM python:3.12-slim-bookworm AS runtime
ENV KESTREL_LISTEN_ADDR=0.0.0.0:8080 \
    KESTREL_WEB_DIST=/app/apps/web/dist \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN groupadd --gid 10001 kestrel && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin kestrel \
    && mkdir -p /data
COPY --from=gateway-build --chown=10001:10001 /out/kestrel /app/kestrel
COPY --from=engine-build --chown=10001:10001 /app/services/engine /app/services/engine
COPY --from=web-build --chown=10001:10001 /src/apps/web/dist /app/apps/web/dist
ENV KESTREL_ENGINE_PYTHON=/app/services/engine/.venv/bin/python
EXPOSE 8080
USER 10001:10001
ENTRYPOINT ["/app/kestrel", "-root", "/app", "-data", "/data"]
