# Kiến trúc

**Trạng thái:** local-first product direction được chốt ngày 2026-10-18; implementation boundaries còn cần quyết định. Hiện có React/Vite fixture, Go Gateway, FastAPI và CLI; chưa có local SSI integration, auth hay persistence.

- [System architecture](system-architecture.md)
- [Tech stack](tech-stack.md)
- [Repository structure](folder-structure.md)
- [ADR](decisions.md)
- [Glossary](../glossary.md)

V1 clone-and-run trên Windows, mọi config/data tại local. SSI credentials chỉ thuộc local service boundary; browser chỉ gọi loopback API. Hosted auth, cloud database/storage, Vercel và Binance browser WebSocket là hướng cũ, không phải target hiện hành.
