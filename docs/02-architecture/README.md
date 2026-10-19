# Kiến trúc

**Trạng thái:** local-first product direction được chốt; process boundaries và persistence chưa quyết định. Hiện có React/Vite fixture, Go Gateway, FastAPI và CLI; chưa có SSI integration, local auth hay persistence production.

- [System architecture](system-architecture.md)
- [Tech stack](tech-stack.md)
- [Repository structure](folder-structure.md)
- [ADR](decisions.md)
- [Glossary](../glossary.md)

V1 clone-and-run trên Windows, config/data thuộc local installation. SSI credentials chỉ được xử lý tại local service sau khi secret storage được thiết kế; browser chỉ gọi loopback API. Các lựa chọn cụ thể về process, storage, password security và launcher vẫn pending cho tới khi ADR được chấp nhận.
