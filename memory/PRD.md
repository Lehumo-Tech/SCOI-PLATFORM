# SCOI - SA Corruption OSINT Investigator

## Original Problem Statement
SCOI is a legally compliant, open-source intelligence (OSINT) platform for mapping corruption networks in South Africa. It ingests publicly available data, resolves entities, builds relationship graphs, applies pattern-detection rules, and generates auditable investigative reports.

## Architecture
- **Backend**: FastAPI + MongoDB (motor) + Python
- **Frontend**: React + TailwindCSS + Shadcn UI + @xyflow/react
- **Auth**: JWT + RBAC (Admin/Investigator/User)
- **Entity Resolution**: RapidFuzz + Phonetics
- **AI**: GPT-5.2 via Emergent Universal Key for report generation
- **Design**: Swiss Brutalist theme with IBM Plex Sans

## User Personas
1. **Admin**: Full access - data ingestion, audit logs, entity management
2. **Investigator**: Search, graph, asset tracing, red flag analysis, reports
3. **User**: Basic search and entity viewing

## Core Requirements (Static)
- POPIA-compliant data handling (hashed identifiers, audit trails)
- Public data only (no private/leaked datasets)
- No automated conclusions (patterns only, human verification required)
- Rate limiting and ethical scraping compliance
- Immutable audit logs for every action

## What's Been Implemented (2026-04-06)
- [x] JWT Auth with RBAC (admin/investigator/user)
- [x] Entity CRUD with fuzzy search (RapidFuzz)
- [x] 2-hop relationship graph traversal + React Flow visualization
- [x] Red Flag Detection Engine (5 rules: RAPID_TENDER, TRUST_SHIELD, DIRECTOR_ROTATION, ADDRESS_CLUSTER, FORFEITURE_AVOIDANCE)
- [x] Asset Tracing - pierce trust veils to link assets to individuals
- [x] Compliance audit logging for all actions
- [x] LLM-powered investigation report generation (GPT-5.2)
- [x] Mock data seeding (SA corruption patterns)
- [x] Admin data ingestion interface
- [x] Swiss Brutalist UI design

## Prioritized Backlog
### P0 (Critical)
- [ ] Real data source integration (CIPC, Government Gazette, eTender Portal)
- [ ] Increase LLM budget for report generation

### P1 (High)
- [ ] Celery + Redis for async ingestion workers
- [ ] PDF/CSV report export
- [ ] Entity deduplication pipeline
- [ ] Batch entity import

### P2 (Medium)
- [ ] Address cluster detection rule (full implementation)
- [ ] Forfeiture avoidance detection
- [ ] Trust shield rule implementation
- [ ] OpenTelemetry observability
- [ ] 24-month data retention policy enforcement

### P3 (Low)
- [ ] Prometheus/Grafana monitoring
- [ ] Role-based UI restrictions (investigator vs user)
- [ ] Unit/integration tests (>80% coverage)
- [ ] COMPLIANCE.md document

## Next Tasks
1. Integrate real CIPC API for company/director data
2. Build Government Gazette scraper (Scrapy)
3. Add PDF/CSV export for reports
4. Implement remaining red flag rules fully
5. Add entity merge/dedup workflow
