# SCOI - SA Corruption OSINT Investigator v1.2

## Architecture
- **Backend**: FastAPI + MongoDB (motor) + Python
- **Frontend**: React + TailwindCSS + Shadcn UI + @xyflow/react
- **Auth**: JWT + RBAC (Admin/Investigator/User)
- **Entity Resolution**: RapidFuzz (partial_ratio + token_sort) + Phonetics
- **AI**: Gemini 2.5 Flash Lite (cheapest) via Emergent Universal Key with budget fallback
- **Design**: Swiss Brutalist theme with IBM Plex Sans

## What's Been Implemented (2026-04-06)
- [x] JWT Auth with RBAC (admin/investigator/user) + brute force protection
- [x] Entity CRUD with fuzzy search (RapidFuzz partial + token sort + substring)
- [x] 2-hop relationship graph traversal + React Flow visualization
- [x] Red Flag Detection Engine (5 rules: RAPID_TENDER, TRUST_SHIELD, DIRECTOR_ROTATION, ADDRESS_CLUSTER, FORFEITURE_AVOIDANCE)
- [x] Asset Tracing - pierce trust veils, nominee detection, hidden asset linking
- [x] Watchlist/Alert System - monitor entities, auto-detect red flags, asset transfers, tender awards
- [x] Multi-Agent Investigation Pipeline (5 agents: lead_investigator, deep_researcher, entity_resolver, compliance_auditor, report_synthesizer)
- [x] Human-in-the-loop approval gate for investigations
- [x] Investigation export (Markdown + CSV)
- [x] One-click ZIP download of entire project
- [x] Compliance audit logging for all actions
- [x] LLM-powered report generation (Gemini 2.5 Flash Lite with fallback)
- [x] Mock data seeding (SA corruption patterns)
- [x] Admin data ingestion interface
- [x] Swiss Brutalist UI design (8 tabs)

## Prioritized Backlog
### P0 (Critical)
- [ ] Real data source integration (CIPC, Government Gazette, eTender Portal)
- [ ] Scheduled watchlist scanning (cron-based daily alerts)
- [ ] PDF export with compliance footer

### P1 (High)
- [ ] Celery + Redis for async ingestion workers
- [ ] SearXNG integration for public record mining
- [ ] Entity deduplication pipeline
- [ ] Batch entity import (CSV/JSON)

### P2 (Medium)
- [ ] Full ADDRESS_CLUSTER, FORFEITURE_AVOIDANCE, TRUST_SHIELD rules
- [ ] OpenTelemetry observability
- [ ] 24-month data retention enforcement
- [ ] Qdrant vector memory for long-term pattern recall

### P3 (Low)
- [ ] Prometheus/Grafana monitoring
- [ ] COMPLIANCE.md document
- [ ] Unit/integration tests (>80% coverage)
