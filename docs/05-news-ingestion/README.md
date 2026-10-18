# News engine

**Trạng thái:** separate future workstream. Product owner requested a project-built engine for international and Vietnamese news, with later integration into Research Terminal. It is not part of first market/portfolio MVP; current fixture news is synthetic.

The engine's future purpose is to discover, normalize, deduplicate, correct and link allowed news evidence to Vietnamese instruments/events. It needs its own source inventory, rights gates, local/remote operating model, retention, crawl/fetch constraints and output contract before implementation. Do not assume a page/RSS being reachable allows full-text storage, translation, ML or redistribution.

Current design references:

1. [Adapters and ingestion lifecycle](adapters-and-jobs.md).
2. [Deduplication, entities, events and corrections](intelligence-and-corrections.md).

These are conceptual material from the previous hosted product direction. Rewrite them for the standalone/local engine before using as implementation instructions. Later integration must keep provenance, publication/first-seen/correction times, source policy and partial/unavailable status. See [source register](../03-market-research/source-register.md).
