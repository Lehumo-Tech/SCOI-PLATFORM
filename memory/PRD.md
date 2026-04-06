# SCOI - SA Corruption OSINT Investigator

## Original Problem Statement
SCOI is a legally compliant OSINT platform for mapping corruption networks in South Africa using publicly available data, entity resolution, relationship graphs, pattern detection, and auditable investigative reports.

## Architecture
- **Backend**: FastAPI + MongoDB (motor) + Python
- **Frontend**: React + TailwindCSS + Shadcn UI + @xyflow/react
- **Auth**: JWT + RBAC (Admin/Investigator/User)
- **Entity Resolution**: RapidFuzz (partial_ratio + token_sort) + Phonetics
- **AI**: Gemini 2.5 Flash Lite (cheapest) via Emergent Universal Key with budget fallback
- **Design**: Swiss Brutalist theme with IBM Plex Sans

## What's Been Implemented (2026-04-06)
- [x] JWT Auth with RBAC (admin/investigator/user) + brute force protection
- [x] Entity CRUD with fuzzy search (RapidFuzz partial + token sort)
- [x] 2-hop relationship graph traversal + React Flow visualization
- [x] Red Flag Detection Engine (5 rules: RAPID_TENDER, TRUST_SHIELD, DIRECTOR_ROTATION, ADDRESS_CLUSTER, FORFEITURE_AVOIDANCE)
- [x] Asset Tracing - pierce trust veils, nominee detection, link hidden assets to individuals
- [x] **Watchlist/Alert System** - monitor entities, auto-detect red flags, asset transfers, tender awards
- [x] Compliance audit logging for all actions
- [x] LLM-powered investigation report generation (Gemini 2.5 Flash Lite with fallback)
- [x] Mock data seeding (SA corruption patterns: 7 persons, 5 companies, 2 trusts, 5 tenders, 4 assets)
- [x] Admin data ingestion interface
- [x] Swiss Brutalist UI design
- [x] Offline project ZIP backup at /app/scoi-project.zip

## Prioritized Backlog
### P0 (Critical)
- [ ] Real data source integration (CIPC, Government Gazette, eTender Portal)
- [ ] LangGraph multi-agent system (lead_investigator, deep_researcher, document_analyst, entity_resolver, compliance_auditor, report_synthesizer)
- [ ] PDF/CSV report export with compliance footer

### P1 (High)
- [ ] Celery + Redis for async ingestion workers
- [ ] SearXNG integration for public record mining
- [ ] Entity deduplication pipeline
- [ ] Batch entity import
- [ ] Scheduled watchlist scanning (cron-based)

### P2 (Medium)
- [ ] Full ADDRESS_CLUSTER detection
- [ ] Full FORFEITURE_AVOIDANCE detection
- [ ] Full TRUST_SHIELD implementation
- [ ] OpenTelemetry observability
- [ ] 24-month data retention enforcement

### P3 (Low)
- [ ] Prometheus/Grafana monitoring
- [ ] Qdrant vector memory for long-term pattern recall
- [ ] COMPLIANCE.md document
- [ ] Unit/integration tests (>80% coverage)
