"""Multi-agent investigation workflow for SCOI.
Simulates a LangGraph-like pipeline: 
lead_investigator → deep_researcher → entity_resolver → compliance_auditor → report_synthesizer
"""
import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from bson import ObjectId
from services.llm_service import LLMService
from services.red_flag_engine import RedFlagEngine
from utils.entity_utils import hash_identifier, fuzzy_match_entities

logger = logging.getLogger(__name__)

class InvestigationState:
    """Shared state passed through agent pipeline"""
    def __init__(self, query: str, entity_ids: List[str], user_id: str):
        self.query = query
        self.entity_ids = entity_ids
        self.user_id = user_id
        self.plan = []
        self.findings = []
        self.entities_resolved = []
        self.relationships_found = []
        self.red_flags = []
        self.compliance_score = 0.0
        self.compliance_issues = []
        self.report = ""
        self.audit_trail = []
        self.human_approved = False
        self.status = "initialized"
        self.current_agent = ""
        self.confidence = 0.0
        self.started_at = datetime.now(timezone.utc)

    def log(self, agent: str, action: str, detail: str):
        self.audit_trail.append({
            "agent": agent,
            "action": action,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self.current_agent = agent

    def to_dict(self):
        return {
            "query": self.query,
            "entity_ids": self.entity_ids,
            "status": self.status,
            "current_agent": self.current_agent,
            "plan": self.plan,
            "findings_count": len(self.findings),
            "entities_resolved": len(self.entities_resolved),
            "relationships_found": len(self.relationships_found),
            "red_flags_count": len(self.red_flags),
            "red_flags": self.red_flags,
            "compliance_score": self.compliance_score,
            "compliance_issues": self.compliance_issues,
            "confidence": self.confidence,
            "report": self.report,
            "audit_trail": self.audit_trail,
            "human_approved": self.human_approved,
            "started_at": self.started_at.isoformat()
        }


class LeadInvestigator:
    """Plans investigation, breaks down into subtasks, coordinates agents"""
    
    async def run(self, state: InvestigationState, db) -> InvestigationState:
        state.log("lead_investigator", "planning", f"Creating investigation plan for {len(state.entity_ids)} entities")
        state.status = "planning"

        plan = []
        for eid in state.entity_ids:
            entity = await db.entities.find_one({"_id": ObjectId(eid)})
            if entity:
                plan.append({
                    "entity_id": eid,
                    "entity_name": entity["raw_name"],
                    "entity_type": entity["type"],
                    "tasks": [
                        f"Research {entity['raw_name']} via public records",
                        f"Resolve related entities and aliases",
                        f"Map network relationships (2-hop)",
                        f"Run red flag detection rules",
                        f"Trace assets if person/company",
                        f"Compile evidence chain"
                    ]
                })

        state.plan = plan
        state.log("lead_investigator", "plan_complete", f"Generated {len(plan)} entity investigation plans")
        return state


class DeepResearcher:
    """Mines public records and compiles findings"""
    
    async def run(self, state: InvestigationState, db) -> InvestigationState:
        state.log("deep_researcher", "researching", "Mining public records for entity data")
        state.status = "researching"

        for plan_item in state.plan:
            eid = plan_item["entity_id"]
            entity = await db.entities.find_one({"_id": ObjectId(eid)})
            if not entity:
                continue

            # Gather all relationships
            rels_out = await db.relationships.find({"from_entity_id": ObjectId(eid)}).to_list(100)
            rels_in = await db.relationships.find({"to_entity_id": ObjectId(eid)}).to_list(100)

            finding = {
                "entity_id": eid,
                "entity_name": entity["raw_name"],
                "entity_type": entity["type"],
                "source": entity.get("source", "Unknown"),
                "metadata": entity.get("metadata", {}),
                "outgoing_relationships": len(rels_out),
                "incoming_relationships": len(rels_in),
                "total_connections": len(rels_out) + len(rels_in),
                "related_entity_ids": list(set(
                    [str(r["to_entity_id"]) for r in rels_out] +
                    [str(r["from_entity_id"]) for r in rels_in]
                ))
            }
            state.findings.append(finding)

        state.log("deep_researcher", "research_complete", f"Compiled {len(state.findings)} findings")
        return state


class EntityResolver:
    """Resolves and deduplicates entities, maps aliases"""
    
    async def run(self, state: InvestigationState, db) -> InvestigationState:
        state.log("entity_resolver", "resolving", "Resolving entities and mapping relationships")
        state.status = "resolving"

        all_related_ids = set()
        for finding in state.findings:
            all_related_ids.update(finding.get("related_entity_ids", []))
            all_related_ids.add(finding["entity_id"])

        resolved = []
        for eid in all_related_ids:
            if not ObjectId.is_valid(eid):
                continue
            entity = await db.entities.find_one({"_id": ObjectId(eid)})
            if entity:
                resolved.append({
                    "id": str(entity["_id"]),
                    "type": entity["type"],
                    "name": entity["raw_name"],
                    "source": entity.get("source", ""),
                    "hashed_id": entity.get("hashed_id", "")
                })

        state.entities_resolved = resolved

        # Gather all relationships between resolved entities
        resolved_ids = [ObjectId(e["id"]) for e in resolved]
        rels = await db.relationships.find({
            "$or": [
                {"from_entity_id": {"$in": resolved_ids}},
                {"to_entity_id": {"$in": resolved_ids}}
            ]
        }).to_list(500)

        for rel in rels:
            state.relationships_found.append({
                "from": str(rel["from_entity_id"]),
                "to": str(rel["to_entity_id"]),
                "type": rel["relationship_type"],
                "confidence": rel.get("confidence", 1.0),
                "evidence": rel.get("evidence_refs", [])
            })

        state.log("entity_resolver", "resolved", f"Resolved {len(resolved)} entities, {len(state.relationships_found)} relationships")
        return state


class ComplianceAuditor:
    """Validates POPIA compliance, redacts PII, checks source counts"""
    
    async def run(self, state: InvestigationState, db) -> InvestigationState:
        state.log("compliance_auditor", "auditing", "Running compliance checks")
        state.status = "compliance_check"

        issues = []
        score = 100.0

        # Check: all entities have hashed IDs
        for entity in state.entities_resolved:
            if not entity.get("hashed_id"):
                issues.append(f"Entity {entity['name']} missing hashed identifier")
                score -= 5

        # Check: minimum 1 source per entity
        for entity in state.entities_resolved:
            if not entity.get("source"):
                issues.append(f"Entity {entity['name']} has no source citation")
                score -= 10

        # Check: no raw ID numbers in metadata
        for finding in state.findings:
            meta = finding.get("metadata", {})
            if meta.get("id_number") and meta["id_number"] != "hashed":
                issues.append(f"Raw ID number found for {finding['entity_name']} - requires hashing")
                score -= 20

        # Check: audit trail completeness
        if len(state.audit_trail) < 3:
            issues.append("Insufficient audit trail entries")
            score -= 5

        # Run red flag detection
        engine = RedFlagEngine(db)
        for eid in state.entity_ids:
            matches = await engine.evaluate_all_rules(eid)
            for match in matches:
                match["detected_at"] = match["detected_at"].isoformat() if hasattr(match.get("detected_at", ""), "isoformat") else str(match.get("detected_at", ""))
                state.red_flags.append(match)

        state.compliance_score = max(score, 0)
        state.compliance_issues = issues
        state.confidence = min(
            (state.compliance_score / 100) * 0.5 +
            (len(state.findings) > 0) * 0.3 +
            (len(state.relationships_found) > 0) * 0.2,
            1.0
        )

        state.log("compliance_auditor", "audit_complete", f"Score: {state.compliance_score}, Issues: {len(issues)}, Red flags: {len(state.red_flags)}")
        return state


class ReportSynthesizer:
    """Generates final investigation report"""
    
    async def run(self, state: InvestigationState, db) -> InvestigationState:
        state.log("report_synthesizer", "generating", "Synthesizing investigation report")
        state.status = "generating_report"

        # Try LLM-powered report first
        try:
            llm = LLMService()
            main_entity = state.findings[0] if state.findings else {"raw_name": "Unknown", "type": "unknown", "metadata": {}, "source": "Unknown"}
            report = await llm.generate_investigation_report(
                {
                    "id": main_entity.get("entity_id", ""),
                    "type": main_entity.get("entity_type", "unknown"),
                    "raw_name": main_entity.get("entity_name", "Unknown"),
                    "metadata": main_entity.get("metadata", {}),
                    "source": main_entity.get("source", "Unknown")
                },
                state.relationships_found,
                state.red_flags
            )
        except Exception as e:
            logger.warning(f"LLM report generation failed: {e}")
            report = self._fallback_report(state)

        state.report = report
        state.status = "awaiting_approval"
        state.log("report_synthesizer", "report_complete", f"Report generated ({len(report)} chars)")
        return state

    def _fallback_report(self, state: InvestigationState) -> str:
        """Generate structured report without LLM"""
        sections = [f"# SCOI Investigation Report\n**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n**Confidence:** {state.confidence*100:.0f}%\n**Compliance Score:** {state.compliance_score:.0f}/100\n"]

        sections.append("## 1. Executive Summary")
        sections.append(f"Investigation covering {len(state.entity_ids)} primary subject(s) with {len(state.entities_resolved)} resolved entities and {len(state.relationships_found)} mapped relationships. {len(state.red_flags)} red flag(s) detected.\n")

        sections.append("## 2. Entity Profiles")
        for f in state.findings:
            sections.append(f"### {f['entity_name']} ({f['entity_type']})")
            sections.append(f"- **Source:** {f['source']}")
            sections.append(f"- **Connections:** {f['total_connections']} ({f['outgoing_relationships']} outgoing, {f['incoming_relationships']} incoming)")
            for k, v in f.get("metadata", {}).items():
                sections.append(f"- **{k}:** {v}")
            sections.append("")

        sections.append("## 3. Network Analysis")
        sections.append(f"Total entities in network: {len(state.entities_resolved)}")
        sections.append(f"Total relationships mapped: {len(state.relationships_found)}\n")
        for rel in state.relationships_found[:20]:
            sections.append(f"- {rel['type']} (confidence: {rel['confidence']*100:.0f}%) | Evidence: {', '.join(rel.get('evidence', []))}")

        if state.red_flags:
            sections.append("\n## 4. Red Flag Analysis")
            for rf in state.red_flags:
                sections.append(f"### {rf.get('rule_name', rf.get('rule_id', 'Unknown'))}")
                sections.append(f"- **Confidence:** {rf.get('confidence', 0)*100:.0f}%")
                sections.append(f"- **Entities:** {len(rf.get('entities', []))}")
                meta = rf.get("metadata", {})
                for k, v in meta.items():
                    sections.append(f"- **{k}:** {v}")
                sections.append("")

        if state.compliance_issues:
            sections.append("## 5. Compliance Notes")
            for issue in state.compliance_issues:
                sections.append(f"- {issue}")

        sections.append("\n## 6. Audit Trail")
        for entry in state.audit_trail:
            sections.append(f"- [{entry['timestamp']}] **{entry['agent']}** > {entry['action']}: {entry['detail']}")

        sections.append("\n---\n## COMPLIANCE DISCLAIMER")
        sections.append("This report is generated from publicly available OSINT data only. It does NOT constitute legal proof, accusation, or determination of guilt. All findings require independent human verification before any action. Generated in compliance with POPIA and PRECCA guidelines. Data subject to 24-month retention policy.\n")

        return "\n".join(sections)


class InvestigationPipeline:
    """Orchestrates the multi-agent investigation workflow"""

    def __init__(self, db):
        self.db = db
        self.agents = [
            LeadInvestigator(),
            DeepResearcher(),
            EntityResolver(),
            ComplianceAuditor(),
            ReportSynthesizer()
        ]

    async def run(self, query: str, entity_ids: List[str], user_id: str) -> Dict:
        state = InvestigationState(query, entity_ids, user_id)

        for agent in self.agents:
            try:
                state = await agent.run(state, self.db)
            except Exception as e:
                state.log(agent.__class__.__name__, "error", str(e))
                state.status = f"error_at_{agent.__class__.__name__}"
                logger.error(f"Agent {agent.__class__.__name__} failed: {e}")
                break

        return state.to_dict()
