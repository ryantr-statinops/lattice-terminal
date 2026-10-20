# Kestrel Terminal — Documentation Hub

**2026-10-20: fixture development build.** Former prototype code was replaced. SSI production and real-market simulation remain blocked; synthetic tests do not approve them.

## Start here

1. [Rebuild decisions](13-rebuild/README.md) and [progress / limitations](13-rebuild/progress.md).
2. [Product](01-product/vision-and-scope.md), [constraints](CONSTRAINTS.md), [glossary](glossary.md).
3. [Architecture](02-architecture/system-architecture.md), [stack](02-architecture/tech-stack.md), [ADR](02-architecture/decisions.md).
4. [Source register](03-market-research/source-register.md), [SSI evidence](13-rebuild/ssi-evidence.md), [market rules](07-portfolio/vn-market-rules.md).
5. [Data](04-data/README.md), [market lifecycle](06-market-data/README.md), [Portfolio](07-portfolio/README.md).
6. [API](09-api/README.md), [UI](10-ui-ux/README.md), [engineering](11-engineering/README.md), [operations](12-operations/README.md).

News is a [separate design workstream](05-news-ingestion/README.md); [Model Lab](08-model-lab/README.md) is deferred. `_archive/` is historical design, not current runtime.

## Status vocabulary

Accepted = product/design decision. Implemented fixture = synthetic code path exists. Blocked = missing source/data/rules/operational evidence. Deferred = outside current build. External research retains its original review date; rebuilding code does not refresh or approve market evidence.
