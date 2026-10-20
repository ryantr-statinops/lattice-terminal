# Authentication / HTTP

Single local account configured by username/password in repository .env. API exposes auth/login, auth/status and auth/lock under /api/v1; there is no browser setup route. Argon2id verifier is held in memory; HttpOnly SameSite=Strict cookie, 30-minute session lifetime (including active SSE). Edit .env and restart to change credentials. Password is not disk encryption.

Go binds 127.0.0.1:8080, accepts localhost/127.0.0.1:8080 Host and requires allowed loopback Origin on mutating browser requests; dev allows 127.0.0.1:5173. Stop requires a local control token. Health/readiness/setup/status/login are public; private APIs need session auth. Headers: no-store/nosniff/no-referrer.

Python uses an ephemeral loopback port and internal bearer supplied through bootstrap, not browser assets. Proxy allows selected market/quant/source/data GETs and program inspection only. Unknown API returns 404, not SPA HTML. Gateway application JSON rejects trailing values/unknown fields with bounded bodies; financial values remain strings.

SSE persists/replays events with Last-Event-ID and checks session validity. Lock ends viewing, not jobs. User output may be private/sensitive; only explicit diagnostic summaries are redacted by construction.
