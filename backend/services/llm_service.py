import os
from emergentintegrations.llm.chat import LlmChat, UserMessage
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

# Use cheapest available model
LLM_PROVIDER = "gemini"
LLM_MODEL = "gemini-2.5-flash-lite"

class LLMService:
    def __init__(self):
        self.api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment")
    
    def _create_chat(self, session_id: str, system_message: str) -> LlmChat:
        return LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=system_message
        ).with_model(LLM_PROVIDER, LLM_MODEL)
    
    async def _safe_send(self, chat: LlmChat, prompt: str) -> Optional[str]:
        """Send message with graceful budget/error fallback"""
        try:
            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            return response
        except Exception as e:
            error_msg = str(e)
            if "budget" in error_msg.lower() or "exceeded" in error_msg.lower():
                logger.warning(f"LLM budget exceeded: {error_msg}")
                return None
            logger.error(f"LLM call failed: {error_msg}")
            return None
    
    async def enhance_entity_matching(self, entity1: Dict, entity2: Dict) -> Dict:
        """Use LLM to determine if two entities are likely the same"""
        chat = self._create_chat(
            f"match_{entity1.get('id', 'x')}",
            "Entity resolution expert. Respond ONLY with JSON."
        )
        
        prompt = f"""Do these refer to the same entity? Entity 1: {entity1.get('raw_name')} ({entity1.get('type')}). Entity 2: {entity2.get('raw_name')} ({entity2.get('type')}). Reply JSON: {{"match":bool,"confidence":0-1,"reasoning":"brief"}}"""
        
        response = await self._safe_send(chat, prompt)
        if not response:
            return {"match": False, "confidence": 0.0, "reasoning": "LLM unavailable - budget exceeded or service error"}
        try:
            return json.loads(response)
        except:
            return {"match": False, "confidence": 0.0, "reasoning": "Parse error"}
    
    async def infer_relationships(self, entities: List[Dict]) -> List[Dict]:
        """Use LLM to infer potential relationships between entities"""
        if len(entities) < 2:
            return []
        
        chat = self._create_chat(
            f"rel_{len(entities)}",
            "Corruption network analyst. Respond ONLY with JSON array."
        )
        
        entities_brief = ", ".join([f"{e.get('raw_name')} ({e.get('type')})" for e in entities[:8]])
        prompt = f"""Identify relationships between: {entities_brief}. Reply JSON array: [{{"from_id":"id","to_id":"id","type":"rel","confidence":0-1,"reasoning":"brief"}}]. Empty [] if none."""
        
        response = await self._safe_send(chat, prompt)
        if not response:
            return []
        try:
            result = json.loads(response)
            return result if isinstance(result, list) else []
        except:
            return []
    
    async def generate_investigation_report(self, entity: Dict, relationships: List[Dict], red_flags: List[Dict]) -> str:
        """Generate investigation report with citations"""
        chat = self._create_chat(
            f"report_{entity.get('id', 'x')}",
            "Investigative analyst. Generate factual Markdown reports with citations."
        )
        
        rel_summary = f"{len(relationships)} relationships found" if relationships else "No relationships"
        flag_summary = json.dumps(red_flags[:5], default=str) if red_flags else "No red flags"
        
        prompt = f"""Investigation report for {entity.get('raw_name')} ({entity.get('type')}).
Source: {entity.get('source')}. Metadata: {json.dumps(entity.get('metadata', {}))}.
{rel_summary}. Red flags: {flag_summary}.
Generate Markdown: 1.Summary 2.Profile 3.Network 4.Red Flags 5.Sources 6.Compliance Warning (OSINT only, not legal)."""
        
        response = await self._safe_send(chat, prompt)
        if not response:
            return self._generate_fallback_report(entity, relationships, red_flags)
        return response
    
    async def analyze_watchlist_entity(self, entity: Dict, relationships: List[Dict]) -> Dict:
        """Quick analysis for watchlist alerts"""
        chat = self._create_chat(
            f"watch_{entity.get('id', 'x')}",
            "Alert analyst. Respond ONLY with JSON."
        )
        
        prompt = f"""Analyze {entity.get('raw_name')} ({entity.get('type')}) with {len(relationships)} connections. Any suspicious patterns? Reply JSON: {{"risk_level":"low/medium/high/critical","summary":"1 sentence","flags":["list"]}}"""
        
        response = await self._safe_send(chat, prompt)
        if not response:
            return {"risk_level": "unknown", "summary": "LLM unavailable", "flags": []}
        try:
            return json.loads(response)
        except:
            return {"risk_level": "unknown", "summary": response[:200], "flags": []}
    
    def _generate_fallback_report(self, entity: Dict, relationships: List[Dict], red_flags: List[Dict]) -> str:
        """Generate a basic report without LLM when budget is exceeded"""
        name = entity.get('raw_name', 'Unknown')
        etype = entity.get('type', 'unknown')
        source = entity.get('source', 'Unknown')
        metadata = entity.get('metadata', {})
        
        report = f"""# Investigation Report: {name}

## Executive Summary
This automated report covers entity **{name}** (type: {etype}) sourced from {source}.
{len(relationships)} relationship(s) and {len(red_flags)} red flag(s) identified.

## Entity Profile
- **Name:** {name}
- **Type:** {etype}
- **Source:** {source}
"""
        for k, v in metadata.items():
            report += f"- **{k}:** {v}\n"
        
        report += f"\n## Network Analysis\n{len(relationships)} relationship(s) detected.\n"
        for r in relationships[:10]:
            report += f"- {r.get('type', 'UNKNOWN')}: confidence {r.get('confidence', 'N/A')}\n"
        
        report += f"\n## Red Flag Analysis\n{len(red_flags)} flag(s) detected.\n"
        for f in red_flags[:10]:
            report += f"- **{f.get('rule_name', f.get('rule_id', 'Unknown'))}**: confidence {f.get('confidence', 'N/A')}\n"
        
        report += """
## Compliance Warning
This report is generated from publicly available OSINT data only. It does not constitute legal proof or accusation. Human verification required before any action. POPIA-compliant data handling in effect.

*Report generated without AI assistance (budget fallback mode).*
"""
        return report